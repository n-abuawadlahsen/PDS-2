"""Publicacion de notas en Canvas y reconciliacion (SPEC 12 S12.10, S12.13,
S12.14; A-139..A-143, A-169, A-206; Etapa F12).

La publicacion es la escritura sincrona #5 (A-169): lectura previa, intencion
persistida antes de la llamada (PUBLICANDO), resultado con el literal de
Canvas, bitacora y ninguna comunicacion directa (el aviso al estudiante va
por el outbox). Toda escritura usa la credencial operativa del curso y nunca
`as_user_id`. `FALLIDO` no existe aqui: un error queda ERROR_PUBLICACION y
solo una persona lo reintenta.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.adaptadores import (
    bitacora_repo,
    canvas_repo,
    comunicaciones_repo,
    correccion_repo,
    incidencia_repo,
    trabajos_repo,
)
from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_canvas import (
    CalificacionCanvas,
    ClienteCanvas,
    FalloProveedorCanvas,
    crear_cliente_canvas,
)
from app.adaptadores.modelos_aprovisionamiento import FechaEfectiva, Sujeto
from app.adaptadores.modelos_correccion import (
    Correccion,
    EstadoCanvasSubmission,
    PublicacionNota,
)
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_identidad import Usuario
from app.adaptadores.modelos_padron import Estudiante
from app.adaptadores.modelos_tarea import AssignmentCanvas, Entrega, Tarea
from app.adaptadores.modelos_version import VersionEntrega
from app.dominio.correccion import TERMINALES, es_solo_lectura, huella_rubrica, normalizar_nota
from app.dominio.estado_correccion import (
    contraste_canvas,
    hay_conflicto,
    pie_comentario,
    resultado_verificacion,
)
from app.dominio.estados import EstadoCorreccion
from app.dominio.fechas import formatear_fecha
from app.infraestructura.cerrojos import cerrojo_canvas
from app.infraestructura.cifrado import Llavero
from app.infraestructura.config import obtener_configuracion

TIPO_RECONCILIAR = "reconciliar_notas_canvas"
VENTANA_CORRECCION = timedelta(days=21)


class RechazoPublicacion(Exception):
    def __init__(
        self, motivo: str, *, codigo: int = 409, detalle: dict[str, Any] | None = None
    ) -> None:
        super().__init__(motivo)
        self.motivo = motivo
        self.codigo = codigo
        self.detalle = detalle or {}


# --- Acceso a Canvas ---


def _cliente_y_token(bd: Session, curso: Curso) -> tuple[ClienteCanvas, str, uuid.UUID]:
    credencial = canvas_repo.obtener_credencial_operativa(bd, curso.id)
    if credencial is None or curso.canvas_course_id is None:
        raise RechazoPublicacion("El curso no tiene una credencial de Canvas operativa.")
    settings = obtener_configuracion()
    token = canvas_repo.descifrar_token(
        Llavero(settings.llavero_cifrado(), settings.app_encryption_key_activa), credencial
    )
    cliente = crear_cliente_canvas(
        modo=settings.canvas_modo, canvas_base_url=curso.canvas_base_url or settings.canvas_base_url
    )
    return cliente, token, credencial.id


def _individual_en_canvas(bd: Session, entrega: Entrega) -> bool:
    """El grano lo decide Canvas (`grade_group_students_individually`), nunca
    la aplicacion (S12.10.3)."""
    espejo = (
        bd.query(AssignmentCanvas)
        .filter(
            AssignmentCanvas.curso_id == entrega.curso_id,
            AssignmentCanvas.canvas_assignment_id == entrega.canvas_assignment_id,
        )
        .one_or_none()
    )
    return bool((espejo.payload or {}).get("grade_group_students_individually")) if espejo else True


def guardar_espejo(
    bd: Session, entrega: Entrega, calificaciones: list[CalificacionCanvas], *, ahora: datetime
) -> None:
    por_canvas = {
        e.canvas_user_id: e.id
        for e in bd.query(Estudiante).filter(Estudiante.curso_id == entrega.curso_id)
    }
    for cal in calificaciones:
        estudiante_id = por_canvas.get(cal.canvas_user_id)
        if estudiante_id is None:
            continue
        fila = bd.get(EstadoCanvasSubmission, (entrega.id, estudiante_id))
        if fila is None:
            fila = EstadoCanvasSubmission(
                entrega_id=entrega.id, estudiante_id=estudiante_id, sincronizado_en=ahora
            )
            bd.add(fila)
        fila.workflow_state = cal.workflow_state
        fila.score = cal.score
        fila.entered_score = cal.entered_score
        fila.grade = cal.grade
        fila.graded_at = cal.graded_at
        fila.grader_id = cal.grader_id
        fila.excused = cal.excused
        fila.late = cal.late
        fila.seconds_late = cal.seconds_late
        fila.points_deducted = cal.points_deducted
        fila.submitted_at = cal.submitted_at
        fila.posted_at = cal.posted_at
        fila.sincronizado_en = ahora
    bd.flush()


# --- Pre-chequeo (S12.10.4) ---


def _fecha_de_entrega(bd: Session, entrega: Entrega, sujeto_id: uuid.UUID) -> datetime | None:
    fecha = (
        bd.query(FechaEfectiva)
        .filter(
            FechaEfectiva.entrega_id == entrega.id,
            FechaEfectiva.sujeto_id == sujeto_id,
            FechaEfectiva.estado == "VIGENTE",
        )
        .one_or_none()
    )
    return fecha.due_at_utc if fecha and fecha.due_at_utc else entrega.due_at_base


def _marcar_no_publicable(bd: Session, c: Correccion, motivo: str) -> None:
    c.publicable = False
    c.motivo_no_publicable = motivo
    bd.flush()


def _payload(
    bd: Session,
    c: Correccion,
    *,
    entrega: Entrega,
    curso: Curso,
    corrector: Usuario | None,
    rol: str,
    grupal_no_individual: bool,
) -> dict[str, Any]:
    version = bd.get(VersionEntrega, c.version_entrega_id) if c.version_entrega_id else None
    fecha = _fecha_de_entrega(bd, entrega, c.sujeto_id)
    texto = pie_comentario(
        texto=c.comentario or "",
        entrega=entrega.nombre,
        cierre=formatear_fecha(fecha, curso.zona_horaria) if fecha else "sin fecha",
        sha=version.commit_sha if version and version.estado != "SIN_COMMITS" else None,
        repositorio_full_name=version.repositorio_full_name if version else None,
        corrector=corrector.nombre if corrector else "el equipo docente",
        rol="profesor" if rol == "PROFESOR" else "ayudante",
    )
    c.comentario_renderizado = texto
    payload: dict[str, Any] = {
        "submission": {
            "posted_grade": normalizar_nota(
                entrega.grading_type, c.nota_local, entrega.puntos_posibles
            ),
            "late_policy_status": "none",
        },
        "comment": {"text_comment": texto},
    }
    if grupal_no_individual:
        payload["comment"]["group_comment"] = True
    criterios, _, _ = correccion_repo.rubrica_de(bd, entrega)
    evaluables = {str(x.get("id")): x for x in criterios if not es_solo_lectura(x)}
    rubrica = {
        cid: {
            k: v
            for k, v in (valor or {}).items()
            if k in ("points", "rating_id", "comments") and v is not None
        }
        for cid, valor in (c.rubrica_local or {}).items()
        if cid in evaluables
    }
    if criterios and rubrica:
        payload["rubric_assessment"] = rubrica
    return payload


def _intento_siguiente(bd: Session, correccion_id: uuid.UUID, estudiante_id: uuid.UUID) -> int:
    actual = (
        bd.query(func.max(PublicacionNota.intento))
        .filter(
            PublicacionNota.correccion_id == correccion_id,
            PublicacionNota.estudiante_id == estudiante_id,
        )
        .scalar()
    )
    return int(actual or 0) + 1


def publicar(
    bd: Session,
    c: Correccion,
    *,
    entrega: Entrega,
    curso: Curso,
    actor: MembresiaCurso,
    resolucion: str | None = None,
    version_revisada: bool = False,
    confirmacion_reclamo: str | None = None,
    reconocimiento_sin_codigo: bool = False,
) -> dict[str, Any]:
    if c.estado != EstadoCorreccion.LISTA_PARA_PUBLICAR.value:
        raise RechazoPublicacion("Solo se publica una corrección marcada como lista.")
    if not c.publicable:
        raise RechazoPublicacion(
            "Esta corrección no se puede publicar en Canvas.",
            detalle={"motivo_no_publicable": c.motivo_no_publicable},
        )
    criterios, ajustes, _ = correccion_repo.rubrica_de(bd, entrega)
    if (
        criterios
        and c.huella_rubrica is not None
        and c.huella_rubrica != huella_rubrica(criterios, ajustes)
        and c.rubrica_revisada_en is None
    ):
        raise RechazoPublicacion(
            "La rúbrica cambió en Canvas: revisa los criterios antes de publicar."
        )
    if c.version_desactualizada and not version_revisada:
        raise RechazoPublicacion("Hay una versión nueva registrada: confirma que la revisaste.")
    if c.reclamo_abierto and len((confirmacion_reclamo or "").strip()) < 10:
        raise RechazoPublicacion("Hay un reclamo abierto: escribe por qué publicas igual.")
    sujeto = bd.get(Sujeto, c.sujeto_id)
    assert sujeto is not None
    repo = correccion_repo.repositorio_de(bd, sujeto.id)
    if repo is not None and repo.estado == "INACCESIBLE" and not c.reconocimiento_sin_codigo:
        if not reconocimiento_sin_codigo:
            raise RechazoPublicacion(
                "Confirma que calificas sin haber podido abrir el código de esta versión."
            )
        c.reconocimiento_sin_codigo = True
        c.reconocimiento_sin_codigo_en = ahora_utc()
        bitacora_repo.registrar(
            bd,
            accion="CALIFICADA_SIN_CODIGO",
            entidad="correccion",
            entidad_id=str(c.id),
            actor_usuario_id=actor.usuario_id,
            curso_id=curso.id,
        )
    miembros = correccion_repo.integrantes(bd, sujeto)
    if not miembros:
        raise RechazoPublicacion("El sujeto no tiene integrantes a quienes poner la nota.")
    assert entrega.canvas_assignment_id is not None and curso.canvas_course_id is not None
    cliente, token, credencial_id = _cliente_y_token(bd, curso)
    ahora = ahora_utc()

    # 1. Pre-chequeo contra Canvas: periodo cerrado y calificables.
    with cerrojo_canvas(bd, curso.id):
        periodos = cliente.obtener_periodos_calificacion(token, curso.canvas_course_id)
        fecha = _fecha_de_entrega(bd, entrega, sujeto.id)
        if fecha is not None and any(
            p.is_closed and p.start_date and p.end_date and p.start_date <= fecha <= p.end_date
            for p in periodos
        ):
            _marcar_no_publicable(bd, c, "PERIODO_CERRADO")
            raise RechazoPublicacion("El período de calificación de Canvas está cerrado.")
        calificables = cliente.estudiantes_calificables(
            token, curso.canvas_course_id, entrega.canvas_assignment_id
        )
        if not any(m.canvas_user_id in calificables for m in miembros):
            _marcar_no_publicable(bd, c, "NO_GRADEABLE")
            raise RechazoPublicacion("Canvas no deja calificar a este sujeto en la tarea.")
        # 2. Conflicto: la misma lectura masiva que alimenta el espejo.
        leidas = cliente.leer_calificaciones(
            token, curso.canvas_course_id, entrega.canvas_assignment_id
        )
    guardar_espejo(bd, entrega, leidas, ahora=ahora)
    ultimas = correccion_repo.ultima_publicacion_por_estudiante(bd, [c.id])
    en_canvas = {m.id: bd.get(EstadoCanvasSubmission, (entrega.id, m.id)) for m in miembros}
    conflictos = [
        _resumen_conflicto(m, en_canvas[m.id])
        for m in miembros
        if hay_conflicto(ultimas.get((c.id, m.id)), en_canvas[m.id])
    ]
    if conflictos and resolucion != "PUBLICAR_MIA":
        incidencia_repo.abrir_o_actualizar(
            bd,
            tipo="NOTA_DIVERGENTE_EN_CANVAS",
            severidad="ADVERTENCIA",
            sujeto_tipo="CORRECCION",
            curso_id=curso.id,
            sujeto_id=c.id,
            detalle={"conflictos": conflictos, "nota_propia": c.nota_local},
        )
        raise RechazoPublicacion(
            "Canvas ya tiene otra nota para esta entrega.",
            detalle={"codigo": "CONFLICTO", "conflictos": conflictos, "nota_propia": c.nota_local},
        )

    # 3. Intencion persistida antes de la llamada (A-169 punto 2).
    grupal = sujeto.grupo_id is not None
    individual = not grupal or _individual_en_canvas(bd, entrega)
    corrector = bd.get(Usuario, c.corrector_usuario_id) if c.corrector_usuario_id else None
    rol_corrector = actor.rol
    try:
        payload = _payload(
            bd,
            c,
            entrega=entrega,
            curso=curso,
            corrector=corrector,
            rol=rol_corrector,
            grupal_no_individual=grupal and not individual,
        )
    except ValueError as exc:
        raise RechazoPublicacion(str(exc), codigo=422) from exc
    correccion_repo.transicionar(
        bd,
        c,
        EstadoCorreccion.PUBLICANDO,
        actor_usuario_id=actor.usuario_id,
        curso_id=curso.id,
        detalle={"resolucion": resolucion} if resolucion else None,
    )
    c.intentos += 1
    bd.commit()

    # 4. Escritura: una llamada por integrante, o una sola con group_comment.
    destinos = (
        [
            min(
                (m for m in miembros if m.canvas_user_id in calificables),
                key=lambda m: m.canvas_user_id,
            )
        ]
        if grupal and not individual
        else [m for m in miembros if m.canvas_user_id in calificables]
    )
    respuestas: dict[uuid.UUID, tuple[int | None, dict[str, Any]]] = {}
    error: str | None = None
    try:
        with cerrojo_canvas(bd, curso.id):
            for m in destinos:
                r = cliente.publicar_nota(
                    token,
                    curso.canvas_course_id,
                    entrega.canvas_assignment_id,
                    m.canvas_user_id,
                    payload,
                )
                respuestas[m.id] = (r.codigo_http, r.cuerpo)
                if r.codigo_http >= 300:
                    error = str(r.cuerpo)[:2000]
                    break
            if error is None:
                leidas = cliente.leer_calificaciones(
                    token, curso.canvas_course_id, entrega.canvas_assignment_id
                )
                por_uid = {x.canvas_user_id: x for x in leidas}
                # Remedio: si la propagacion de grupo no alcanzo a alguien, PUT individual.
                for m in miembros:
                    fila = por_uid.get(m.canvas_user_id)
                    if m.canvas_user_id in calificables and (
                        fila is None or fila.graded_at is None
                    ):
                        r = cliente.publicar_nota(
                            token,
                            curso.canvas_course_id,
                            entrega.canvas_assignment_id,
                            m.canvas_user_id,
                            {k: v for k, v in payload.items() if k != "comment"}
                            | {"comment": {"text_comment": payload["comment"]["text_comment"]}},
                        )
                        respuestas[m.id] = (r.codigo_http, r.cuerpo)
                if any(m.id in respuestas for m in miembros):
                    leidas = cliente.leer_calificaciones(
                        token, curso.canvas_course_id, entrega.canvas_assignment_id
                    )
    except FalloProveedorCanvas as exc:
        error = str(exc)
    ahora = ahora_utc()
    if error is not None:
        c.ultimo_error = error
        for m in destinos:
            codigo, cuerpo = respuestas.get(m.id, (None, {"error": error}))
            _evidencia(bd, c, m, payload, codigo, cuerpo, None, actor, credencial_id, ahora)
        correccion_repo.transicionar(
            bd,
            c,
            EstadoCorreccion.ERROR_PUBLICACION,
            actor_usuario_id=actor.usuario_id,
            curso_id=curso.id,
            detalle={"error": error},
        )
        return {"estado": c.estado, "error": error}

    # 5. Verificacion posterior contra lo que Canvas guardo (S12.10.5).
    guardar_espejo(bd, entrega, leidas, ahora=ahora)
    por_uid = {x.canvas_user_id: x for x in leidas}
    enviado = _valor_numerico(payload["submission"]["posted_grade"])
    resultados = []
    for m in miembros:
        fila = por_uid.get(m.canvas_user_id)
        codigo, cuerpo = respuestas.get(m.id, (200, {"propagado_desde": "comentario de grupo"}))
        _evidencia(bd, c, m, payload, codigo, cuerpo, fila, actor, credencial_id, ahora)
        resultados.append(
            resultado_verificacion(
                enviado=enviado,
                devuelto_score=fila.score if fila else None,
                devuelto_entered=fila.entered_score if fila else None,
                points_deducted=fila.points_deducted if fila else None,
                calificado=bool(fila and fila.graded_at),
            )
        )
    final = (
        EstadoCorreccion.PUBLICADA
        if all(r == "PUBLICADA" for r in resultados)
        else EstadoCorreccion.PUBLICADA_CON_ADVERTENCIA
    )
    c.publicada_en = ahora
    c.ultimo_error = None
    correccion_repo.transicionar(bd, c, final, actor_usuario_id=actor.usuario_id, curso_id=curso.id)
    incidencia_repo.cerrar(bd, tipo="NOTA_DIVERGENTE_EN_CANVAS", curso_id=curso.id, sujeto_id=c.id)
    _avisar_estudiantes(
        bd,
        c,
        entrega=entrega,
        curso=curso,
        miembros=miembros,
        nota=payload["submission"]["posted_grade"],
    )
    encolar_reconciliacion(bd, curso.id, entrega.id, motivo=f"publicacion:{c.id}:{c.intentos}")
    return {"estado": c.estado, "resultados": resultados}


def _resumen_conflicto(m: Estudiante, fila: EstadoCanvasSubmission | None) -> dict[str, Any]:
    return {
        "estudiante": m.nombre,
        "nota_canvas": float(fila.score) if fila is not None and fila.score is not None else None,
        "calificada_en": fila.graded_at.isoformat()
        if fila is not None and fila.graded_at
        else None,
    }


def _valor_numerico(nota: str) -> float | None:
    try:
        return float(nota.rstrip("%"))
    except ValueError:
        return None


def _evidencia(
    bd: Session,
    c: Correccion,
    m: Estudiante,
    payload: dict[str, Any],
    codigo: int | None,
    cuerpo: dict[str, Any],
    fila: CalificacionCanvas | None,
    actor: MembresiaCurso,
    credencial_id: uuid.UUID,
    ahora: datetime,
) -> None:
    """Una fila por estudiante e intento, tambien en grupos (S12.2.4)."""
    bd.add(
        PublicacionNota(
            correccion_id=c.id,
            estudiante_id=m.id,
            intento=_intento_siguiente(bd, c.id, m.id),
            payload_enviado=payload,
            codigo_http=codigo,
            respuesta=cuerpo,
            score_devuelto=fila.score if fila else None,
            entered_score_devuelto=fila.entered_score if fila else None,
            grade_devuelto=fila.grade if fila else None,
            grader_id_reportado=fila.grader_id if fila else None,
            late_policy_status_enviado="none",
            publicado_por_usuario_id=actor.usuario_id,
            credencial_canvas_id=credencial_id,
            intentada_en=ahora,
        )
    )
    bd.flush()


def _avisar_estudiantes(
    bd: Session,
    c: Correccion,
    *,
    entrega: Entrega,
    curso: Curso,
    miembros: list[Estudiante],
    nota: str,
) -> None:
    """`correccion_publicada` (apagado por defecto): nace con la fila de
    publicacion verificada, una por persona con su propia nota. El
    interruptor lo filtra en el despacho (guarda 4)."""
    for m in miembros:
        comunicaciones_repo.encolar_a_estudiante(
            bd,
            curso=curso,
            estudiante=m,
            evento="correccion_publicada",
            plantilla="correccion_publicada",
            entidad=f"{c.id}:{m.id}:{c.intentos}",
            referencia={"entrega_nombre": entrega.nombre, "nota": nota},
            tarea_id=entrega.tarea_id,
            entrega_id=entrega.id,
            sujeto_id=c.sujeto_id,
        )


# --- Salidas del conflicto, reintento y reapertura (S12.14.2, S12.15.2) ---


def adoptar_nota_de_canvas(
    bd: Session, c: Correccion, *, entrega: Entrega, actor: MembresiaCurso
) -> None:
    """Copia la nota de Canvas al borrador y cierra la incidencia; no escribe
    en Canvas (CA-12.14-04)."""
    sujeto = bd.get(Sujeto, c.sujeto_id)
    assert sujeto is not None
    miembros = correccion_repo.integrantes(bd, sujeto)
    filas = [bd.get(EstadoCanvasSubmission, (entrega.id, m.id)) for m in miembros]
    nota = next((f.score for f in filas if f is not None and f.score is not None), None)
    if nota is None:
        raise RechazoPublicacion("Canvas no tiene una nota que adoptar.")
    antes = c.nota_local
    c.nota_local = f"{float(nota):g}"
    c.actualizado_en = ahora_utc()
    incidencia_repo.cerrar(
        bd, tipo="NOTA_DIVERGENTE_EN_CANVAS", curso_id=entrega.curso_id, sujeto_id=c.id
    )
    bitacora_repo.registrar(
        bd,
        accion="NOTA_DE_CANVAS_ADOPTADA",
        entidad="correccion",
        entidad_id=str(c.id),
        actor_usuario_id=actor.usuario_id,
        curso_id=entrega.curso_id,
        antes={"nota_local": antes},
        despues={"nota_local": c.nota_local},
    )


def reintentar(bd: Session, c: Correccion, *, actor: MembresiaCurso, curso_id: uuid.UUID) -> None:
    if c.estado != EstadoCorreccion.ERROR_PUBLICACION.value:
        raise RechazoPublicacion("Solo se reintenta una publicación que falló.")
    correccion_repo.transicionar(
        bd,
        c,
        EstadoCorreccion.LISTA_PARA_PUBLICAR,
        actor_usuario_id=actor.usuario_id,
        curso_id=curso_id,
    )


def reabrir(
    bd: Session, c: Correccion, *, actor: MembresiaCurso, curso_id: uuid.UUID, motivo: str
) -> None:
    """La nota publicada nunca cambia sola; reabrir es un acto explicito con
    motivo (CA-12.15-03). La proxima publicacion es un intento nuevo."""
    if c.estado not in TERMINALES:
        raise RechazoPublicacion("Solo se reabre una corrección publicada.")
    if len(motivo.strip()) < 5:
        raise RechazoPublicacion("Escribe por qué reabres la corrección.", codigo=422)
    c.motivo_reapertura = motivo
    c.reabierta_en = ahora_utc()
    c.reabierta_por = actor.usuario_id
    correccion_repo.transicionar(
        bd,
        c,
        EstadoCorreccion.EN_CURSO,
        actor_usuario_id=actor.usuario_id,
        curso_id=curso_id,
        detalle={"motivo": motivo},
    )


# --- Reconciliacion (S12.13) ---


def encolar_reconciliacion(
    bd: Session, curso_id: uuid.UUID, entrega_id: uuid.UUID, *, motivo: str
) -> None:
    from app.adaptadores.modelos_infraestructura import Trabajo
    from app.dominio.estados import EstadoTrabajo

    clave = f"{TIPO_RECONCILIAR}:{entrega_id}:{motivo}"
    if (
        bd.query(Trabajo.id)
        .filter(
            Trabajo.clave_idempotencia == clave,
            Trabajo.estado.notin_([EstadoTrabajo.OK.value, EstadoTrabajo.CANCELADO.value]),
        )
        .first()
    ):
        return
    trabajos_repo.encolar(
        bd,
        tipo=TIPO_RECONCILIAR,
        clave_idempotencia=clave,
        max_intentos=4,
        curso_id=curso_id,
        payload={"entrega_id": str(entrega_id)},
    )


def entregas_a_reconciliar(bd: Session, curso: Curso, *, ahora: datetime) -> list[Entrega]:
    """Cada 30 minutos dentro de la ventana de correccion (desde que vencio la
    ultima fecha efectiva, hasta que todo este publicado o pasen 21 dias); una
    vez al dia fuera de ella; nunca en una tarea archivada."""
    salida = []
    for entrega, tarea in (
        bd.query(Entrega, Tarea)
        .join(Tarea, Tarea.id == Entrega.tarea_id)
        .filter(
            Tarea.curso_id == curso.id, Tarea.estado.in_(("ACTIVA", "INCONSISTENTE", "CERRADA"))
        )
    ):
        ultima = (
            bd.query(func.max(FechaEfectiva.due_at_utc))
            .filter(FechaEfectiva.entrega_id == entrega.id, FechaEfectiva.estado == "VIGENTE")
            .scalar()
        )
        if not isinstance(ultima, datetime) or ultima > ahora:
            continue
        leido = (
            bd.query(func.max(EstadoCanvasSubmission.sincronizado_en))
            .filter(EstadoCanvasSubmission.entrega_id == entrega.id)
            .scalar()
        )
        pendientes = (
            bd.query(Correccion.id)
            .filter(
                Correccion.entrega_id == entrega.id, Correccion.estado.notin_(tuple(TERMINALES))
            )
            .first()
            is not None
        )
        en_ventana = ahora - ultima <= VENTANA_CORRECCION and pendientes
        if tarea.estado == "CERRADA" and not en_ventana:
            continue
        cadencia = timedelta(minutes=30) if en_ventana else timedelta(days=1)
        if not isinstance(leido, datetime) or ahora - leido >= cadencia:
            salida.append(entrega)
    return salida


def reconciliar(bd: Session, curso: Curso, entrega: Entrega) -> int:
    """Lee Canvas una vez por entrega, renueva el espejo y abre
    NOTA_DIVERGENTE_EN_CANVAS donde el contraste da DIVERGE. Nunca pisa el
    estado local."""
    assert entrega.canvas_assignment_id is not None and curso.canvas_course_id is not None
    cliente, token, _ = _cliente_y_token(bd, curso)
    ahora = ahora_utc()
    with cerrojo_canvas(bd, curso.id):
        leidas = cliente.leer_calificaciones(
            token, curso.canvas_course_id, entrega.canvas_assignment_id
        )
    guardar_espejo(bd, entrega, leidas, ahora=ahora)
    correccion_repo.asegurar_filas(bd, entrega)
    divergentes = 0
    correcciones = bd.query(Correccion).filter(Correccion.entrega_id == entrega.id).all()
    ultimas = correccion_repo.ultima_publicacion_por_estudiante(bd, [c.id for c in correcciones])
    for c in correcciones:
        sujeto = bd.get(Sujeto, c.sujeto_id)
        if sujeto is None:
            continue
        miembros = correccion_repo.integrantes(bd, sujeto)
        contraste = contraste_canvas(
            [ultimas.get((c.id, m.id)) for m in miembros],
            [bd.get(EstadoCanvasSubmission, (entrega.id, m.id)) for m in miembros],
        )
        if contraste == "DIVERGE":
            divergentes += 1
            filas = [bd.get(EstadoCanvasSubmission, (entrega.id, m.id)) for m in miembros]
            incidencia_repo.abrir_o_actualizar(
                bd,
                tipo="NOTA_DIVERGENTE_EN_CANVAS",
                severidad="ADVERTENCIA",
                sujeto_tipo="CORRECCION",
                curso_id=curso.id,
                sujeto_id=c.id,
                detalle={
                    "canvas": [
                        {
                            "nota": float(f.score) if f and f.score is not None else None,
                            "grader_id": f.grader_id if f else None,
                        }
                        for f in filas
                    ],
                    "aplicacion": c.nota_local,
                },
            )
    bd.flush()
    return divergentes
