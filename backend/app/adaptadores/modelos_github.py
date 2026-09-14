"""Modelos ORM de la vinculacion con GitHub (SPEC 04 S4.2.2, SPEC 06; Etapa P4).

`instalacion_github`: el SPEC (S4.2.2) describe su PK como `installation_id`
literal. Se aparta aqui deliberadamente hacia el mixin `ConId` (UUIDv7,
ARQUITECTURA.md S8: "nunca un identificador externo como clave primaria"),
por la misma razon que motiva esa regla general: S6.2.4 documenta que
`installation_id` es "reemplazable" tras una reinstalacion y se "sustituye...
en la misma transaccion" -- un PK no deberia mutar. Con UUIDv7 como PK e
`installation_id` como columna unica normal, esa sustitucion es un UPDATE de
columna corriente, no una mutacion de clave primaria.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.adaptadores.base import Base, ConId
from app.dominio.estados import (
    EstadoAccesoDocente,
    EstadoEquipoGithub,
    OrigenVerificacion,
    ResultadoVerificacion,
    ViaAccesoDocente,
    ViaEfectivaEquipoGithub,
)

_TZ = DateTime(timezone=True)
_UUID = UUID(as_uuid=True)

_VALORES_ESTADO_EQUIPO = tuple(e.value for e in EstadoEquipoGithub)
_VALORES_VIA_EFECTIVA = tuple(e.value for e in ViaEfectivaEquipoGithub)
_VALORES_ORIGEN = tuple(e.value for e in OrigenVerificacion)
_VALORES_RESULTADO = tuple(e.value for e in ResultadoVerificacion)
_VALORES_ESTADO_ACCESO_DOCENTE = tuple(e.value for e in EstadoAccesoDocente)
_VALORES_VIA_ACCESO_DOCENTE = tuple(e.value for e in ViaAccesoDocente)


class InstalacionGithub(Base, ConId):
    """Una instalacion huerfana tiene `curso_id` nulo (S4.6.5)."""

    __tablename__ = "instalacion_github"
    __table_args__ = (
        Index("uq_instalacion_github_installation_id", "installation_id", unique=True),
        # Unico donde no es nulo: en Postgres un indice unico corriente ya
        # admite multiples NULL (instalaciones huerfanas), sin necesitar un
        # indice parcial (S4.6.5).
        Index("uq_instalacion_github_curso_id", "curso_id", unique=True),
    )

    installation_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    curso_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=True
    )
    org_login: Mapped[str] = mapped_column(Text, nullable=False)
    org_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    repository_selection: Mapped[str] = mapped_column(Text, nullable=False)
    permisos_pendientes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    suspendida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    actualizada_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class EquipoGithubCurso(Base, ConId):
    """El equipo `docentes` de la organizacion (S4.2.2, S6.10.3)."""

    __tablename__ = "equipo_github_curso"
    __table_args__ = (
        Index("uq_equipo_github_curso_curso_id", "curso_id", unique=True),
        CheckConstraint(f"estado IN {_VALORES_ESTADO_EQUIPO}", name="estado_valido"),
        CheckConstraint(f"via_efectiva IN {_VALORES_VIA_EFECTIVA}", name="via_efectiva_valida"),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    team_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    team_slug: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(
        Text, nullable=False, default=EstadoEquipoGithub.ACTIVO.value
    )
    via_efectiva: Mapped[str] = mapped_column(
        Text, nullable=False, default=ViaEfectivaEquipoGithub.TEAM.value
    )
    creado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    ultimo_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class VerificacionVinculacion(Base, ConId):
    """21 codigos de checklist mas filas `RUNTIME` de degradacion (S4.2.2, S4.7, S4.8)."""

    __tablename__ = "verificacion_vinculacion"
    __table_args__ = (
        Index("ix_verificacion_vinculacion_curso_id_ejecucion_id", "curso_id", "ejecucion_id"),
        Index("ix_verificacion_vinculacion_curso_id_item", "curso_id", "item"),
        Index("ix_verificacion_vinculacion_curso_id_capacidad", "curso_id", "capacidad"),
        CheckConstraint(f"origen IN {_VALORES_ORIGEN}", name="origen_valido"),
        CheckConstraint(f"resultado IN {_VALORES_RESULTADO}", name="resultado_valido"),
        CheckConstraint(
            "(origen = 'CHECKLIST' AND item IS NOT NULL AND capacidad IS NULL) OR "
            "(origen = 'RUNTIME' AND capacidad IS NOT NULL AND item IS NULL)",
            name="origen_item_capacidad_coherentes",
        ),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    ejecucion_id: Mapped[uuid.UUID] = mapped_column(_UUID, nullable=False)
    item: Mapped[str | None] = mapped_column(Text, nullable=True)
    origen: Mapped[str] = mapped_column(Text, nullable=False)
    capacidad: Mapped[str | None] = mapped_column(Text, nullable=True)
    resultado: Mapped[str] = mapped_column(Text, nullable=False)
    detalle: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    ejecutada_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    ejecutada_por: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )


class IntentoInstalacionGithub(Base, ConId):
    """Persiste la intencion antes de salir a GitHub (S4.6.5, "ley del
    intento antes de la llamada")."""

    __tablename__ = "intento_instalacion_github"

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    jti: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    org_login_sugerido: Mapped[str | None] = mapped_column(Text, nullable=True)
    emitido_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    consumido_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)


