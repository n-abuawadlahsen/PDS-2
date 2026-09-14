"""Modelos ORM del espejo de Canvas: estudiantes, secciones y grupos
(SPEC 07 S7.2; Etapa P5).

Columnas tomadas literalmente de la tabla de S7.2.1. Todas las FK son
`ON DELETE RESTRICT` (S7.2.5, A-030): ninguna fila de este espejo se borra
jamas, se marca `ACTIVA`/`ELIMINADA`/`RETIRADO`/`activa=false` segun la
entidad.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.adaptadores.base import Base, ConId
from app.dominio.estados import (
    EstadoEstudiante,
    EstadoGrupo,
    EstadoSeccion,
    WorkflowStatePertenenciaGrupo,
)

_TZ = DateTime(timezone=True)
_UUID = UUID(as_uuid=True)

_VALORES_ESTADO_SECCION = tuple(e.value for e in EstadoSeccion)
_VALORES_ESTADO_ESTUDIANTE = tuple(e.value for e in EstadoEstudiante)
_VALORES_ESTADO_GRUPO = tuple(e.value for e in EstadoGrupo)
_VALORES_WORKFLOW_PERTENENCIA = tuple(e.value for e in WorkflowStatePertenenciaGrupo)


class Seccion(Base, ConId):
    """S7.2.1, S7.3.2. `nonxlist_course_id` no nulo = seccion cross-listed (A-053)."""

    __tablename__ = "seccion"
    __table_args__ = (
        Index(
            "uq_seccion_curso_id_canvas_section_id", "curso_id", "canvas_section_id", unique=True
        ),
        CheckConstraint(f"estado IN {_VALORES_ESTADO_SECCION}", name="estado_valido"),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    canvas_section_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    sis_section_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    nonxlist_course_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    estado: Mapped[str] = mapped_column(Text, nullable=False, default=EstadoSeccion.ACTIVA.value)
    ciclos_ausente: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sincronizado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class Estudiante(Base, ConId):
    """S7.2.1, S7.2.4. `canvas_user_id` es la clave de identidad efectiva
    (RG-156, A-074); `sis_user_id`/`login_id`/`uuid`/`past_uuid` son solo
    para reconciliacion (Etapa P6), nunca identidad."""

    __tablename__ = "estudiante"
    __table_args__ = (
        Index("uq_estudiante_curso_id_canvas_user_id", "curso_id", "canvas_user_id", unique=True),
        CheckConstraint(f"estado IN {_VALORES_ESTADO_ESTUDIANTE}", name="estado_valido"),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    canvas_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    nombre_ordenable: Mapped[str | None] = mapped_column(Text, nullable=True)
    login_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    sis_user_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    uuid: Mapped[str | None] = mapped_column(Text, nullable=True)
    past_uuid: Mapped[str | None] = mapped_column(Text, nullable=True)
    group_ids_canvas: Mapped[list[int]] = mapped_column(JSONB, nullable=False, default=list)
    estado: Mapped[str] = mapped_column(Text, nullable=False, default=EstadoEstudiante.ACTIVO.value)
    ciclos_ausente: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    primera_vista_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    ultima_vista_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    retirado_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    # Columna de Etapa P6 (recordatorio manual de Pendientes, "tope 1/dia").
    ultimo_recordatorio_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)


class Matricula(Base, ConId):
    """S7.2.1: una fila por matricula, no por persona (A-044). `tipo`/`estado`
    son el `type`/`workflow_state` que Canvas devuelve, texto libre: mirroring
    de un vocabulario externo, no un catalogo propio (a diferencia de
    `estudiante.estado`, que si es nuestro y esta cerrado)."""

    __tablename__ = "matricula"
    __table_args__ = (
        Index(
            "uq_matricula_curso_id_canvas_enrollment_id",
            "curso_id",
            "canvas_enrollment_id",
            unique=True,
        ),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    estudiante_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("estudiante.id", ondelete="RESTRICT"), nullable=False
    )
    seccion_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("seccion.id", ondelete="RESTRICT"), nullable=False
    )
    canvas_enrollment_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    estado: Mapped[str] = mapped_column(Text, nullable=False)
    limitada_a_seccion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sincronizado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class ConjuntoGrupos(Base, ConId):
    """S7.2.1, S7.3.3. Solo los colaborativos generan `grupo`; las
    *differentiation tags* (`no_colaborativo=true`) son solo informativas."""

    __tablename__ = "conjunto_grupos"
    __table_args__ = (
        Index(
            "uq_conjunto_grupos_curso_id_canvas_group_category_id",
            "curso_id",
            "canvas_group_category_id",
            unique=True,
        ),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    canvas_group_category_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    no_colaborativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    self_signup: Mapped[str | None] = mapped_column(Text, nullable=True)
    group_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    auto_leader: Mapped[str | None] = mapped_column(Text, nullable=True)
    sincronizado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class Grupo(Base, ConId):
    """S7.2.1, S7.3.3."""

    __tablename__ = "grupo"
    __table_args__ = (
        Index("uq_grupo_curso_id_canvas_group_id", "curso_id", "canvas_group_id", unique=True),
        CheckConstraint(f"estado IN {_VALORES_ESTADO_GRUPO}", name="estado_valido"),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    conjunto_grupos_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("conjunto_grupos.id", ondelete="RESTRICT"), nullable=False
    )
    canvas_group_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(Text, nullable=False, default=EstadoGrupo.ACTIVO.value)
    lider_estudiante_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("estudiante.id", ondelete="RESTRICT"), nullable=True
    )
    is_full: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ciclos_ausente: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sincronizado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class PertenenciaGrupo(Base, ConId):
    """S7.2.1, S7.3.4. `entro_en`/`salio_en` no existen (RG-008): la vigencia
    se lee de `activa_desde`/`activa_hasta`. Deliberadamente **sin** unicidad
    `(conjunto_grupos, estudiante)` (A-049, S7.3.6): Canvas no lo garantiza."""

    __tablename__ = "pertenencia_grupo"
    __table_args__ = (
        Index(
            "uq_pertenencia_grupo_grupo_id_estudiante_id", "grupo_id", "estudiante_id", unique=True
        ),
        CheckConstraint(
            f"workflow_state IN {_VALORES_WORKFLOW_PERTENENCIA}", name="workflow_state_valido"
        ),
    )

    grupo_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("grupo.id", ondelete="RESTRICT"), nullable=False
    )
    estudiante_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("estudiante.id", ondelete="RESTRICT"), nullable=False
    )
    workflow_state: Mapped[str] = mapped_column(Text, nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    activa_desde: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    activa_hasta: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    ciclos_ausente: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    origen: Mapped[str | None] = mapped_column(Text, nullable=True)
    sincronizado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
