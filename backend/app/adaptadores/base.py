"""Base declarativa y convencion de nombres de restricciones (SPEC 14 S14.8.1).

"Convencion de nombres de restricciones fijada desde la primera migracion, en la
metadata del ORM. Sin ella, la herramienta genera nombres distintos en cada
entorno y las migraciones dejan de ser reproducibles."
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import MetaData, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.infraestructura.identificadores import uuid7

CONVENCION_NOMBRES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCION_NOMBRES)


def ahora_utc() -> datetime:
    return datetime.now(UTC)


class ConTimestamps:
    """Mixin `creado_en` server-side, en UTC (fundamentos globales del plan)."""

    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())


class ConId:
    """Clave primaria propia UUIDv7 (ARQUITECTURA.md S8): "id UUID (v7,
    ordenable por tiempo) en toda tabla; nunca un identificador externo como
    clave primaria".
    """

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
