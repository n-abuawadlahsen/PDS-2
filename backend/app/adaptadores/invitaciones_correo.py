"""Invitaciones nominales por el outbox existente; tokens cifrados, nunca logs."""

import base64
import html
import uuid
from datetime import datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.adaptadores import cursos_repo, programacion_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_aprovisionamiento import MensajeSaliente
from app.adaptadores.modelos_curso import Curso, InvitacionEquipo
from app.adaptadores.modelos_infraestructura import Incidencia
from app.adaptadores.proveedor_correo import FalloCorreo, crear_proveedor_correo, motivo_bloqueo
from app.infraestructura.cerrojos import bloquear_cuota_correo
from app.infraestructura.cifrado import DescifradoFallido, Llavero, ValorCifrado
from app.infraestructura.config import Settings, obtener_configuracion

EVENTO = "invitacion_equipo"


def mensaje_de_invitacion(bd: Session, invitacion: InvitacionEquipo) -> MensajeSaliente | None:
    return (
        bd.query(MensajeSaliente)
        .filter_by(clave_idempotencia=f"invitacion:{invitacion.id}")
        .one_or_none()
    )


def encolar(
    bd: Session, creada: cursos_repo.InvitacionCreada, settings: Settings
) -> MensajeSaliente:
    i = creada.invitacion
    curso = bd.get(Curso, i.curso_id)
    assert curso is not None
    llavero = Llavero(settings.llavero_cifrado(), settings.app_encryption_key_activa)
    secreto = base64.b64encode(
        llavero.cifrar(creada.token_plano.encode(), curso_id=i.curso_id).empaquetar()
    ).decode()
    mensaje = MensajeSaliente(
        curso_id=i.curso_id,
        canal="CORREO",
        evento=EVENTO,
        clave_idempotencia=f"invitacion:{i.id}",
        generacion=1,
        referencia={
            "invitacion_id": str(i.id),
            "token_cifrado": secreto,
            "curso_nombre": curso.nombre,
            "rol": i.rol,
            "origen": settings.frontend_origen.rstrip("/"),
            "reserva": "MARGEN",
        },
        destinatario=i.email,
        plantilla=EVENTO,
        plantilla_version=1,
        origen="MANUAL",
        caduca_en=i.expira_en,
        estado="PENDIENTE",
        intentos=0,
        creado_en=ahora_utc(),
    )
    bd.add(mensaje)
    programacion_repo.asegurar_periodicos_globales(bd)
    bd.flush()
    return mensaje


def enlace(bd: Session, i: InvitacionEquipo, settings: Settings) -> str | None:
    if i.estado != "PENDIENTE" or cursos_repo.invitacion_esta_vencida(i):
        return None
    m = mensaje_de_invitacion(bd, i)
    if m is None or not m.referencia.get("token_cifrado"):
        return None  # invitacion antigua: reenviar genera un token recuperable
    try:
        valor = ValorCifrado.desempaquetar(base64.b64decode(m.referencia["token_cifrado"]))
        token = (
            Llavero(settings.llavero_cifrado(), settings.app_encryption_key_activa)
            .descifrar(valor, curso_id=i.curso_id)
            .decode()
        )
    except (DescifradoFallido, ValueError, KeyError):
        return None
    return f"{m.referencia['origen']}/invitaciones/{token}"


def cancelar(bd: Session, i: InvitacionEquipo) -> None:
    m = mensaje_de_invitacion(bd, i)
    if m is None:
        return
    m.referencia = {k: v for k, v in m.referencia.items() if k != "token_cifrado"}
    if m.estado not in {"ENVIADO", "FALLIDO", "CADUCADO"}:
        m.estado = "CANCELADO"
        m.motivo_estado = "INVITACION_NO_VIGENTE"
    bd.flush()


