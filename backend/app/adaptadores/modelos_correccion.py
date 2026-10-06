"""Correccion: asignacion, borrador, notas internas, espejo de Canvas y
evidencia de publicacion (SPEC 12 S12.2; A-134..A-143, A-206, A-214;
Etapas F11-F12).

Ninguna columna espeja a Canvas dentro de `correccion` (S12.2.3): lo que
Canvas tiene vive solo en `estado_canvas_submission`, y el contraste entre
los dos se calcula, nunca se guarda (A-206).
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
    LargeBinary,
    Numeric,
    SmallInteger,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.adaptadores.base import Base, ConId
from app.dominio.estados import (
    ClaseNotaInterna,
    CriterioAsignacion,
    DesenlaceReclamo,
    EstadoCorreccion,
    MotivoNoPublicable,
)

_TZ = DateTime(timezone=True)
_UUID = UUID(as_uuid=True)


def _valores(enum: Any) -> tuple[str, ...]:
    return tuple(e.value for e in enum)


class AsignacionCorreccion(Base, ConId):
    """El grano es `(entrega, sujeto)`; `membresia_id` nulo = sin corrector.
    Sin columna de estado: el estado es de `correccion` (RG-034)."""

    __tablename__ = "asignacion_correccion"
    __table_args__ = (
        Index(
            "uq_asignacion_correccion_entrega_id_sujeto_id",
            "entrega_id",
            "sujeto_id",
            unique=True,
        ),
        Index("ix_asignacion_correccion_membresia_id", "membresia_id"),
        CheckConstraint(f"criterio IN {_valores(CriterioAsignacion)}", name="criterio_valido"),
        CheckConstraint(
            "desalineada_motivo IS NULL OR desalineada_motivo IN "
            "('CAMBIO_DE_SECCION', 'CAMBIO_DE_GRUPO')",
            name="desalineada_motivo_valido",
        ),
    )

    entrega_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("entrega.id", ondelete="RESTRICT"), nullable=False
    )
    sujeto_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("sujeto.id", ondelete="RESTRICT"), nullable=False
    )
    membresia_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("membresia_curso.id", ondelete="RESTRICT"), nullable=True
    )
    asignada_por: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("membresia_curso.id", ondelete="RESTRICT"), nullable=True
    )
    asignada_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    iniciada_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    criterio: Mapped[str] = mapped_column(Text, nullable=False)
    criterio_seccion_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("seccion.id", ondelete="RESTRICT"), nullable=True
    )
    criterio_contexto: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    desalineada_motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    desalineada_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)


class Correccion(Base, ConId):
    __tablename__ = "correccion"
    __table_args__ = (
        Index("uq_correccion_entrega_id_sujeto_id", "entrega_id", "sujeto_id", unique=True),
        CheckConstraint(f"estado IN {_valores(EstadoCorreccion)}", name="estado_valido"),
        CheckConstraint(
            f"motivo_no_publicable IS NULL OR motivo_no_publicable IN "
            f"{_valores(MotivoNoPublicable)}",
            name="motivo_no_publicable_valido",
        ),
        CheckConstraint(
            "publicable OR motivo_no_publicable IS NOT NULL", name="motivo_si_no_publicable"
        ),
        CheckConstraint("tipo_resultado IN ('NOTA', 'EXCUSADA')", name="tipo_resultado_valido"),
    )

    entrega_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("entrega.id", ondelete="RESTRICT"), nullable=False
    )
    sujeto_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("sujeto.id", ondelete="RESTRICT"), nullable=False
    )
    version_entrega_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("version_entrega.id", ondelete="RESTRICT"), nullable=True
    )
    estado: Mapped[str] = mapped_column(
        Text, nullable=False, default=EstadoCorreccion.SIN_CORRECTOR.value
    )
    trabajo_publicacion_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("trabajo.id", ondelete="RESTRICT"), nullable=True
    )
    # Borrador: pertenece al par (entrega, sujeto), no al corrector.
    nota_local: Mapped[str | None] = mapped_column(Text, nullable=True)
    rubrica_local: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)
    comentario_renderizado: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalado_aplicado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    huella_rubrica: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    rubrica_revisada_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    corrector_usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    actualizado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    lista_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    publicable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    motivo_no_publicable: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Banderas ortogonales al estado (S12.3.4).
    version_desactualizada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reclamo_abierto: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sin_commits: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reconocimiento_sin_codigo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reconocimiento_sin_codigo_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    tipo_resultado: Mapped[str] = mapped_column(Text, nullable=False, default="NOTA")
    publicada_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ultimo_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    motivo_reapertura: Mapped[str | None] = mapped_column(Text, nullable=True)
    reabierta_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    reabierta_por: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    banderas: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)


class NotaInternaCorreccion(Base, ConId):
    """Canal interno *append-only*: un disparador rechaza todo UPDATE. El
    reclamo del estudiante vive aqui y nunca abre incidencia (S12.15.1)."""

    __tablename__ = "nota_interna_correccion"
    __table_args__ = (
        Index("ix_nota_interna_correccion_correccion_id", "correccion_id"),
        CheckConstraint(f"clase IN {_valores(ClaseNotaInterna)}", name="clase_valida"),
        CheckConstraint(
            f"desenlace_reclamo IS NULL OR desenlace_reclamo IN {_valores(DesenlaceReclamo)}",
            name="desenlace_valido",
        ),
        CheckConstraint(
            "(clase = 'RECLAMO_CERRADO') = (desenlace_reclamo IS NOT NULL)",
            name="desenlace_solo_al_cerrar",
        ),
    )

    correccion_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("correccion.id", ondelete="RESTRICT"), nullable=False
    )
    autor_membresia_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("membresia_curso.id", ondelete="RESTRICT"), nullable=False
    )
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    clase: Mapped[str] = mapped_column(Text, nullable=False, default="NOTA")
    desenlace_reclamo: Mapped[str | None] = mapped_column(Text, nullable=True)
    creada_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class EstadoCanvasSubmission(Base):
    """La unica fuente de «que tiene Canvas» (A-206). Nunca se lee
    `submission_summary`."""

    __tablename__ = "estado_canvas_submission"

    entrega_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("entrega.id", ondelete="RESTRICT"), primary_key=True
    )
    estudiante_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("estudiante.id", ondelete="RESTRICT"), primary_key=True
    )
    workflow_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    entered_score: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    grade: Mapped[str | None] = mapped_column(Text, nullable=True)
    graded_at: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    grader_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    excused: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    late: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    seconds_late: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points_deducted: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    gradeable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    origen: Mapped[str] = mapped_column(
        Text, nullable=False, default="CANVAS", server_default="CANVAS"
    )
    sincronizado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class PublicacionNota(Base, ConId):
    """Evidencia *append-only* de lo que se escribio en Canvas: una fila por
    estudiante e intento, tambien en grupos. Un disparador rechaza UPDATE."""

    __tablename__ = "publicacion_nota"
    __table_args__ = (
        Index(
            "uq_publicacion_nota_correccion_estudiante_intento",
            "correccion_id",
            "estudiante_id",
            "intento",
            unique=True,
        ),
    )

    correccion_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("correccion.id", ondelete="RESTRICT"), nullable=False
    )
    estudiante_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("estudiante.id", ondelete="RESTRICT"), nullable=False
    )
    intento: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    payload_enviado: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    codigo_http: Mapped[int | None] = mapped_column(Integer, nullable=True)
    respuesta: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    score_devuelto: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    entered_score_devuelto: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    grade_devuelto: Mapped[str | None] = mapped_column(Text, nullable=True)
    grader_id_reportado: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    late_policy_status_enviado: Mapped[str] = mapped_column(Text, nullable=False, default="none")
    publicado_por_usuario_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    credencial_canvas_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("credencial_canvas.id", ondelete="RESTRICT"), nullable=True
    )
    intentada_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
