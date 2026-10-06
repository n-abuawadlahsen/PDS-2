"""Estado público de un trabajo: excluye payload, credenciales y errores internos."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.adaptadores.modelos_infraestructura import Trabajo


class TrabajoSalida(BaseModel):
    id: uuid.UUID
    estado: str
    intentos: int
    max_intentos: int
    creado_en: datetime
    proximo_intento_en: datetime | None
    terminado_en: datetime | None


def salida_trabajo(trabajo: Trabajo) -> TrabajoSalida:
    return TrabajoSalida(
        id=trabajo.id,
        estado=trabajo.estado,
        intentos=trabajo.intentos,
        max_intentos=trabajo.max_intentos,
        creado_en=trabajo.creado_en,
        proximo_intento_en=trabajo.proximo_intento_en,
        terminado_en=trabajo.terminado_en,
    )
