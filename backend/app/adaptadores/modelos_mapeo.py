"""Modelos ORM del puente Canvas <-> GitHub (SPEC 07 S7.2.2; Etapa P6).

`cuenta_github` es un catalogo global (sin `curso_id`): una cuenta real de
GitHub es una sola fila en todo el sistema. `mapeo_github` es *append-only*
(Ley 2, A-078): corregir nunca hace `UPDATE` sobre el vigente, cierra la fila
con `SUPERSEDIDO` y crea una nueva.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.adaptadores.base import Base, ConId
from app.dominio.estados import (
    EstadoCuentaGithub,
    EstadoMapeoGithub,
    MotivoInvalidacionMapeo,
    TipoCuentaGithub,
)

_TZ = DateTime(timezone=True)
_UUID = UUID(as_uuid=True)

_VALORES_TIPO_CUENTA = tuple(e.value for e in TipoCuentaGithub)
_VALORES_ESTADO_CUENTA = tuple(e.value for e in EstadoCuentaGithub)
_VALORES_ESTADO_MAPEO = tuple(e.value for e in EstadoMapeoGithub)
_VALORES_MOTIVO_INVALIDACION = tuple(e.value for e in MotivoInvalidacionMapeo)


class CuentaGithub(Base, ConId):
    """S7.2.2, S7.2.4: `login` con las mayusculas canonicas de la API
    (nunca minusculas); toda comparacion se hace por `github_user_id`."""

    __tablename__ = "cuenta_github"
    __table_args__ = (
        Index("uq_cuenta_github_github_user_id", "github_user_id", unique=True),
        CheckConstraint(f"tipo IN {_VALORES_TIPO_CUENTA}", name="tipo_valido"),
        CheckConstraint(f"estado IN {_VALORES_ESTADO_CUENTA}", name="estado_valido"),
    )

    github_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    login: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(Text, nullable=False, default=TipoCuentaGithub.USER.value)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(
        Text, nullable=False, default=EstadoCuentaGithub.VALIDA.value
    )
    revalidado_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)


class MapeoGithub(Base, ConId):
    """S7.2.2, S7.6: *append-only*, `SUPERSEDIDO` el unico estado terminal.

    Las tres unicidades parciales son literales del SPEC (la segunda es
    logicamente redundante con la primera dado que `VIGENTE` ya excluye
    `SUPERSEDIDO`, pero se declaran las tres tal como las fija S7.2.2 en vez
    de asumir que una sobra)."""

    __tablename__ = "mapeo_github"
    __table_args__ = (
        Index(
            "uq_mapeo_github_curso_id_estudiante_id_no_supersedido",
            "curso_id",
            "estudiante_id",
            unique=True,
            postgresql_where=text("estado <> 'SUPERSEDIDO'"),
        ),
        Index(
            "uq_mapeo_github_curso_id_estudiante_id_vigente",
            "curso_id",
            "estudiante_id",
            unique=True,
            postgresql_where=text("estado = 'VIGENTE'"),
        ),
        Index(
            "uq_mapeo_github_curso_id_cuenta_github_id_vigente",
            "curso_id",
            "cuenta_github_id",
            unique=True,
            postgresql_where=text("estado = 'VIGENTE'"),
        ),
        CheckConstraint(f"estado IN {_VALORES_ESTADO_MAPEO}", name="estado_valido"),
        CheckConstraint(
            f"motivo_invalidacion IS NULL OR motivo_invalidacion IN {_VALORES_MOTIVO_INVALIDACION}",
            name="motivo_invalidacion_valido",
        ),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    estudiante_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("estudiante.id", ondelete="RESTRICT"), nullable=False
    )
    cuenta_github_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("cuenta_github.id", ondelete="RESTRICT"), nullable=True
    )
    origen: Mapped[str | None] = mapped_column(Text, nullable=True)
    confianza: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidencia: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    estado: Mapped[str] = mapped_column(
        Text, nullable=False, default=EstadoMapeoGithub.SIN_DATO.value
    )
    motivo_invalidacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    vigente_desde: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    vigente_hasta: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    creado_por: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    creado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    revalidado_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
