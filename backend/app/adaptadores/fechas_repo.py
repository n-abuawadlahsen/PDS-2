"""Reglas de fecha y fecha efectiva materializada (SPEC 09 S9.3-S9.4; A-054,
A-055, A-056, A-082; Etapa P8 en lectura, F3 con excepciones completas).

F3: toda fecha ambigua abre incidencia (`ESTUDIANTE_EN_DOS_SECCIONES` o
`DISCREPANCIA_FECHAS`), un override con datos sucios abre
`OVERRIDE_NO_INTERPRETABLE`, y un cambio solo cosmetico (el titulo) se
actualiza en silencio, sin historial ni bitacora (S9.4.3).

La fuente de autoridad son los overrides del endpoint 14; la fila `BASE` sale
del propio assignment. Cambia la huella: se reescriben las reglas y se
recalculan las fechas por supersede, nunca en sitio (Ley 2).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.adaptadores import comunicaciones_repo, incidencia_repo, trabajos_repo, versiones_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.bitacora_repo import registrar as registrar_bitacora
from app.adaptadores.modelos_aprovisionamiento import FechaEfectiva, ReglaFecha, Sujeto
from app.adaptadores.modelos_padron import (
    Estudiante,
    Grupo,
    Matricula,
    PertenenciaGrupo,
    Seccion,
)
from app.adaptadores.modelos_tarea import Entrega, Tarea, VisibilidadEntrega
from app.dominio.estados import (
    AlcanceReglaFecha,
    EstadoFechaEfectiva,
    EstadoValidacionEntrega,
    ModalidadTarea,
    TipoSujeto,
    WorkflowStatePertenenciaGrupo,
)
from app.dominio.fechas import (
    IntegranteFecha,
    ReglaFechaDatos,
    ResultadoFecha,
    fecha_efectiva_grupal,
    fecha_efectiva_individual,
    huella_reglas,
    incidencia_de_fecha,
    overrides_no_interpretables,
)
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
        _actualizar_titulos(bd, entrega, datos)
        _revisar_overrides(bd, curso_id=curso_id, entrega=entrega)
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
        fila.retirada_en = None
        usadas.append(fila)
    for fila in existentes:
        if not any(fila is usada for usada in usadas) and fila.retirada_en is None:
            # Override retirado en Canvas: se marca, nunca se borra (Ley 2).
            fila.retirada_en = ahora

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
    _revisar_overrides(bd, curso_id=curso_id, entrega=entrega)
    # S10.6.6: las ventanas no se persisten; el recomputo las deja correctas.
    trabajos_repo.encolar(
        bd,
        tipo="agregar_metricas",
        clave_idempotencia=f"metricas:{curso_id}:fechas:{entrega.id}:{huella.hex()}",
        max_intentos=2,
        curso_id=curso_id,
    )
    return True


def _actualizar_titulos(bd: Session, entrega: Entrega, datos: list[ReglaFechaDatos]) -> None:
    """CA-9.4-02: el `title` de un override es cosmetico. Se actualiza en
    silencio, sin fila nueva de `fecha_efectiva` ni entrada en bitacora."""
    titulos = {d.canvas_override_id: d.titulo for d in datos if d.canvas_override_id}
    for fila in reglas_vigentes(bd, entrega.id):
        if fila.canvas_override_id in titulos and fila.titulo != titulos[fila.canvas_override_id]:
            fila.titulo = titulos[fila.canvas_override_id]
    bd.flush()


def _revisar_overrides(bd: Session, *, curso_id: uuid.UUID, entrega: Entrega) -> None:
    """S9.3.5: se revisa en cada ciclo, porque un dato sucio puede arreglarse
    sin que cambie la huella (llega la seccion en el roster siguiente). La
    primera vez que aparece una seccion desconocida se encola un `sync_roster`
    prioritario; mientras siga, la incidencia cuenta los ciclos."""
    tarea = bd.get(Tarea, entrega.tarea_id)
    assert tarea is not None
    grupos: set[int] | None = None
    if tarea.modalidad == ModalidadTarea.GRUPAL.value:
        grupos = {
            g.canvas_group_id
            for g in bd.query(Grupo).filter(Grupo.conjunto_grupos_id == tarea.conjunto_grupos_id)
        }
    hallazgos = overrides_no_interpretables(
        _reglas_de_entrega(bd, entrega.id),
        secciones_conocidas={
            s.canvas_section_id for s in bd.query(Seccion).filter(Seccion.curso_id == curso_id)
        },
        estudiantes_conocidos={
            e.canvas_user_id for e in bd.query(Estudiante).filter(Estudiante.curso_id == curso_id)
        },
        grupos_de_la_tarea=grupos,
    )
    if not hallazgos:
        incidencia_repo.cerrar(
            bd, tipo="OVERRIDE_NO_INTERPRETABLE", curso_id=curso_id, sujeto_id=entrega.id
        )
        return
    abierta = incidencia_repo.abierta(
        bd, tipo="OVERRIDE_NO_INTERPRETABLE", curso_id=curso_id, sujeto_id=entrega.id
    )
    ciclos = int(abierta.detalle.get("ciclos", 0)) + 1 if abierta is not None else 1
    if abierta is None and any(h.motivo == "SECCION_DESCONOCIDA" for h in hallazgos):
        trabajos_repo.encolar(
            bd,
            tipo="sync_roster",
            clave_idempotencia=f"roster_por_override:{curso_id}:{ahora_utc().date().isoformat()}",
            max_intentos=4,
            curso_id=curso_id,
        )
    incidencia_repo.abrir_o_actualizar(
        bd,
        tipo="OVERRIDE_NO_INTERPRETABLE",
        severidad="ADVERTENCIA",
        sujeto_tipo="ENTREGA",
        curso_id=curso_id,
        sujeto_id=entrega.id,
        detalle={
            "entrega": entrega.nombre,
            "ciclos": ciclos,
            "overrides": [
                {"canvas_override_id": h.canvas_override_id, "motivo": h.motivo} for h in hallazgos
            ],
        },
    )


def _reglas_de_entrega(bd: Session, entrega_id: uuid.UUID) -> list[ReglaFechaDatos]:
    return datos_de_reglas(reglas_vigentes(bd, entrega_id))


def datos_de_reglas(reglas: list[ReglaFecha]) -> list[ReglaFechaDatos]:
    """Las filas persistidas, en la forma que consume el dominio (`ref` = id)."""
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
        for r in reglas
    ]


def reglas_vigentes(bd: Session, entrega_id: uuid.UUID) -> list[ReglaFecha]:
    """Las reglas que Canvas sigue declarando (sin las retiradas)."""
    return (
        bd.query(ReglaFecha)
        .filter(ReglaFecha.entrega_id == entrega_id, ReglaFecha.retirada_en.is_(None))
        .order_by(ReglaFecha.canvas_override_id.nulls_first())
        .all()
    )


def recalcular_fechas_entrega(bd: Session, *, curso_id: uuid.UUID, entrega: Entrega) -> None:
    """Materializa la fecha de cada sujeto activo visible en la entrega. Un
    sujeto no visible no recibe fecha (S9.3.2); si tenia una, se supersede.

    Sujeto grupal (S9.3.3): visible si lo es alguno de sus integrantes
    `accepted`; su fecha es el maximo de la cadena de cada uno de ellos."""
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
        bd.query(Sujeto).filter(Sujeto.tarea_id == entrega.tarea_id, Sujeto.activo.is_(True)).all()
    )
    for sujeto in sujetos:
        resultado: ResultadoFecha | None
        if sujeto.tipo == TipoSujeto.GRUPO.value:
            grupo = bd.get(Grupo, sujeto.grupo_id)
            assert grupo is not None
            integrantes = [
                IntegranteFecha(
                    canvas_user_id=e.canvas_user_id,
                    canvas_section_ids=frozenset(secciones.get(e.id, set())),
                )
                for e in integrantes_aceptados(bd, grupo.id)
                if e.id in visibles
            ]
            resultado = fecha_efectiva_grupal(
                reglas=reglas, canvas_group_id=grupo.canvas_group_id, integrantes=integrantes
            )
        else:
            estudiante = bd.get(Estudiante, sujeto.estudiante_id)
            assert estudiante is not None
            resultado = (
                fecha_efectiva_individual(
                    reglas=reglas,
                    canvas_user_id=estudiante.canvas_user_id,
                    canvas_section_ids=frozenset(secciones.get(estudiante.id, set())),
                )
                if estudiante.id in visibles
                else None
            )
        _materializar(bd, entrega=entrega, sujeto=sujeto, resultado=resultado, ahora=ahora)
        bd.flush()
        _registrar_incidencia_de_fecha(
            bd, curso_id=curso_id, entrega=entrega, sujeto=sujeto, resultado=resultado
        )
    bd.flush()


_TIPOS_INCIDENCIA_FECHA = ("ESTUDIANTE_EN_DOS_SECCIONES", "DISCREPANCIA_FECHAS")


def _registrar_incidencia_de_fecha(
    bd: Session,
    *,
    curso_id: uuid.UUID,
    entrega: Entrega,
    sujeto: Sujeto,
    resultado: ResultadoFecha | None,
) -> None:
    """S9.3.2: una fecha ambigua siempre abre incidencia, una por sujeto. Se
    cierra cuando ya no queda ninguna fecha vigente ambigua de ese sujeto en
    ninguna entrega de la tarea."""
    hallazgo = incidencia_de_fecha(resultado) if resultado is not None else None
    if hallazgo is not None:
        tipo, detalle = hallazgo
        incidencia_repo.abrir_o_actualizar(
            bd,
            tipo=tipo,
            severidad="ADVERTENCIA",
            sujeto_tipo="SUJETO",
            curso_id=curso_id,
            sujeto_id=sujeto.id,
            detalle={**detalle, "entrega_id": str(entrega.id), "entrega": entrega.nombre},
        )
        return
    queda_ambigua = (
        bd.query(FechaEfectiva.id)
        .filter(
            FechaEfectiva.sujeto_id == sujeto.id,
            FechaEfectiva.estado == EstadoFechaEfectiva.VIGENTE.value,
            FechaEfectiva.ambigua.is_(True),
        )
        .first()
    )
    if queda_ambigua is None:
        for tipo in _TIPOS_INCIDENCIA_FECHA:
            incidencia_repo.cerrar(bd, tipo=tipo, curso_id=curso_id, sujeto_id=sujeto.id)


def integrantes_aceptados(bd: Session, grupo_id: uuid.UUID) -> list[Estudiante]:
    """A-048: solo cuenta quien esta `accepted` en la pertenencia vigente."""
    return (
        bd.query(Estudiante)
        .join(PertenenciaGrupo, PertenenciaGrupo.estudiante_id == Estudiante.id)
        .filter(
            PertenenciaGrupo.grupo_id == grupo_id,
            PertenenciaGrupo.activa.is_(True),
            PertenenciaGrupo.workflow_state == WorkflowStatePertenenciaGrupo.ACCEPTED.value,
        )
        .all()
    )


def _materializar(
    bd: Session,
    *,
    entrega: Entrega,
    sujeto: Sujeto,
    resultado: ResultadoFecha | None,
    ahora: datetime,
) -> None:
    """Ley 2: nunca en sitio. `resultado = None` = el sujeto no es visible en
    la entrega: la fecha vigente, si la habia, se supersede sin sustituta."""
    vigente = (
        bd.query(FechaEfectiva)
        .filter(
            FechaEfectiva.entrega_id == entrega.id,
            FechaEfectiva.sujeto_id == sujeto.id,
            FechaEfectiva.estado == EstadoFechaEfectiva.VIGENTE.value,
        )
        .one_or_none()
    )
    if resultado is None:
        if vigente is not None:
            vigente.estado = EstadoFechaEfectiva.SUPERSEDIDA.value
            vigente.vigente_hasta = ahora
            versiones_repo.al_cambiar_la_fecha(
                bd,
                entrega_id=entrega.id,
                sujeto_id=sujeto.id,
                fecha_anterior=vigente.due_at_utc,
                fecha_nueva=None,
            )
        return
    if (
        vigente is not None
        and vigente.due_at_utc == resultado.due_at_utc
        and vigente.origen == resultado.origen.value
        and vigente.ambigua == resultado.ambigua
    ):
        return
    if vigente is not None:
        vigente.estado = EstadoFechaEfectiva.SUPERSEDIDA.value
        vigente.vigente_hasta = ahora
        bd.flush()
        if vigente.due_at_utc != resultado.due_at_utc:
            # S9.8.2 (A-103): la version capturada con la fecha anterior se
            # supersede; el barrido captura de nuevo con la nueva.
            versiones_repo.al_cambiar_la_fecha(
                bd,
                entrega_id=entrega.id,
                sujeto_id=sujeto.id,
                fecha_anterior=vigente.due_at_utc,
                fecha_nueva=resultado.due_at_utc,
            )
            # S11.6.2, S11.8.3 (F10): cancela el aviso de cierre con la fecha
            # vieja y agrupa el cambio para anunciarlo.
            comunicaciones_repo.al_cambiar_fecha(
                bd,
                entrega=entrega,
                sujeto=sujeto,
                anterior=vigente.due_at_utc,
                nueva=resultado.due_at_utc,
                origen=resultado.origen.value,
                ahora=ahora,
            )
    bd.add(
        FechaEfectiva(
            entrega_id=entrega.id,
            sujeto_id=sujeto.id,
            due_at_utc=resultado.due_at_utc,
            origen=resultado.origen.value,
            regla_fecha_id=(
                resultado.regla_ref if isinstance(resultado.regla_ref, uuid.UUID) else None
            ),
            ambigua=resultado.ambigua,
            calculada_en=ahora,
            estado=EstadoFechaEfectiva.VIGENTE.value,
        )
    )


def recalcular_fechas_tarea(bd: Session, *, curso_id: uuid.UUID, tarea_id: uuid.UUID) -> None:
    for entrega in bd.query(Entrega).filter(
        Entrega.tarea_id == tarea_id,
        Entrega.estado_validacion.in_(
            [
                EstadoValidacionEntrega.VIGENTE.value,
                EstadoValidacionEntrega.VINCULADA_TRAS_EL_CIERRE.value,
            ]
        ),
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
