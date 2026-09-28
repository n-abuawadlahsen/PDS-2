"""Metricas de seguimiento, predicados de actividad y estado agregado de una
entrega (SPEC 10 S10.4-S10.8; A-118 a A-124, A-171, A-205, A-220 a A-223;
Etapa F6).

«Una sola definicion por numero» (P2): el tablero, la comparacion, el
timeline y el informe diario usan estas funciones y ninguna copia.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Protocol
from zoneinfo import ZoneInfo

from app.dominio.estados import MotivoExclusionCommit


class _ConMotivo(Protocol):
    motivo_exclusion: str


# --- S10.5.1: el commit contable ---


def es_commit_contable(commit: _ConMotivo) -> bool:
    """Un solo argumento y tres exclusiones cerradas (merge, commit inicial,
    huerfano). Bots y docentes SI son contables: no se miran aqui."""
    return commit.motivo_exclusion == MotivoExclusionCommit.NINGUNO.value


# --- S10.5.4: el dia del curso ---


def dia_del_curso(instante: datetime, zona_horaria: str) -> date:
    """`(fecha_committer AT TIME ZONE curso.zona_horaria)::date`. Un dia tiene
    zona; un intervalo no (los umbrales se evaluan como diferencias)."""
    return instante.astimezone(ZoneInfo(zona_horaria)).date()


# --- S10.6.2-S10.6.3: la ventana de una entrega, por sujeto ---


@dataclass(frozen=True)
class Ventana:
    """`(inicio, fin]`: abierta por la izquierda, cerrada por la derecha."""

    inicio: datetime
    fin: datetime


def ventana_entrega(
    *,
    due_anterior: datetime | None,
    repositorio_creado_en: datetime,
    due_actual: datetime | None,
    ahora: datetime,
    activa_desde: datetime | None = None,
    activa_hasta: datetime | None = None,
) -> Ventana | None:
    """Inicio: el cierre de la entrega anterior para el sujeto o la creacion
    del repositorio, lo mas tardio, recortado a la pertenencia del integrante.
    Sin fecha de cierre, la ventana queda abierta hasta ahora (S10.6.7).
    `None` si el recorte deja la ventana vacia."""
    inicio = max(t for t in (due_anterior, repositorio_creado_en, activa_desde) if t is not None)
    fin = due_actual if due_actual is not None else ahora
    if activa_hasta is not None:
        fin = min(fin, activa_hasta)
    if fin <= inicio:
        return None
    return Ventana(inicio=inicio, fin=fin)


def en_ventana(instante: datetime, ventana: Ventana) -> bool:
    return ventana.inicio < instante <= ventana.fin


# --- S10.5.3: umbral, actividad y causas de «sin participacion» ---

UMBRAL_VENTANA_CRITICA = 2
_VENTANA_CRITICA = timedelta(hours=72)


def umbral_aplicable(umbral_curso: int, *, proximo_cierre: datetime | None, ahora: datetime) -> int:
    """Baja a 2 dias cuando una entrega de ese repositorio vence en menos de
    72 horas: un valor derivado, no una segunda columna."""
    if proximo_cierre is not None and ahora <= proximo_cierre <= ahora + _VENTANA_CRITICA:
        return min(umbral_curso, UMBRAL_VENTANA_CRITICA)
    return umbral_curso


@dataclass(frozen=True)
class ResultadoActividad:
    estado: str  # SIN_DATO_SUFICIENTE | SIN_ACTIVIDAD | CON_ACTIVIDAD
    dias_observados: int
    umbral_dias: int


def evaluar_actividad(
    *,
    observado_desde: datetime,
    ultimo_commit_estudiantil: datetime | None,
    umbral_dias: int,
    ahora: datetime,
) -> ResultadoActividad:
    """R2.5.3 sobre la actividad de los estudiantes, nunca sobre el recuento
    crudo. Un indicador no se pronuncia sobre una ventana observada mas corta
    que su propio umbral (CA-10.5-03)."""
    observados = max(0, (ahora - observado_desde).days)
    if ahora - observado_desde < timedelta(days=umbral_dias):
        return ResultadoActividad("SIN_DATO_SUFICIENTE", observados, umbral_dias)
    limite = ahora - timedelta(days=umbral_dias)
    if ultimo_commit_estudiantil is None or ultimo_commit_estudiantil < limite:
        return ResultadoActividad("SIN_ACTIVIDAD", observados, umbral_dias)
    return ResultadoActividad("CON_ACTIVIDAD", observados, umbral_dias)


_ACCESO_ACEPTADO = frozenset({"ACEPTADO", "ACCESO_DIRECTO"})


def causa_sin_participacion(
    *, acceso: str | None, commits: int, hay_sin_atribuir: bool
) -> str | None:
    """Tres causas excluyentes, en este orden; cada una con su accion docente.
    Mientras haya commits sin atribuir, nadie queda con la mas grave (P4)."""
    if commits > 0:
        return None
    if acceso not in _ACCESO_ACEPTADO:
        return "SIN_ACCESO"
    if hay_sin_atribuir:
        return "SIN_ATRIBUIR"
    return "SIN_COMMITS"


# --- S10.6.1: el estado agregado de una entrega ---


class EstadoEntregaAgregado(StrEnum):
    EXCLUIDA = "EXCLUIDA"
    ELIMINADA_EN_CANVAS = "ELIMINADA_EN_CANVAS"
    NO_PUBLICADA = "NO_PUBLICADA"
    VINCULADA_TRAS_EL_CIERRE = "VINCULADA_TRAS_EL_CIERRE"
    SIN_FECHA = "SIN_FECHA"
    ABIERTA = "ABIERTA"
    EN_CIERRE = "EN_CIERRE"
    CERRADA_CAPTURANDO = "CERRADA_CAPTURANDO"
    CERRADA_REGISTRADA = "CERRADA_REGISTRADA"


@dataclass(frozen=True)
class SujetoEntrega:
    due_at: datetime | None
    estado_version: str | None


def estado_entrega(
    *, estado_validacion: str, publicada: bool, sujetos: list[SujetoEntrega], ahora: datetime
) -> EstadoEntregaAgregado:
    """Nueve valores, derivados y no persistidos; el primero que se cumple."""
    if estado_validacion == "EXCLUIDA":
        return EstadoEntregaAgregado.EXCLUIDA
    if estado_validacion == "ELIMINADA_EN_CANVAS":
        return EstadoEntregaAgregado.ELIMINADA_EN_CANVAS
    if not publicada:
        return EstadoEntregaAgregado.NO_PUBLICADA
    if estado_validacion == "VINCULADA_TRAS_EL_CIERRE":
        return EstadoEntregaAgregado.VINCULADA_TRAS_EL_CIERRE
    con_fecha = [s for s in sujetos if s.due_at is not None]
    if not con_fecha:
        return EstadoEntregaAgregado.SIN_FECHA
    vencidos = [s for s in con_fecha if s.due_at <= ahora]  # type: ignore[operator]
    if not vencidos:
        return EstadoEntregaAgregado.ABIERTA
    if len(vencidos) < len(con_fecha):
        return EstadoEntregaAgregado.EN_CIERRE
    if any(s.estado_version is None for s in vencidos):
        return EstadoEntregaAgregado.CERRADA_CAPTURANDO
    return EstadoEntregaAgregado.CERRADA_REGISTRADA


# --- S10.8.2: indice de desequilibrio ---

MUESTRA_MINIMA_REPARTO = 10


def indice_desequilibrio(commits_por_integrante: list[int]) -> int | None:
    """Commits contables del que mas aporta sobre los atribuidos del grupo, en
    porcentaje entero. `None` = «no calculable» (nunca 0 % ni 100 %)."""
    total = sum(commits_por_integrante)
    if total == 0:
        return None
    return round(100 * max(commits_por_integrante) / total)


def senal_reparto_concentrado(
    commits_por_integrante: list[int], *, con_acceso: int, umbral_pct: int
) -> bool:
    """Senal, no veredicto: dos integrantes con acceso, muestra minima de 10 y
    el indice sobre el umbral; o uno en cero y otro con tres o mas."""
    if con_acceso < 2 or len(commits_por_integrante) < 2:
        return False
    if min(commits_por_integrante) == 0 and max(commits_por_integrante) >= 3:
        return True
    indice = indice_desequilibrio(commits_por_integrante)
    return (
        sum(commits_por_integrante) >= MUESTRA_MINIMA_REPARTO
        and indice is not None
        and indice > umbral_pct
    )


# --- S10.8.3-S10.8.4: posicion frente al curso y metricas adicionales ---


def cuartiles(valores: list[float]) -> tuple[float, float, float] | None:
    if not valores:
        return None
    if len(valores) == 1:
        v = float(valores[0])
        return v, v, v
    q1, q2, q3 = statistics.quantiles(sorted(valores), n=4, method="inclusive")
    return float(q1), float(q2), float(q3)


def racha_sin_actividad(ultimo_dia_con_commit: date | None, hoy: date) -> int | None:
    """Metrica 3: dias del curso completos desde el ultimo commit contable.
    `None` = «sin actividad desde su creacion»."""
    if ultimo_dia_con_commit is None:
        return None
    return (hoy - ultimo_dia_con_commit).days


def progreso_frente_al_cierre(
    sujetos: list[tuple[datetime, datetime | None]], *, ahora: datetime
) -> int | None:
    """Metrica 4: porcentaje de sujetos con al menos un commit contable en las
    48 horas previas a **su propia** fecha de cierre. Cada tupla es
    `(cierre, ultimo commit contable anterior o igual al cierre)`."""
    if not sujetos:
        return None
    con = sum(
        1
        for cierre, ultimo in sujetos
        if ultimo is not None and cierre - timedelta(hours=48) <= ultimo <= cierre
    )
    return round(100 * con / len(sujetos))
