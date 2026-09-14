"""Outbox de comunicaciones al estudiante (SPEC 11 S11.2; SPEC 08 S8.10; A-125,
A-127, A-224, A-227; Etapa P8).

Ninguna comunicacion sale de una vista: se inserta en `mensaje_saliente` con su
clave de idempotencia por persona y la despacha `despachar_outbox`. El cuerpo se
renderiza en el despacho, no al encolar (S11.2.1).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adaptadores import canvas_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_canvas import FalloProveedorCanvas, crear_cliente_canvas
from app.adaptadores.modelos_aprovisionamiento import (
    AccesoRepositorio,
    MensajeSaliente,
    Repositorio,
    Sujeto,
)
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_mapeo import CuentaGithub
from app.adaptadores.modelos_padron import Estudiante
from app.adaptadores.modelos_tarea import Tarea
from app.dominio.comunicaciones import (
    PLANTILLAS,
    PlantillaInvalida,
    clave_idempotencia,
    guardas_outbox,
    instrucciones_de_acceso,
    renderizar,
)
from app.dominio.estados import (
    CanalComunicacionActivo,
    CanalMensaje,
    EstadoAccesoRepositorio,
    EstadoMensaje,
    OrigenMensaje,
)
from app.dominio.fechas import formatear_fecha
from app.infraestructura.cerrojos import cerrojo_canvas
from app.infraestructura.cifrado import Llavero
from app.infraestructura.config import obtener_configuracion

EVENTO_REPOSITORIO_DISPONIBLE = "repositorio_disponible"
EVENTO_INVITACION_ACEPTADA = "invitacion_aceptada"

# S11.2.2: seis intentos con retroceso, tope 5 minutos.
_MAX_INTENTOS = 6
_ESPERA_BLOQUEADO = timedelta(minutes=30)


def _canal_para(curso: Curso) -> CanalMensaje:
    """A-127: canal 1 mensaje directo; canal 2 comentario en la entrega de la
    tarea de registro. Con el checklist sin correr todavia se intenta el 1."""
    if curso.canal_comunicacion_activo == CanalComunicacionActivo.COMENTARIO_ENTREGA.value:
        return CanalMensaje.CANVAS_COMENTARIO
    return CanalMensaje.CANVAS_CONVERSACION


def encolar_aviso_acceso(
    bd: Session,
    *,
    curso: Curso,
    tarea: Tarea,
    sujeto: Sujeto,
    repositorio: Repositorio,
    estudiante: Estudiante,
    acceso: AccesoRepositorio,
    evento: str,
    fecha_cierre: datetime | None,
    trabajo_id: uuid.UUID | None = None,
) -> MensajeSaliente | None:
    """R2.3.12 por persona (A-127): una clave por `(tarea, sujeto, estudiante)`
    para `repositorio_disponible` y por `acceso_repositorio` para
    `invitacion_aceptada` (S11.6.1). Encolar dos veces el mismo hecho no crea
    un segundo mensaje. Devuelve la fila nueva, o `None` si ya existia."""
    canal = _canal_para(curso)
    entidad = (
        f"{tarea.id}:{sujeto.id}:{estudiante.id}"
        if evento == EVENTO_REPOSITORIO_DISPONIBLE
        else str(acceso.id)
    )
    clave = clave_idempotencia(
        canal=canal.value,
        destinatario=str(estudiante.canvas_user_id),
        plantilla=evento,
        entidad=entidad,
    )
    if bd.query(MensajeSaliente.id).filter(MensajeSaliente.clave_idempotencia == clave).first():
        return None
    plantilla = PLANTILLAS[evento]
    mensaje = MensajeSaliente(
        curso_id=curso.id,
        canal=canal.value,
        evento=evento,
        clave_idempotencia=clave,
        generacion=1,
        tarea_id=tarea.id,
        sujeto_id=sujeto.id,
        repositorio_id=repositorio.id,
        estudiante_id=estudiante.id,
        referencia={
            "acceso_repositorio_id": str(acceso.id),
            "via_invitacion": acceso.estado == EstadoAccesoRepositorio.INVITADO.value,
            "invitacion_url": acceso.invitacion_html_url,
            "fecha_cierre": fecha_cierre.isoformat() if fecha_cierre else None,
        },
        destinatario=estudiante.nombre,
        destinatario_canvas_user_id=estudiante.canvas_user_id,
        plantilla=evento,
        plantilla_version=plantilla.version,
        origen=OrigenMensaje.AUTOMATICO.value,
        disparado_por_trabajo_id=trabajo_id,
        # S11.2.4: `repositorio_disponible` e `invitacion_aceptada` nunca caducan.
        caduca_en=None,
        estado=EstadoMensaje.PENDIENTE.value,
        intentos=0,
        creado_en=ahora_utc(),
    )
    bd.add(mensaje)
    bd.flush()
    return mensaje


def _valores(bd: Session, mensaje: MensajeSaliente, curso: Curso) -> dict[str, str]:
    tarea = bd.get(Tarea, mensaje.tarea_id)
    repositorio = bd.get(Repositorio, mensaje.repositorio_id)
    estudiante = bd.get(Estudiante, mensaje.estudiante_id)
    assert tarea is not None and repositorio is not None and estudiante is not None
    referencia: dict[str, Any] = mensaje.referencia or {}
    acceso = (
        bd.get(AccesoRepositorio, uuid.UUID(referencia["acceso_repositorio_id"]))
        if referencia.get("acceso_repositorio_id")
        else None
    )
    cuenta = (
        bd.get(CuentaGithub, acceso.cuenta_github_id)
        if acceso is not None and acceso.cuenta_github_id
        else None
    )
    fecha = referencia.get("fecha_cierre")
    return {
        "estudiante.nombre": estudiante.nombre,
        "tarea.nombre": tarea.nombre,
        "curso.nombre": curso.nombre,
        "organizacion.nombre": curso.github_org_login or "",
        "repositorio.nombre": repositorio.nombre,
        "repositorio.url": repositorio.url_html or "",
        "acceso.instrucciones": instrucciones_de_acceso(
            via_invitacion=bool(referencia.get("via_invitacion")),
            invitacion_url=referencia.get("invitacion_url"),
        ),
        "entrega.fecha_cierre": formatear_fecha(
            datetime.fromisoformat(fecha) if fecha else None, curso.zona_horaria
        ),
        "cuenta_github.login": cuenta.login if cuenta is not None else "",
    }


def despachar_pendientes(bd: Session, *, tomado_por: str, limite: int = 20) -> int:
    """Una pasada de `despachar_outbox`. Las guardas se evaluan inmediatamente
    antes de cada intento, no al encolar (S11.2.3)."""
    ahora = ahora_utc()
    mensajes = (
        bd.execute(
            select(MensajeSaliente)
            .where(
                MensajeSaliente.estado.in_(
                    [
                        EstadoMensaje.PENDIENTE.value,
                        EstadoMensaje.REINTENTAR.value,
                        EstadoMensaje.BLOQUEADO.value,
                    ]
                ),
                (MensajeSaliente.programado_para.is_(None))
                | (MensajeSaliente.programado_para <= ahora),
            )
            .order_by(MensajeSaliente.creado_en)
            .limit(limite)
            .with_for_update(skip_locked=True)
        )
        .scalars()
        .all()
    )
    despachados = 0
    for mensaje in mensajes:
        _despachar_uno(bd, mensaje, tomado_por=tomado_por, ahora=ahora)
        despachados += 1
    return despachados


def _despachar_uno(
    bd: Session, mensaje: MensajeSaliente, *, tomado_por: str, ahora: datetime
) -> None:
    curso = bd.get(Curso, mensaje.curso_id)
    estudiante = bd.get(Estudiante, mensaje.estudiante_id) if mensaje.estudiante_id else None
    assert curso is not None

    guarda = guardas_outbox(
        ahora=ahora,
        caduca_en=mensaje.caduca_en,
        estado_estudiante=estudiante.estado if estudiante is not None else None,
    )
    if guarda is not None:
        mensaje.estado, mensaje.motivo_estado = guarda[0].value, guarda[1]
        bd.flush()
        return

    if curso.canal_comunicacion_activo == CanalComunicacionActivo.BLOQUEADO.value:
        # A-227: sin canal no se da por enviado; se reevalua cada 30 min.
        mensaje.estado = EstadoMensaje.BLOQUEADO.value
        mensaje.ultimo_error_literal = "El curso no tiene ningún canal de Canvas disponible."
        mensaje.programado_para = ahora + _ESPERA_BLOQUEADO
        bd.flush()
        return

    plantilla = PLANTILLAS[mensaje.plantilla]
    try:
        valores = _valores(bd, mensaje, curso)
        mensaje.asunto = renderizar(plantilla.asunto, plantilla, valores)[:255]
        mensaje.cuerpo_renderizado = renderizar(plantilla.cuerpo, plantilla, valores)
    except PlantillaInvalida as exc:
        mensaje.estado = EstadoMensaje.FALLIDO.value
        mensaje.ultimo_error_literal = str(exc)
        bd.flush()
        return

    credencial = canvas_repo.obtener_credencial_operativa(bd, curso.id)
    if credencial is None or curso.canvas_course_id is None:
        mensaje.estado = EstadoMensaje.ESPERANDO_CREDENCIAL.value
        mensaje.ultimo_error_literal = "El curso no tiene una credencial de Canvas operativa."
        bd.flush()
        return

    settings = obtener_configuracion()
    token = canvas_repo.descifrar_token(
        Llavero(settings.llavero_cifrado(), settings.app_encryption_key_activa), credencial
    )
    cliente = crear_cliente_canvas(
        modo=settings.canvas_modo, canvas_base_url=curso.canvas_base_url or settings.canvas_base_url
    )

    mensaje.estado = EstadoMensaje.EN_CURSO.value
    mensaje.tomado_por = tomado_por
    mensaje.tomado_en = ahora
    mensaje.intentos += 1
    bd.flush()

    canal = CanalMensaje(mensaje.canal)
    try:
        with cerrojo_canvas(bd, curso.id):
            if canal == CanalMensaje.CANVAS_COMENTARIO and curso.canvas_assignment_id_registro:
                enviado = cliente.comentar_entrega(
                    token,
                    curso.canvas_course_id,
                    curso.canvas_assignment_id_registro,
                    mensaje.destinatario_canvas_user_id or 0,
                    f"{mensaje.asunto}\n\n{mensaje.cuerpo_renderizado}",
                )
            else:
                canal = CanalMensaje.CANVAS_CONVERSACION
                enviado = cliente.enviar_conversacion(
                    token,
                    destinatarios_canvas_user_ids=[mensaje.destinatario_canvas_user_id or 0],
                    asunto=mensaje.asunto or "",
                    cuerpo=mensaje.cuerpo_renderizado or "",
                )
    except FalloProveedorCanvas as exc:
        _reintentar(mensaje, ahora=ahora, error=str(exc))
        bd.flush()
        return

    mensaje.canal_efectivo = canal.value
    mensaje.tomado_por = None
    mensaje.tomado_en = None
    if enviado:
        mensaje.estado = EstadoMensaje.ENVIADO.value
        mensaje.enviado_en = ahora
        mensaje.ultimo_error_literal = None
    else:
        # El cliente de Canvas solo informa exito o rechazo: un rechazo 4xx es
        # PERMANENTE y no se reintenta solo (S11.2.2).
        mensaje.estado = EstadoMensaje.FALLIDO.value
        mensaje.ultimo_error_literal = "Canvas rechazó el mensaje."
    bd.flush()


def _reintentar(mensaje: MensajeSaliente, *, ahora: datetime, error: str) -> None:
    mensaje.tomado_por = None
    mensaje.tomado_en = None
    mensaje.ultimo_error_literal = error
    if mensaje.intentos >= _MAX_INTENTOS:
        mensaje.estado = EstadoMensaje.FALLIDO.value
        return
    mensaje.estado = EstadoMensaje.REINTENTAR.value
    espera = min(2 * (2 ** (mensaje.intentos - 1)), 300)
    mensaje.programado_para = ahora + timedelta(seconds=espera)
