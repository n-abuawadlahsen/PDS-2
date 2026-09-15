"""Correo transaccional por HTTPS; fuera de produccion nunca envia a terceros."""

from dataclasses import dataclass
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
    ) -> ResultadoCorreo:
        # No registrar el enlace nominal, el cuerpo ni el correo personal.
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


def motivo_bloqueo(settings: Settings, destinatario: str) -> str | None:
    if settings.comunicaciones_salientes != "activadas":
        return "COMUNICACIONES_PAUSADAS"
    permitidos = {
        v.strip().lower() for v in settings.destinatarios_permitidos.split(",") if v.strip()
    }
    if permitidos and destinatario.lower() not in permitidos:
        return "DESTINATARIO_NO_PERMITIDO"
    if settings.entorno == "produccion":
        if settings.email_proveedor != "resend":
            return "CORREO_SIN_CONFIGURAR"
        dominio = settings.email_from.partition("@")[2].lower()
        verificado = settings.email_dominio_verificado.strip().lower()
        if (
            not settings.email_provider_api_key.strip()
            or not dominio
            or not verificado
            or not (dominio == verificado or dominio.endswith("." + verificado))
            or not settings.email_reply_to.strip()
        ):
            return "CORREO_SIN_CONFIGURAR"
    return None


def crear_proveedor_correo(settings: Settings) -> ProveedorCorreo:
    return CorreoResend(settings) if settings.entorno == "produccion" else CorreoConsola()
