"""Modelos ORM de curso, equipo docente e invitaciones (SPEC 02 S2.4-S2.5; Etapa P2).

Los cuatro CHECK de `permisos` (S2.3.10, A-181, RG-124, RG-145) se repiten
identicos en `membresia_curso` e `invitacion_equipo`: catalogo cerrado a los
siete configurables, prohibicion de un permiso NO CONCEDIBLE en fila de
AYUDANTE, `permisos = '{}'` obligatorio en fila de PROFESOR, y prohibicion de
NULL dentro del array.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.adaptadores.base import Base, ConId
from app.dominio.estados import (
    CanalComunicacionActivo,
    EstadoCurso,
    EstadoInvitacion,
    EstadoMembresia,
    EstadoOrgGithubMembresia,
    EstadoTareaRegistro,
    RolMembresia,
    ViaAnuncioSeccion,
)
from app.dominio.permisos import PERMISOS_CONFIGURABLES, PERMISOS_NO_CONCEDIBLES

_TZ = DateTime(timezone=True)
_UUID = UUID(as_uuid=True)

_VALORES_ESTADO_CURSO = tuple(e.value for e in EstadoCurso)
_VALORES_ROL = tuple(e.value for e in RolMembresia)
_VALORES_ESTADO_MEMBRESIA = tuple(e.value for e in EstadoMembresia)
_VALORES_ESTADO_INVITACION = tuple(e.value for e in EstadoInvitacion)
_VALORES_ORG_GITHUB_ESTADO = tuple(e.value for e in EstadoOrgGithubMembresia)

_LISTA_CONFIGURABLES_SQL = (
    "ARRAY[" + ",".join(f"'{p.value}'" for p in PERMISOS_CONFIGURABLES) + "]::text[]"
)
_LISTA_NO_CONCEDIBLES_SQL = (
    "ARRAY[" + ",".join(f"'{p.value}'" for p in PERMISOS_NO_CONCEDIBLES) + "]::text[]"
)


def _checks_permisos(tabla: str) -> tuple[CheckConstraint, ...]:
    """Los cuatro CHECK de S2.3.10, parametrizados por tabla (nombre unico)."""
    return (
        CheckConstraint(
            f"permisos <@ {_LISTA_CONFIGURABLES_SQL}",
            name=f"{tabla}_permisos_catalogo_cerrado",
        ),
        CheckConstraint(
            f"NOT (rol = 'AYUDANTE' AND permisos && {_LISTA_NO_CONCEDIBLES_SQL})",
            name=f"{tabla}_permisos_no_concedible_a_ayudante",
        ),
        CheckConstraint(
            "(rol <> 'PROFESOR' OR permisos = '{}')",
            name=f"{tabla}_permisos_vacio_para_profesor",
        ),
        CheckConstraint(
            "array_position(permisos, NULL) IS NULL",
            name=f"{tabla}_permisos_sin_null",
        ),
    )


class Curso(Base, ConId):
    """Existe antes de ambos vinculos (Canvas/GitHub) y sobrevive a que uno se rompa."""

    __tablename__ = "curso"
    __table_args__ = (
        CheckConstraint(f"estado IN {_VALORES_ESTADO_CURSO}", name="estado_valido"),
        CheckConstraint("length(codigo) <= 12", name="codigo_longitud_maxima"),
        CheckConstraint("length(periodo) = 6", name="periodo_longitud_exacta"),
        CheckConstraint("length(slug) <= 24", name="slug_longitud_maxima"),
        Index("uq_curso_github_org_id", "github_org_id", unique=True),
        Index("uq_curso_github_installation_id", "github_installation_id", unique=True),
        CheckConstraint(
            f"via_anuncio_seccion IN {tuple(e.value for e in ViaAnuncioSeccion)}",
            name="via_anuncio_seccion_valida",
        ),
        CheckConstraint(
            f"canal_comunicacion_activo IS NULL OR canal_comunicacion_activo IN "
            f"{tuple(e.value for e in CanalComunicacionActivo)}",
            name="canal_comunicacion_activo_valido",
        ),
        CheckConstraint(
            f"registro_estado IN {tuple(e.value for e in EstadoTareaRegistro)}",
            name="registro_estado_valido",
        ),
    )

    estado: Mapped[str] = mapped_column(Text, nullable=False, default=EstadoCurso.BORRADOR.value)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    codigo: Mapped[str] = mapped_column(Text, nullable=False)
    periodo: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    zona_horaria: Mapped[str] = mapped_column(Text, nullable=False)
    umbral_dias_sin_actividad: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    umbral_desbalance_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=70)
    # Columnas de Etapa P3 (vinculacion Canvas), creadas ahora por S14.8.1.
    canvas_base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    canvas_course_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Columnas de Etapa P4 (vinculacion GitHub), SPEC 04 S4.2.1.
    github_org_login: Mapped[str | None] = mapped_column(Text, nullable=True)
    github_org_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    github_installation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    via_anuncio_seccion: Mapped[str] = mapped_column(
        Text, nullable=False, default=ViaAnuncioSeccion.NO_VERIFICADO.value
    )
    canal_comunicacion_activo: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Columnas de Etapa P6 (tarea de registro de GitHub), SPEC 07 S7.2.3.
    canvas_assignment_id_registro: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    registro_creado_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    registro_creado_por: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    registro_estado: Mapped[str] = mapped_column(
        Text, nullable=False, default=EstadoTareaRegistro.NO_CREADA.value
    )
    registro_huella_config: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class MembresiaCurso(Base, ConId):
    """El rol vive en la membresia, no en el usuario (S2.4.1, A-020). Nunca DELETE."""

    __tablename__ = "membresia_curso"
    __table_args__ = (
        Index("uq_membresia_curso_curso_id_usuario_id", "curso_id", "usuario_id", unique=True),
        CheckConstraint(f"rol IN {_VALORES_ROL}", name="rol_valido"),
        CheckConstraint(f"estado IN {_VALORES_ESTADO_MEMBRESIA}", name="estado_valido"),
        CheckConstraint(
            f"org_github_estado IS NULL OR org_github_estado IN {_VALORES_ORG_GITHUB_ESTADO}",
            name="org_github_estado_valido",
        ),
        *_checks_permisos("membresia_curso"),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    rol: Mapped[str] = mapped_column(Text, nullable=False)
    permisos: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    estado: Mapped[str] = mapped_column(Text, nullable=False, default=EstadoMembresia.ACTIVA.value)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    es_via_compartida: Mapped[bool] = mapped_column(nullable=False, default=False)
    # Columnas de Etapa P4 (vinculacion GitHub / org), creadas ahora por S14.8.1.
    org_github_alta_por_app: Mapped[bool] = mapped_column(nullable=False, default=False)
    org_github_estado: Mapped[str | None] = mapped_column(Text, nullable=True)
    org_github_invitada_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    org_github_activa_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    org_github_reenvios: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    org_github_ultimo_reenvio_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    org_github_ultimo_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    invitada_por: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    creada_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    retirada_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    retirada_por: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )


class InvitacionEquipo(Base, ConId):
    """Enlace nominal de un solo uso, caducidad 7 dias (S2.5.1, A-024)."""

    __tablename__ = "invitacion_equipo"
    __table_args__ = (
        Index(
            "uq_invitacion_equipo_curso_id_email_canonico_pendiente",
            "curso_id",
            "email_canonico",
            unique=True,
            postgresql_where=text("estado = 'PENDIENTE'"),
        ),
        CheckConstraint(f"rol IN {_VALORES_ROL}", name="rol_valido"),
        CheckConstraint(f"estado IN {_VALORES_ESTADO_INVITACION}", name="estado_valido"),
        *_checks_permisos("invitacion_equipo"),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    email: Mapped[str] = mapped_column(CITEXT, nullable=False)
    email_canonico: Mapped[str] = mapped_column(CITEXT, nullable=False)
    rol: Mapped[str] = mapped_column(Text, nullable=False)
    permisos: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    github_login_declarado: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    estado: Mapped[str] = mapped_column(
        Text, nullable=False, default=EstadoInvitacion.PENDIENTE.value
    )
    invitada_por: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    creada_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    expira_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    aceptada_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    revocada_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    revocada_por: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
