"""Correo transaccional por HTTPS (Resend o API de Gmail) o SMTP; fuera de
produccion nunca envia a terceros."""

import base64
import smtplib
import ssl
from collections import deque
from dataclasses import dataclass, field
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from typing import Protocol

import httpx

from app.infraestructura.config import Settings
from app.infraestructura.logs import obtener_logger


class FalloCorreo(Exception):
    def __init__(self, mensaje: str, *, reintentable: bool, status: int | None = None):
        super().__init__(mensaje)
        self.reintentable = reintentable
        self.status = status


@dataclass(frozen=True)
class ResultadoCorreo:
    id: str
    simulado: bool = False


@dataclass(frozen=True)
class CorreoSimulado:
    """Lo que el proveedor de consola «envio». Solo lo leen las pruebas; vive en
    memoria del proceso y nunca se registra en el log."""

    destinatario: str
    asunto: str
    html: str
    texto: str
    cabeceras: dict[str, str] = field(default_factory=dict)


correos_consola: deque[CorreoSimulado] = deque(maxlen=50)


class ProveedorCorreo(Protocol):
    def enviar(
        self,
        *,
        destinatario: str,
        asunto: str,
        html: str,
        texto: str,
        clave_idempotencia: str,
        reserva: str,
        cabeceras: dict[str, str] | None = None,
    ) -> ResultadoCorreo: ...


class CorreoConsola:
    def enviar(
        self,
        *,
        destinatario: str,
        asunto: str,
        html: str,
        texto: str,
        clave_idempotencia: str,
        reserva: str,
        cabeceras: dict[str, str] | None = None,
    ) -> ResultadoCorreo:
        # No registrar el enlace nominal, el cuerpo ni el correo personal.
        correos_consola.append(
            CorreoSimulado(destinatario, asunto, html, texto, dict(cabeceras or {}))
        )
        obtener_logger(__name__).info("correo.simulado", clave=clave_idempotencia, reserva=reserva)
        return ResultadoCorreo(id=f"consola:{clave_idempotencia}", simulado=True)


class CorreoResend:
    def __init__(self, settings: Settings):
        self.settings = settings

    def enviar(
        self,
        *,
        destinatario: str,
        asunto: str,
        html: str,
        texto: str,
        clave_idempotencia: str,
        reserva: str,
        cabeceras: dict[str, str] | None = None,
    ) -> ResultadoCorreo:
        try:
            r = httpx.post(
                "https://api.resend.com/emails",
                timeout=20,
                headers={
                    "Authorization": f"Bearer {self.settings.email_provider_api_key}",
                    "Idempotency-Key": clave_idempotencia,
                },
                json={
                    "from": f"{self.settings.email_from_nombre} <{self.settings.email_from}>",
                    "to": [destinatario],
                    "reply_to": self.settings.email_reply_to,
                    "subject": asunto,
                    "html": html,
                    "text": texto,
                    **({"headers": cabeceras} if cabeceras else {}),
                },
            )
        except httpx.TransportError as exc:
            raise FalloCorreo(
                "No se pudo contactar con el proveedor de correo.", reintentable=True
            ) from exc
        if not r.is_success:
            # El cuerpo del proveedor puede contener destinatarios y credenciales.
            raise FalloCorreo(
                f"El proveedor de correo respondió HTTP {r.status_code}.",
                reintentable=r.status_code in {408, 409, 429} or r.status_code >= 500,
                status=r.status_code,
            )
        try:
            identificador = r.json()["id"]
            if not isinstance(identificador, str) or not identificador:
                raise ValueError("id ausente")
        except (ValueError, KeyError, TypeError) as exc:
            raise FalloCorreo(
                "El proveedor no confirmó el identificador del envío.", reintentable=True
            ) from exc
        return ResultadoCorreo(id=identificador)


def _mensaje_mime(
    s: Settings,
    destinatario: str,
    asunto: str,
    html: str,
    texto: str,
    cabeceras: dict[str, str] | None,
) -> EmailMessage:
    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = formataddr((s.email_from_nombre, s.email_from))
    mensaje["To"] = destinatario
    mensaje["Reply-To"] = s.email_reply_to
    mensaje["Message-ID"] = make_msgid(domain=s.email_from.partition("@")[2] or None)
    for nombre, valor in (cabeceras or {}).items():
        mensaje[nombre] = valor
    mensaje.set_content(texto)
    mensaje.add_alternative(html, subtype="html")
    return mensaje


