"""Correccion: filas, reparto, borrador, reclamos y la matriz de estado (SPEC 12
S12.2-S12.8, S12.11, S12.15; A-134..A-138, A-180, A-206, A-214; Etapa F11).

Ninguna funcion de aqui llama a Canvas ni a GitHub: el borrador, la marca de
lista y el reparto son escrituras locales; la rubrica se lee del espejo de la
tarea de Canvas. `transicionar` es la unica que escribe `correccion.estado`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.adaptadores import bitacora_repo, incidencia_repo, versiones_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_aprovisionamiento import (
    AccesoRepositorio,
    FechaEfectiva,
    Repositorio,
    Sujeto,
)
from app.adaptadores.modelos_correccion import (
    AsignacionCorreccion,
    Correccion,
    EstadoCanvasSubmission,
    NotaInternaCorreccion,
)
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_github import AccesoDocenteRepositorio
from app.adaptadores.modelos_identidad import Usuario
from app.adaptadores.modelos_infraestructura import Bitacora, Incidencia
from app.adaptadores.modelos_padron import Estudiante, Grupo, Matricula, PertenenciaGrupo, Seccion
from app.adaptadores.modelos_tarea import AssignmentCanvas, Entrega, Tarea
from app.adaptadores.modelos_version import VersionEntrega
from app.dominio.correccion import (
    ETIQUETA_ESTADO,
    TERMINALES,
    Corrector,
    NotaInvalida,
    SujetoReparto,
    huella_rubrica,
    motivo_no_publicable,
    normalizar_nota,
    puede_transicionar,
    reparto_equitativo,
    reparto_por_seccion,
    validar_rubrica_local,
)
from app.dominio.estado_correccion import pie_comentario
from app.dominio.estados import (
    CriterioAsignacion,
    EstadoCorreccion,
    EstadoMembresia,
    RolMembresia,
)
from app.dominio.fechas import formatear_fecha
from app.infraestructura.cerrojos import cerrojo_reparto

# Motivos que fija la lectura de Canvas, no la tarea: no se pisan aqui.
_MOTIVOS_DE_CANVAS = frozenset({"PERIODO_CERRADO", "NO_GRADEABLE", "PUBLICACION_NO_AUTORIZADA"})
_NO_REASIGNABLES = frozenset({EstadoCorreccion.PUBLICANDO.value})


class RechazoCorreccion(Exception):
    def __init__(self, motivo: str, *, codigo: int = 409) -> None:
        super().__init__(motivo)
        self.motivo = motivo
        self.codigo = codigo


# --- Transicion unica (S12.3.2) ---


def transicionar(
    bd: Session,
    correccion: Correccion,
    nuevo: EstadoCorreccion,
    *,
    actor_usuario_id: uuid.UUID | None,
    curso_id: uuid.UUID,
    detalle: dict[str, Any] | None = None,
) -> None:
    antes = correccion.estado
    if antes == nuevo.value:
        return
    if not puede_transicionar(antes, nuevo.value):
        raise RechazoCorreccion(
            f"No se puede pasar de «{ETIQUETA_ESTADO[antes]}» a «{ETIQUETA_ESTADO[nuevo.value]}»."
        )
    correccion.estado = nuevo.value
    correccion.actualizado_en = ahora_utc()
    bd.flush()
    bitacora_repo.registrar(
        bd,
        accion="CORRECCION_ESTADO",
        entidad="correccion",
        entidad_id=str(correccion.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=curso_id,
        antes={"estado": antes},
        despues={"estado": nuevo.value, **(detalle or {})},
    )


# --- Sujetos, nombres y secciones ---


def nombre_de_sujeto(bd: Session, sujeto: Sujeto) -> tuple[str, str]:
    """(nombre, nombre ordenable)."""
    if sujeto.estudiante_id:
        est = bd.get(Estudiante, sujeto.estudiante_id)
        return (est.nombre, est.nombre_ordenable or est.nombre) if est else ("—", "—")
    grupo = bd.get(Grupo, sujeto.grupo_id) if sujeto.grupo_id else None
    return (grupo.nombre, grupo.nombre) if grupo else ("—", "—")


def integrantes(bd: Session, sujeto: Sujeto) -> list[Estudiante]:
    if sujeto.estudiante_id:
        est = bd.get(Estudiante, sujeto.estudiante_id)
        return [est] if est else []
    return (
        bd.query(Estudiante)
        .join(PertenenciaGrupo, PertenenciaGrupo.estudiante_id == Estudiante.id)
        .filter(
            PertenenciaGrupo.grupo_id == sujeto.grupo_id,
            PertenenciaGrupo.workflow_state == "accepted",
            PertenenciaGrupo.activa_hasta.is_(None),
        )
        .order_by(Estudiante.canvas_user_id)
        .all()
    )


def secciones_de_sujeto(bd: Session, sujeto: Sujeto) -> tuple[uuid.UUID, ...]:
    """Individual: su matricula activa. Grupo: la del integrante aceptado con
    menor `canvas_user_id` (regla escrita en pantalla, S12.5.3)."""
    miembros = integrantes(bd, sujeto)
    if not miembros:
        return ()
    ids = [
        s
        for (s,) in bd.query(Matricula.seccion_id)
        .filter(Matricula.estudiante_id == miembros[0].id, Matricula.activa.is_(True))
        .distinct()
    ]
    return tuple(sorted(ids, key=str))


# --- Filas de correccion (S12.3.2 transicion 1) ---


def _sujetos_de_entrega(bd: Session, entrega: Entrega) -> list[Sujeto]:
    """Entran los sujetos activos con fecha efectiva vigente, y los retirados
    que ya tienen version o correccion."""
    activos = (
        bd.query(Sujeto)
        .join(FechaEfectiva, FechaEfectiva.sujeto_id == Sujeto.id)
        .filter(
            FechaEfectiva.entrega_id == entrega.id,
            FechaEfectiva.estado == "VIGENTE",
            Sujeto.activo.is_(True),
        )
        .all()
    )
    ids = {s.id for s in activos}
    condiciones = [
        Sujeto.tarea_id == entrega.tarea_id,
        Sujeto.id.in_(
            bd.query(VersionEntrega.sujeto_id).filter(VersionEntrega.entrega_id == entrega.id)
        )
        | Sujeto.id.in_(bd.query(Correccion.sujeto_id).filter(Correccion.entrega_id == entrega.id)),
    ]
    if ids:
        condiciones.append(Sujeto.id.notin_(ids))
    con_rastro = bd.query(Sujeto).filter(*condiciones).all()
    return activos + con_rastro


def _hubo_reparto(bd: Session, entrega_id: uuid.UUID) -> bool:
    return (
        bd.query(AsignacionCorreccion.id)
        .filter(
            AsignacionCorreccion.entrega_id == entrega_id,
            AsignacionCorreccion.membresia_id.isnot(None),
        )
        .first()
        is not None
    )


def asegurar_filas(bd: Session, entrega: Entrega, *, ahora: datetime | None = None) -> int:
    """Materializa las filas que faltan y refresca las banderas derivadas. Un
    sujeto tardio queda SIN_CORRECTOR con incidencia, sin tocar otras filas."""
    ahora = ahora or ahora_utc()
    hubo_reparto = _hubo_reparto(bd, entrega.id)
    nuevos = 0
    for sujeto in _sujetos_de_entrega(bd, entrega):
        correccion = (
            bd.query(Correccion)
            .filter(Correccion.entrega_id == entrega.id, Correccion.sujeto_id == sujeto.id)
            .one_or_none()
        )
        if correccion is None:
            correccion = Correccion(
                entrega_id=entrega.id,
                sujeto_id=sujeto.id,
                estado=EstadoCorreccion.SIN_CORRECTOR.value,
                actualizado_en=ahora,
                publicable=True,
                banderas=[],
            )
            bd.add(correccion)
            bd.add(
                AsignacionCorreccion(
                    entrega_id=entrega.id,
                    sujeto_id=sujeto.id,
                    membresia_id=None,
                    criterio=CriterioAsignacion.MANUAL.value,
                )
            )
            bd.flush()
            bitacora_repo.registrar(
                bd,
                accion="CORRECCION_ESTADO",
                entidad="correccion",
                entidad_id=str(correccion.id),
                curso_id=entrega.curso_id,
                antes=None,
                despues={"estado": EstadoCorreccion.SIN_CORRECTOR.value, "alta": True},
            )
            nuevos += 1
        _refrescar_banderas(bd, correccion, entrega, sujeto, ahora=ahora)
    if nuevos and hubo_reparto:
        sin = (
            bd.query(Correccion)
            .filter(
                Correccion.entrega_id == entrega.id,
                Correccion.estado == EstadoCorreccion.SIN_CORRECTOR.value,
            )
            .count()
        )
        incidencia_repo.abrir_o_actualizar(
            bd,
            tipo="CORRECCION_SIN_CORRECTOR",
            severidad="ADVERTENCIA",
            sujeto_tipo="ENTREGA",
            curso_id=entrega.curso_id,
            sujeto_id=entrega.id,
            detalle={"entrega": entrega.nombre, "sin_corrector": sin},
        )
    bd.flush()
    return nuevos


def _refrescar_banderas(
    bd: Session, c: Correccion, entrega: Entrega, sujeto: Sujeto, *, ahora: datetime
) -> None:
    motivo = motivo_no_publicable(
        grading_type=entrega.grading_type,
        moderada=bool(entrega.moderated_grading),
        anonima=bool(entrega.anonymous_grading),
        publicada=bool(entrega.publicada),
        estado_validacion=entrega.estado_validacion,
        sujeto_activo=sujeto.activo,
    )
    if c.motivo_no_publicable not in _MOTIVOS_DE_CANVAS or motivo is not None:
        c.publicable = motivo is None
        c.motivo_no_publicable = motivo
    vigente = versiones_repo.version_vigente(bd, entrega.id, sujeto.id)
    c.sin_commits = vigente is not None and vigente.estado == "SIN_COMMITS"
    if (
        vigente is not None
        and c.version_entrega_id is not None
        and c.version_entrega_id != vigente.id
    ):
        if not c.version_desactualizada:
            c.version_desactualizada = True
            incidencia_repo.abrir_o_actualizar(
                bd,
                tipo="CORRECCION_DESACTUALIZADA",
                severidad="ADVERTENCIA",
                sujeto_tipo="CORRECCION",
                curso_id=entrega.curso_id,
                sujeto_id=c.id,
                detalle={"entrega": entrega.nombre, "version_nueva": str(vigente.id)},
            )


# --- Correctores y reparto (S12.5) ---


def correctores(bd: Session, curso_id: uuid.UUID) -> list[tuple[MembresiaCurso, Usuario]]:
    filas = (
        bd.query(MembresiaCurso, Usuario)
        .join(Usuario, Usuario.id == MembresiaCurso.usuario_id)
        .filter(
            MembresiaCurso.curso_id == curso_id,
            MembresiaCurso.estado == EstadoMembresia.ACTIVA.value,
        )
        .order_by(Usuario.nombre)
        .all()
    )
    return [(m, u) for m, u in filas]


def peso_de(m: MembresiaCurso) -> int:
    if m.peso_correccion is not None:
        return m.peso_correccion
    return 0 if m.rol == RolMembresia.PROFESOR.value else 1


@dataclass
class FilaPropuesta:
    sujeto_id: uuid.UUID
    sujeto: str
    actual: uuid.UUID | None
    propuesto: uuid.UUID | None
    estado: str
    sobrescribe: bool


@dataclass
class Propuesta:
    filas: list[FilaPropuesta] = field(default_factory=list)
    totales: dict[str, int] = field(default_factory=dict)
    requiere_decision: list[uuid.UUID] = field(default_factory=list)


def _entrega_anterior(bd: Session, entrega: Entrega) -> Entrega | None:
    return (
        bd.query(Entrega)
        .filter(Entrega.tarea_id == entrega.tarea_id, Entrega.orden < entrega.orden)
        .order_by(Entrega.orden.desc())
        .first()
    )


def previsualizar(
    bd: Session,
    entrega: Entrega,
    *,
    criterio: CriterioAsignacion,
    reasignar: bool = False,
    incluir_no_calificables: bool = False,
    manual: dict[uuid.UUID, uuid.UUID | None] | None = None,
    por_seccion: dict[uuid.UUID, uuid.UUID] | None = None,
) -> Propuesta:
    """Nada se escribe: la propuesta muestra totales, fila a fila y que se
    sobrescribiria (S12.5.3)."""
    asegurar_filas(bd, entrega)
    filas = (
        bd.query(AsignacionCorreccion, Correccion, Sujeto)
        .join(
            Correccion,
            (Correccion.entrega_id == AsignacionCorreccion.entrega_id)
            & (Correccion.sujeto_id == AsignacionCorreccion.sujeto_id),
        )
        .join(Sujeto, Sujeto.id == AsignacionCorreccion.sujeto_id)
        .filter(AsignacionCorreccion.entrega_id == entrega.id)
        .all()
    )
    nombres = {s.id: nombre_de_sujeto(bd, s) for _, _, s in filas}
    sujetos = [
        SujetoReparto(
            sujeto_id=s.id,
            nombre_ordenable=nombres[s.id][1],
            seccion_ids=secciones_de_sujeto(bd, s)
            if criterio == CriterioAsignacion.SECCION
            else (),
            actual=a.membresia_id,
            empezada=c.estado
            not in (EstadoCorreccion.SIN_CORRECTOR.value, EstadoCorreccion.ASIGNADA.value),
            calificable=c.publicable or c.motivo_no_publicable != "NO_GRADEABLE",
        )
        for a, c, s in filas
        if c.estado not in _NO_REASIGNABLES and c.estado not in TERMINALES
    ]
    requiere: list[uuid.UUID] = []
    if criterio == CriterioAsignacion.EQUITATIVO:
        miembros = correctores(bd, entrega.curso_id)
        asignacion = reparto_equitativo(
            sujetos,
            [Corrector(m.id, u.nombre, peso_de(m)) for m, u in miembros],
            reasignar=reasignar,
            incluir_no_calificables=incluir_no_calificables,
        )
    elif criterio == CriterioAsignacion.SECCION:
        asignacion, requiere = reparto_por_seccion(sujetos, por_seccion or {}, reasignar=reasignar)
    elif criterio == CriterioAsignacion.COPIA_ENTREGA_ANTERIOR:
        anterior = _entrega_anterior(bd, entrega)
        previas = (
            {
                a.sujeto_id: a.membresia_id
                for a in bd.query(AsignacionCorreccion).filter(
                    AsignacionCorreccion.entrega_id == anterior.id
                )
                if a.membresia_id
            }
            if anterior
            else {}
        )
        asignacion = {
            s.sujeto_id: previas[s.sujeto_id]
            for s in sujetos
            if s.sujeto_id in previas and (s.actual is None or reasignar)
        }
    else:
        asignacion = {k: v for k, v in (manual or {}).items() if v is not None}
    quitar = (
        {k for k, v in (manual or {}).items() if v is None}
        if criterio == CriterioAsignacion.MANUAL
        else set()
    )
    propuesta = Propuesta(requiere_decision=requiere)
    elegibles = {s.sujeto_id for s in sujetos}
    for a, c, s in sorted(filas, key=lambda f: (nombres[f[2].id][1].lower(), str(f[2].id))):
        propuesto = asignacion.get(s.id, a.membresia_id)
        if s.id in quitar and s.id in elegibles:
            propuesto = None
        if s.id not in elegibles:
            propuesto = a.membresia_id
        propuesta.filas.append(
            FilaPropuesta(
                sujeto_id=s.id,
                sujeto=nombres[s.id][0],
                actual=a.membresia_id,
                propuesto=propuesto,
                estado=c.estado,
                sobrescribe=a.membresia_id is not None and propuesto != a.membresia_id,
            )
        )
        clave = str(propuesto) if propuesto else "sin corrector"
        propuesta.totales[clave] = propuesta.totales.get(clave, 0) + 1
    return propuesta


def aplicar(
    bd: Session,
    entrega: Entrega,
    *,
    criterio: CriterioAsignacion,
    actor: MembresiaCurso,
    reasignar: bool = False,
    incluir_no_calificables: bool = False,
    manual: dict[uuid.UUID, uuid.UUID | None] | None = None,
    por_seccion: dict[uuid.UUID, uuid.UUID] | None = None,
) -> int:
    """En una transaccion con cerrojo por entrega: una segunda ejecucion
    concurrente ve el resultado de la primera y no asigna nada dos veces."""
    cerrojo_reparto(bd, entrega.id)
    propuesta = previsualizar(
        bd,
        entrega,
        criterio=criterio,
        reasignar=reasignar,
        incluir_no_calificables=incluir_no_calificables,
        manual=manual,
        por_seccion=por_seccion,
    )
    ahora = ahora_utc()
    cambios = 0
    for fila in propuesta.filas:
        if fila.propuesto == fila.actual:
            continue
        a = (
            bd.query(AsignacionCorreccion)
            .filter(
                AsignacionCorreccion.entrega_id == entrega.id,
                AsignacionCorreccion.sujeto_id == fila.sujeto_id,
            )
            .one()
        )
        c = (
            bd.query(Correccion)
            .filter(Correccion.entrega_id == entrega.id, Correccion.sujeto_id == fila.sujeto_id)
            .one()
        )
        if c.estado in _NO_REASIGNABLES or c.estado in TERMINALES:
            continue
        a.membresia_id = fila.propuesto
        a.asignada_por = actor.id
        a.asignada_en = ahora
        a.criterio = criterio.value
        if fila.propuesto is None:
            transicionar(
                bd,
                c,
                EstadoCorreccion.SIN_CORRECTOR,
                actor_usuario_id=actor.usuario_id,
                curso_id=entrega.curso_id,
                detalle={"motivo": "reasignacion"},
            )
        elif c.estado == EstadoCorreccion.SIN_CORRECTOR.value:
            transicionar(
                bd,
                c,
                EstadoCorreccion.ASIGNADA,
                actor_usuario_id=actor.usuario_id,
                curso_id=entrega.curso_id,
                detalle={"criterio": criterio.value},
            )
        bitacora_repo.registrar(
            bd,
            accion="CORRECCION_ASIGNADA",
            entidad="asignacion_correccion",
            entidad_id=str(a.id),
            actor_usuario_id=actor.usuario_id,
            curso_id=entrega.curso_id,
            antes={"membresia_id": str(fila.actual) if fila.actual else None},
            despues={
                "membresia_id": str(fila.propuesto) if fila.propuesto else None,
                "criterio": criterio.value,
            },
        )
        cambios += 1
    if (
        not bd.query(Correccion.id)
        .filter(
            Correccion.entrega_id == entrega.id,
            Correccion.estado == EstadoCorreccion.SIN_CORRECTOR.value,
        )
        .first()
    ):
        incidencia_repo.cerrar(
            bd, tipo="CORRECCION_SIN_CORRECTOR", curso_id=entrega.curso_id, sujeto_id=entrega.id
        )
    bd.flush()
    return cambios


def al_retirar_miembro(
    bd: Session, membresia: MembresiaCurso, *, actor_usuario_id: uuid.UUID
) -> int:
    """S12.5.5: lo no publicado vuelve a SIN_CORRECTOR con el borrador
    intacto; lo publicado conserva quien lo corrigio. Una incidencia por
    entrega afectada."""
    afectadas: dict[uuid.UUID, Entrega] = {}
    for a in bd.query(AsignacionCorreccion).filter(
        AsignacionCorreccion.membresia_id == membresia.id
    ):
        c = (
            bd.query(Correccion)
            .filter(Correccion.entrega_id == a.entrega_id, Correccion.sujeto_id == a.sujeto_id)
            .one()
        )
        if c.estado in TERMINALES or c.estado in _NO_REASIGNABLES:
            continue
        a.membresia_id = None
        transicionar(
            bd,
            c,
            EstadoCorreccion.SIN_CORRECTOR,
            actor_usuario_id=actor_usuario_id,
            curso_id=membresia.curso_id,
            detalle={"motivo": "retiro_del_corrector"},
        )
        entrega = bd.get(Entrega, a.entrega_id)
        if entrega is not None:
            afectadas[entrega.id] = entrega
    for entrega in afectadas.values():
        incidencia_repo.abrir_o_actualizar(
            bd,
            tipo="CORRECCION_SIN_CORRECTOR",
            severidad="ADVERTENCIA",
            sujeto_tipo="ENTREGA",
            curso_id=entrega.curso_id,
            sujeto_id=entrega.id,
            detalle={"entrega": entrega.nombre, "motivo": "retiro de un corrector"},
        )
    bd.flush()
    return len(afectadas)


# --- Pantalla de correccion (S12.8) ---


def es_propietario(membresia: MembresiaCurso, asignacion: AsignacionCorreccion) -> bool:
    """La propiedad acota el trabajo, no la lectura: el profesor, todas; el
    ayudante, solo las suyas."""
    return membresia.rol == RolMembresia.PROFESOR.value or asignacion.membresia_id == membresia.id


def fila(
    bd: Session, entrega_id: uuid.UUID, sujeto_id: uuid.UUID
) -> tuple[Correccion, AsignacionCorreccion]:
    c = (
        bd.query(Correccion)
        .filter(Correccion.entrega_id == entrega_id, Correccion.sujeto_id == sujeto_id)
        .one_or_none()
    )
    a = (
        bd.query(AsignacionCorreccion)
        .filter(
            AsignacionCorreccion.entrega_id == entrega_id,
            AsignacionCorreccion.sujeto_id == sujeto_id,
        )
        .one_or_none()
    )
    if c is None or a is None:
        raise RechazoCorreccion("Esa corrección no existe.", codigo=404)
    return c, a


def abrir(
    bd: Session,
    c: Correccion,
    a: AsignacionCorreccion,
    *,
    membresia: MembresiaCurso,
    curso_id: uuid.UUID,
) -> None:
    """Primera apertura por su corrector: EN_CURSO sin boton (CA-12.3-04)."""
    if c.estado == EstadoCorreccion.ASIGNADA.value and a.membresia_id == membresia.id:
        a.iniciada_en = a.iniciada_en or ahora_utc()
        transicionar(
            bd,
            c,
            EstadoCorreccion.EN_CURSO,
            actor_usuario_id=membresia.usuario_id,
            curso_id=curso_id,
        )
    if c.version_entrega_id is None:
        vigente = versiones_repo.version_vigente(bd, c.entrega_id, c.sujeto_id)
        c.version_entrega_id = vigente.id if vigente else None
        bd.flush()


def rubrica_de(bd: Session, entrega: Entrega) -> tuple[list[dict[str, Any]], dict[str, Any], bool]:
    """(criterios, ajustes, usar para calificar) desde el espejo de la tarea."""
    espejo = (
        bd.query(AssignmentCanvas)
        .filter(
            AssignmentCanvas.curso_id == entrega.curso_id,
            AssignmentCanvas.canvas_assignment_id == entrega.canvas_assignment_id,
        )
        .one_or_none()
    )
    payload = (espejo.payload if espejo else None) or {}
    return (
        list(payload.get("rubric") or []),
        dict(payload.get("rubric_settings") or {}),
        bool(payload.get("use_rubric_for_grading")),
    )


def guardar_borrador(
    bd: Session,
    c: Correccion,
    a: AsignacionCorreccion,
    *,
    entrega: Entrega,
    membresia: MembresiaCurso,
    nota: str | None,
    rubrica: dict[str, Any] | None,
    comentario: str | None,
    version_esperada: int | None,
) -> None:
    """Nunca llama a Canvas (CA-12.10-01). Se permite aunque no sea publicable."""
    if not es_propietario(membresia, a):
        raise RechazoCorreccion("Esta corrección está asignada a otra persona.", codigo=403)
    if c.estado in (EstadoCorreccion.PUBLICANDO.value, *TERMINALES):
        raise RechazoCorreccion("Para cambiarla, primero reabre la corrección.")
    if version_esperada is not None and version_esperada != c.version:
        raise RechazoCorreccion(
            "Alguien guardó otra versión del borrador; recarga antes de seguir."
        )
    criterios, _, _ = rubrica_de(bd, entrega)
    errores = validar_rubrica_local(criterios, rubrica)
    if errores:
        raise RechazoCorreccion("; ".join(errores), codigo=422)
    if c.estado == EstadoCorreccion.SIN_CORRECTOR.value:
        # Quien puede repartir y escribe en una fila sin corrector se la
        # asigna a si mismo, de forma explicita y con bitacora.
        a.membresia_id = membresia.id
        a.asignada_por = membresia.id
        a.asignada_en = ahora_utc()
        a.criterio = CriterioAsignacion.MANUAL.value
        transicionar(
            bd,
            c,
            EstadoCorreccion.ASIGNADA,
            actor_usuario_id=membresia.usuario_id,
            curso_id=entrega.curso_id,
            detalle={"criterio": "MANUAL", "al_corregir": True},
        )
    if c.estado == EstadoCorreccion.ASIGNADA.value:
        a.iniciada_en = a.iniciada_en or ahora_utc()
        transicionar(
            bd,
            c,
            EstadoCorreccion.EN_CURSO,
            actor_usuario_id=membresia.usuario_id,
            curso_id=entrega.curso_id,
        )
    c.nota_local = nota
    c.rubrica_local = rubrica
    c.comentario = comentario
    c.corrector_usuario_id = membresia.usuario_id
    c.huella_rubrica = huella_rubrica(criterios, rubrica_de(bd, entrega)[1]) if criterios else None
    c.version += 1
    c.actualizado_en = ahora_utc()
    autor = bd.get(Usuario, membresia.usuario_id)
    bitacora_repo.registrar(
        bd,
        accion="BORRADOR_GUARDADO",
        entidad="correccion",
        entidad_id=str(c.id),
        actor_usuario_id=membresia.usuario_id,
        curso_id=entrega.curso_id,
        despues={
            "version": c.version,
            "membresia_id": str(membresia.id),
            "rol": membresia.rol,
            "nombre": autor.nombre if autor else "Equipo docente",
            "es_via_compartida": membresia.es_via_compartida,
        },
    )
    bd.flush()


def metadatos_borrador(bd: Session, c: Correccion) -> dict[str, Any]:
    guardado = (
        bd.query(Bitacora)
        .filter_by(accion="BORRADOR_GUARDADO", entidad="correccion", entidad_id=str(c.id))
        .order_by(Bitacora.creado_en.desc(), Bitacora.id.desc())
        .first()
    )
    if guardado is not None:
        datos = guardado.despues or {}
        return {
            "guardado_en": guardado.creado_en.isoformat(),
            "autor": {
                "usuario_id": str(guardado.actor_usuario_id),
                "nombre": datos.get("nombre"),
                "rol": datos.get("rol"),
                "es_via_compartida": datos.get("es_via_compartida", False),
            },
        }
    # Borradores anteriores a esta corrección no tienen un instante de guardado auditable.
    autor = bd.get(Usuario, c.corrector_usuario_id) if c.corrector_usuario_id else None
    return {
        "guardado_en": None,
        "autor": {
            "usuario_id": str(autor.id),
            "nombre": autor.nombre,
            "rol": None,
            "es_via_compartida": False,
        }
        if autor
        else None,
    }


def comentario_para_canvas(bd: Session, c: Correccion, entrega: Entrega, curso: Curso) -> str:
    meta = metadatos_borrador(bd, c)
    autor = meta["autor"] or {}
    rol = autor.get("rol")
    if rol is None and c.corrector_usuario_id is not None:
        miembro = (
            bd.query(MembresiaCurso)
            .filter_by(curso_id=curso.id, usuario_id=c.corrector_usuario_id)
            .one_or_none()
        )
        rol = miembro.rol if miembro else None
    version = bd.get(VersionEntrega, c.version_entrega_id) if c.version_entrega_id else None
    fecha = (
        bd.query(FechaEfectiva)
        .filter_by(entrega_id=entrega.id, sujeto_id=c.sujeto_id)
        .one_or_none()
    )
    return pie_comentario(
        texto=c.comentario or "",
        entrega=entrega.nombre,
        cierre=formatear_fecha(fecha.due_at_utc, curso.zona_horaria)
        if fecha and fecha.due_at_utc
        else "sin fecha",
        sha=version.commit_sha if version and version.estado != "SIN_COMMITS" else None,
        repositorio_full_name=version.repositorio_full_name if version else None,
        corrector=autor.get("nombre") or "el equipo docente",
        rol="profesor"
        if rol == "PROFESOR"
        else "ayudante"
        if rol == "AYUDANTE"
        else "equipo docente",
    )


def marcar_lista(
    bd: Session,
    c: Correccion,
    a: AsignacionCorreccion,
    *,
    entrega: Entrega,
    membresia: MembresiaCurso,
) -> None:
    if not es_propietario(membresia, a):
        raise RechazoCorreccion("Esta corrección está asignada a otra persona.", codigo=403)
    try:
        c.nota_local = normalizar_nota(entrega.grading_type, c.nota_local, entrega.puntos_posibles)
    except NotaInvalida as exc:
        raise RechazoCorreccion(str(exc), codigo=422) from exc
    vigente = versiones_repo.version_vigente(bd, entrega.id, c.sujeto_id)
    if vigente is None:
        raise RechazoCorreccion("Todavía no hay una versión registrada para esta entrega.")
    if c.version_desactualizada or c.version_entrega_id is None:
        c.version_entrega_id = vigente.id
        c.version_desactualizada = False
    c.lista_en = ahora_utc()
    transicionar(
        bd,
        c,
        EstadoCorreccion.LISTA_PARA_PUBLICAR,
        actor_usuario_id=membresia.usuario_id,
        curso_id=entrega.curso_id,
    )


def agregar_nota_interna(
    bd: Session,
    c: Correccion,
    *,
    membresia: MembresiaCurso,
    texto: str,
    clase: str = "NOTA",
    desenlace: str | None = None,
) -> NotaInternaCorreccion:
    nota = NotaInternaCorreccion(
        correccion_id=c.id,
        autor_membresia_id=membresia.id,
        texto=texto,
        clase=clase,
        desenlace_reclamo=desenlace,
        creada_en=ahora_utc(),
    )
    bd.add(nota)
    if clase == "RECLAMO_ABIERTO":
        c.reclamo_abierto = True
    elif clase == "RECLAMO_CERRADO":
        c.reclamo_abierto = False
    bd.flush()
    return nota


def acceso_docente(bd: Session, repositorio_id: uuid.UUID | None) -> str | None:
    if repositorio_id is None:
        return None
    estados = [
        a.estado
        for a in bd.query(AccesoDocenteRepositorio).filter(
            AccesoDocenteRepositorio.repositorio_id == repositorio_id
        )
    ]
    if not estados:
        return None
    return "CONCEDIDO" if all(e == "CONCEDIDO" for e in estados) else sorted(set(estados))[0]


# --- Matriz «Estado de la entrega» (S12.11) ---


def matriz(bd: Session, curso: Curso, tarea: Tarea) -> dict[str, Any]:
    """Una sola pasada sobre las filas de la tarea; nunca `submission_summary`
    de Canvas: el lado de Canvas sale de `estado_canvas_submission`."""
    from app.dominio.estado_correccion import contraste_canvas

    entregas = bd.query(Entrega).filter(Entrega.tarea_id == tarea.id).order_by(Entrega.orden).all()
    for e in entregas:
        asegurar_filas(bd, e)
    nombres_miembros = {m.id: u.nombre for m, u in correctores(bd, curso.id)}
    filas = (
        bd.query(Correccion, AsignacionCorreccion, Sujeto)
        .join(
            AsignacionCorreccion,
            (AsignacionCorreccion.entrega_id == Correccion.entrega_id)
            & (AsignacionCorreccion.sujeto_id == Correccion.sujeto_id),
        )
        .join(Sujeto, Sujeto.id == Correccion.sujeto_id)
        .filter(Correccion.entrega_id.in_([e.id for e in entregas]))
        .all()
        if entregas
        else []
    )
    espejo: dict[tuple[uuid.UUID, uuid.UUID], EstadoCanvasSubmission] = (
        {
            (s.entrega_id, s.estudiante_id): s
            for s in bd.query(EstadoCanvasSubmission).filter(
                EstadoCanvasSubmission.entrega_id.in_([e.id for e in entregas])
            )
        }
        if entregas
        else {}
    )
    publicaciones = ultima_publicacion_por_estudiante(bd, [c.id for c, _, _ in filas])
    repositorios: dict[uuid.UUID, Repositorio] = {}
    for repo in (
        bd.query(Repositorio)
        .filter(Repositorio.tarea_id == tarea.id, Repositorio.github_repo_id.isnot(None))
        .order_by(Repositorio.creado_en.desc())
    ):
        repositorios.setdefault(repo.sujeto_id, repo)
    accesos = {
        (acceso.repositorio_id, acceso.estudiante_id): acceso
        for acceso in bd.query(AccesoRepositorio).filter(
            AccesoRepositorio.repositorio_id.in_([r.id for r in repositorios.values()])
        )
    }
    causas: dict[tuple[str, str, str], Incidencia] = {}
    for incidencia in bd.query(Incidencia).filter(
        Incidencia.curso_id == curso.id,
        Incidencia.tipo == "SIN_PARTICIPACION",
        Incidencia.abierta.is_(True),
    ):
        detalle = incidencia.detalle
        if detalle.get("tarea_id") != str(tarea.id) or detalle.get("causa") not in {
            "SIN_ACCESO",
            "SIN_ATRIBUIR",
            "SIN_COMMITS",
        }:
            continue
        causas[
            (
                str(detalle.get("repositorio_id")),
                str(detalle.get("estudiante_id")),
                str(detalle.get("entrega_id")),
            )
        ] = incidencia
    sujetos: dict[uuid.UUID, dict[str, Any]] = {}
    por_corrector: dict[str, dict[str, int]] = {}
    por_entrega: dict[str, dict[str, int]] = {}
    por_seccion: dict[str, dict[str, int]] = {}
    nombres_seccion = {
        s.id: s.nombre for s in bd.query(Seccion).filter(Seccion.curso_id == curso.id)
    }
    corregidas = con_nota_canvas = total = 0
    comprobado: datetime | None = None
    for c, a, s in filas:
        nombre, ordenable = nombre_de_sujeto(bd, s)
        miembros = integrantes(bd, s)
        repositorio = repositorios.get(s.id)
        filas_canvas = [espejo.get((c.entrega_id, m.id)) for m in miembros]
        contraste = contraste_canvas(
            [publicaciones.get((c.id, m.id)) for m in miembros],
            filas_canvas,
        )
        for fc in filas_canvas:
            if fc is not None and (comprobado is None or fc.sincronizado_en > comprobado):
                comprobado = fc.sincronizado_en
        seccion_ids = secciones_de_sujeto(bd, s)
        entrada = sujetos.setdefault(
            s.id,
            {
                "sujeto_id": str(s.id),
                "sujeto": nombre,
                "orden": ordenable.lower(),
                "activo": s.activo,
                "seccion": nombres_seccion.get(seccion_ids[0]) if seccion_ids else None,
                "repositorio_id": str(repositorio.id) if repositorio else None,
                "accesos": [
                    {
                        "estudiante_id": str(m.id),
                        "nombre": m.nombre,
                        "estado": acceso.estado if acceso else None,
                        "verificado_en": acceso.verificado_en.isoformat()
                        if acceso and acceso.verificado_en
                        else None,
                    }
                    for m in miembros
                    for acceso in [accesos.get((repositorio.id, m.id)) if repositorio else None]
                ],
                "celdas": {},
            },
        )
        corrector = nombres_miembros.get(a.membresia_id) if a.membresia_id else None
        entrada["celdas"][str(c.entrega_id)] = {
            "estado": c.estado,
            "etiqueta": ETIQUETA_ESTADO[c.estado],
            "corrector": corrector,
            "corrector_membresia_id": str(a.membresia_id) if a.membresia_id else None,
            "publicable": c.publicable,
            "motivo_no_publicable": c.motivo_no_publicable,
            "banderas": [
                b
                for b, v in (
                    ("version_desactualizada", c.version_desactualizada),
                    ("reclamo_abierto", c.reclamo_abierto),
                    ("sin_commits", c.sin_commits),
                    ("reconocimiento_sin_codigo", c.reconocimiento_sin_codigo),
                    ("desalineada", a.desalineada_motivo is not None),
                )
                if v
            ],
            "contraste": contraste,
            "causas_sin_participacion": [
                {
                    "estudiante_id": str(m.id),
                    "nombre": m.nombre,
                    "causa": incidencia.detalle["causa"],
                    "registrada_en": incidencia.creado_en.isoformat(),
                }
                for m in miembros
                for incidencia in [causas.get((str(repositorio.id), str(m.id), str(c.entrega_id)))]
                if repositorio and incidencia is not None
            ]
            if repositorio
            else [],
        }
        total += 1
        if c.estado in TERMINALES:
            corregidas += 1
        if any(
            fc is not None and fc.graded_at is not None and fc.score is not None
            for fc in filas_canvas
        ):
            con_nota_canvas += 1
        for tabla, clave in (
            (por_corrector, corrector or "Sin corrector"),
            (por_entrega, str(c.entrega_id)),
            (por_seccion, entrada["seccion"] or "Sin sección"),
        ):
            fila_agregado = tabla.setdefault(clave, {})
            fila_agregado[c.estado] = fila_agregado.get(c.estado, 0) + 1
    ordenadas = sorted(sujetos.values(), key=lambda x: (x["orden"], x["sujeto_id"]))
    return {
        "entregas": [{"id": str(e.id), "nombre": e.nombre, "orden": e.orden} for e in entregas],
        "sujetos": ordenadas,
        "por_corrector": por_corrector,
        "por_entrega": por_entrega,
        "por_seccion": por_seccion,
        "contador": {
            "corregidas": corregidas,
            "con_nota_en_canvas": con_nota_canvas,
            "total": total,
            "comprobado_en": comprobado.isoformat() if comprobado else None,
        },
    }


def mis_asignaciones(bd: Session, curso: Curso, membresia: MembresiaCurso) -> list[dict[str, Any]]:
    """Solo las filas de quien pregunta, agrupadas por entrega y en orden de
    nombre (S12.6.1)."""
    salida = []
    for a, c, s, e in (
        bd.query(AsignacionCorreccion, Correccion, Sujeto, Entrega)
        .join(
            Correccion,
            (Correccion.entrega_id == AsignacionCorreccion.entrega_id)
            & (Correccion.sujeto_id == AsignacionCorreccion.sujeto_id),
        )
        .join(Sujeto, Sujeto.id == AsignacionCorreccion.sujeto_id)
        .join(Entrega, Entrega.id == AsignacionCorreccion.entrega_id)
        .filter(Entrega.curso_id == curso.id, AsignacionCorreccion.membresia_id == membresia.id)
    ):
        nombre, ordenable = nombre_de_sujeto(bd, s)
        salida.append(
            {
                "entrega_id": str(e.id),
                "entrega": e.nombre,
                "tarea_id": str(e.tarea_id),
                "sujeto_id": str(s.id),
                "sujeto": nombre,
                "orden": ordenable.lower(),
                "estado": c.estado,
                "etiqueta": ETIQUETA_ESTADO[c.estado],
                "sin_commits": c.sin_commits,
                "reclamo_abierto": c.reclamo_abierto,
                "version_desactualizada": c.version_desactualizada,
                "asignada_en": a.asignada_en.isoformat() if a.asignada_en else None,
                "nueva": bool(
                    a.asignada_en
                    and (
                        membresia.correccion_vista_en is None
                        or a.asignada_en > membresia.correccion_vista_en
                    )
                ),
                "actualizado_en": c.actualizado_en.isoformat(),
            }
        )
    return sorted(salida, key=lambda x: (x["entrega"], x["orden"], x["sujeto_id"]))


def orden_de_recorrido(bd: Session, entrega: Entrega) -> list[uuid.UUID]:
    """El recorrido de una entrega: nombre ascendente y luego id; nunca cruza
    entregas (S12.7)."""
    sujetos = (
        bd.query(Sujeto)
        .join(Correccion, Correccion.sujeto_id == Sujeto.id)
        .filter(Correccion.entrega_id == entrega.id)
    )
    return [
        s.id for s in sorted(sujetos, key=lambda s: (nombre_de_sujeto(bd, s)[1].lower(), str(s.id)))
    ]


def repositorio_de(bd: Session, sujeto_id: uuid.UUID) -> Repositorio | None:
    return (
        bd.query(Repositorio)
        .filter(Repositorio.sujeto_id == sujeto_id, Repositorio.github_repo_id.isnot(None))
        .order_by(Repositorio.creado_en.desc())
        .first()
    )


def ultima_publicacion_por_estudiante(
    bd: Session, correccion_ids: list[uuid.UUID]
) -> dict[tuple[uuid.UUID, uuid.UUID], Any]:
    """La ultima publicacion exitosa (2xx) de cada (correccion, estudiante)."""
    from app.adaptadores.modelos_correccion import PublicacionNota

    if not correccion_ids:
        return {}
    salida: dict[tuple[uuid.UUID, uuid.UUID], Any] = {}
    for p in (
        bd.query(PublicacionNota)
        .filter(
            PublicacionNota.correccion_id.in_(correccion_ids),
            PublicacionNota.codigo_http >= 200,
            PublicacionNota.codigo_http < 300,
        )
        .order_by(PublicacionNota.intento)
    ):
        salida[(p.correccion_id, p.estudiante_id)] = p
    return salida


def hay_filas(bd: Session, entrega_id: uuid.UUID) -> bool:
    """La correccion de una entrega empieza con el primer reparto o apertura."""
    return bd.query(Correccion.id).filter(Correccion.entrega_id == entrega_id).first() is not None
