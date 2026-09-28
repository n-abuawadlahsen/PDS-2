"""Espejo de la actividad de GitHub (SPEC 10 S10.2.10, S10.3.2, S10.3.4; A-205,
A-221; Etapa F5).

`commit`, `autoria_commit` e `identidad_git` son evidencia y no se purgan
(S10.2.8). Un commit que desaparece de la historia se marca `huerfano`, nunca
se borra. Toda escritura de `commit` enriquece solo campos nulos y nunca
reescribe `sha`, `fecha_committer`, `recibido_en` ni `origen_ingesta`.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.adaptadores.base import Base, ConId
from app.dominio.estados import (
    EstadoEventoWebhook,
    EstadoIdentidadGit,
    FirmaEstadoCommit,
    MotivoExclusionCommit,
    OrigenIngesta,
    PapelAutoria,
    ReglaAtribucion,
)

_TZ = DateTime(timezone=True)
_UUID = UUID(as_uuid=True)


def _valores(enum: type) -> tuple[str, ...]:
    return tuple(e.value for e in enum)  # type: ignore[attr-defined]


class EventoWebhook(Base, ConId):
    """Cabecera indefinida y cuerpo truncado a 64 KB de cada entrega."""

    __tablename__ = "evento_webhook"
    __table_args__ = (
        Index("uq_evento_webhook_delivery_id", "delivery_id", unique=True),
        CheckConstraint(f"estado IN {_valores(EstadoEventoWebhook)}", name="estado_valido"),
    )

    delivery_id: Mapped[str] = mapped_column(Text, nullable=False)
    evento: Mapped[str] = mapped_column(Text, nullable=False)
    accion: Mapped[str | None] = mapped_column(Text, nullable=True)
    firma_valida: Mapped[bool] = mapped_column(Boolean, nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    payload_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload_truncado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    repositorio_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("repositorio.id", ondelete="RESTRICT"), nullable=True
    )
    repositorio_base_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("repositorio_base.id", ondelete="RESTRICT"), nullable=True
    )
    motivo_no_resuelto: Mapped[str | None] = mapped_column(Text, nullable=True)
    recibido_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    procesado_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    estado: Mapped[str] = mapped_column(Text, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class EventoPush(Base, ConId):
    """Metadatos de cada push (tambien los de rama creada o borrada)."""

    __tablename__ = "evento_push"
    __table_args__ = (
        Index("ix_evento_push_repositorio_id_recibido_en", "repositorio_id", "recibido_en"),
    )

    repositorio_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("repositorio.id", ondelete="RESTRICT"), nullable=False
    )
    delivery_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    ref: Mapped[str] = mapped_column(Text, nullable=False)
    before_sha: Mapped[str] = mapped_column(Text, nullable=False)
    after_sha: Mapped[str] = mapped_column(Text, nullable=False)
    n_commits_payload: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    forzado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    divergido: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    n_commits_huerfanos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recibido_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class IdentidadGit(Base, ConId):
    """S10.3.4: autores no resueltos por correo, append-only con una fila
    vigente por `(repositorio, email_normalizado)` (RG-006)."""

    __tablename__ = "identidad_git"
    __table_args__ = (
        Index(
            "uq_identidad_git_repositorio_id_email_vigente",
            "repositorio_id",
            "email_normalizado",
            unique=True,
            postgresql_where=text("estado <> 'SUPERSEDIDA'"),
        ),
        Index("ix_identidad_git_curso_id_email_normalizado", "curso_id", "email_normalizado"),
        CheckConstraint(f"estado IN {_valores(EstadoIdentidadGit)}", name="estado_valido"),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    repositorio_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("repositorio.id", ondelete="RESTRICT"), nullable=False
    )
    email_normalizado: Mapped[str] = mapped_column(Text, nullable=False)
    email_visto: Mapped[str] = mapped_column(Text, nullable=False)
    nombre_visto: Mapped[str | None] = mapped_column(Text, nullable=True)
    nombre_visto_ultimo: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(
        Text, nullable=False, default=EstadoIdentidadGit.SIN_RESOLVER.value
    )
    estudiante_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("estudiante.id", ondelete="RESTRICT"), nullable=True
    )
    resuelta_por: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    resuelta_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    vigente_desde: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    vigente_hasta: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)


class Commit(Base, ConId):
    __tablename__ = "commit"
    __table_args__ = (
        Index("uq_commit_repositorio_id_sha", "repositorio_id", "sha", unique=True),
        Index("ix_commit_repositorio_id_fecha_committer", "repositorio_id", "fecha_committer"),
        Index(
            "ix_commit_repositorio_id_estudiante_id_fecha",
            "repositorio_id",
            "estudiante_id",
            "fecha_committer",
        ),
        Index(
            "ix_commit_repositorio_id_rama_defecto_fecha",
            "repositorio_id",
            "en_rama_por_defecto",
            "fecha_committer",
        ),
        CheckConstraint(
            f"origen_ingesta IN {_valores(OrigenIngesta)}", name="origen_ingesta_valido"
        ),
        CheckConstraint(
            f"motivo_exclusion IN {_valores(MotivoExclusionCommit)}", name="motivo_exclusion_valido"
        ),
        CheckConstraint(
            f"regla_atribucion IN {_valores(ReglaAtribucion)}", name="regla_atribucion_valida"
        ),
        CheckConstraint(
            f"firma_estado IN {_valores(FirmaEstadoCommit)}", name="firma_estado_valido"
        ),
    )

    repositorio_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("repositorio.id", ondelete="RESTRICT"), nullable=False
    )
    sha: Mapped[str] = mapped_column(Text, nullable=False)
    parent_shas: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    n_padres: Mapped[int | None] = mapped_column(Integer, nullable=True)
    es_merge: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rama_detectada: Mapped[str | None] = mapped_column(Text, nullable=True)
    en_rama_por_defecto: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mensaje_resumen: Mapped[str | None] = mapped_column(Text, nullable=True)
    autor_nombre: Mapped[str | None] = mapped_column(Text, nullable=True)
    autor_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    autor_github_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    committer_github_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    fecha_autor: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    fecha_committer: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    via_web: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    adiciones: Mapped[int | None] = mapped_column(Integer, nullable=True)
    eliminaciones: Mapped[int | None] = mapped_column(Integer, nullable=True)
    archivos_tocados: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sin_cambios: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    identidad_git_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("identidad_git.id", ondelete="RESTRICT"), nullable=True
    )
    estudiante_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("estudiante.id", ondelete="RESTRICT"), nullable=True
    )
    regla_atribucion: Mapped[str] = mapped_column(
        Text, nullable=False, default=ReglaAtribucion.SIN_ATRIBUIR.value
    )
    motivo_exclusion: Mapped[str] = mapped_column(
        Text, nullable=False, default=MotivoExclusionCommit.NINGUNO.value
    )
    autor_es_bot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    autor_es_docente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    huerfano: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    huerfano_desde: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    historia_importada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    firma_estado: Mapped[str] = mapped_column(
        Text, nullable=False, default=FirmaEstadoCommit.DESCONOCIDA.value
    )
    firma_motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    origen_ingesta: Mapped[str] = mapped_column(Text, nullable=False)
    recibido_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    ingresado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    enriquecido_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)


class AutoriaCommit(Base, ConId):
    """S10.3.2 (A-205): la unica tabla de autoria. `commit.estudiante_id`,
    `regla_atribucion` e `identidad_git_id` son la copia de la fila `AUTOR`."""

    __tablename__ = "autoria_commit"
    __table_args__ = (
        Index(
            "uq_autoria_commit_commit_id_acreditado",
            "commit_id",
            text("coalesce(estudiante_id, identidad_git_id)"),
            unique=True,
        ),
        CheckConstraint(f"papel IN {_valores(PapelAutoria)}", name="papel_valido"),
        CheckConstraint(
            f"regla_atribucion IN {_valores(ReglaAtribucion)}", name="regla_atribucion_valida"
        ),
        CheckConstraint(
            "confianza IS NULL OR confianza IN ('ALTA', 'MEDIA')", name="confianza_valida"
        ),
        CheckConstraint(
            "estudiante_id IS NOT NULL OR identidad_git_id IS NOT NULL", name="acreditado_presente"
        ),
    )

    commit_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("commit.id", ondelete="RESTRICT"), nullable=False
    )
    estudiante_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("estudiante.id", ondelete="RESTRICT"), nullable=True
    )
    identidad_git_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("identidad_git.id", ondelete="RESTRICT"), nullable=True
    )
    papel: Mapped[str] = mapped_column(Text, nullable=False)
    regla_atribucion: Mapped[str] = mapped_column(Text, nullable=False)
    confianza: Mapped[str | None] = mapped_column(Text, nullable=True)
