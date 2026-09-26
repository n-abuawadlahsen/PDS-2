"""Proveedor de correo transaccional (SPEC 14 S14.12; A-133; Etapa F9).

Dos implementaciones: `ProveedorCorreoResend` (produccion, plan gratuito de
Resend) y `ProveedorCorreoConsola` (local, ensayo y pruebas: nada sale del
sistema y todo queda en el log estructurado, S14.12 CA-6). Solo lo llama
`despachar_outbox`; ninguna vista envia correo.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from app.infraestructura.logs import obtener_logger

_logger = obtener_logger(__name__)
_TIMEOUT = 20.0


@dataclass(frozen=True)
class CorreoSaliente:
    destinatario: str
    asunto: str
    html: str
    texto: str
    clave_idempotencia: str
    reserva: str
    cabeceras: dict[str, str] = field(default_factory=dict)


class FalloProveedorCorreo(Exception):
    def __init__(self, literal: str, *, codigo_http: int | None, reintentable: bool) -> None:
        super().__init__(literal)
        self.literal = literal
        self.codigo_http = codigo_http
        self.reintentable = reintentable


class ProveedorCorreo(Protocol):
    def enviar(self, correo: CorreoSaliente) -> str:
        """Devuelve el identificador del proveedor."""
        ...


# Solo para pruebas: lo que el proveedor de consola «envio».
correos_consola: list[CorreoSaliente] = []


class ProveedorCorreoConsola:
    def enviar(self, correo: CorreoSaliente) -> str:
        correos_consola.append(correo)
        _logger.info(
            "correo_no_enviado_fuera_de_produccion",
            extra={"asunto": correo.asunto, "reserva": correo.reserva},
        )
        return f"consola-{uuid.uuid4()}"


class ProveedorCorreoResend:
    def __init__(self, *, api_key: str, remitente: str, responder_a: str) -> None:
        self._api_key = api_key
        self._remitente = remitente
        self._responder_a = responder_a

    def enviar(self, correo: CorreoSaliente) -> str:
        cuerpo: dict[str, Any] = {
            "from": self._remitente,
            "to": [correo.destinatario],
            "subject": correo.asunto,
            "html": correo.html,
            "text": correo.texto,
            "reply_to": self._responder_a,
            "headers": correo.cabeceras,
        }
        try:
            respuesta = httpx.post(
                "https://api.resend.com/emails",
                json=cuerpo,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Idempotency-Key": correo.clave_idempotencia[:256],
                },
                timeout=_TIMEOUT,
            )
        except httpx.HTTPError as exc:
            raise FalloProveedorCorreo(str(exc), codigo_http=None, reintentable=True) from exc
        if respuesta.status_code >= 300:
            raise FalloProveedorCorreo(
                respuesta.text[:2000],
                codigo_http=respuesta.status_code,
                reintentable=respuesta.status_code == 429 or respuesta.status_code >= 500,
            )
        return str(respuesta.json().get("id", ""))


def crear_proveedor_correo(settings: Any) -> ProveedorCorreo:
    """Solo produccion envia de verdad (S14.12 CA-6)."""
    if settings.entorno == "produccion" and settings.email_provider_api_key:
        return ProveedorCorreoResend(
            api_key=settings.email_provider_api_key,
            remitente=f'"{settings.email_from_nombre}" <{settings.email_from}>',
            responder_a=settings.email_reply_to,
        )
    return ProveedorCorreoConsola()
