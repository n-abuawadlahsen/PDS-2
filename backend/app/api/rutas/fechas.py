"""Fechas de cierre de las entregas: linea de fechas con excepciones y
historial (SPEC 09 S9.3-S9.5, S9.12; Etapa P8 en lectura, F3 completa).

Nada de este modulo llama a Canvas: lee `regla_fecha` y `fecha_efectiva`, que
solo escribe `sync_tareas_y_fechas` (Ley 1, CA-9.1-01). Todo instante sale con
la zona del curso escrita al lado (A-152, CA-9.5-01).
"""

from __future__ import annotations

import uuid
from collections.abc import Hashable
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adaptadores import fechas_repo
from app.adaptadores.modelos_aprovisionamiento import FechaEfectiva, ReglaFecha, Sujeto
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_padron import Estudiante, Grupo, Matricula, Seccion
from app.adaptadores.modelos_tarea import Entrega, Tarea
from app.api.dependencias import obtener_sesion_bd, requiere
from app.dominio.estados import AlcanceReglaFecha, EstadoFechaEfectiva, OrigenFechaEfectiva
from app.dominio.fechas import IntegranteFecha, candidatas_fecha, formatear_fecha
from app.dominio.permisos import Permiso

router = APIRouter(tags=["fechas"])


class ExcepcionFechaSalida(BaseModel):
    """Una excepcion de la linea de entregas (S9.5): etiqueta de origen, fecha,
    a quien alcanza y el `canvas_override_id` para copiarlo."""

    origen: str
    etiqueta: str
    fecha: str
    canvas_override_id: int | None
    titulo: str | None
    sujetos: list[str]


class CandidataSalida(BaseModel):
    origen: str
    etiqueta: str
    fecha: str
    canvas_override_id: int | None


class FechaAmbiguaSalida(BaseModel):
    """CA-9.5-03: la insignia «fecha ambigua» despliega todas las candidatas."""

    sujeto_id: uuid.UUID
    sujeto: str
    fecha: str
    candidatas: list[CandidataSalida]


class FechasEntregaSalida(BaseModel):
    entrega_id: uuid.UUID
    nombre: str
    tipo: str
    orden: int
    estado_validacion: str
    cierre_base: str
    fechas_distintas: int
    excepciones: list[ExcepcionFechaSalida]
    ambiguas: list[FechaAmbiguaSalida]
    sujetos_con_fecha: int
    sujetos_sin_fecha: int


class _Contexto:
    """Lo que la pantalla necesita del padron para nombrar sujetos y calcular
    candidatas, leido una sola vez por peticion."""

    def __init__(self, bd: Session, curso: Curso) -> None:
        self.zona = curso.zona_horaria
        self.secciones = {
            s.canvas_section_id: s.nombre
            for s in bd.query(Seccion).filter(Seccion.curso_id == curso.id)
        }
        estudiantes = bd.query(Estudiante).filter(Estudiante.curso_id == curso.id).all()
        self.por_canvas = {e.canvas_user_id: e for e in estudiantes}
        self.por_id = {e.id: e for e in estudiantes}
        self.secciones_de: dict[uuid.UUID, set[int]] = {}
        for estudiante_id, canvas_section_id in (
            bd.query(Matricula.estudiante_id, Seccion.canvas_section_id)
            .join(Seccion, Seccion.id == Matricula.seccion_id)
            .filter(Matricula.curso_id == curso.id, Matricula.activa.is_(True))
        ):
            self.secciones_de.setdefault(estudiante_id, set()).add(canvas_section_id)
        self.grupos = {
            g.canvas_group_id: g for g in bd.query(Grupo).filter(Grupo.curso_id == curso.id)
        }

    def etiqueta(self, origen: str, regla: ReglaFecha | None) -> str:
        """S9.5: `ADHOC` -> «Extension individual», `GRUPO` -> «Grupo X»,
        `SECCION` -> «Seccion X»."""
        if origen == OrigenFechaEfectiva.ADHOC.value:
            return "Extensión individual"
        if origen == OrigenFechaEfectiva.GRUPO.value and regla is not None:
            grupo = self.grupos.get(regla.canvas_group_id or 0)
            return f"Grupo {grupo.nombre if grupo else regla.canvas_group_id}"
        if origen == OrigenFechaEfectiva.SECCION.value and regla is not None:
            nombre = self.secciones.get(regla.canvas_section_id or 0, regla.canvas_section_id)
            return f"Sección {nombre}"
        return "Fecha base"

    def sujetos_de_regla(self, regla: ReglaFecha) -> list[str]:
        if regla.alcance == AlcanceReglaFecha.ESTUDIANTES.value:
            nombres = [
                self.por_canvas[i].nombre for i in regla.estudiante_ids if i in self.por_canvas
            ]
        elif regla.alcance == AlcanceReglaFecha.SECCION.value:
            nombres = [
                e.nombre
                for eid, secciones in self.secciones_de.items()
                if regla.canvas_section_id in secciones and (e := self.por_id.get(eid))
            ]
        else:
            grupo = self.grupos.get(regla.canvas_group_id or 0)
            nombres = [grupo.nombre] if grupo is not None else []
        return sorted(nombres)


