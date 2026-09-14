"""Reglas de fecha y fecha efectiva materializada (SPEC 09 S9.3-S9.4; A-054,
A-055, A-056, A-082; Etapa P8, modo lectura).

La fuente de autoridad son los overrides del endpoint 14; la fila `BASE` sale
del propio assignment. Cambia la huella: se reescriben las reglas y se
recalculan las fechas por supersede, nunca en sitio (Ley 2).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.adaptadores.base import ahora_utc
from app.adaptadores.bitacora_repo import registrar as registrar_bitacora
from app.adaptadores.modelos_aprovisionamiento import FechaEfectiva, ReglaFecha, Sujeto
from app.adaptadores.modelos_padron import Estudiante, Grupo, Matricula, Seccion
from app.adaptadores.modelos_tarea import Entrega, VisibilidadEntrega
from app.dominio.estados import (
    AlcanceReglaFecha,
    EstadoFechaEfectiva,
    EstadoValidacionEntrega,
    TipoSujeto,
)
from app.dominio.fechas import ReglaFechaDatos, fecha_efectiva_individual, huella_reglas
from app.dominio.tareas_canvas import AssignmentCanvasCrudo, OverrideCanvasCrudo


def _fecha(valor: object) -> datetime | None:
    if not valor:
        return None
    return datetime.fromisoformat(str(valor).replace("Z", "+00:00"))


def _datos_desde_canvas(
    crudo: AssignmentCanvasCrudo, overrides: list[OverrideCanvasCrudo]
) -> list[ReglaFechaDatos]:
    base = ReglaFechaDatos(
        ref=("BASE", None),
        alcance=AlcanceReglaFecha.BASE,
        canvas_override_id=None,
        seccion_canvas_id=None,
        grupo_canvas_id=None,
        estudiante_canvas_ids=(),
        due_at=crudo.due_at,
        unlock_at=_fecha(crudo.payload.get("unlock_at")),
        lock_at=_fecha(crudo.payload.get("lock_at")),
        titulo=None,
    )
    reglas = [base]
    for o in overrides:
        if o.student_ids is not None:
            alcance = AlcanceReglaFecha.ESTUDIANTES
        elif o.group_id is not None:
            alcance = AlcanceReglaFecha.GRUPO
        else:
            alcance = AlcanceReglaFecha.SECCION
        reglas.append(
            ReglaFechaDatos(
                ref=("OVERRIDE", o.canvas_override_id),
                alcance=alcance,
                canvas_override_id=o.canvas_override_id,
                seccion_canvas_id=o.course_section_id,
                grupo_canvas_id=o.group_id,
                estudiante_canvas_ids=tuple(o.student_ids or ()),
                due_at=o.due_at,
                unlock_at=None,
                lock_at=None,
                titulo=o.titulo,
            )
        )
    return reglas


def sincronizar_fechas_entrega(
    bd: Session,
    *,
    curso_id: uuid.UUID,
    entrega: Entrega,
    crudo: AssignmentCanvasCrudo,
    overrides: list[OverrideCanvasCrudo],
) -> bool:
    """Devuelve `True` si la huella cambio y se reescribieron las reglas."""
    datos = _datos_desde_canvas(crudo, overrides)
    huella = huella_reglas(datos)
    if entrega.huella_fechas == huella:
        return False

    ahora = ahora_utc()
    secciones = {
        s.canvas_section_id: s.id for s in bd.query(Seccion).filter(Seccion.curso_id == curso_id)
    }
    grupos = {g.canvas_group_id: g.id for g in bd.query(Grupo).filter(Grupo.curso_id == curso_id)}
    existentes = bd.query(ReglaFecha).filter(ReglaFecha.entrega_id == entrega.id).all()
    usadas: list[ReglaFecha] = []
    for d in datos:
        # La BASE es una por entrega; un override se reconoce por su id aunque
        # haya cambiado de alcance en Canvas.
        if d.alcance == AlcanceReglaFecha.BASE:
            fila = next((r for r in existentes if r.alcance == AlcanceReglaFecha.BASE.value), None)
        else:
            fila = next(
                (r for r in existentes if r.canvas_override_id == d.canvas_override_id), None
            )
        if fila is None:
            fila = ReglaFecha(entrega_id=entrega.id, canvas_override_id=d.canvas_override_id)
            bd.add(fila)
        fila.alcance = d.alcance.value
        fila.canvas_section_id = d.seccion_canvas_id
        fila.canvas_group_id = d.grupo_canvas_id
        fila.seccion_id = secciones.get(d.seccion_canvas_id) if d.seccion_canvas_id else None
        fila.grupo_id = grupos.get(d.grupo_canvas_id) if d.grupo_canvas_id else None
        fila.estudiante_ids = list(d.estudiante_canvas_ids)
        fila.due_at = d.due_at
        fila.unlock_at = d.unlock_at
        fila.lock_at = d.lock_at
        fila.titulo = d.titulo
        fila.sincronizado_en = ahora
        usadas.append(fila)
    for fila in existentes:
        if not any(fila is usada for usada in usadas):
            bd.delete(fila)  # override retirado en Canvas; la fecha superseda conserva su instante

    habia_huella = entrega.huella_fechas is not None
    entrega.huella_fechas = huella
    bd.flush()
    if habia_huella:
        registrar_bitacora(
            bd,
            accion="FECHAS_ENTREGA_CAMBIARON",
            entidad="entrega",
            entidad_id=str(entrega.id),
            curso_id=curso_id,
            despues={"reglas": len(datos)},
        )
    recalcular_fechas_entrega(bd, curso_id=curso_id, entrega=entrega)
    return True


def _reglas_de_entrega(bd: Session, entrega_id: uuid.UUID) -> list[ReglaFechaDatos]:
    return [
        ReglaFechaDatos(
            ref=r.id,
            alcance=AlcanceReglaFecha(r.alcance),
            canvas_override_id=r.canvas_override_id,
            seccion_canvas_id=r.canvas_section_id,
            grupo_canvas_id=r.canvas_group_id,
            estudiante_canvas_ids=tuple(r.estudiante_ids or ()),
            due_at=r.due_at,
            unlock_at=r.unlock_at,
            lock_at=r.lock_at,
            titulo=r.titulo,
        )
        for r in bd.query(ReglaFecha).filter(ReglaFecha.entrega_id == entrega_id)
    ]


def recalcular_fechas_entrega(bd: Session, *, curso_id: uuid.UUID, entrega: Entrega) -> None:
    """Materializa la fecha de cada sujeto activo visible en la entrega. Un
    sujeto no visible no recibe fecha (S9.3.2); si tenia una, se supersede."""
    reglas = _reglas_de_entrega(bd, entrega.id)
    if not reglas:
        return  # la entrega aun no paso por un ciclo de sync_tareas_y_fechas
    ahora = ahora_utc()
    visibles = {
        v.estudiante_id
        for v in bd.query(VisibilidadEntrega).filter(
            VisibilidadEntrega.entrega_id == entrega.id, VisibilidadEntrega.visible.is_(True)
        )
    }
    secciones: dict[uuid.UUID, set[int]] = {}
    for estudiante_id, canvas_section_id in (
        bd.query(Matricula.estudiante_id, Seccion.canvas_section_id)
        .join(Seccion, Seccion.id == Matricula.seccion_id)
        .filter(Matricula.curso_id == curso_id, Matricula.activa.is_(True))
    ):
        secciones.setdefault(estudiante_id, set()).add(canvas_section_id)

    sujetos = (
        bd.query(Sujeto, Estudiante)
        .join(Estudiante, Estudiante.id == Sujeto.estudiante_id)
        .filter(
            Sujeto.tarea_id == entrega.tarea_id,
            Sujeto.tipo == TipoSujeto.ESTUDIANTE.value,
            Sujeto.activo.is_(True),
        )
        .all()
    )
    for sujeto, estudiante in sujetos:
        vigente = (
            bd.query(FechaEfectiva)
            .filter(
                FechaEfectiva.entrega_id == entrega.id,
                FechaEfectiva.sujeto_id == sujeto.id,
                FechaEfectiva.estado == EstadoFechaEfectiva.VIGENTE.value,
            )
            .one_or_none()
        )
        if estudiante.id not in visibles:
            if vigente is not None:
                vigente.estado = EstadoFechaEfectiva.SUPERSEDIDA.value
                vigente.vigente_hasta = ahora
            continue
        resultado = fecha_efectiva_individual(
            reglas=reglas,
            canvas_user_id=estudiante.canvas_user_id,
            canvas_section_ids=frozenset(secciones.get(estudiante.id, set())),
        )
        regla_id = resultado.regla_ref if isinstance(resultado.regla_ref, uuid.UUID) else None
        if (
            vigente is not None
            and vigente.due_at_utc == resultado.due_at_utc
            and vigente.origen == resultado.origen.value
            and vigente.ambigua == resultado.ambigua
        ):
            continue
        if vigente is not None:
            vigente.estado = EstadoFechaEfectiva.SUPERSEDIDA.value
            vigente.vigente_hasta = ahora
            bd.flush()
        bd.add(
            FechaEfectiva(
                entrega_id=entrega.id,
                sujeto_id=sujeto.id,
                due_at_utc=resultado.due_at_utc,
                origen=resultado.origen.value,
                regla_fecha_id=regla_id,
                ambigua=resultado.ambigua,
                calculada_en=ahora,
                estado=EstadoFechaEfectiva.VIGENTE.value,
            )
        )
    bd.flush()


def recalcular_fechas_tarea(bd: Session, *, curso_id: uuid.UUID, tarea_id: uuid.UUID) -> None:
    for entrega in bd.query(Entrega).filter(
        Entrega.tarea_id == tarea_id,
        Entrega.estado_validacion == EstadoValidacionEntrega.VIGENTE.value,
    ):
        recalcular_fechas_entrega(bd, curso_id=curso_id, entrega=entrega)


def fecha_cierre_primera_entrega(
    bd: Session, *, tarea_id: uuid.UUID, sujeto_id: uuid.UUID
) -> tuple[bool, datetime | None]:
    """S8.10.3: `(resuelta, instante)`. Resuelta = la fecha ya esta materializada
    para la primera entrega aplicable al sujeto; `None` como instante es «sin
    fecha de cierre», que tambien es un dato resuelto."""
    filas = (
        bd.query(Entrega.orden, FechaEfectiva.due_at_utc)
        .join(FechaEfectiva, FechaEfectiva.entrega_id == Entrega.id)
        .filter(
            Entrega.tarea_id == tarea_id,
            FechaEfectiva.sujeto_id == sujeto_id,
            FechaEfectiva.estado == EstadoFechaEfectiva.VIGENTE.value,
        )
        .order_by(Entrega.orden)
        .first()
    )
    if filas is None:
        return False, None
    return True, filas[1]
