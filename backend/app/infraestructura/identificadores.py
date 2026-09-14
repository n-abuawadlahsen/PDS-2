"""Generador de UUID v7 (ARQUITECTURA.md S8: "clave primaria propia id UUID
(v7, ordenable por tiempo) en toda tabla").

UUIDv7 (RFC 9562) es ordenable por tiempo de creacion sin ser un identificador
externo ni filtrar mas que el instante aproximado de creacion. Se implementa
a mano (sin dependencia externa) porque el algoritmo es corto y estable:
48 bits de milisegundos Unix + version (4 bits) + 12 bits aleatorios + variante
(2 bits) + 62 bits aleatorios.
"""

from __future__ import annotations

import os
import time
import uuid


def uuid7() -> uuid.UUID:
    timestamp_ms = time.time_ns() // 1_000_000
    aleatorio = os.urandom(10)

    bytes_uuid = bytearray(16)
    bytes_uuid[0:6] = timestamp_ms.to_bytes(6, "big")
    bytes_uuid[6] = 0x70 | (aleatorio[0] & 0x0F)  # version 7
    bytes_uuid[7] = aleatorio[1]
    bytes_uuid[8] = 0x80 | (aleatorio[2] & 0x3F)  # variante RFC 9562
    bytes_uuid[9:16] = aleatorio[3:10]

    return uuid.UUID(bytes=bytes(bytes_uuid))
