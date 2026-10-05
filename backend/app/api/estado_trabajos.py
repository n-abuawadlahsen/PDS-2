"""Contrato de seguimiento legible sin payloads, credenciales ni errores del proveedor."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.adaptadores.modelos_infraestructura import Trabajo


class TrabajoSalida(BaseModel):
    id: uuid.UUID
    tipo: str
    estado: str
    intentos: int
    max_intentos: int
    creado_en: datetime
    terminado_en: datetime | None
    proximo_intento_en: datetime | None
    requiere_atencion: bool


def salida_trabajo(trabajo: Trabajo) -> TrabajoSalida:
    return TrabajoSalida(
        id=trabajo.id,
        tipo=trabajo.tipo,
        estado=trabajo.estado,
        intentos=trabajo.intentos,
        max_intentos=trabajo.max_intentos,
        creado_en=trabajo.creado_en,
        terminado_en=trabajo.terminado_en,
        proximo_intento_en=trabajo.proximo_intento_en,
        requiere_atencion=trabajo.estado
        in {"REQUIERE_ATENCION", "BLOQUEADO", "ESPERANDO_CREDENCIAL", "CANCELADO"},
    )
