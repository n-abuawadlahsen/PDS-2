"""Correccion: estados, reparto, nota y rubrica (SPEC 12 S12.3, S12.5, S12.9,
S12.10.1; A-134..A-138, A-214; Etapa F11).

Funciones puras. Toda transicion de `correccion.estado` pasa por
`puede_transicionar`, con la tabla de transiciones legales como datos; la
unica funcion que escribe el estado (en `correccion_repo`) la consulta y deja
la bitacora en la misma transaccion.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from typing import Any

from app.dominio.estados import EstadoCorreccion as E

ETIQUETA_ESTADO = {
    E.SIN_CORRECTOR.value: "Sin corrector",
    E.ASIGNADA.value: "Asignada",
    E.EN_CURSO.value: "En curso",
    E.LISTA_PARA_PUBLICAR.value: "Lista para publicar",
    E.PUBLICANDO.value: "Publicando",
    E.PUBLICADA.value: "Publicada",
    E.PUBLICADA_CON_ADVERTENCIA.value: "Publicada con advertencia",
    E.ERROR_PUBLICACION.value: "Error al publicar",
}
ETIQUETA_MOTIVO_NO_PUBLICABLE = {
    "PERIODO_CERRADO": "el período de calificación de Canvas está cerrado",
    "NO_GRADEABLE": "Canvas no deja calificar a este estudiante en la tarea",
    "NO_GRADED": "la tarea de Canvas no lleva nota",
    "GPA_SCALE": "la escala GPA no se publica desde aquí",
    "LETTER_GRADE_SIN_ESQUEMA": "la tarea usa letras sin esquema de calificación",
    "MODERADA_O_ANONIMA": "la tarea es moderada o anónima en Canvas",
    "ENTREGA_DESPUBLICADA": "la tarea está despublicada en Canvas",
    "ENTREGA_ELIMINADA": "la tarea se eliminó en Canvas",
    "SUJETO_EXCLUIDO": "el sujeto quedó excluido de la entrega",
    "PUBLICACION_NO_AUTORIZADA": "la credencial de Canvas no permite publicar notas",
}
TERMINALES = frozenset({E.PUBLICADA.value, E.PUBLICADA_CON_ADVERTENCIA.value})

# S12.3.2: las once transiciones legales, como datos.
TRANSICIONES: dict[str, frozenset[str]] = {
    E.SIN_CORRECTOR.value: frozenset({E.ASIGNADA.value}),
    E.ASIGNADA.value: frozenset({E.EN_CURSO.value, E.SIN_CORRECTOR.value}),
    E.EN_CURSO.value: frozenset({E.LISTA_PARA_PUBLICAR.value, E.SIN_CORRECTOR.value}),
    E.LISTA_PARA_PUBLICAR.value: frozenset({E.PUBLICANDO.value, E.SIN_CORRECTOR.value}),
    E.PUBLICANDO.value: frozenset(
        {
            E.PUBLICADA.value,
            E.PUBLICADA_CON_ADVERTENCIA.value,
            E.ERROR_PUBLICACION.value,
            E.LISTA_PARA_PUBLICAR.value,
        }
    ),
    E.ERROR_PUBLICACION.value: frozenset({E.LISTA_PARA_PUBLICAR.value, E.SIN_CORRECTOR.value}),
    E.PUBLICADA.value: frozenset({E.EN_CURSO.value}),
    E.PUBLICADA_CON_ADVERTENCIA.value: frozenset({E.EN_CURSO.value}),
}


def puede_transicionar(actual: str, nuevo: str) -> bool:
    return nuevo in TRANSICIONES.get(actual, frozenset())


# --- Nota (S12.10.1, A-141) ---


class NotaInvalida(ValueError):
    pass


_NUMERO = re.compile(r"^\d+(?:[.,]\d{1,2})?$")


def normalizar_nota(
    grading_type: str | None, valor: str | None, puntos_posibles: float | None
) -> str:
    """El `posted_grade` exacto que se enviara a Canvas; nunca redondea."""
    texto = (valor or "").strip()
    tipo = grading_type or "points"
    if tipo in ("gpa_scale", "not_graded"):
        raise NotaInvalida("esta tarea de Canvas no admite una nota publicada desde aquí")
    if not texto:
        raise NotaInvalida("falta la nota")
    if tipo == "pass_fail":
        mapa = {"pass": "pass", "fail": "fail", "complete": "pass", "incomplete": "fail"}
        if texto.lower() not in mapa:
            raise NotaInvalida("en esta tarea la nota es pass o fail")
        return mapa[texto.lower()]
    if tipo == "letter_grade":
        if len(texto) > 5:
            raise NotaInvalida("la letra es demasiado larga")
        return texto
    numero = texto.rstrip("%").strip()
    if not _NUMERO.match(numero):
        raise NotaInvalida("la nota es un número con hasta dos decimales")
    numero = numero.replace(",", ".")
    if tipo == "percent":
        if float(numero) > 100:
            raise NotaInvalida("el porcentaje no puede superar 100")
        return f"{numero}%"
    if puntos_posibles is not None and float(numero) > puntos_posibles * 2:
        raise NotaInvalida(f"la nota supera por mucho el máximo de {puntos_posibles:g} puntos")
    return numero


def motivo_no_publicable(
    *,
    grading_type: str | None,
    moderada: bool,
    anonima: bool,
    publicada: bool,
    estado_validacion: str | None,
    sujeto_activo: bool,
) -> str | None:
    """Los motivos que dependen de la tarea y del sujeto (los de Canvas en
    vivo, periodo cerrado y no calificable, los fija la reconciliacion)."""
    if estado_validacion == "ELIMINADA_EN_CANVAS":
        return "ENTREGA_ELIMINADA"
    if not sujeto_activo:
        return "SUJETO_EXCLUIDO"
    if grading_type == "not_graded":
        return "NO_GRADED"
    if grading_type == "gpa_scale":
        return "GPA_SCALE"
    if moderada or anonima:
        return "MODERADA_O_ANONIMA"
    if not publicada:
        return "ENTREGA_DESPUBLICADA"
    return None


# --- Reparto (S12.5.3) ---


@dataclass(frozen=True)
class Corrector:
    membresia_id: uuid.UUID
    nombre: str
    peso: int


@dataclass(frozen=True)
class SujetoReparto:
    sujeto_id: uuid.UUID
    nombre_ordenable: str
    seccion_ids: tuple[uuid.UUID, ...]
    actual: uuid.UUID | None
    empezada: bool
    calificable: bool = True


def _objetivos(sujetos: list[SujetoReparto], *, reasignar: bool) -> list[SujetoReparto]:
    """Por defecto solo se llenan las filas sin corrector."""
    return sorted(
        (s for s in sujetos if s.actual is None or reasignar),
        key=lambda s: (s.nombre_ordenable.lower(), str(s.sujeto_id)),
    )


def reparto_equitativo(
    sujetos: list[SujetoReparto],
    correctores: list[Corrector],
    *,
    reasignar: bool = False,
    incluir_no_calificables: bool = False,
) -> dict[uuid.UUID, uuid.UUID]:
    """Equilibra pares (entrega, sujeto) normalizados por peso: cada sujeto,
    en orden de nombre, va a quien tenga menos asignados/peso; empate por
    peso mayor y luego por nombre. Mismo conjunto, mismo resultado."""
    elegibles = sorted(
        (c for c in correctores if c.peso > 0),
        key=lambda c: (c.nombre.lower(), str(c.membresia_id)),
    )
    if not elegibles:
        return {}
    objetivos = [
        s
        for s in _objetivos(sujetos, reasignar=reasignar)
        if s.calificable or incluir_no_calificables
    ]
    ids_objetivo = {s.sujeto_id for s in objetivos}
    carga = {c.membresia_id: 0 for c in elegibles}
    for s in sujetos:
        if s.sujeto_id not in ids_objetivo and s.actual in carga:
            carga[s.actual] += 1
    resultado: dict[uuid.UUID, uuid.UUID] = {}
    for s in objetivos:
        elegido = min(
            elegibles, key=lambda c: (carga[c.membresia_id] / c.peso, -c.peso, c.nombre.lower())
        )
        resultado[s.sujeto_id] = elegido.membresia_id
        carga[elegido.membresia_id] += 1
    return resultado


def reparto_por_seccion(
    sujetos: list[SujetoReparto],
    corrector_por_seccion: dict[uuid.UUID, uuid.UUID],
    *,
    reasignar: bool = False,
) -> tuple[dict[uuid.UUID, uuid.UUID], list[uuid.UUID]]:
    """Un corrector por seccion. Un sujeto con dos secciones activas no se
    asigna: «requiere decision»."""
    asignados: dict[uuid.UUID, uuid.UUID] = {}
    requiere_decision: list[uuid.UUID] = []
    for s in _objetivos(sujetos, reasignar=reasignar):
        if len(s.seccion_ids) > 1:
            requiere_decision.append(s.sujeto_id)
        elif s.seccion_ids and s.seccion_ids[0] in corrector_por_seccion:
            asignados[s.sujeto_id] = corrector_por_seccion[s.seccion_ids[0]]
    return asignados, requiere_decision


# --- Rubrica (S12.9, A-137) ---


def huella_rubrica(rubrica: list[dict[str, Any]] | None, ajustes: dict[str, Any] | None) -> bytes:
    """SHA-256 de la serializacion canonica de criterios, niveles y los tres
    ajustes de presentacion; se recalcula en cada lectura."""
    canonica = {
        "criterios": [
            {
                "id": c.get("id"),
                "points": c.get("points"),
                "ignore_for_scoring": bool(c.get("ignore_for_scoring")),
                "ratings": [(r.get("id"), r.get("points")) for r in c.get("ratings") or []],
            }
            for c in rubrica or []
        ],
        "ajustes": {
            k: (ajustes or {}).get(k)
            for k in ("free_form_criterion_comments", "hide_points", "hide_score_total")
        },
    }
    return hashlib.sha256(json.dumps(canonica, sort_keys=True).encode()).digest()


def es_solo_lectura(criterio: dict[str, Any]) -> bool:
    """Criterios de resultados de aprendizaje o por rango: se evaluan en
    SpeedGrader y nunca viajan en el payload."""
    return bool(criterio.get("learning_outcome_id") or criterio.get("criterion_use_range"))


def validar_rubrica_local(
    rubrica: list[dict[str, Any]] | None, local: dict[str, Any] | None
) -> list[str]:
    errores: list[str] = []
    por_id = {c.get("id"): c for c in rubrica or []}
    for criterio_id, valor in (local or {}).items():
        criterio = por_id.get(criterio_id)
        if criterio is None:
            errores.append(f"el criterio {criterio_id} ya no existe en la rúbrica de Canvas")
            continue
        if es_solo_lectura(criterio):
            errores.append(f"el criterio «{criterio.get('description')}» se evalúa en SpeedGrader")
            continue
        puntos = (valor or {}).get("points")
        if puntos is not None and not (0 <= float(puntos) <= float(criterio.get("points") or 0)):
            errores.append(f"los puntos de «{criterio.get('description')}» están fuera de rango")
        rating = (valor or {}).get("rating_id")
        if rating is not None and rating not in {
            r.get("id") for r in criterio.get("ratings") or []
        }:
            errores.append(f"el nivel elegido no pertenece a «{criterio.get('description')}»")
    return errores


def suma_rubrica(
    rubrica: list[dict[str, Any]] | None, local: dict[str, Any] | None
) -> float | None:
    """Suma sugerida; `None` si hay criterios de solo lectura (S12.9)."""
    if not rubrica or any(es_solo_lectura(c) for c in rubrica):
        return None
    total = 0.0
    for c in rubrica:
        if c.get("ignore_for_scoring"):
            continue
        puntos = ((local or {}).get(str(c.get("id"))) or {}).get("points")
        total += float(puntos or 0)
    return total
