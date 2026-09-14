"""Estado de los repositorios de una tarea y fechas de sus entregas (SPEC 08 S8.9,
S8.11; SPEC 09 S9.5; SPEC 13 S13.5.2; Etapa P8).

Nada de este modulo llama a Canvas ni a GitHub: lee lo que los trabajos dejaron
escrito (A-089). «Reintentar» y «sustituir» solo marcan y encolan (A-226).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adaptadores import aprovisionamiento_repo
from app.adaptadores.modelos_aprovisionamiento import (
    AccesoRepositorio,
    FechaEfectiva,
    ReglaFecha,
    Repositorio,
    Sujeto,
)
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_github import AccesoDocenteRepositorio
from app.adaptadores.modelos_mapeo import CuentaGithub
from app.adaptadores.modelos_padron import Estudiante, Seccion
from app.adaptadores.modelos_tarea import Entrega, Tarea
from app.api.dependencias import exigir_csrf, obtener_sesion_bd, requiere
from app.dominio.estados import EstadoFechaEfectiva
from app.dominio.fechas import formatear_fecha
from app.dominio.permisos import Permiso

router = APIRouter(tags=["repositorios"])


def _tarea(bd: Session, curso_id: uuid.UUID, tarea_id: uuid.UUID) -> Tarea:
    tarea = bd.query(Tarea).filter(Tarea.id == tarea_id, Tarea.curso_id == curso_id).one_or_none()
    if tarea is None:
        raise HTTPException(status_code=404)
    return tarea


class ResumenSalida(BaseModel):
    operativos: int
    degradados: int
    bloqueados: int
    esperando_limite: int
    error_transitorio: int
    error_permanente: int
    inaccesibles: int
    fuera_de_alcance: int
    archivados: int
    esperando_informacion: int
    listos_para_crear: int
    creando: int
    sujetos_activos: int
    sujetos_inactivos: int
    en_curso: bool
    creados: int
    minutos_restantes: int


class FilaRepositorioSalida(BaseModel):
    repositorio_id: uuid.UUID
    estudiante_id: uuid.UUID | None
    sujeto: str
    sujeto_activo: bool
    motivo_desactivacion: str | None
    nombre: str
    url_html: str | None
    estado: str
    motivo: str | None
    error_codigo: str | None
    error_mensaje_literal: str | None
    intentos: int
    proximo_intento_en: datetime | None
    cuenta_github: str | None
    acceso_estado: str | None
    acceso_error: str | None
    invitacion_url: str | None
    acceso_docente: str | None
    reemplaza_a_id: uuid.UUID | None
    listo_en: datetime | None


class RepositoriosSalida(BaseModel):
    resumen: ResumenSalida
    filas: list[FilaRepositorioSalida]


@router.get(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/repositorios", response_model=RepositoriosSalida
)
def listar_repositorios(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> RepositoriosSalida:
    """R2.3.11: una fila por sujeto con su estado traducible y su motivo."""
    tarea = _tarea(bd, curso_id, tarea_id)
    resumen = aprovisionamiento_repo.resumen_repositorios(bd, tarea_id=tarea.id)
    filas = []
    consulta = (
        bd.query(Repositorio, Sujeto, Estudiante)
        .join(Sujeto, Sujeto.id == Repositorio.sujeto_id)
        .outerjoin(Estudiante, Estudiante.id == Sujeto.estudiante_id)
        .filter(Repositorio.tarea_id == tarea.id)
        .order_by(Estudiante.nombre_ordenable, Estudiante.nombre, Repositorio.creado_en)
    )
    for repositorio, sujeto, estudiante in consulta:
        acceso = (
            bd.query(AccesoRepositorio)
            .filter(AccesoRepositorio.repositorio_id == repositorio.id)
            .first()
        )
        cuenta = (
            bd.get(CuentaGithub, acceso.cuenta_github_id)
            if acceso is not None and acceso.cuenta_github_id
            else None
        )
        docente = (
            bd.query(AccesoDocenteRepositorio)
            .filter(AccesoDocenteRepositorio.repositorio_id == repositorio.id)
            .first()
        )
        filas.append(
            FilaRepositorioSalida(
                repositorio_id=repositorio.id,
                estudiante_id=estudiante.id if estudiante is not None else None,
                sujeto=estudiante.nombre if estudiante is not None else "—",
                sujeto_activo=sujeto.activo,
                motivo_desactivacion=sujeto.motivo_desactivacion,
                nombre=repositorio.nombre,
                url_html=repositorio.url_html,
                estado=repositorio.estado,
                motivo=repositorio.motivo,
                error_codigo=repositorio.error_codigo,
                error_mensaje_literal=repositorio.error_mensaje_literal,
                intentos=repositorio.intentos,
                proximo_intento_en=repositorio.proximo_intento_en,
                cuenta_github=cuenta.login if cuenta is not None else None,
                acceso_estado=acceso.estado if acceso is not None else None,
                acceso_error=acceso.ultimo_error if acceso is not None else None,
                invitacion_url=acceso.invitacion_html_url if acceso is not None else None,
                acceso_docente=docente.estado if docente is not None else None,
                reemplaza_a_id=repositorio.reemplaza_a_id,
                listo_en=repositorio.listo_en,
            )
        )
    return RepositoriosSalida(resumen=ResumenSalida(**resumen.__dict__), filas=filas)


def _repositorio(bd: Session, tarea: Tarea, repositorio_id: uuid.UUID) -> Repositorio:
    repositorio = (
        bd.query(Repositorio)
        .filter(Repositorio.id == repositorio_id, Repositorio.tarea_id == tarea.id)
        .one_or_none()
    )
    if repositorio is None:
        raise HTTPException(status_code=404)
    return repositorio


@router.post(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/repositorios/{repositorio_id}/reintentar",
    status_code=202,
    dependencies=[Depends(exigir_csrf)],
)
def reintentar_repositorio(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    repositorio_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.TAREA_ADMINISTRAR)),
) -> dict[str, bool]:
    tarea = _tarea(bd, curso_id, tarea_id)
    try:
        aprovisionamiento_repo.reintentar(
            bd,
            repositorio=_repositorio(bd, tarea, repositorio_id),
            actor_usuario_id=membresia.usuario_id,
        )
    except aprovisionamiento_repo.AccionNoPermitida as exc:
        raise HTTPException(
            status_code=409, detail={"motivo": "NO_REINTENTABLE", "detalle": exc.detalle}
        ) from None
    return {"ok": True}


class SustituirEntrada(BaseModel):
    confirmacion: str


@router.post(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/repositorios/{repositorio_id}/sustituir",
    status_code=202,
    dependencies=[Depends(exigir_csrf)],
)
def sustituir_repositorio(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    repositorio_id: uuid.UUID,
    datos: SustituirEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.TAREA_ADMINISTRAR)),
) -> dict[str, str]:
    """S8.11.2: confirmacion escrita que nombra el repositorio perdido."""
    tarea = _tarea(bd, curso_id, tarea_id)
    repositorio = _repositorio(bd, tarea, repositorio_id)
    if datos.confirmacion.strip() != repositorio.nombre:
        raise HTTPException(
            status_code=422,
            detail={
                "motivo": "CONFIRMACION_INCORRECTA",
                "detalle": f"Para sustituirlo escribe exactamente el nombre: {repositorio.nombre}",
            },
        )
    try:
        nuevo = aprovisionamiento_repo.sustituir(
            bd, repositorio=repositorio, actor_usuario_id=membresia.usuario_id
        )
    except aprovisionamiento_repo.AccionNoPermitida as exc:
        raise HTTPException(
            status_code=409, detail={"motivo": "NO_SUSTITUIBLE", "detalle": exc.detalle}
        ) from None
    return {"repositorio_id": str(nuevo.id)}


class ExcepcionFechaSalida(BaseModel):
    origen: str
    etiqueta: str
    fecha: str


class FechasEntregaSalida(BaseModel):
    entrega_id: uuid.UUID
    nombre: str
    tipo: str
    orden: int
    cierre_base: str
    fechas_distintas: int
    excepciones: list[ExcepcionFechaSalida]
    sujetos_con_fecha: int
    sujetos_sin_fecha: int


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
    """R2.4.1-R2.4.3 en modo lectura (S9.5): «Cierre: ... · Sección 2: ... · N
    excepciones», con la zona del curso escrita."""
    tarea = _tarea(bd, curso_id, tarea_id)
    curso = bd.get(Curso, curso_id)
    assert curso is not None
    zona = curso.zona_horaria
    secciones = {
        s.canvas_section_id: s.nombre
        for s in bd.query(Seccion).filter(Seccion.curso_id == curso_id)
    }
    salida = []
    for entrega in bd.query(Entrega).filter(Entrega.tarea_id == tarea.id).order_by(Entrega.orden):
        excepciones = []
        for regla in bd.query(ReglaFecha).filter(
            ReglaFecha.entrega_id == entrega.id, ReglaFecha.alcance != "BASE"
        ):
            if regla.alcance == "SECCION":
                seccion = secciones.get(regla.canvas_section_id or 0, regla.canvas_section_id)
                etiqueta = f"Sección {seccion}"
            elif regla.alcance == "GRUPO":
                etiqueta = f"Grupo {regla.canvas_group_id}"
            else:
                etiqueta = f"Extensión individual ({len(regla.estudiante_ids)} estudiante/s)"
            excepciones.append(
                ExcepcionFechaSalida(
                    origen=regla.alcance,
                    etiqueta=etiqueta,
                    fecha=formatear_fecha(regla.due_at, zona),
                )
            )
        vigentes = (
            bd.query(FechaEfectiva)
            .filter(
                FechaEfectiva.entrega_id == entrega.id,
                FechaEfectiva.estado == EstadoFechaEfectiva.VIGENTE.value,
            )
            .all()
        )
        salida.append(
            FechasEntregaSalida(
                entrega_id=entrega.id,
                nombre=entrega.nombre,
                tipo=entrega.tipo,
                orden=entrega.orden,
                cierre_base=formatear_fecha(entrega.due_at_base, zona),
                fechas_distintas=len({f.due_at_utc for f in vigentes if f.due_at_utc is not None}),
                excepciones=excepciones,
                sujetos_con_fecha=sum(1 for f in vigentes if f.due_at_utc is not None),
                sujetos_sin_fecha=sum(1 for f in vigentes if f.due_at_utc is None),
            )
        )
    return salida
