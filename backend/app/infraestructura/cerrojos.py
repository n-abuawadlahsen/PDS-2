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
_ESPACIO_REPOSITORIO = 3
_ESPACIO_REPARTO = 4


def bloquear_ciclo_curso(sesion: Session, curso_id: uuid.UUID, *, exclusivo: bool = False) -> None:
    """El archivo espera las escrituras en curso; una escritura espera el archivo.

    Espacio independiente de Canvas/GitHub, tomado antes de sus cerrojos.
    La exclusión dura hasta COMMIT/ROLLBACK, también para el outbox global.
    """
    funcion = "pg_advisory_xact_lock" if exclusivo else "pg_advisory_xact_lock_shared"
    sesion.execute(text(f"SELECT {funcion}(5, hashtext(:curso_id))"), {"curso_id": str(curso_id)})


def bloquear_equipo(sesion: Session) -> None:
    """Serializa cambios de identidad/membresias hasta COMMIT o ROLLBACK.

    El cierre puede abarcar varios cursos. Un cerrojo transaccional compartido
    evita que dos cierres o una degradacion simultanea dejen cero profesores.
    No se libera al salir de una funcion: la comprobacion y el cambio son atomicos.
    """
    sesion.execute(text("SELECT pg_advisory_xact_lock(hashtext('identidad_y_equipo'))"))


def bloquear_cuota_correo(sesion: Session) -> None:
    sesion.execute(text("SELECT pg_advisory_xact_lock(hashtext('cuota_correo'))"))


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


def cerrojo_repositorio(sesion: Session, clave_repositorio: str) -> None:
    """`pg_advisory_xact_lock(3, hashtext(repositorio))` (S10.2.4 regla 4): la
    ingesta de un repositorio se serializa y el cerrojo se libera solo con la
    transaccion; nunca un cerrojo de sesion en la ruta de ingesta."""
    sesion.execute(
        text("SELECT pg_advisory_xact_lock(:espacio, hashtext(:clave))"),
        {"espacio": _ESPACIO_REPOSITORIO, "clave": clave_repositorio},
    )


def cerrojo_reparto(sesion: Session, entrega_id: uuid.UUID) -> None:
    """`pg_advisory_xact_lock(4, hashtext(entrega))` (S12.5.6): dos repartos
    automaticos de la misma entrega nunca corren a la vez; el segundo ve el
    resultado del primero. Se libera con la transaccion."""
    sesion.execute(
        text("SELECT pg_advisory_xact_lock(:espacio, hashtext(:clave))"),
        {"espacio": _ESPACIO_REPARTO, "clave": str(entrega_id)},
    )