class VerificacionCanal(Base, ConId):
    """Bloque "Canales de comunicacion" del paso 4, distinto del checklist (S4.2.2, S4.9).

    # TODO(Etapa F9/F10 o donde viva la logica de canales de comunicacion):
    # esta tabla nace aqui porque S4.2.2 la lista entre las "tablas propias de
    # la vinculacion", pero su logica de verificacion (S4.9) no es del alcance
    # de Etapa P4 segun docs/PLAN-IMPLEMENTACION.md.
    """

    __tablename__ = "verificacion_canal"
    __table_args__ = (
        Index("uq_verificacion_canal_curso_id_canal", "curso_id", "canal", unique=True),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    canal: Mapped[str] = mapped_column(Text, nullable=False)
    resultado: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidencia: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    verificado_por: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    verificado_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)


class AccesoDocenteRepositorio(Base, ConId):
    """A-163: lectura del equipo docente sobre un repositorio. Nacio en Etapa P4
    como esqueleto; Etapa P8 le da la forma completa.

    Con `via = TEAM` hay una fila logica por repositorio con `membresia_id`
    nulo, porque el acceso es del equipo; con `via = COLABORADOR`, una por
    persona. `github_permission` es siempre `pull`: nunca `write`, nunca `admin`.
    """

    __tablename__ = "acceso_docente_repositorio"
    __table_args__ = (
        Index(
            "uq_acceso_docente_repositorio_repositorio_membresia",
            "repositorio_id",
            text("coalesce(membresia_id, '00000000-0000-0000-0000-000000000000'::uuid)"),
            unique=True,
        ),
        CheckConstraint(f"estado IN {_VALORES_ESTADO_ACCESO_DOCENTE}", name="estado_valido"),
        CheckConstraint(f"via IN {_VALORES_VIA_ACCESO_DOCENTE}", name="via_valida"),
        CheckConstraint("github_permission = 'pull'", name="solo_lectura"),
        CheckConstraint("(via = 'TEAM') = (membresia_id IS NULL)", name="membresia_segun_via"),
    )

    repositorio_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("repositorio.id", ondelete="RESTRICT"), nullable=False
    )
    membresia_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("membresia_curso.id", ondelete="RESTRICT"), nullable=True
    )
    estado: Mapped[str] = mapped_column(Text, nullable=False)
    via: Mapped[str] = mapped_column(Text, nullable=False)
    github_permission: Mapped[str] = mapped_column(Text, nullable=False, default="pull")
    concedido_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    revocado_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    ultimo_error: Mapped[str | None] = mapped_column(Text, nullable=True)
