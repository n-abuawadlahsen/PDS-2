"""Reglas puras del espejo de Canvas (SPEC 07 S7.2-S7.3, S7.9).

Recibe datos ya obtenidos (DTOs, recuentos), decide. La llamada HTTP y las
escrituras viven en `app/adaptadores/padron_repo.py`.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from app.dominio.estados import EstadoEstudiante

# S7.3.2/S7.9.1: una seccion o un estudiante ausente durante dos ciclos
# consecutivos pasa a ELIMINADA/RETIRADO; un solo ciclo de ausencia no basta
# (Canvas puede fallar transitoriamente una llamada).
CICLOS_PARA_CONFIRMAR_AUSENCIA = 2

# S7.3.8/S7.9.10 (A-045): un recuento que cae a menos de este umbral respecto
# del ciclo anterior no aplica ninguna baja.
UMBRAL_ROSTER_SOSPECHOSO = 0.6

# S7.9.10: mas de este porcentaje de los activos cambiando de estado a la vez
# exige confirmacion explicita en vez de aplicarse solo.
UMBRAL_CAMBIO_MASIVO = 0.3

_ORDEN_ESTADO_POR_PRECEDENCIA = (
    EstadoEstudiante.ACTIVO,
    EstadoEstudiante.INVITADO,
    EstadoEstudiante.INACTIVO,
    EstadoEstudiante.CONCLUIDO,
)

# S7.2.1: el `workflow_state` que Canvas devuelve por matricula, mapeado al
# estado propio y cerrado de `estudiante` (A-044). No hay tabla explicita en
# el SPEC para esta correspondencia exacta -- se infiere de los cuatro
# nombres que S7.2.1 usa para `estudiante.estado` y del vocabulario que la
# API de Canvas documenta para `enrollment.workflow_state`; decision
# documentada, no una regla citada literalmente.
_MAPA_WORKFLOW_A_ESTADO: dict[str, EstadoEstudiante] = {
    "active": EstadoEstudiante.ACTIVO,
    "invited": EstadoEstudiante.INVITADO,
    "creation_pending": EstadoEstudiante.INVITADO,
    "inactive": EstadoEstudiante.INACTIVO,
    "completed": EstadoEstudiante.CONCLUIDO,
}


def slug_desde_nombre(nombre: str, *, canvas_group_id: int) -> str:
    """`grupo.slug` no viene de Canvas (su API no expone uno, S7.2.1 nota).
    Se deriva del nombre para uso propio; el `canvas_group_id` como sufijo
    evita colisiones entre dos grupos con el mismo nombre visible."""
    normalizado = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^a-z0-9]+", "-", normalizado.lower()).strip("-") or "grupo"
    return f"{base}-{canvas_group_id}"


def estado_estudiante_desde_matriculas(workflow_states: list[str]) -> EstadoEstudiante:
    """S7.2.1: `estudiante.estado` se deriva del conjunto de matriculas
    relevantes (A-044), con ACTIVO ganando sobre cualquier otro estado
    presente, y CONCLUIDO como ultimo recurso antes de no reconocer nada."""
    estados_presentes = {
        _MAPA_WORKFLOW_A_ESTADO[w] for w in workflow_states if w in _MAPA_WORKFLOW_A_ESTADO
    }
    for candidato in _ORDEN_ESTADO_POR_PRECEDENCIA:
        if candidato in estados_presentes:
            return candidato
    return EstadoEstudiante.INACTIVO


def confirma_ausencia(ciclos_ausente: int) -> bool:
    """S7.3.2 (secciones), S7.9.1 (estudiantes): dos ciclos consecutivos."""
    return ciclos_ausente >= CICLOS_PARA_CONFIRMAR_AUSENCIA


def roster_sospechoso(*, cantidad_anterior: int, cantidad_actual: int) -> bool:
    """S7.3.8/S7.9.10 (A-045): cae a 0, o a menos del 60% del ciclo anterior."""
    if cantidad_anterior == 0:
        return False
    if cantidad_actual == 0:
        return True
    return cantidad_actual < cantidad_anterior * UMBRAL_ROSTER_SOSPECHOSO


def cambio_masivo_de_estado(*, activos_anterior: int, cantidad_cambiados: int) -> bool:
    """S7.9.10: mas del 30% de los activos cambia de estado en un solo ciclo."""
    if activos_anterior == 0:
        return False
    return cantidad_cambiados > activos_anterior * UMBRAL_CAMBIO_MASIVO


@dataclass(frozen=True)
class ResultadoDeteccionGrupo:
    es_traslado: bool
    conjunto_ambiguo: bool  # True = doble pertenencia al mismo conjunto (S7.3.6)


def detectar_traslado_o_doble_pertenencia(
    *, grupos_aceptados_anteriores: frozenset[Any], grupos_aceptados_actuales: frozenset[Any]
) -> ResultadoDeteccionGrupo:
    """S7.3.6 (doble pertenencia, BLOQUEANTE), S7.3.7 (traslado). Los
    conjuntos son ids de `grupo` (no de `conjunto_grupos`): el llamador ya
    filtro por estudiante y por conjunto de grupos antes de invocar esto.

    - Mas de un grupo aceptado a la vez (antes o ahora) en el mismo conjunto
      es doble pertenencia: nunca es un traslado limpio.
    - Exactamente un grupo antes y exactamente otro distinto ahora es un
      traslado.
    """
    if len(grupos_aceptados_actuales) > 1 or len(grupos_aceptados_anteriores) > 1:
        return ResultadoDeteccionGrupo(es_traslado=False, conjunto_ambiguo=True)
    if (
        len(grupos_aceptados_anteriores) == 1
        and len(grupos_aceptados_actuales) == 1
        and grupos_aceptados_anteriores != grupos_aceptados_actuales
    ):
        return ResultadoDeteccionGrupo(es_traslado=True, conjunto_ambiguo=False)
    return ResultadoDeteccionGrupo(es_traslado=False, conjunto_ambiguo=False)
