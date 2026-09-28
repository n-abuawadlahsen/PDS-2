"""`version_entrega`: la evidencia de R2.4.5-R2.4.8 (SPEC 09 S9.6-S9.9; SPEC 03
fila 36; A-084, A-204, A-213, RG-025, RG-026, RG-028; Etapa F4).

No existe ninguna fila antes de que el SHA quede resuelto (S9.6.1). La fila
nunca se borra ni se actualiza fuera de la lista cerrada de columnas
mutables: lo garantizan `app/dominio/versiones.validar_cambios` en la
aplicacion y el disparador `version_entrega_inmutable` en la base (migracion
0003), para que ni un `UPDATE` a mano pueda tocar la evidencia (CA-9.8-01).

«FK para navegar, copia para leer» (S9.9.1): ademas de las claves foraneas,
la fila copia en el momento de la captura el bloque de contexto que la hace
legible aunque el origen cambie o desaparezca.
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
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.adaptadores.base import Base, ConId
from app.dominio.estados import (
    EstadoVersion,
    MotivoVersion,
    OrigenCaptura,
    TagEstado,
    TagMotivo,
)

_TZ = DateTime(timezone=True)
_UUID = UUID(as_uuid=True)


def _valores(enum: type) -> tuple[str, ...]:
    return tuple(e.value for e in enum)  # type: ignore[attr-defined]


class VersionEntrega(Base, ConId):
    __tablename__ = "version_entrega"
    __table_args__ = (
        Index(
            "uq_version_entrega_entrega_id_sujeto_id_intento",
            "entrega_id",
            "sujeto_id",
            "intento",
            unique=True,
        ),
        Index(
            "uq_version_entrega_entrega_id_sujeto_id_vigente",
            "entrega_id",
            "sujeto_id",
            unique=True,
            postgresql_where=text("vigente"),
        ),
        Index(
            "ix_version_entrega_integrantes",
            "integrantes",
            postgresql_using="gin",
            postgresql_ops={"integrantes": "jsonb_path_ops"},
        ),
        CheckConstraint(f"estado IN {_valores(EstadoVersion)}", name="estado_valido"),
        CheckConstraint(
            f"motivo IS NULL OR motivo IN {_valores(MotivoVersion)}", name="motivo_valido"
        ),
        CheckConstraint(f"tag_estado IN {_valores(TagEstado)}", name="tag_estado_valido"),
        CheckConstraint(
            f"tag_motivo IS NULL OR tag_motivo IN {_valores(TagMotivo)}",
            name="tag_motivo_valido",
        ),
        CheckConstraint(
            f"origen_captura IN {_valores(OrigenCaptura)}", name="origen_captura_valido"
        ),
        # S9.6.3 (RG-025): el invariante escrito por implicaciones.
        CheckConstraint(
            "(estado <> 'CAPTURADA' OR tag_estado = 'CREADO')"
            " AND (estado <> 'CAPTURADA_SIN_TAG'"
            " OR tag_estado IN ('PENDIENTE', 'CONFLICTO', 'FALLIDO'))"
            " AND (estado NOT IN ('SIN_COMMITS', 'SIN_REPOSITORIO', 'ERROR')"
            " OR tag_estado = 'NO_APLICA')"
            " AND (estado <> 'REVISAR'"
            " OR tag_estado IN ('CREADO', 'PENDIENTE', 'CONFLICTO', 'FALLIDO'))",
            name="estado_implica_tag",
        ),
        # S9.8.8: una accion manual siempre lleva actor y motivo escrito.
        CheckConstraint(
            "origen_captura = 'AUTOMATICA'"
            " OR (creada_por_usuario_id IS NOT NULL AND length(trim(motivo_manual)) >= 10)",
            name="manual_con_actor_y_motivo",
        ),
        CheckConstraint(
            "estado IN ('SIN_COMMITS', 'SIN_REPOSITORIO', 'ERROR') OR commit_sha IS NOT NULL",
            name="sha_si_hay_version",
        ),
    )

    entrega_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("entrega.id", ondelete="RESTRICT"), nullable=False
    )
    sujeto_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey("sujeto.id", ondelete="RESTRICT"), nullable=False
    )
    repositorio_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("repositorio.id", ondelete="RESTRICT"), nullable=True
    )
    intento: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_corte_utc: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    rama: Mapped[str | None] = mapped_column(Text, nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(Text, nullable=True)
    commit_tree_sha: Mapped[str | None] = mapped_column(Text, nullable=True)
    commit_fecha_autor: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    commit_fecha_committer: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    commit_mensaje: Mapped[str | None] = mapped_column(Text, nullable=True)
    tag_nombre: Mapped[str | None] = mapped_column(Text, nullable=True)
    tag_estado: Mapped[str] = mapped_column(Text, nullable=False)
    tag_motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    tag_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    tag_creado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Sin DEFAULT: el estado siempre lo decide quien captura (A-213).
    estado: Mapped[str] = mapped_column(Text, nullable=False)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    motivo_repositorio: Mapped[str | None] = mapped_column(Text, nullable=True)
    vigente: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reemplaza_a_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("version_entrega.id", ondelete="RESTRICT"), nullable=True
    )
    advertencias: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    verificacion: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    integrantes: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    origen_captura: Mapped[str] = mapped_column(Text, nullable=False)
    creada_por_usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    motivo_manual: Mapped[str | None] = mapped_column(Text, nullable=True)
    capturada_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    # Bloque de contexto congelado (S9.9.1).
    github_repo_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    repositorio_full_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    org_login: Mapped[str | None] = mapped_column(Text, nullable=True)
    installation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    sujeto_tipo: Mapped[str] = mapped_column(Text, nullable=False)
    sujeto_etiqueta: Mapped[str] = mapped_column(Text, nullable=False)
    estado_sujeto_al_cierre: Mapped[str | None] = mapped_column(Text, nullable=True)
    seccion_nombre: Mapped[str | None] = mapped_column(Text, nullable=True)
    canvas_section_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    fecha_origen: Mapped[str | None] = mapped_column(Text, nullable=True)
    canvas_override_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    override_titulo: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_ambigua: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
