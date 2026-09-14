"""Modelos ORM del aprovisionamiento, las fechas efectivas y el outbox (SPEC 08
S8.5-S8.10, SPEC 09 S9.3-S9.4, SPEC 11 S11.2; A-080, A-081, A-092, A-202, A-212,
A-224; Etapa P8).

Nada de este bloque se borra (A-030): un sujeto se desactiva, un repositorio
perdido queda `INACCESIBLE` con su historia, una fecha efectiva se supersede y
un mensaje queda en su estado terminal.
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
    SmallInteger,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.adaptadores.base import Base, ConId
from app.dominio.estados import (
    AlcanceReglaFecha,
    CanalMensaje,
    EstadoAccesoRepositorio,
    EstadoFechaEfectiva,
    EstadoMensaje,
    EstadoRepositorio,
    MotivoDegradado,
    MotivoDesactivacionSujeto,
    MotivoEsperandoInformacion,
    MotivoInaccesible,
    OrigenFechaEfectiva,
    OrigenMensaje,
    SubtipoErrorPermanente,
    TipoSujeto,
)

_TZ = DateTime(timezone=True)
_UUID = UUID(as_uuid=True)


def _valores(*enums: type) -> tuple[str, ...]:
    return tuple(e.value for enum in enums for e in enum)  # type: ignore[attr-defined]


class Sujeto(Base, ConId):
    """A-081: la unidad de aprovisionamiento. Cuelga de `tarea`, nunca de `entrega`."""

    __tablename__ = "sujeto"
    __table_args__ = (
        Index(
            "uq_sujeto_tarea_id_tipo_referencia",
            "tarea_id",
            "tipo",
            text("coalesce(estudiante_id, grupo_id)"),
            unique=True,
        ),
        CheckConstraint(f"tipo IN {_valores(TipoSujeto)}", name="tipo_valido"),
        CheckConstraint(
            "(estudiante_id IS NULL) <> (grupo_id IS NULL)", name="exactamente_una_referencia"
        ),
        CheckConstraint(
            f"motivo_desactivacion IS NULL OR motivo_desactivacion IN "
            f"{_valores(MotivoDesactivacionSujeto)}",
            name="motivo_desactivacion_valido",
        ),
    )

    tarea_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("tarea.id", ondelete="RESTRICT"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    estudiante_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("estudiante.id", ondelete="RESTRICT"), nullable=True
    )
    grupo_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("grupo.id", ondelete="RESTRICT"), nullable=True
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    desactivado_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    motivo_desactivacion: Mapped[str | None] = mapped_column(Text, nullable=True)


class Repositorio(Base, ConId):
    """A-092/A-211 (maquina 2) con las unicidades parciales de A-202: una fila
    `INACCESIBLE` conserva su nombre y su `github_repo_id` como evidencia, y la
    sustitucion crea una fila nueva con `reemplaza_a_id`."""

    __tablename__ = "repositorio"
    __table_args__ = (
        Index(
            "uq_repositorio_sujeto_id_no_inaccesible",
            "sujeto_id",
            unique=True,
            postgresql_where=text("estado <> 'INACCESIBLE'"),
        ),
        Index(
            "uq_repositorio_curso_id_nombre_no_inaccesible",
            "curso_id",
            "nombre",
            unique=True,
            postgresql_where=text("estado <> 'INACCESIBLE'"),
        ),
        Index(
            "uq_repositorio_github_repo_id",
            "github_repo_id",
            unique=True,
            postgresql_where=text("github_repo_id IS NOT NULL"),
        ),
        Index("ix_repositorio_tarea_id_estado", "tarea_id", "estado"),
        CheckConstraint(f"estado IN {_valores(EstadoRepositorio)}", name="estado_valido"),
        CheckConstraint(
            f"motivo IS NULL OR motivo IN "
            f"{_valores(MotivoEsperandoInformacion, MotivoDegradado, MotivoInaccesible)}",
            name="motivo_valido",
        ),
        CheckConstraint(
            f"error_codigo IS NULL OR error_codigo IN {_valores(SubtipoErrorPermanente)}",
            name="error_codigo_valido",
        ),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    tarea_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("tarea.id", ondelete="RESTRICT"), nullable=False
    )
    sujeto_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("sujeto.id", ondelete="RESTRICT"), nullable=False
    )
    github_repo_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    # A-202 punto 6: el nombre calculado por A-107/A-108, para comparar tras un renombrado.
    nombre_canonico: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    url_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    rama_por_defecto: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(
        Text, nullable=False, default=EstadoRepositorio.ESPERANDO_INFORMACION.value
    )
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    clase_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_codigo: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_mensaje_literal: Mapped[str | None] = mapped_column(Text, nullable=True)
    commit_inicial_sha: Mapped[str | None] = mapped_column(Text, nullable=True)
    intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sondeos_contenido: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    proximo_intento_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    reemplaza_a_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("repositorio.id", ondelete="RESTRICT"), nullable=True
    )
    recreado_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    listo_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class AccesoRepositorio(Base, ConId):
    """A-212 (maquina 3): el acceso del estudiante, con `push` (A-064)."""

    __tablename__ = "acceso_repositorio"
    __table_args__ = (
        Index(
            "uq_acceso_repositorio_repositorio_id_estudiante_id",
            "repositorio_id",
            "estudiante_id",
            unique=True,
        ),
        CheckConstraint(f"estado IN {_valores(EstadoAccesoRepositorio)}", name="estado_valido"),
    )

    repositorio_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("repositorio.id", ondelete="RESTRICT"), nullable=False
    )
    estudiante_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("estudiante.id", ondelete="RESTRICT"), nullable=False
    )
    cuenta_github_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("cuenta_github.id", ondelete="RESTRICT"), nullable=True
    )
    estado: Mapped[str] = mapped_column(Text, nullable=False)
    github_invitation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    invitacion_html_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    invitado_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    aceptado_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    reenvios: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    ultimo_reenvio_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    ultimo_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class ReglaFecha(Base, ConId):
    """A-080: copia cruda de lo que devuelve Canvas; una fila `BASE` por entrega."""

    __tablename__ = "regla_fecha"
    __table_args__ = (
        Index(
            "uq_regla_fecha_entrega_id_canvas_override_id",
            "entrega_id",
            "canvas_override_id",
            unique=True,
            postgresql_where=text("canvas_override_id IS NOT NULL"),
        ),
        Index(
            "uq_regla_fecha_entrega_id_base",
            "entrega_id",
            unique=True,
            postgresql_where=text("alcance = 'BASE'"),
        ),
        CheckConstraint(f"alcance IN {_valores(AlcanceReglaFecha)}", name="alcance_valido"),
    )

    entrega_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("entrega.id", ondelete="RESTRICT"), nullable=False
    )
    alcance: Mapped[str] = mapped_column(Text, nullable=False)
    canvas_override_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    seccion_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("seccion.id", ondelete="RESTRICT"), nullable=True
    )
    grupo_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("grupo.id", ondelete="RESTRICT"), nullable=True
    )
    # Ids crudos de Canvas, tal como llegan (la FK resuelta puede faltar si la
    # seccion o el grupo aun no estan en el espejo, S9.3.5).
    canvas_section_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    canvas_group_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    estudiante_ids: Mapped[list[int]] = mapped_column(
        ARRAY(BigInteger), nullable=False, default=list
    )
    due_at: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    unlock_at: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    lock_at: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    titulo: Mapped[str | None] = mapped_column(Text, nullable=True)
    sincronizado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class FechaEfectiva(Base, ConId):
    """A-082, S9.4.1: materializada y *append-only* por supersede (Ley 2).
    `due_at_utc` nulo es «sin fecha de cierre» (S9.3.2)."""

    __tablename__ = "fecha_efectiva"
    __table_args__ = (
        Index(
            "uq_fecha_efectiva_entrega_id_sujeto_id_vigente",
            "entrega_id",
            "sujeto_id",
            unique=True,
            postgresql_where=text("estado = 'VIGENTE'"),
        ),
        Index(
            "ix_fecha_efectiva_estado_due_at_utc_vigente",
            "estado",
            "due_at_utc",
            postgresql_where=text("estado = 'VIGENTE'"),
        ),
        CheckConstraint(f"origen IN {_valores(OrigenFechaEfectiva)}", name="origen_valido"),
        CheckConstraint(f"estado IN {_valores(EstadoFechaEfectiva)}", name="estado_valido"),
    )

    entrega_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("entrega.id", ondelete="RESTRICT"), nullable=False
    )
    sujeto_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("sujeto.id", ondelete="RESTRICT"), nullable=False
    )
    due_at_utc: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    origen: Mapped[str] = mapped_column(Text, nullable=False)
    # La regla puede reescribirse cuando cambia la huella (S9.4.2): la fila
    # superseda conserva su instante aunque la regla que la produjo ya no exista.
    regla_fecha_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("regla_fecha.id", ondelete="SET NULL"), nullable=True
    )
    ambigua: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    calculada_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    estado: Mapped[str] = mapped_column(
        Text, nullable=False, default=EstadoFechaEfectiva.VIGENTE.value
    )
    vigente_hasta: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)


class MensajeSaliente(Base, ConId):
    """S11.2.1 (A-125, A-224): un solo outbox. Etapa P8 lo usa para R2.3.12
    (`repositorio_disponible`, `invitacion_aceptada`); las columnas de las
    guardas 3-7 y de retractacion llegan con el Bloque 3."""

    __tablename__ = "mensaje_saliente"
    __table_args__ = (
        Index("uq_mensaje_saliente_clave_idempotencia", "clave_idempotencia", unique=True),
        Index("ix_mensaje_saliente_estado_programado_para", "estado", "programado_para"),
        Index("ix_mensaje_saliente_tarea_id", "tarea_id"),
        Index("ix_mensaje_saliente_estudiante_id", "estudiante_id"),
        Index("ix_mensaje_saliente_repositorio_id", "repositorio_id"),
        CheckConstraint(f"canal IN {_valores(CanalMensaje)}", name="canal_valido"),
        CheckConstraint(f"estado IN {_valores(EstadoMensaje)}", name="estado_valido"),
        CheckConstraint(f"origen IN {_valores(OrigenMensaje)}", name="origen_valido"),
    )

    curso_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=False
    )
    canal: Mapped[str] = mapped_column(Text, nullable=False)
    evento: Mapped[str] = mapped_column(Text, nullable=False)
    clave_idempotencia: Mapped[str] = mapped_column(Text, nullable=False)
    generacion: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    reemplaza_a_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("mensaje_saliente.id", ondelete="RESTRICT"), nullable=True
    )
    tarea_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("tarea.id", ondelete="RESTRICT"), nullable=True
    )
    sujeto_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("sujeto.id", ondelete="RESTRICT"), nullable=True
    )
    repositorio_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("repositorio.id", ondelete="RESTRICT"), nullable=True
    )
    estudiante_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("estudiante.id", ondelete="RESTRICT"), nullable=True
    )
    referencia: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    destinatario: Mapped[str] = mapped_column(Text, nullable=False)
    destinatario_canvas_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    plantilla: Mapped[str] = mapped_column(Text, nullable=False)
    plantilla_version: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    asunto: Mapped[str | None] = mapped_column(Text, nullable=True)
    cuerpo_renderizado: Mapped[str | None] = mapped_column(Text, nullable=True)
    canal_efectivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    origen: Mapped[str] = mapped_column(
        Text, nullable=False, default=OrigenMensaje.AUTOMATICO.value
    )
    disparado_por_trabajo_id: Mapped[uuid.UUID | None] = mapped_column(_UUID, nullable=True)
    programado_para: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    caduca_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    estado: Mapped[str] = mapped_column(Text, nullable=False, default=EstadoMensaje.PENDIENTE.value)
    motivo_estado: Mapped[str | None] = mapped_column(Text, nullable=True)
    intentos: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    ultimo_codigo_http: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ultimo_error_literal: Mapped[str | None] = mapped_column(Text, nullable=True)
    tomado_por: Mapped[str | None] = mapped_column(Text, nullable=True)
    tomado_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    canvas_id_resultante: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    enviado_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
