"""Informe docente diario y su suscripcion (SPEC 11 S11.3.2, S11.4.2; A-229;
Etapa F9).

`informe_diario` es *append-only*: el contenido se congela al generar (Ley 2)
y dos ejecuciones del mismo dia producen una sola fila. La suscripcion es por
curso y la gobierna cada persona; no es un permiso.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.adaptadores.base import Base, ConId

_TZ = DateTime(timezone=True)
_UUID = UUID(as_uuid=True)

ESTADOS_INFORME = ("GENERADO", "SIN_TAREAS_ACTIVAS", "NO_GENERADO")
ORIGENES_INFORME = ("PROGRAMADO", "MANUAL")
ORIGENES_BAJA = ("USUARIO", "TOPE_SUSCRIPTORES", "RETIRO_MEMBRESIA", "REBOTE")


class InformeDiario(Base, ConId):
    __tablename__ = "informe_diario"
    __table_args__ = (
        Index("uq_informe_diario_curso_id_fecha", "curso_id", "fecha", unique=True),
        CheckConstraint(f"estado IN {ESTADOS_INFORME}", name="estado_valido"),
        CheckConstraint(f"origen IN {ORIGENES_INFORME}", name="origen_valido"),
        CheckConstraint(
            "estado <> 'NO_GENERADO' OR motivo IS NOT NULL", name="motivo_si_no_generado"
        ),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    fecha: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Dia en la zona horaria del curso (curso.zona_horaria)"
    )
    estado: Mapped[str] = mapped_column(Text, nullable=False)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    ventana_desde_utc: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    ventana_hasta_utc: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    origen: Mapped[str] = mapped_column(Text, nullable=False)
    disparado_por_usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    frescura: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    contenido: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    contenido_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    contenido_texto: Mapped[str | None] = mapped_column(Text, nullable=True)
    generado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class SuscripcionInforme(Base):
    __tablename__ = "suscripcion_informe"
    __table_args__ = (
        CheckConstraint(
            f"origen_baja IS NULL OR origen_baja IN {ORIGENES_BAJA}", name="origen_baja_valido"
        ),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), primary_key=True
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), primary_key=True
    )
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    origen_baja: Mapped[str | None] = mapped_column(Text, nullable=True)
    dada_de_baja_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    actualizada_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
