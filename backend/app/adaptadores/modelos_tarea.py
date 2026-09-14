"""Modelos ORM de tareas, entregas y repositorio base (SPEC 08 S8.2-S8.3;
A-080, A-164, A-203, A-208; Etapa P7).

Columnas tomadas de A-080 (con las enmiendas de A-203 sobre `entrega` y de
A-208 sobre `repositorio_base`). Todas las FK son `ON DELETE RESTRICT`: nada de
este bloque se borra (A-030).

`tarea.repositorio_base_id` y `repositorio_base.tarea_id` se referencian en
ciclo, tal como las declara A-080; la FK de `tarea` hacia `repositorio_base`
se crea despues de ambas tablas (`use_alter`).
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
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    SmallInteger,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.adaptadores.base import Base, ConId
from app.dominio.estados import (
    AdvertenciaEntrega,
    EstadoRepositorioBase,
    EstadoTarea,
    EstadoValidacionEntrega,
    ModalidadTarea,
    OrigenVisibilidadEntrega,
    TipoEntrega,
)

_TZ = DateTime(timezone=True)
_UUID = UUID(as_uuid=True)

_VALORES_MODALIDAD = tuple(e.value for e in ModalidadTarea)
_VALORES_ESTADO_TAREA = tuple(e.value for e in EstadoTarea)
_VALORES_TIPO_ENTREGA = tuple(e.value for e in TipoEntrega)
_VALORES_ESTADO_VALIDACION = tuple(e.value for e in EstadoValidacionEntrega)
_VALORES_ORIGEN_VISIBILIDAD = tuple(e.value for e in OrigenVisibilidadEntrega)
_VALORES_ESTADO_BASE = tuple(e.value for e in EstadoRepositorioBase)
_LISTA_ADVERTENCIAS_SQL = (
    "ARRAY[" + ",".join(f"'{a.value}'" for a in AdvertenciaEntrega) + "]::text[]"
)


class AssignmentCanvas(Base, ConId):
    """Espejo de las tareas de Canvas del curso (SPEC 03 entidad 20). Es de
    donde el profesor elige al crear una tarea: la pantalla nunca consulta a
    Canvas en vivo (A-089). `payload` se trunca a 64 KB al escribirse (A-090)."""

    __tablename__ = "assignment_canvas"
    __table_args__ = (
        Index(
            "uq_assignment_canvas_curso_id_canvas_assignment_id",
            "curso_id",
            "canvas_assignment_id",
            unique=True,
        ),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    canvas_assignment_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    es_grupal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    group_category_id_canvas: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    only_visible_to_overrides: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    publicada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    due_at: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    ciclos_ausente: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ausente_en_canvas: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sincronizado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class Tarea(Base, ConId):
    """A-080: `modalidad` derivada de Canvas y congelada tras el primer
    aprovisionamiento; `repositorio_base_id` nullable (R2.3.5)."""

    __tablename__ = "tarea"
    __table_args__ = (
        Index("uq_tarea_curso_id_slug", "curso_id", "slug", unique=True),
        CheckConstraint(f"modalidad IN {_VALORES_MODALIDAD}", name="modalidad_valida"),
        CheckConstraint(f"estado IN {_VALORES_ESTADO_TAREA}", name="estado_valido"),
        CheckConstraint("length(slug) <= 24", name="slug_longitud_maxima"),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    modalidad: Mapped[str] = mapped_column(Text, nullable=False)
    conjunto_grupos_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("conjunto_grupos.id", ondelete="RESTRICT"), nullable=True
    )
    repositorio_base_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID,
        ForeignKey(
            "repositorio_base.id",
            ondelete="RESTRICT",
            use_alter=True,
            name="fk_tarea_repositorio_base_id_repositorio_base",
        ),
        nullable=True,
    )
    gitignore_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(Text, nullable=False, default=EstadoTarea.BORRADOR.value)
    creada_por: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    activada_por: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    activada_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    creada_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    actualizada_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class Entrega(Base, ConId):
    """A-080 + A-203. Una tarea de Canvas pertenece a una sola entrega; `orden`
    desde 1 y contiguo; como mucho una `FINAL` por tarea."""

    __tablename__ = "entrega"
    __table_args__ = (
        Index(
            "uq_entrega_curso_id_canvas_assignment_id",
            "curso_id",
            "canvas_assignment_id",
            unique=True,
        ),
        Index("uq_entrega_tarea_id_orden", "tarea_id", "orden", unique=True),
        Index("uq_entrega_tarea_id_slug", "tarea_id", "slug", unique=True),
        Index(
            "uq_entrega_tarea_id_final",
            "tarea_id",
            unique=True,
            postgresql_where=text("tipo = 'FINAL'"),
        ),
        CheckConstraint(f"tipo IN {_VALORES_TIPO_ENTREGA}", name="tipo_valido"),
        CheckConstraint("orden >= 1", name="orden_desde_uno"),
        CheckConstraint(
            f"estado_validacion IN {_VALORES_ESTADO_VALIDACION}", name="estado_validacion_valido"
        ),
        CheckConstraint(
            f"advertencias <@ {_LISTA_ADVERTENCIAS_SQL}", name="advertencias_catalogo_cerrado"
        ),
    )

    tarea_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("tarea.id", ondelete="RESTRICT"), nullable=False
    )
    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    canvas_assignment_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    puntos_posibles: Mapped[float | None] = mapped_column(Float, nullable=True)
    grading_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    publicada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    moderated_grading: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    anonymous_grading: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    group_category_id_canvas: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    es_grupal_canvas: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    only_visible_to_overrides: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    due_at_base: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    huella_fechas: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    canvas_updated_at: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    estado_validacion: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=EstadoValidacionEntrega.VIGENTE.value,
        server_default=EstadoValidacionEntrega.VIGENTE.value,
    )
    validaciones: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    advertencias: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list, server_default=text("'{}'::text[]")
    )
    ciclos_ausente: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default=text("0")
    )
    detectada_ausente_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    sincronizado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class VisibilidadEntrega(Base):
    """A-164 paso 1. PK compuesta sin `id` propio (SPEC 03 C-02)."""

    __tablename__ = "visibilidad_entrega"
    __table_args__ = (
        CheckConstraint(f"origen IN {_VALORES_ORIGEN_VISIBILIDAD}", name="origen_valido"),
    )

    entrega_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("entrega.id", ondelete="RESTRICT"), primary_key=True
    )
    estudiante_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("estudiante.id", ondelete="RESTRICT"), primary_key=True
    )
    visible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    origen: Mapped[str] = mapped_column(Text, nullable=False)
    sincronizado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class RepositorioBase(Base, ConId):
    """A-080 + A-208. `github_repo_id` y `rama_por_defecto` quedan nulos
    mientras la creacion esta `CREANDO`: la intencion se persiste antes de
    llamar a GitHub (A-169 punto 2)."""

    __tablename__ = "repositorio_base"
    __table_args__ = (
        Index("uq_repositorio_base_tarea_id", "tarea_id", unique=True),
        Index(
            "uq_repositorio_base_github_repo_id",
            "github_repo_id",
            unique=True,
            postgresql_where=text("github_repo_id IS NOT NULL"),
        ),
        CheckConstraint(f"estado IN {_VALORES_ESTADO_BASE}", name="estado_valido"),
    )

    tarea_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("tarea.id", ondelete="RESTRICT"), nullable=False
    )
    github_repo_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    url_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    es_plantilla: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rama_por_defecto: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=EstadoRepositorioBase.CREANDO.value,
        server_default=EstadoRepositorioBase.CREANDO.value,
    )
    clase_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_mensaje_literal: Mapped[str | None] = mapped_column(Text, nullable=True)
    inaccesible_desde: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    creado_por: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    creado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class ArchivoRepositorioBase(Base, ConId):
    """A-067, A-090: metadatos y `sha` de cada archivo inicial, nunca su contenido."""

    __tablename__ = "archivo_repositorio_base"
    __table_args__ = (
        Index(
            "uq_archivo_repositorio_base_repositorio_base_id_ruta",
            "repositorio_base_id",
            "ruta",
            unique=True,
        ),
    )

    repositorio_base_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("repositorio_base.id", ondelete="RESTRICT"), nullable=False
    )
    ruta: Mapped[str] = mapped_column(Text, nullable=False)
    sha: Mapped[str] = mapped_column(Text, nullable=False)
    tamano_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    actualizado_por: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    actualizado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