def _curso(bd: Session, curso_id: uuid.UUID) -> Curso:
    curso = bd.get(Curso, curso_id)
    if curso is None:
        raise HTTPException(status_code=404)
    return curso


def _nombre_sujeto(bd: Session, sujeto: Sujeto) -> str:
    if sujeto.grupo_id is not None:
        grupo = bd.get(Grupo, sujeto.grupo_id)
        return grupo.nombre if grupo is not None else "—"
    estudiante = bd.get(Estudiante, sujeto.estudiante_id)
    return estudiante.nombre if estudiante is not None else "—"


def _candidatas(
    bd: Session, ctx: _Contexto, entrega: Entrega, sujeto: Sujeto
) -> list[CandidataSalida]:
    reglas = fechas_repo.reglas_vigentes(bd, entrega.id)
    por_ref: dict[Hashable, ReglaFecha] = {r.id: r for r in reglas}
    if sujeto.grupo_id is not None:
        grupo = bd.get(Grupo, sujeto.grupo_id)
        assert grupo is not None
        miembros = fechas_repo.integrantes_aceptados(bd, grupo.id)
        canvas_group_id: int | None = grupo.canvas_group_id
    else:
        estudiante = bd.get(Estudiante, sujeto.estudiante_id)
        miembros = [estudiante] if estudiante is not None else []
        canvas_group_id = None
    candidatas = candidatas_fecha(
        reglas=fechas_repo.datos_de_reglas(reglas),
        integrantes=[
            IntegranteFecha(
                canvas_user_id=m.canvas_user_id,
                canvas_section_ids=frozenset(ctx.secciones_de.get(m.id, set())),
            )
            for m in miembros
        ],
        canvas_group_id=canvas_group_id,
    )
    return [
        CandidataSalida(
            origen=c.origen.value,
            etiqueta=ctx.etiqueta(c.origen.value, por_ref.get(c.regla_ref)),
            fecha=formatear_fecha(c.due_at, ctx.zona),
            canvas_override_id=c.canvas_override_id,
        )
        for c in candidatas
    ]


