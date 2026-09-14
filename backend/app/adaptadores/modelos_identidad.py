"""Modelos ORM de identidad y sesion (SPEC 02 S2.2.5, S2.2.6; Etapa P1).

Columnas tomadas de docs/PLAN-IMPLEMENTACION.md Etapa P1 y de
docs/SPEC/02-roles-y-permisos.md S2.2.5-S2.2.6. Tipos explicitos (Text,
DateTime(timezone=True)) para que coincidan exactamente con la migracion 0001
y la puerta de divergencia (S14.9.2) quede en verde. Claves primarias UUIDv7
via el mixin `ConId` (ARQUITECTURA.md S8).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Text, text
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.adaptadores.base import Base, ConId

_TZ = DateTime(timezone=True)


class Usuario(Base, ConId):
    """Identidad de persona. `activo=false` = cuenta cerrada por su propio dueño.

    Nunca se borra la fila (A-030, A-190, S2.10.3).
    """

    __tablename__ = "usuario"
    __table_args__ = (
        CheckConstraint("email LIKE '%@gmail.com'", name="email_dominio_gmail"),
        Index(
            "uq_usuario_cuenta_github_id",
            "cuenta_github_id",
            unique=True,
            postgresql_where=text("cuenta_github_id IS NOT NULL"),
        ),
    )

    google_sub: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)
    email_canonico: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # `cuenta_github_id` sera un FK a la futura tabla `cuenta_github` (SPEC 02
    # S2.4.3, catalogo global con elegibilidad -- Etapa P6). Se creo en Etapa
    # P1 como columna de solo tipo, sin escritor todavia.
    cuenta_github_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Simplificacion de Etapa P4 (SPEC 02 S2.8.1, "declaracion de la cuenta"):
    # el login validado en vivo contra GitHub, para poder incorporar al equipo
    # docente sin esperar al catalogo `cuenta_github` completo de P6. Cuando
    # P6 exista, `cuenta_github_id` pasa a ser la fuente y esta columna se
    # retira -- documentado, no una decision silenciosa.
    github_login_declarado: Mapped[str | None] = mapped_column(Text, nullable=True)
    consentimiento_github_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    generacion_enlaces: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class Sesion(Base, ConId):
    """Cookie opaca respaldada en base de datos (S2.2.6). Nunca un JWT autocontenido."""

    __tablename__ = "sesion"
    __table_args__ = (Index("ix_sesion_usuario_id", "usuario_id"),)

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    # La unicidad de jti_oidc es el mecanismo estructural anti-repeticion de
    # `state` (S2.2.2): un segundo canje del mismo jti viola esta restriccion.
    jti_oidc: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    creada_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    expira_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    revocada_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    agente: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_truncada: Mapped[str | None] = mapped_column(Text, nullable=True)


class SesionMembresia(Base):
    """Da efecto inmediato a cambios de rol/permisos (A-023, S2.2.6)."""

    __tablename__ = "sesion_membresia"

    sesion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sesion.id", ondelete="RESTRICT"), primary_key=True
    )
    membresia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("membresia_curso.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    refrescada_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
