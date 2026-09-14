"""Modelos ORM de las tablas de infraestructura propia (SPEC 14, Etapa 0).

Columnas tomadas literalmente de docs/SPEC/14-infraestructura-y-despliegue.md
S14.7.1 (trabajo, trabajo_periodico) y de docs/PLAN-IMPLEMENTACION.md Etapa 0
(presupuesto_api, cubo_tasa, bitacora, incidencia, sincronizacion,
cursor_sincronizacion). Donde una tabla solo tenia "-" como columnas
(salud_proveedor_curso, estado_sistema, resultado_invariante) o no tenia
columnas propias documentadas (respaldo), se deja un esquema minimo con un
comentario `# TODO(etapa-operacion)` citando de donde debe salir el esquema
completo -- nunca se inventan columnas de negocio no citadas.

Tipos de columna explicitos en todas partes (Text/DateTime(timezone)) en vez
de dejar que `Mapped[str|datetime]` infiera String/DateTime naive: son los
tipos que la migracion 0001 realmente crea, y la puerta de CI de divergencia
(S14.9.2) compara exactamente esto. Claves primarias UUIDv7 via el mixin
`ConId`; `curso_id` es UUID con FK a `curso.id` desde que esa tabla existe
(Etapa P2) -- ver ARQUITECTURA.md S8.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.adaptadores.base import Base, ConId
from app.dominio.estados import EstadoTrabajo, ResultadoSincronizacion

_VALORES_ESTADO_TRABAJO = tuple(e.value for e in EstadoTrabajo)
_VALORES_RESULTADO_SYNC = tuple(e.value for e in ResultadoSincronizacion)

_TZ = DateTime(timezone=True)
_UUID = UUID(as_uuid=True)


class Trabajo(Base, ConId):
    """Cola de trabajos en segundo plano (S14.7.1). Sustituye a Redis/Celery."""

    __tablename__ = "trabajo"
    __table_args__ = (
        CheckConstraint(f"estado IN {_VALORES_ESTADO_TRABAJO}", name="estado_valido"),
        # Indice unico parcial: la clave de idempotencia solo es unica mientras
        # el trabajo no llego a un estado terminal (S14.7.2 garantia 1).
        Index(
            "uq_trabajo_clave_idempotencia_no_terminal",
            "clave_idempotencia",
            unique=True,
            postgresql_where=text("estado NOT IN ('OK', 'CANCELADO')"),
        ),
        Index("ix_trabajo_estado_proximo_intento", "estado", "proximo_intento_en"),
    )

    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    clave_idempotencia: Mapped[str] = mapped_column(Text, nullable=False)
    curso_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    estado: Mapped[str] = mapped_column(Text, nullable=False, default=EstadoTrabajo.PENDIENTE.value)
    intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_intentos: Mapped[int] = mapped_column(Integer, nullable=False)
    proximo_intento_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    tomado_por: Mapped[str | None] = mapped_column(Text, nullable=True)
    tomado_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    ultimo_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    coste_api: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    creado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    terminado_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    motivo_cancelacion: Mapped[str | None] = mapped_column(Text, nullable=True)


class TrabajoPeriodico(Base, ConId):
    """Planificador: filas recorridas por el tick del trabajador cada 30s (S14.7.1)."""

    __tablename__ = "trabajo_periodico"
    __table_args__ = (UniqueConstraint("tipo", "curso_id"),)

    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    curso_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=True
    )
    cadencia_segundos: Mapped[int] = mapped_column(Integer, nullable=False)
    proxima_ejecucion: Mapped[datetime] = mapped_column(_TZ, nullable=False)
    ultima_ejecucion: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class PresupuestoApi(Base, ConId):
    """Los 4 cubos de limite de tasa: PRIMARIO, CONTENIDO, GRAFO (GitHub) y CANVAS."""

    __tablename__ = "presupuesto_api"
    __table_args__ = (UniqueConstraint("ambito", "ambito_id", "cubo"),)

    ambito: Mapped[str] = mapped_column(Text, nullable=False)
    ambito_id: Mapped[str] = mapped_column(Text, nullable=False)
    cubo: Mapped[str] = mapped_column(Text, nullable=False)
    capacidad: Mapped[int] = mapped_column(Integer, nullable=False)
    restante: Mapped[int] = mapped_column(Integer, nullable=False)
    reinicio: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class CuboTasa(Base):
    """Limitador de tasa de rutas publicas. Retencion 24h/6h (purga_retencion).

    Clave natural (clave, ventana_inicio), no un `id` sustituto: no le aplica
    la convencion de UUIDv7 de ARQUITECTURA.md S8, que rige la clave primaria
    "propia" de una entidad, no la de un contador tecnico como este.
    """

    __tablename__ = "cubo_tasa"

    clave: Mapped[str] = mapped_column(Text, primary_key=True)
    ventana_inicio: Mapped[datetime] = mapped_column(_TZ, primary_key=True)
    # Columna no citada literalmente por el SPEC; es la unica forma razonable de
    # que un "limitador de tasa" limite algo. Ver docs/operacion.md al fijarla.
    contador: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Bitacora(Base, ConId):
    """Auditoria append-only de acciones con consecuencia sobre un curso (S14.8.1)."""

    __tablename__ = "bitacora"
    __table_args__ = (Index("ix_bitacora_curso_id_creado_en", "curso_id", "creado_en"),)

    curso_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=True
    )
    accion: Mapped[str] = mapped_column(Text, nullable=False)
    entidad: Mapped[str] = mapped_column(Text, nullable=False)
    entidad_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    permiso_exigido: Mapped[str | None] = mapped_column(Text, nullable=True)
    ruta: Mapped[str | None] = mapped_column(Text, nullable=True)
    metodo: Mapped[str | None] = mapped_column(Text, nullable=True)
    antes: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    despues: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class Incidencia(Base, ConId):
    """Alertas al equipo docente. Catalogo cerrado de 51 tipos (S14.8.1).

    # TODO(etapa-operacion): el CHECK sobre `tipo` con los 51 valores se añade
    # cuando se sinteticen desde los capitulos que los originan, antes del
    # 16-sep (S14.8.1). Hasta entonces `tipo` es texto libre validado en app.
    """

    __tablename__ = "incidencia"
    __table_args__ = (Index("ix_incidencia_abierta", "abierta"),)

    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    severidad: Mapped[str] = mapped_column(Text, nullable=False)
    sujeto_tipo: Mapped[str] = mapped_column(Text, nullable=False)
    # Referencia polimorfica (segun `sujeto_tipo`): sin FK fija posible.
    sujeto_id: Mapped[uuid.UUID | None] = mapped_column(_UUID, nullable=True)
    curso_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=True
    )
    # Columna de Etapa P5 (SPEC 07 S7.2.5: "con el detalle de todos los
    # huerfanos dentro"): Etapa 0 dejo el esqueleto sin `detalle` porque
    # ningun codigo escribia incidencias todavia; P5 es el primer escritor
    # real.
    detalle: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    abierta: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    resuelta_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    silenciada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    creado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class Sincronizacion(Base, ConId):
    """Rastro de cada ciclo de sincronizacion (S14.8.1)."""

    __tablename__ = "sincronizacion"
    __table_args__ = (
        CheckConstraint(f"resultado IN {_VALORES_RESULTADO_SYNC}", name="resultado_valido"),
    )

    curso_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=True
    )
    recurso: Mapped[str] = mapped_column(Text, nullable=False)
    resultado: Mapped[str] = mapped_column(Text, nullable=False)
    contadores: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    creado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class CursorSincronizacion(Base, ConId):
    """Punteros incrementales por curso/recurso (S14.8.1, SPEC 05 S5.4.2).

    `per_page_medido`, `ultimo_exito_en` y `ultimo_error` son de Etapa P5:
    Etapa 0 dejo el esqueleto sin ellos porque ningun sincronizador corria
    todavia; P5 (`sync_roster`/`sync_grupos`) es el primer escritor real y
    los necesita para el sello de antigüedad (A-231) y para no asumir nunca
    `per_page=100` (S5.4.2).
    """

    __tablename__ = "cursor_sincronizacion"
    __table_args__ = (UniqueConstraint("curso_id", "recurso", "referencia"),)

    curso_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=True
    )
    recurso: Mapped[str] = mapped_column(Text, nullable=False)
    referencia: Mapped[str] = mapped_column(Text, nullable=False)
    etag: Mapped[str | None] = mapped_column(Text, nullable=True)
    ultimo_head_sha: Mapped[str | None] = mapped_column(Text, nullable=True)
    per_page_medido: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ultimo_exito_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    ultimo_backfill_en: Mapped[datetime | None] = mapped_column(_TZ, nullable=True)
    estado: Mapped[str | None] = mapped_column(Text, nullable=True)
    ultimo_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class SaludProveedorCurso(Base, ConId):
    """Panel de operacion: salud de Canvas/GitHub por curso.

    # TODO(etapa-operacion): esquema completo cuando se implemente /operacion;
    # SPEC 14 solo la nombra como parte de "Panel de operacion, invariantes,
    # respaldo" sin detallar columnas (docs/PLAN-IMPLEMENTACION.md Etapa 0).
    """

    __tablename__ = "salud_proveedor_curso"

    curso_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID, ForeignKey("curso.id", ondelete="RESTRICT"), nullable=True
    )
    proveedor: Mapped[str] = mapped_column(Text, nullable=False)
    detalle: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    creado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class EstadoSistema(Base):
    """Cache de estado agregado del sistema para GET /estado y /operacion.

    Clave natural (`clave`), no un `id` sustituto -- es una tabla de
    configuracion tipo clave-valor, no una entidad con identidad propia.

    # TODO(etapa-operacion): ver nota de SaludProveedorCurso.
    """

    __tablename__ = "estado_sistema"

    clave: Mapped[str] = mapped_column(Text, primary_key=True)
    valor: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    actualizado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class ResultadoInvariante(Base, ConId):
    """Resultado de una comprobacion de invariante de datos.

    # TODO(etapa-operacion): ver nota de SaludProveedorCurso.
    """

    __tablename__ = "resultado_invariante"

    invariante: Mapped[str] = mapped_column(Text, nullable=False)
    cumple: Mapped[bool] = mapped_column(Boolean, nullable=False)
    detalle: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    creado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)


class Respaldo(Base, ConId):
    """Un registro por ejecucion del trabajo `respaldo_base_datos` (SPEC 14 S14.11).

    Sostiene GET /estado -> respaldo.ultimo_exito_en y respaldo.tamano_bytes
    (S14.11 CA-2).
    """

    __tablename__ = "respaldo"
    __table_args__ = (UniqueConstraint("fecha"),)

    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    exitoso: Mapped[bool] = mapped_column(Boolean, nullable=False)
    tamano_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(_TZ, nullable=False)
