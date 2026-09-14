"""Dos espacios de cerrojo consultivo por curso, uno por proveedor (SPEC 14 S14.7.3).

Unicos puntos de toma de `pg_advisory_lock` para trafico con Canvas o GitHub.
Una prueba de arquitectura (tests/arquitectura/test_cerrojos.py) falla la
construccion si aparece una toma de `pg_advisory_lock`/`pg_advisory_xact_lock`
fuera de este modulo, en orden inverso (2 antes que 1) o anidada dentro del mismo
espacio.

Regla dura (A-217, RG-062): quien necesita los dos cerrojos los toma siempre en
orden 1 (Canvas) y luego 2 (GitHub), y nunca retiene uno mientras espera al otro.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Protocol

from sqlalchemy import text
from sqlalchemy.orm import Session


class _EjecutorSql(Protocol):
    """Cualquier cosa con `.execute(text(...), params)`: Session o Connection."""

    def execute(self, *args: Any, **kwargs: Any) -> Any: ...


_ESPACIO_CANVAS = 1
_ESPACIO_GITHUB = 2


def _clave_curso(curso_id: uuid.UUID) -> str:
    """`curso.id` es UUIDv7 (ARQUITECTURA.md S8), no cabe en el `int4` que pide
    la variante de dos claves de `pg_advisory_lock`. Se reduce con `hashtext`,
    igual que ya hace `cerrojo_global` con su clave de texto."""
    return str(curso_id)


@contextmanager
def cerrojo_canvas(sesion: Session, curso_id: uuid.UUID) -> Iterator[None]:
    """`pg_advisory_lock(1, hashtext(curso_id))`: una sola peticion
    simultanea a Canvas por curso."""
    sesion.execute(
        text("SELECT pg_advisory_lock(:espacio, hashtext(:curso_id))"),
        {"espacio": _ESPACIO_CANVAS, "curso_id": _clave_curso(curso_id)},
    )
    try:
        yield
    finally:
        sesion.execute(
            text("SELECT pg_advisory_unlock(:espacio, hashtext(:curso_id))"),
            {"espacio": _ESPACIO_CANVAS, "curso_id": _clave_curso(curso_id)},
        )


@contextmanager
def cerrojo_github(sesion: Session, curso_id: uuid.UUID) -> Iterator[None]:
    """`pg_advisory_lock(2, hashtext(curso_id))`: trafico con GitHub, techo
    por presupuesto medido."""
    sesion.execute(
        text("SELECT pg_advisory_lock(:espacio, hashtext(:curso_id))"),
        {"espacio": _ESPACIO_GITHUB, "curso_id": _clave_curso(curso_id)},
    )
    try:
        yield
    finally:
        sesion.execute(
            text("SELECT pg_advisory_unlock(:espacio, hashtext(:curso_id))"),
            {"espacio": _ESPACIO_GITHUB, "curso_id": _clave_curso(curso_id)},
        )


@contextmanager
def cerrojo_global(sesion: _EjecutorSql, clave_texto: str) -> Iterator[None]:
    """`pg_advisory_lock(hashtext(clave))` para trabajos de alcance global (S14.7.3)."""
    sesion.execute(text("SELECT pg_advisory_lock(hashtext(:clave))"), {"clave": clave_texto})
    try:
        yield
    finally:
        sesion.execute(text("SELECT pg_advisory_unlock(hashtext(:clave))"), {"clave": clave_texto})
