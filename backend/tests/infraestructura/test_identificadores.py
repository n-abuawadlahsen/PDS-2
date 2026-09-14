from __future__ import annotations

import time
import uuid

from app.infraestructura.identificadores import uuid7


def test_genera_uuid_version_7():
    valor = uuid7()
    assert isinstance(valor, uuid.UUID)
    assert valor.version == 7


def test_es_ordenable_por_tiempo():
    """Dos UUIDv7 generados en milisegundos distintos ordenan por ese instante.

    Dentro del mismo milisegundo el orden entre dos UUIDv7 es aleatorio por
    diseño (RFC 9562): no se compara ahi.
    """
    primero = uuid7()
    time.sleep(0.002)
    segundo = uuid7()
    assert primero < segundo
