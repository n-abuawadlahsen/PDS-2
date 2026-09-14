"""Reglas puras de admision e identidad de cuenta Google (SPEC 02 S2.2.4-S2.2.7).

Sin I/O, sin ORM, sin cliente HTTP: una prueba de arquitectura falla la
construccion si este paquete importa algo de eso (SPEC 14 S14.1).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

_DOMINIOS_GOOGLE_PERSONAL = {"gmail.com", "googlemail.com"}


class MotivoRechazoCorreo(StrEnum):
    """Motivos tipados de rechazo de la regla de admision (S2.2.4)."""

    HD_PRESENTE = "HD_PRESENTE"
    DOMINIO_NO_GMAIL = "DOMINIO_NO_GMAIL"
    CORREO_NO_VERIFICADO = "CORREO_NO_VERIFICADO"


class MotivoRechazoAcceso(StrEnum):
    """Catalogo cerrado de desenlaces de un intento de acceso (S2.2.7), fila 1-8.

    La fila 6 (cookie ausente) no es un rechazo: es el camino de confirmacion
    degradada y se modela aparte en la capa de API.
    """

    DOMINIO_NO_GMAIL = "DOMINIO_NO_GMAIL"
    HD_PRESENTE = "HD_PRESENTE"
    CORREO_NO_VERIFICADO = "CORREO_NO_VERIFICADO"
    ACCESO_CANCELADO = "ACCESO_CANCELADO"
    STATE_INVALIDO = "STATE_INVALIDO"
    CUENTA_CERRADA = "CUENTA_CERRADA"
    FALLO_PROVEEDOR = "FALLO_PROVEEDOR"


@dataclass(frozen=True)
class RechazoAcceso(Exception):
    """Tipo unico de rechazo de acceso; el callback nunca devuelve 500 por esto."""

    motivo: MotivoRechazoAcceso
    detalle: str = ""


@dataclass(frozen=True)
class CorreoAdmitido:
    email: str
    email_canonico: str


def normalizar_correo_google(email: str, *, email_verified: bool, hd: str | None) -> CorreoAdmitido:
    """Aplica S2.2.4 (admision) y S2.2.5 (normalizacion), en ese orden.

    Devuelve el correo normalizado o levanta `MotivoRechazoCorreo` tipado.
    Casos de prueba obligatorios (S2.2.4): ana@gmail.com; Ana@GMail.com;
    ana@googlemail.com; ana@uandes.cl con hd; ana@gmail.com con hd (se rechaza
    igual); email_verified=false.
    """
    if not email_verified:
        raise RechazoCorreo(MotivoRechazoCorreo.CORREO_NO_VERIFICADO)

    # hd manda y se rechaza aunque la direccion termine en @gmail.com.
    if hd:
        raise RechazoCorreo(MotivoRechazoCorreo.HD_PRESENTE)

    correo_minusculas = email.strip().lower()
    if "@" not in correo_minusculas:
        raise RechazoCorreo(MotivoRechazoCorreo.DOMINIO_NO_GMAIL)
    local_part, _, dominio = correo_minusculas.partition("@")

    if dominio not in _DOMINIOS_GOOGLE_PERSONAL:
        raise RechazoCorreo(MotivoRechazoCorreo.DOMINIO_NO_GMAIL)

    email_normalizado = f"{local_part}@gmail.com"
    local_part_canonico = local_part.split("+", 1)[0].replace(".", "")
    email_canonico = f"{local_part_canonico}@gmail.com"

    return CorreoAdmitido(email=email_normalizado, email_canonico=email_canonico)


class RechazoCorreo(Exception):
    def __init__(self, motivo: MotivoRechazoCorreo) -> None:
        self.motivo = motivo
        super().__init__(motivo.value)