@router.get(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/entregas/fechas",
    response_model=list[FechasEntregaSalida],
)
def fechas_de_entregas(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> list[FechasEntregaSalida]:
    """R2.4.1-R2.4.3 (S9.5): «Cierre: ... · Sección 2: ... · N excepciones»,
    con cada excepcion desplegable y las fechas ambiguas con sus candidatas."""
    tarea = bd.query(Tarea).filter(Tarea.id == tarea_id, Tarea.curso_id == curso_id).one_or_none()
    if tarea is None:
        raise HTTPException(status_code=404)
    ctx = _Contexto(bd, _curso(bd, curso_id))
    salida = []
    for entrega in bd.query(Entrega).filter(Entrega.tarea_id == tarea.id).order_by(Entrega.orden):
        excepciones = [
            ExcepcionFechaSalida(
                origen=(
                    OrigenFechaEfectiva.ADHOC.value
                    if regla.alcance == AlcanceReglaFecha.ESTUDIANTES.value
                    else regla.alcance
                ),
                etiqueta=ctx.etiqueta(
                    OrigenFechaEfectiva.ADHOC.value
                    if regla.alcance == AlcanceReglaFecha.ESTUDIANTES.value
                    else regla.alcance,
                    regla,
                ),
                fecha=formatear_fecha(regla.due_at, ctx.zona),
                canvas_override_id=regla.canvas_override_id,
                titulo=regla.titulo,
                sujetos=ctx.sujetos_de_regla(regla),
            )
            for regla in fechas_repo.reglas_vigentes(bd, entrega.id)
            if regla.alcance != AlcanceReglaFecha.BASE.value
        ]
        vigentes = (
            bd.query(FechaEfectiva, Sujeto)
            .join(Sujeto, Sujeto.id == FechaEfectiva.sujeto_id)
            .filter(
                FechaEfectiva.entrega_id == entrega.id,
                FechaEfectiva.estado == EstadoFechaEfectiva.VIGENTE.value,
            )
            .all()
        )
        ambiguas = sorted(
            (
                FechaAmbiguaSalida(
                    sujeto_id=sujeto.id,
                    sujeto=_nombre_sujeto(bd, sujeto),
                    fecha=formatear_fecha(fecha.due_at_utc, ctx.zona),
                    candidatas=_candidatas(bd, ctx, entrega, sujeto),
                )
                for fecha, sujeto in vigentes
                if fecha.ambigua
            ),
            key=lambda a: a.sujeto,
        )
        salida.append(
            FechasEntregaSalida(
                entrega_id=entrega.id,
                nombre=entrega.nombre,
                tipo=entrega.tipo,
                orden=entrega.orden,
                estado_validacion=entrega.estado_validacion,
                cierre_base=formatear_fecha(entrega.due_at_base, ctx.zona),
                fechas_distintas=len(
                    {f.due_at_utc for f, _ in vigentes if f.due_at_utc is not None}
                ),
                excepciones=excepciones,
                ambiguas=ambiguas,
                sujetos_con_fecha=sum(1 for f, _ in vigentes if f.due_at_utc is not None),
                sujetos_sin_fecha=sum(1 for f, _ in vigentes if f.due_at_utc is None),
            )
        )
    return salida


class FechaHistorialSalida(BaseModel):
    fecha: str
    due_at_utc: datetime | None
    origen: str
    etiqueta: str
    canvas_override_id: int | None
    override_titulo: str | None
    override_retirado: bool
    ambigua: bool
    estado: str
    calculada_en: datetime
    vigente_hasta: datetime | None


class HistorialSujetoSalida(BaseModel):
    sujeto_id: uuid.UUID
    sujeto: str
    fechas: list[FechaHistorialSalida]


@router.get(
    "/api/cursos/{curso_id}/entregas/{entrega_id}/historial-fechas",
    response_model=list[HistorialSujetoSalida],
)
def historial_fechas(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> list[HistorialSujetoSalida]:
    """S9.4.1: el encadenamiento de `fecha_efectiva` por sujeto **es** el
    historial de cambios de fecha; no hay una tabla aparte."""
    entrega = (
        bd.query(Entrega)
        .filter(Entrega.id == entrega_id, Entrega.curso_id == curso_id)
        .one_or_none()
    )
    if entrega is None:
        raise HTTPException(status_code=404)
    ctx = _Contexto(bd, _curso(bd, curso_id))
    por_sujeto: dict[uuid.UUID, list[FechaHistorialSalida]] = {}
    sujetos: dict[uuid.UUID, Sujeto] = {}
    filas = (
        bd.query(FechaEfectiva, Sujeto, ReglaFecha)
        .join(Sujeto, Sujeto.id == FechaEfectiva.sujeto_id)
        .outerjoin(ReglaFecha, ReglaFecha.id == FechaEfectiva.regla_fecha_id)
        .filter(FechaEfectiva.entrega_id == entrega.id)
        .order_by(FechaEfectiva.calculada_en, FechaEfectiva.id)
    )
    for fecha, sujeto, regla in filas:
        sujetos[sujeto.id] = sujeto
        por_sujeto.setdefault(sujeto.id, []).append(
            FechaHistorialSalida(
                fecha=formatear_fecha(fecha.due_at_utc, ctx.zona),
                due_at_utc=fecha.due_at_utc,
                origen=fecha.origen,
                etiqueta=ctx.etiqueta(fecha.origen, regla),
                canvas_override_id=regla.canvas_override_id if regla is not None else None,
                override_titulo=regla.titulo if regla is not None else None,
                override_retirado=regla is not None and regla.retirada_en is not None,
                ambigua=fecha.ambigua,
                estado=fecha.estado,
                calculada_en=fecha.calculada_en,
                vigente_hasta=fecha.vigente_hasta,
            )
        )
    return sorted(
        (
            HistorialSujetoSalida(
                sujeto_id=sid, sujeto=_nombre_sujeto(bd, sujetos[sid]), fechas=fechas
            )
            for sid, fechas in por_sujeto.items()
        ),
        key=lambda h: h.sujeto,
    )
