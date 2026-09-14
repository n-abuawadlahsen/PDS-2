"""Utilidades compartidas de pruebas.

`fabrica_bd()` es un singleton de proceso: un solo Engine/pool para toda la
sesion de pytest. Crear un Engine nuevo por test (`crear_fabrica_sesiones(...)`
cada vez) agota rapido `max_connections` de Postgres, porque cada Engine abre
su propio pool de 10 conexiones (S14.3.2) que nunca se libera hasta el final
del proceso.
"""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from app.infraestructura.config import obtener_configuracion
from app.infraestructura.db import crear_fabrica_sesiones

_fabrica: sessionmaker[Session] | None = None


def fabrica_bd() -> sessionmaker[Session]:
    global _fabrica
    if _fabrica is None:
        _fabrica = crear_fabrica_sesiones(obtener_configuracion())
    return _fabrica
