"""Agregados de seguimiento (SPEC 10 S10.4.2; A-114, A-221; Etapa F6).

Los produce solo `agregar_metricas`, borrando e insertando la ventana
recalculada en una transaccion: ninguna ruta de ingesta suma a un contador
(P3). Por eso ejecutarlo dos veces no cambia ninguna fila.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.adaptadores.base import Base, ConId

_TZ = DateTime(timezone=True)
_UUID = UUID(as_uuid=True)


class MetricaRepositorioDia(Base, ConId):
    """`dia` es el dia del curso: `(fecha_committer AT TIME ZONE 'UTC' AT TIME
    ZONE curso.zona_horaria)::date` (S10.5.4)."""

    __tablename__ = "metrica_repositorio_dia"
    __table_args__ = (
        Index(
            "uq_metrica_repositorio_dia_repositorio_id_dia", "repositorio_id", "dia", unique=True
        ),
    )

    repositorio_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("repositorio.id", ondelete="RESTRICT"), nullable=False
    )
    dia: Mapped[date] = mapped_column(Date, nullable=False)
    commits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    commits_estudiantiles: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    commits_excluidos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    commits_merge: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    commits_de_bot: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    commits_docentes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dias_activos_acumulados: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ParticipacionEntrega(Base, ConId):
    """Por `(entrega, repositorio, estudiante)`, en la ventana de ese sujeto.
    `adiciones`/`eliminaciones` nulas = «no disponible», nunca cero."""

    __tablename__ = "participacion_entrega"
    __table_args__ = (
        Index(
            "uq_participacion_entrega_entrega_repositorio_estudiante",
            "entrega_id",
            "repositorio_id",
            "estudiante_id",
            unique=True,
        ),
    )

    entrega_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("entrega.id", ondelete="RESTRICT"), nullable=False
    )
    repositorio_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("repositorio.id", ondelete="RESTRICT"), nullable=False
    )
    estudiante_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("estudiante.id", ondelete="RESTRICT"), nullable=False
    )
    commits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    adiciones: Mapped[int | None] = mapped_column(Integer, nullable=True)
    eliminaciones: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dias_activos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    primer_commit_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    ultimo_commit_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    commits_coautorados: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    commits_sin_atribuir_repo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ventana_inicio: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    ventana_fin: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class ResumenTarea(Base, ConId):
    """La parte superior del tablero con una consulta por clave (S10.7.5)."""

    __tablename__ = "resumen_tarea"
    __table_args__ = (Index("uq_resumen_tarea_tarea_id", "tarea_id", unique=True),)

    tarea_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("tarea.id", ondelete="RESTRICT"), nullable=False
    )
    calculado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    contadores: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
