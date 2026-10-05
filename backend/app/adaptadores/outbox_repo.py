"""Outbox de comunicaciones al estudiante (SPEC 11 S11.2; SPEC 08 S8.10; A-125,
A-127, A-224, A-227; Etapa P8).

Ninguna comunicacion sale de una vista: se inserta en `mensaje_saliente` con su
clave de idempotencia por persona y la despacha `despachar_outbox`. El cuerpo se
renderiza en el despacho, no al encolar (S11.2.1).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adaptadores import canvas_repo, invitaciones_correo
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
EVENTO_AVISO_ARCHIVADO_PREVIO = "aviso_archivado_previo"
EVENTO_AVISO_ARCHIVADO = "aviso_archivado"

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


def encolar_aviso_archivado(
    bd: Session,
    *,
    curso: Curso,
    tarea: Tarea,
    repositorio: Repositorio,
    estudiante: Estudiante,
    evento: str,
    origen: OrigenMensaje,
    trabajo_id: uuid.UUID | None = None,
) -> MensajeSaliente | None:
    """Guarda 4 de A-197: un aviso por `(tarea, repositorio, estudiante)` y
    evento. Devuelve la fila nueva, o `None` si ese aviso ya existia."""
    canal = _canal_para(curso)
    clave = clave_idempotencia(
        canal=canal.value,
        destinatario=str(estudiante.canvas_user_id),
        plantilla=evento,
        entidad=f"{tarea.id}:{repositorio.id}:{estudiante.id}",
    )
    if bd.query(MensajeSaliente.id).filter(MensajeSaliente.clave_idempotencia == clave).first():
        return None
    mensaje = MensajeSaliente(
        curso_id=curso.id,
        canal=canal.value,
        evento=evento,
        clave_idempotencia=clave,
        generacion=1,
        tarea_id=tarea.id,
        sujeto_id=repositorio.sujeto_id,
        repositorio_id=repositorio.id,
        estudiante_id=estudiante.id,
        referencia={},
        destinatario=estudiante.nombre,
        destinatario_canvas_user_id=estudiante.canvas_user_id,
        plantilla=evento,
        plantilla_version=PLANTILLAS[evento].version,
        origen=origen.value,
        disparado_por_trabajo_id=trabajo_id,
        caduca_en=None,
        estado=EstadoMensaje.PENDIENTE.value,
        intentos=0,
        creado_en=ahora_utc(),
    )
    bd.add(mensaje)
    bd.flush()
    return mensaje


def _titular(bd: Session, curso: Curso) -> str:
    """Quien recibe las respuestas en Canvas: el dueño de la credencial
    operativa (S11.7.7)."""
    from app.adaptadores.modelos_identidad import Usuario

    credencial = canvas_repo.obtener_credencial_operativa(bd, curso.id)
    usuario_id = getattr(credencial, "usuario_id", None) if credencial is not None else None
    usuario = bd.get(Usuario, usuario_id) if usuario_id else None
    return usuario.nombre if usuario is not None else "el profesor del curso"


def _valores(bd: Session, mensaje: MensajeSaliente, curso: Curso) -> dict[str, str]:
    tarea = bd.get(Tarea, mensaje.tarea_id) if mensaje.tarea_id else None
    repositorio = bd.get(Repositorio, mensaje.repositorio_id) if mensaje.repositorio_id else None
    estudiante = bd.get(Estudiante, mensaje.estudiante_id) if mensaje.estudiante_id else None
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
        "estudiante.nombre": estudiante.nombre if estudiante is not None else "",
        "tarea.nombre": tarea.nombre if tarea is not None else "",
        "curso.nombre": curso.nombre,
        "curso.codigo": curso.codigo,
        "curso.titular": _titular(bd, curso),
        "organizacion.nombre": curso.github_org_login or "",
        "repositorio.nombre": repositorio.nombre if repositorio is not None else "",
        "repositorio.url": (repositorio.url_html or "") if repositorio is not None else "",
        "acceso.instrucciones": instrucciones_de_acceso(
            via_invitacion=bool(referencia.get("via_invitacion")),
            invitacion_url=referencia.get("invitacion_url"),
        ),
        "entrega.nombre": str(referencia.get("entrega_nombre", "")),
        "entrega.fecha_cierre": formatear_fecha(
            datetime.fromisoformat(fecha) if fecha else None, curso.zona_horaria
        ),
        "cuenta_github.login": cuenta.login if cuenta is not None else "",
        "grupo.nombre": str(referencia.get("grupo_nombre", "")),
        "correccion.nota": str(referencia.get("nota", "")),
        "mensaje.asunto": str(referencia.get("asunto", "")),
        "mensaje.cuerpo": str(referencia.get("cuerpo", "")),
        "docente.nombre": str(referencia.get("autor", "")),
    }


# Solo las pruebas la apagan: la franja 08:00-21:00 depende de la hora real.
FRANJA_ACTIVA = True
_ESPERA_DIFERIDO = timedelta(minutes=30)
_ESTADOS_A_TOMAR = (
    EstadoMensaje.PENDIENTE.value,
    EstadoMensaje.PROGRAMADO.value,
    EstadoMensaje.REINTENTAR.value,
    EstadoMensaje.BLOQUEADO.value,
    EstadoMensaje.DIFERIDO.value,
)


def despachar_pendientes(
    bd: Session, *, tomado_por: str, limite: int = 20, ahora: datetime | None = None
) -> int:
    """Una pasada de `despachar_outbox`. Las guardas se evaluan inmediatamente
    antes de cada intento, no al encolar (S11.2.3). Dentro de la pasada sale
    primero lo de mayor prioridad (S11.6.5)."""
    from app.dominio.comunicaciones import orden_de_prioridad

    ahora = ahora or ahora_utc()
    mensajes = (
        bd.execute(
            select(MensajeSaliente)
            .where(
                MensajeSaliente.estado.in_(_ESTADOS_A_TOMAR),
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
    for mensaje in sorted(mensajes, key=lambda m: (orden_de_prioridad(m.evento), m.creado_en)):
        _despachar_uno(bd, mensaje, tomado_por=tomado_por, ahora=ahora)
        despachados += 1
    _retractar_pendientes(bd, ahora=ahora)
    return despachados


def _hechos_de_guarda(
    bd: Session,
    mensaje: MensajeSaliente,
    curso: Curso,
    estudiante: Estudiante | None,
    ahora: datetime,
) -> dict[str, Any]:
    from app.adaptadores import comunicaciones_repo

    automatico = mensaje.origen == OrigenMensaje.AUTOMATICO.value
    return {
        "evento": mensaje.evento,
        "automatico": automatico,
        "supresion_alcance": (
            comunicaciones_repo.supresion_vigente(bd, curso.id, estudiante.id, ahora)
            if estudiante is not None
            else None
        ),
        "regla_activa": (
            comunicaciones_repo.regla_activa(bd, curso.id, mensaje.tarea_id, mensaje.evento)
            if automatico
            else True
        ),
        "modo_escritura": curso.modo_escritura,
        "comunicaciones_salientes": curso.comunicaciones_salientes,
        "canal": mensaje.canal,
        "en_ventana_supresion": comunicaciones_repo.en_ventana_supresion(bd, curso.id, ahora),
    }


def _despachar_uno(
    bd: Session, mensaje: MensajeSaliente, *, tomado_por: str, ahora: datetime
) -> None:
    from app.adaptadores import comunicaciones_repo
    from app.dominio.comunicaciones import (
        TOPE_DIARIO_AUTOMATICOS,
        cuenta_para_tope,
        exento_de_franja,
        siguiente_apertura,
    )

    if mensaje.canal == CanalMensaje.CORREO.value and mensaje.evento != "INFORME_DIARIO":
        # Invitaciones al equipo docente (entrega parcial): su propio despacho.
        invitaciones_correo.despachar(bd, mensaje, ahora=ahora)
        bd.flush()
        return
    curso = bd.get(Curso, mensaje.curso_id)
    assert curso is not None
    if mensaje.canal == CanalMensaje.CORREO.value:
        _despachar_correo(bd, mensaje, curso, tomado_por=tomado_por, ahora=ahora)
        return
    estudiante = bd.get(Estudiante, mensaje.estudiante_id) if mensaje.estudiante_id else None

    guarda = guardas_outbox(
        ahora=ahora,
        caduca_en=mensaje.caduca_en,
        estado_estudiante=estudiante.estado if estudiante is not None else None,
        **_hechos_de_guarda(bd, mensaje, curso, estudiante, ahora),
    )
    if guarda is not None:
        mensaje.estado, mensaje.motivo_estado = guarda[0].value, guarda[1]
        if guarda[0] == EstadoMensaje.DIFERIDO:
            mensaje.programado_para = ahora + _ESPERA_DIFERIDO
        bd.flush()
        return
    mensaje.motivo_estado = None

    zona = ZoneInfo(curso.zona_horaria)
    referencia: dict[str, Any] = mensaje.referencia or {}
    if (
        FRANJA_ACTIVA
        and mensaje.canal != CanalMensaje.CANVAS_ANUNCIO.value
        and not exento_de_franja(
            evento=mensaje.evento, origen=mensaje.origen, ventana=referencia.get("ventana")
        )
    ):
        apertura = siguiente_apertura(ahora.astimezone(zona))
        if apertura is not None:
            # S11.6.5: fuera de 08:00-21:00 espera a la proxima apertura.
            mensaje.estado = EstadoMensaje.PROGRAMADO.value
            mensaje.programado_para = apertura.astimezone(UTC)
            bd.flush()
            return
    if (
        estudiante is not None
        and cuenta_para_tope(evento=mensaje.evento, origen=mensaje.origen, canal=mensaje.canal)
        and comunicaciones_repo.automaticos_enviados_hoy(bd, curso, estudiante.id, ahora)
        >= TOPE_DIARIO_AUTOMATICOS
    ):
        # Tope de 3 por estudiante y dia del curso: sale al dia siguiente.
        manana = (ahora.astimezone(zona) + timedelta(days=1)).replace(
            hour=8, minute=0, second=0, microsecond=0
        )
        mensaje.estado = EstadoMensaje.PROGRAMADO.value
        mensaje.programado_para = manana.astimezone(UTC)
        bd.flush()
        return

    if curso.canal_comunicacion_activo == CanalComunicacionActivo.BLOQUEADO.value:
        # A-227: sin canal no se da por enviado; se reevalua cada 30 min.
        mensaje.estado = EstadoMensaje.BLOQUEADO.value
        mensaje.ultimo_error_literal = "El curso no tiene ningún canal de Canvas disponible."
        mensaje.programado_para = ahora + _ESPERA_BLOQUEADO
        bd.flush()
        return

    fusionado = None
    if mensaje.canal == CanalMensaje.CANVAS_ANUNCIO.value:
        mensaje.asunto = str(referencia.get("titulo", ""))[:255]
        mensaje.cuerpo_renderizado = str(referencia.get("cuerpo_html", ""))
    else:
        clave_plantilla = mensaje.plantilla
        valores_extra: dict[str, str] = {}
        if mensaje.evento == "repositorio_disponible":
            fusionado = comunicaciones_repo.proximidad_para_fusionar(bd, mensaje)
            if fusionado is not None:
                clave_plantilla = "repositorio_y_cierre"
                ref_prox = fusionado.referencia or {}
                valores_extra = {
                    "entrega.nombre": str(ref_prox.get("entrega_nombre", "")),
                    "entrega.fecha_cierre": formatear_fecha(
                        datetime.fromisoformat(ref_prox["fecha_cierre"]), curso.zona_horaria
                    ),
                }
        plantilla = PLANTILLAS[clave_plantilla]
        try:
            valores = {**_valores(bd, mensaje, curso), **valores_extra}
            mensaje.asunto = renderizar(plantilla.asunto, plantilla, valores)[:255]
            cuerpo = renderizar(plantilla.cuerpo, plantilla, valores)
            mensaje.cuerpo_truncado = len(cuerpo) > 16384
            mensaje.cuerpo_renderizado = cuerpo[:16384]
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

    if mensaje.canal == CanalMensaje.CANVAS_ANUNCIO.value:
        _despachar_anuncio(bd, mensaje, curso, cliente, token, ahora=ahora)
        return

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
        if fusionado is not None:
            # Fusion antes que diferir (S11.6.5): el recordatorio de cierre
            # llego dentro de este mensaje.
            fusionado.estado = EstadoMensaje.ENVIADO.value
            fusionado.enviado_en = ahora
            fusionado.referencia = {**(fusionado.referencia or {}), "fusionado_en": str(mensaje.id)}
    else:
        # El cliente de Canvas solo informa exito o rechazo: un rechazo 4xx es
        # PERMANENTE y no se reintenta solo (S11.2.2).
        mensaje.estado = EstadoMensaje.FALLIDO.value
        mensaje.ultimo_error_literal = "Canvas rechazó el mensaje."
    bd.flush()


def _despachar_anuncio(
    bd: Session,
    mensaje: MensajeSaliente,
    curso: Curso,
    cliente: Any,
    token: str,
    *,
    ahora: datetime,
) -> None:
    """S11.8.7: con `specific_sections` rechazado se reintenta una vez sin
    secciones con el cuerpo del plan B; si tambien falla, FALLIDO (A-216)."""
    referencia: dict[str, Any] = mensaje.referencia or {}
    secciones = [int(x) for x in referencia.get("secciones_canvas", [])] or None
    assert curso.canvas_course_id is not None
    try:
        with cerrojo_canvas(bd, curso.id):
            creado = cliente.crear_anuncio(
                token,
                curso.canvas_course_id,
                titulo=mensaje.asunto or "",
                mensaje_html=mensaje.cuerpo_renderizado or "",
                secciones=secciones,
            )
            if creado is None and secciones and referencia.get("cuerpo_html_plan_b"):
                mensaje.cuerpo_renderizado = str(referencia["cuerpo_html_plan_b"])
                creado = cliente.crear_anuncio(
                    token,
                    curso.canvas_course_id,
                    titulo=mensaje.asunto or "",
                    mensaje_html=mensaje.cuerpo_renderizado,
                    secciones=None,
                )
    except FalloProveedorCanvas as exc:
        _reintentar(mensaje, ahora=ahora, error=str(exc))
        bd.flush()
        return
    mensaje.tomado_por = None
    mensaje.tomado_en = None
    mensaje.canal_efectivo = CanalMensaje.CANVAS_ANUNCIO.value
    if creado is None:
        mensaje.estado = EstadoMensaje.FALLIDO.value
        mensaje.ultimo_error_literal = "Canvas rechazó el anuncio."
    else:
        mensaje.estado = EstadoMensaje.ENVIADO.value
        mensaje.enviado_en = ahora
        mensaje.canvas_id_resultante = {"discussion_topic_id": creado.topic_id}
        mensaje.canvas_html_url = creado.html_url
    bd.flush()


def _retractar_pendientes(bd: Session, *, ahora: datetime) -> None:
    """S11.8.8: solo los anuncios se retractan (DELETE), a pedido docente."""
    for mensaje in (
        bd.query(MensajeSaliente)
        .filter(
            MensajeSaliente.retraccion_solicitada.is_(True),
            MensajeSaliente.estado == EstadoMensaje.ENVIADO.value,
            MensajeSaliente.canal == CanalMensaje.CANVAS_ANUNCIO.value,
        )
        .limit(20)
    ):
        curso = bd.get(Curso, mensaje.curso_id)
        topic = (mensaje.canvas_id_resultante or {}).get("discussion_topic_id")
        credencial = canvas_repo.obtener_credencial_operativa(bd, mensaje.curso_id)
        if curso is None or topic is None or credencial is None or curso.canvas_course_id is None:
            continue
        settings = obtener_configuracion()
        token = canvas_repo.descifrar_token(
            Llavero(settings.llavero_cifrado(), settings.app_encryption_key_activa), credencial
        )
        cliente = crear_cliente_canvas(
            modo=settings.canvas_modo,
            canvas_base_url=curso.canvas_base_url or settings.canvas_base_url,
        )
        try:
            with cerrojo_canvas(bd, curso.id):
                borrado = cliente.borrar_anuncio(token, curso.canvas_course_id, int(topic))
        except FalloProveedorCanvas:
            continue
        if borrado:
            mensaje.estado = EstadoMensaje.RETRACTADO.value
            mensaje.retractado_en = ahora
            mensaje.retraccion_solicitada = False
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


# --- Canal CORREO (S11.5; A-228; Etapa F9) ---


def _usados_hoy(bd: Session, ahora: datetime) -> dict[str, int]:
    """Cuota del despliegue y del dia (UTC), por la reserva consumida."""
    inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    filas = (
        bd.query(MensajeSaliente.reserva, func.count(MensajeSaliente.id))
        .filter(
            MensajeSaliente.canal == CanalMensaje.CORREO.value,
            MensajeSaliente.estado == EstadoMensaje.ENVIADO.value,
            MensajeSaliente.enviado_en >= inicio,
        )
        .group_by(MensajeSaliente.reserva)
        .all()
    )
    return {str(r): int(n) for r, n in filas if r}


def _proximo_dia_0005(curso: Curso, ahora: datetime) -> datetime:
    local = ahora.astimezone(ZoneInfo(curso.zona_horaria))
    manana = (local + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
    return manana.astimezone(UTC)


def _despachar_correo(
    bd: Session, mensaje: MensajeSaliente, curso: Curso, *, tomado_por: str, ahora: datetime
) -> None:
    from app.adaptadores import incidencia_repo, informe_repo
    from app.adaptadores.modelos_curso import MembresiaCurso
    from app.adaptadores.modelos_identidad import Usuario
    from app.adaptadores.modelos_informe import InformeDiario, SuscripcionInforme
    from app.adaptadores.proveedor_correo import (
        FalloCorreo,
        crear_proveedor_correo,
        motivo_bloqueo,
    )
    from app.dominio.informe import reserva_a_consumir
    from app.infraestructura.cerrojos import bloquear_cuota_correo

    membresia = bd.get(MembresiaCurso, mensaje.membresia_id) if mensaje.membresia_id else None
    usuario = bd.get(Usuario, membresia.usuario_id) if membresia is not None else None
    suscripcion = (
        bd.get(SuscripcionInforme, (curso.id, membresia.usuario_id))
        if membresia is not None
        else None
    )
    # Guarda 2 para docentes (S11.4.6): membresia ACTIVA y, salvo que la
    # persona lo haya pedido para si misma, suscripcion activa.
    pedido_propio = mensaje.origen == OrigenMensaje.MANUAL.value
    if (
        membresia is None
        or usuario is None
        or membresia.estado != "ACTIVA"
        or (not pedido_propio and (suscripcion is None or not suscripcion.activa))
    ):
        mensaje.estado = EstadoMensaje.SUPRIMIDO.value
        mensaje.motivo_estado = "MATRICULA_NO_ACTIVA"
        bd.flush()
        return

    settings = obtener_configuracion()
    bloqueo = motivo_bloqueo(settings, usuario.email)
    if bloqueo:
        # Comunicaciones pausadas, destinatario fuera de la lista o correo sin
        # configurar: se reevalua, nunca se da por enviado.
        mensaje.estado = EstadoMensaje.BLOQUEADO.value
        mensaje.motivo_estado = bloqueo
        mensaje.programado_para = ahora + _ESPERA_BLOQUEADO
        bd.flush()
        return
    bloquear_cuota_correo(bd)
    reserva = reserva_a_consumir(mensaje.reserva or "INFORME", _usados_hoy(bd, ahora))
    if reserva is None:
        # A-228: no se pierde; vuelve a intentarse a las 00:05 del dia siguiente.
        mensaje.estado = EstadoMensaje.DIFERIDO.value
        mensaje.motivo_estado = "CUOTA_AGOTADA"
        mensaje.programado_para = _proximo_dia_0005(curso, ahora)
        bd.flush()
        incidencia_repo.abrir_o_actualizar(
            bd,
            tipo="CUOTA_CORREO_AGOTADA",
            severidad="ADVERTENCIA",
            sujeto_tipo="CURSO",
            curso_id=curso.id,
            sujeto_id=curso.id,
            detalle={"reserva": mensaje.reserva},
        )
        return

    informe = bd.get(InformeDiario, uuid.UUID(mensaje.referencia["informe_diario_id"]))
    if informe is None or informe.contenido_html is None:
        mensaje.estado = EstadoMensaje.CANCELADO.value
        mensaje.motivo_estado = "ACCION_DOCENTE"
        bd.flush()
        return
    token = informe_repo.emitir_token_baja(curso.id, usuario, ahora=ahora)
    enlace_baja = informe_repo.url_baja(token)
    enlace_notificaciones = f"{informe_repo._url_app()}/cursos/{curso.id}/mis-notificaciones"
    pie_html = (
        '<p style="color:#777;font-size:12px">'
        f'<a href="{enlace_baja}">Darme de baja de este informe</a> · '
        f'<a href="{enlace_notificaciones}">Mis notificaciones</a></p>'
    )
    texto = (
        f"{informe.contenido_texto}\n\nDarme de baja: {enlace_baja}\n"
        f"Mis notificaciones: {enlace_notificaciones}"
    )
    mensaje.asunto = str((informe.contenido or {}).get("asunto", ""))[:255]
    mensaje.cuerpo_renderizado = texto[:16384]
    mensaje.estado = EstadoMensaje.EN_CURSO.value
    mensaje.tomado_por = tomado_por
    mensaje.tomado_en = ahora
    mensaje.intentos += 1
    bd.flush()
    try:
        resultado = crear_proveedor_correo(settings).enviar(
            destinatario=usuario.email,
            asunto=mensaje.asunto,
            html=informe.contenido_html + pie_html,
            texto=texto,
            clave_idempotencia=mensaje.clave_idempotencia,
            reserva=reserva,
            cabeceras={
                "List-Unsubscribe": f"<{enlace_baja}>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            },
        )
    except FalloCorreo as exc:
        mensaje.ultimo_codigo_http = exc.status
        if exc.reintentable:
            _reintentar(mensaje, ahora=ahora, error=str(exc))
        else:
            mensaje.estado = EstadoMensaje.FALLIDO.value
            mensaje.ultimo_error_literal = str(exc)
        bd.flush()
        return
    # Fuera de produccion el correo se simula y queda SUPRIMIDO/SIMULADO_LOCAL,
    # igual que las invitaciones: nunca cuenta como enviado.
    mensaje.estado = (
        EstadoMensaje.SUPRIMIDO if resultado.simulado else EstadoMensaje.ENVIADO
    ).value
    mensaje.motivo_estado = "SIMULADO_LOCAL" if resultado.simulado else None
    mensaje.enviado_en = None if resultado.simulado else ahora
    mensaje.canal_efectivo = CanalMensaje.CORREO.value
    mensaje.proveedor_id = resultado.id
    mensaje.reserva = reserva
    bd.flush()
