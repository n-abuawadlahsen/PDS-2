"""Modelos ORM de la vinculacion con Canvas (SPEC 04 S4.2.2, SPEC 05 S5.2.2; Etapa P3)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    SmallInteger,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.adaptadores.base import Base, ConId
from app.dominio.estados import EstadoCredencialCanvas

_TZ = DateTime(timezone=True)
_UUID = UUID(as_uuid=True)
_VALORES_ESTADO = tuple(e.value for e in EstadoCredencialCanvas)


class CredencialCanvas(Base, ConId):
    """Token de acceso personal cifrado. Unica tabla que persiste un secreto
    en toda la aplicacion (S14.6.2, A-176). Definida aqui, S05 la usa sin
    redefinirla (S5.2.2).
    """

    __tablename__ = "credencial_canvas"
    __table_args__ = (
        Index("uq_credencial_canvas_curso_id_usuario_id", "curso_id", "usuario_id", unique=True),
        Index(
            "uq_credencial_canvas_operativa_por_curso",
            "curso_id",
            unique=True,
            postgresql_where=text("orden_respaldo = 0"),
        ),
        CheckConstraint(f"estado IN {_VALORES_ESTADO}", name="estado_valido"),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    token_cifrado: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    huella: Mapped[str] = mapped_column(Text, nullable=False)
    canvas_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    estado: Mapped[str] = mapped_column(
        Text, nullable=False, default=EstadoCredencialCanvas.VALIDA.value
    )
    orden_respaldo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    version_clave: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    consentimiento_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    ultimo_chequeo_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    ultimo_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    fallos_403_consecutivos: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class IdentidadCanvasUsuario(Base, ConId):
    """Quien es esta persona en Canvas, ligada al usuario y a la instancia,
    nunca al curso (S5.2.2, A-033). `usuario.canvas_user_id` no existe.
    """

    __tablename__ = "identidad_canvas_usuario"
    __table_args__ = (
        Index(
            "uq_identidad_canvas_usuario_id_base_url", "usuario_id", "canvas_base_url", unique=True
        ),
        Index(
            "uq_identidad_canvas_base_url_canvas_user_id",
            "canvas_base_url",
            "canvas_user_id",
            unique=True,
        ),
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    canvas_base_url: Mapped[str] = mapped_column(Text, nullable=False)
    canvas_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    verificada_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    ultima_confirmacion_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
