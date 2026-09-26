"""Comunicaciones ampliadas (SPEC 11 S11.2.5-S11.2.7, S11.6.3; A-125, A-225;
Etapa F10).

`plantilla_mensaje` es *append-only*: editar cierra la vigente y crea la
version siguiente. `regla_comunicacion` sin fila = valor por defecto del
catalogo; nace con el primer cambio. `cambio_fecha` sostiene el anuncio de un
cambio de fecha con su ventana de agrupacion.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.adaptadores.base import Base, ConId

_TZ = DateTime(timezone=True)
_UUID = UUID(as_uuid=True)

# S11.6.1: catalogo cerrado de siete eventos, y ninguno mas.
EVENTOS_CATALOGO = (
    "repositorio_disponible",
    "invitacion_aceptada",
    "recordatorio_mapeo",
    "recordatorio_invitacion",
    "proximidad_cierre",
    "cambio_de_fecha",
    "correccion_publicada",
)
CANALES_PLANTILLA = ("CANVAS_CONVERSACION", "CANVAS_ANUNCIO", "CANVAS_COMENTARIO", "CORREO")


class PlantillaMensaje(Base, ConId):
    __tablename__ = "plantilla_mensaje"
    __table_args__ = (
        Index(
            "uq_plantilla_mensaje_vigente",
            text("coalesce(curso_id, '00000000-0000-0000-0000-000000000000'::uuid)"),
            "clave",
            "canal",
            unique=True,
            postgresql_where=text("vigente_hasta IS NULL"),
        ),
        CheckConstraint(f"canal IN {CANALES_PLANTILLA}", name="canal_valido"),
        CheckConstraint("char_length(asunto) <= 255", name="asunto_corto"),
    )

    curso_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=True
    )
    clave: Mapped[str] = mapped_column(Text, nullable=False)
    canal: Mapped[str] = mapped_column(Text, nullable=False)
    asunto: Mapped[str] = mapped_column(Text, nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creada_por: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    creada_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    vigente_hasta: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)


class SupresionComunicacion(Base, ConId):
    __tablename__ = "supresion_comunicacion"
    __table_args__ = (
        Index(
            "uq_supresion_comunicacion_vigente",
            "curso_id",
            "estudiante_id",
            unique=True,
            postgresql_where=text("levantada_en IS NULL"),
        ),
        CheckConstraint(
            "alcance IN ('TODAS_AUTOMATICAS', 'SOLO_RECORDATORIOS')", name="alcance_valido"
        ),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    estudiante_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("estudiante.id", ondelete="RESTRICT"), nullable=False
    )
    alcance: Mapped[str] = mapped_column(Text, nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    creada_por: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    creada_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    vigente_hasta: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    levantada_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    levantada_por: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )


class CambioFecha(Base, ConId):
    """Una deteccion de cambio de fecha de una entrega, agrupada durante la
    ventana (S11.8.3). `huella_anterior` guarda la fecha de cada sujeto antes
    del primer cambio de la ventana; `huella_nueva`, la ultima vista."""

    __tablename__ = "cambio_fecha"
    __table_args__ = (
        Index("ix_cambio_fecha_entrega_id", "entrega_id"),
        CheckConstraint("ambito IN ('CURSO', 'SECCION', 'GRUPO', 'ADHOC')", name="ambito_valido"),
    )

    entrega_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("entrega.id", ondelete="RESTRICT"), nullable=False
    )
    huella_anterior: Mapped[str] = mapped_column(Text, nullable=False)
    huella_nueva: Mapped[str] = mapped_column(Text, nullable=False)
    ambito: Mapped[str] = mapped_column(Text, nullable=False)
    seccion_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(_UUID), nullable=False, default=list)
    sujeto_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(_UUID), nullable=False, default=list)
    detectado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    ventana_cierra_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    anunciado_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    mensaje_saliente_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("mensaje_saliente.id", ondelete="RESTRICT"), nullable=True
    )


class ReglaComunicacion(Base, ConId):
    __tablename__ = "regla_comunicacion"
    __table_args__ = (
        Index(
            "uq_regla_comunicacion_curso_tarea_evento",
            "curso_id",
            text("coalesce(tarea_id, '00000000-0000-0000-0000-000000000000'::uuid)"),
            "evento",
            unique=True,
        ),
        CheckConstraint(f"evento IN {EVENTOS_CATALOGO}", name="evento_valido"),
        CheckConstraint("alcance IN ('CURSO', 'TAREA')", name="alcance_valido"),
        CheckConstraint(
            "(alcance = 'CURSO') = (evento = 'recordatorio_mapeo')", name="alcance_curso_mapeo"
        ),
        CheckConstraint("(alcance = 'CURSO') = (tarea_id IS NULL)", name="tarea_segun_alcance"),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    tarea_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("tarea.id", ondelete="RESTRICT"), nullable=True
    )
    alcance: Mapped[str] = mapped_column(Text, nullable=False)
    evento: Mapped[str] = mapped_column(Text, nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False)
    actualizada_por: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    actualizada_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class VentanaSupresion(Base, ConId):
    """Ventana tras una restauracion (A-225): mientras cubre un mensaje, este
    queda DIFERIDO (guarda 7). El SPEC la nombra sin columnas; esta forma es
    una decision registrada en docs/operacion.md."""

    __tablename__ = "ventana_supresion"

    curso_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=True
    )
    desde: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    hasta: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    creada_por: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    creada_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