class CorreoSmtp:
    """SMTP con STARTTLS, para enviar sin dominio propio (p. ej. una cuenta de
    Gmail con contrasena de aplicacion). SMTP no tiene clave de idempotencia:
    el outbox ya evita reenviar un mensaje confirmado."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def enviar(
        self,
        *,
        destinatario: str,
        asunto: str,
        html: str,
        texto: str,
        clave_idempotencia: str,
        reserva: str,
        cabeceras: dict[str, str] | None = None,
    ) -> ResultadoCorreo:
        s = self.settings
        mensaje = _mensaje_mime(s, destinatario, asunto, html, texto, cabeceras)
        try:
            with smtplib.SMTP(s.smtp_host, s.smtp_puerto, timeout=20) as conexion:
                conexion.starttls(context=ssl.create_default_context())
                conexion.login(s.smtp_usuario or "", s.smtp_contrasena or "")
                conexion.send_message(mensaje)
        # La respuesta del servidor puede repetir el usuario: nunca se propaga.
        except smtplib.SMTPAuthenticationError as exc:
            raise FalloCorreo(
                "El servidor de correo rechazó el usuario o la contraseña.",
                reintentable=False,
                status=exc.smtp_code,
            ) from None
        except smtplib.SMTPRecipientsRefused:
            raise FalloCorreo(
                "El servidor de correo rechazó al destinatario.", reintentable=False
            ) from None
        except smtplib.SMTPResponseException as exc:
            raise FalloCorreo(
                f"El servidor de correo respondió {exc.smtp_code}.",
                reintentable=400 <= exc.smtp_code < 500,
                status=exc.smtp_code,
            ) from None
        except (smtplib.SMTPException, OSError):
            raise FalloCorreo(
                "No se pudo contactar con el servidor de correo.", reintentable=True
            ) from None
        return ResultadoCorreo(id=str(mensaje["Message-ID"]))


class CorreoGmailApi:
    """Envia desde una cuenta de Gmail por la API HTTPS (puerto 443), para
    hostings que bloquean los puertos SMTP (p. ej. Render gratuito). Usa un
    refresh token de esa cuenta con el permiso gmail.send."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def enviar(
        self,
        *,
        destinatario: str,
        asunto: str,
        html: str,
        texto: str,
        clave_idempotencia: str,
        reserva: str,
        cabeceras: dict[str, str] | None = None,
    ) -> ResultadoCorreo:
        s = self.settings
        mensaje = _mensaje_mime(s, destinatario, asunto, html, texto, cabeceras)
        try:
            token = httpx.post(
                "https://oauth2.googleapis.com/token",
                timeout=20,
                data={
                    "client_id": s.gmail_client_id or s.google_client_id,
                    "client_secret": s.gmail_client_secret or s.google_client_secret,
                    "refresh_token": s.gmail_refresh_token or "",
                    "grant_type": "refresh_token",
                },
            )
            if not token.is_success:
                # El cuerpo de Google puede repetir credenciales: nunca se propaga.
                raise FalloCorreo(
                    f"Google rechazó el permiso para enviar correo (HTTP {token.status_code}).",
                    reintentable=token.status_code == 429 or token.status_code >= 500,
                    status=token.status_code,
                )
            acceso = token.json()["access_token"]
            r = httpx.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                timeout=20,
                headers={"Authorization": f"Bearer {acceso}"},
                json={"raw": base64.urlsafe_b64encode(mensaje.as_bytes()).decode()},
            )
        except httpx.TransportError:
            raise FalloCorreo("No se pudo contactar con Gmail.", reintentable=True) from None
        except (ValueError, KeyError, TypeError):
            raise FalloCorreo(
                "Google no entregó un token de acceso para enviar correo.", reintentable=True
            ) from None
        if not r.is_success:
            raise FalloCorreo(
                f"Gmail respondió HTTP {r.status_code}.",
                reintentable=r.status_code in {408, 429} or r.status_code >= 500,
                status=r.status_code,
            )
        try:
            identificador = r.json()["id"]
            if not isinstance(identificador, str) or not identificador:
                raise ValueError("id ausente")
        except (ValueError, KeyError, TypeError):
            raise FalloCorreo(
                "Gmail no confirmó el identificador del envío.", reintentable=True
            ) from None
        return ResultadoCorreo(id=identificador)


def motivo_bloqueo(settings: Settings, destinatario: str) -> str | None:
    if settings.comunicaciones_salientes != "activadas":
        return "COMUNICACIONES_PAUSADAS"
    permitidos = {
        v.strip().lower() for v in settings.destinatarios_permitidos.split(",") if v.strip()
    }
    if permitidos and destinatario.lower() not in permitidos:
        return "DESTINATARIO_NO_PERMITIDO"
    if settings.entorno == "produccion":
        if settings.email_proveedor == "resend":
            credenciales = bool(settings.email_provider_api_key.strip())
        elif settings.email_proveedor == "smtp":
            credenciales = bool(
                (settings.smtp_usuario or "").strip() and (settings.smtp_contrasena or "").strip()
            )
        elif settings.email_proveedor == "gmail_api":
            credenciales = bool((settings.gmail_refresh_token or "").strip())
        else:
            return "CORREO_SIN_CONFIGURAR"
        dominio = settings.email_from.partition("@")[2].lower()
        verificado = settings.email_dominio_verificado.strip().lower()
        if (
            not credenciales
            or not dominio
            or not verificado
            or not (dominio == verificado or dominio.endswith("." + verificado))
            or not settings.email_reply_to.strip()
        ):
            return "CORREO_SIN_CONFIGURAR"
    return None


def crear_proveedor_correo(settings: Settings) -> ProveedorCorreo:
    if settings.entorno != "produccion":
        return CorreoConsola()
    if settings.email_proveedor == "smtp":
        return CorreoSmtp(settings)
    if settings.email_proveedor == "gmail_api":
        return CorreoGmailApi(settings)
    return CorreoResend(settings)