def despachar(bd: Session, m: MensajeSaliente, *, ahora: datetime) -> None:
    settings = obtener_configuracion()
    i = bd.get(InvitacionEquipo, uuid.UUID(m.referencia["invitacion_id"]))
    if i is None or i.estado != "PENDIENTE":
        m.estado = "CANCELADO"
        m.motivo_estado = "INVITACION_NO_VIGENTE"
        return
    if i.expira_en <= ahora:
        m.estado = "CADUCADO"
        return
    bloqueo = motivo_bloqueo(settings, m.destinatario)
    if bloqueo:
        m.estado = "BLOQUEADO"
        m.motivo_estado = bloqueo
        m.programado_para = ahora + timedelta(seconds=30)
        return
    url = enlace(bd, i, settings)
    if url is None:
        m.estado = "REQUIERE_ATENCION"
        m.motivo_estado = "ENLACE_NO_RECUPERABLE"
        return
    # La cuota pertenece a todo el despliegue. Incluye reservas de intentos
    # inciertos; un reintento del mismo mensaje no consume otra plaza.
    bloquear_cuota_correo(bd)
    dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    fecha = dia.date().isoformat()
    reservados = bd.query(MensajeSaliente).filter(
        MensajeSaliente.canal == "CORREO",
        or_(
            MensajeSaliente.enviado_en >= dia,
            MensajeSaliente.referencia["cuota_fecha"].astext == fecha,
        ),
    )
    if m.referencia.get("cuota_fecha") != fecha and (
        reservados.count() >= 100
        or reservados.filter(MensajeSaliente.evento == EVENTO).count() >= 10
    ):
        m.estado = "DIFERIDO"
        m.motivo_estado = "CUOTA_AGOTADA"
        m.programado_para = dia + timedelta(days=1)
        if not bd.query(Incidencia).filter_by(tipo="CUOTA_CORREO_AGOTADA", abierta=True).first():
            bd.add(
                Incidencia(
                    tipo="CUOTA_CORREO_AGOTADA",
                    severidad="ADVERTENCIA",
                    sujeto_tipo="despliegue",
                    abierta=True,
                    creado_en=ahora,
                    detalle={"reserva": "MARGEN", "limite_invitaciones": 10},
                )
            )
        return
    primer_intento = m.referencia.get("primer_intento_en")
    if primer_intento and ahora - datetime.fromisoformat(primer_intento) >= timedelta(hours=23):
        # Resend retiene idempotencia 24 h. No repetir automaticamente un envio
        # incierto despues de esa ventana; el profesor puede emitir otro enlace.
        m.estado = "REQUIERE_ATENCION"
        m.motivo_estado = "ENVIO_INCIERTO"
        return
    m.referencia = {
        **m.referencia,
        "cuota_fecha": fecha,
        "primer_intento_en": primer_intento or ahora.isoformat(),
    }
    asunto = f"Invitación al equipo docente: {m.referencia['curso_nombre']}"
    texto = (
        f"Te invitaron como {m.referencia['rol'].lower()} "
        f"al curso {m.referencia['curso_nombre']}.\n\n"
        f"Acepta con tu cuenta personal Gmail desde este enlace:\n{url}\n\n"
        f"Vence el {i.expira_en.isoformat()}. Si no esperabas esta invitación, puedes ignorarla."
    )
    cuerpo_html = (
        '<table role="presentation"><tr><td>'
        + html.escape(texto).replace("\n", "<br>")
        + "</td></tr></table>"
    )
    m.intentos += 1
    try:
        resultado = crear_proveedor_correo(settings).enviar(
            destinatario=m.destinatario,
            asunto=asunto,
            html=cuerpo_html,
            texto=texto,
            clave_idempotencia=m.clave_idempotencia,
            reserva="MARGEN",
        )
    except FalloCorreo as exc:
        m.ultimo_error_literal = str(exc)
        m.ultimo_codigo_http = exc.status
        m.estado = "REINTENTAR" if exc.reintentable and m.intentos < 6 else "REQUIERE_ATENCION"
        m.programado_para = ahora + timedelta(seconds=min(2**m.intentos, 300))
        return
    m.estado = "SUPRIMIDO" if resultado.simulado else "ENVIADO"
    m.motivo_estado = "SIMULADO_LOCAL" if resultado.simulado else None
    m.enviado_en = None if resultado.simulado else ahora
    m.canal_efectivo = "CORREO"
    m.ultimo_error_literal = None
    m.canvas_id_resultante = {"proveedor_id": resultado.id, "simulado": resultado.simulado}
    bd.flush()
