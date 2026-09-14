"""Catalogo cerrado de 21 codigos del checklist de vinculacion (SPEC 04 S4.7.2-S4.7.3,
CA-4.7-06: "el catalogo de dominio/verificacion.py tiene exactamente 21 entradas").

Solo el catalogo y las reglas de calificacion son puras; las llamadas HTTP que
alimentan cada item viven en los adaptadores de Canvas/GitHub.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.dominio.estados import CarrilVerificacion, ResultadoVerificacion


class Severidad(StrEnum):
    """Techo de severidad de cada item cuando falla (S4.7.2 columna 4)."""

    BLOQUEANTE = "BLOQUEANTE"
    ADVERTENCIA_FUERTE = "ADVERTENCIA_FUERTE"
    ADVERTENCIA = "ADVERTENCIA"
    INFORMATIVO = "INFORMATIVO"


@dataclass(frozen=True)
class ItemChecklist:
    id: str
    nombre: str
    carril: CarrilVerificacion
    severidad: Severidad


CATALOGO_VERIFICACION: tuple[ItemChecklist, ...] = (
    ItemChecklist(
        "1", "El token es valido y es tuyo", CarrilVerificacion.CANVAS, Severidad.BLOQUEANTE
    ),
    ItemChecklist(
        "2",
        "El curso existe, es visible y esta publicado",
        CarrilVerificacion.CANVAS,
        Severidad.BLOQUEANTE,
    ),
    ItemChecklist(
        "3",
        "Eres profesor del curso y no estas limitado a una seccion",
        CarrilVerificacion.CANVAS,
        Severidad.BLOQUEANTE,
    ),
    ItemChecklist(
        "4", "Puedes editar notas", CarrilVerificacion.CANVAS, Severidad.ADVERTENCIA_FUERTE
    ),
    ItemChecklist(
        "5", "Puedes publicar anuncios", CarrilVerificacion.CANVAS, Severidad.ADVERTENCIA
    ),
    ItemChecklist(
        "6", "Puedes enviar mensajes", CarrilVerificacion.CANVAS, Severidad.ADVERTENCIA_FUERTE
    ),
    ItemChecklist(
        "7", "Puedes ver correos de estudiantes", CarrilVerificacion.CANVAS, Severidad.INFORMATIVO
    ),
    ItemChecklist(
        "8",
        "Secciones legibles y deteccion de cross-listing",
        CarrilVerificacion.CANVAS,
        Severidad.ADVERTENCIA,
    ),
    ItemChecklist(
        "9", "Conjuntos de grupos colaborativos", CarrilVerificacion.CANVAS, Severidad.INFORMATIVO
    ),
    ItemChecklist(
        "10",
        "Politica de entrega tardia del curso",
        CarrilVerificacion.CANVAS,
        Severidad.ADVERTENCIA_FUERTE,
    ),
    ItemChecklist(
        "11", "Periodos de calificacion abiertos", CarrilVerificacion.CANVAS, Severidad.ADVERTENCIA
    ),
    ItemChecklist(
        "12",
        "Tamano real de pagina que acepta la instancia",
        CarrilVerificacion.CANVAS,
        Severidad.INFORMATIVO,
    ),
    ItemChecklist("13", "Zona horaria del curso", CarrilVerificacion.CANVAS, Severidad.INFORMATIVO),
    ItemChecklist(
        "14",
        "La App esta instalada, con permisos congelados y la organizacion presentable",
        CarrilVerificacion.GITHUB,
        Severidad.BLOQUEANTE,
    ),
    ItemChecklist("15", "Estudiantes legibles", CarrilVerificacion.CANVAS, Severidad.ADVERTENCIA),
    ItemChecklist(
        "16",
        "Puedes crear y editar tareas en Canvas",
        CarrilVerificacion.CANVAS,
        Severidad.BLOQUEANTE,
    ),
    ItemChecklist(
        "17",
        "Puedes escribir comentarios en las entregas",
        CarrilVerificacion.CANVAS,
        Severidad.ADVERTENCIA_FUERTE,
    ),
    ItemChecklist(
        "18",
        "Cada docente del curso tiene membresia activa en la organizacion",
        CarrilVerificacion.GITHUB,
        Severidad.ADVERTENCIA,
    ),
    ItemChecklist(
        "19", "Puedes borrar anuncios propios", CarrilVerificacion.CANVAS, Severidad.INFORMATIVO
    ),
    ItemChecklist(
        "5-bis",
        "Prueba de escritura: anuncio de seccion",
        CarrilVerificacion.CANVAS,
        Severidad.INFORMATIVO,
    ),
    ItemChecklist(
        "17-bis",
        "Prueba de escritura: comentario en una entrega",
        CarrilVerificacion.CANVAS,
        Severidad.INFORMATIVO,
    ),
)

assert (
    len(CATALOGO_VERIFICACION) == 21
), "el catalogo debe tener exactamente 21 entradas (CA-4.7-06)"

# Orden fijo del carril Canvas, bloqueantes primero (S4.7.1).
ORDEN_CARRIL_CANVAS: tuple[str, ...] = (
    "1",
    "2",
    "3",
    "16",
    "4",
    "5",
    "6",
    "17",
    "7",
    "19",
    "11",
    "10",
    "8",
    "9",
    "13",
    "12",
    "15",
)
# Los dos items del carril GitHub, en paralelo entre si (no tienen orden fijo).
ITEMS_CARRIL_GITHUB: tuple[str, ...] = ("14", "18")

assert set(ORDEN_CARRIL_CANVAS) | set(ITEMS_CARRIL_GITHUB) == {
    i.id for i in CATALOGO_VERIFICACION if i.id not in ("5-bis", "17-bis")
}


def resultado_binario(*, aprobado: bool, severidad: Severidad) -> ResultadoVerificacion:
    """Item de si/no cuyo techo de severidad es el declarado en el catalogo."""
    if aprobado:
        return ResultadoVerificacion.CORRECTO
    if severidad == Severidad.BLOQUEANTE:
        return ResultadoVerificacion.BLOQUEANTE
    if severidad in (Severidad.ADVERTENCIA_FUERTE, Severidad.ADVERTENCIA):
        return ResultadoVerificacion.ADVERTENCIA
    return ResultadoVerificacion.CORRECTO


def resultado_item_17(*, aprobado: bool, item_6_fallo: bool) -> ResultadoVerificacion:
    """S4.7.2 fila 17: "bloqueante si el item 6 salio rojo"."""
    if aprobado:
        return ResultadoVerificacion.CORRECTO
    if item_6_fallo:
        return ResultadoVerificacion.BLOQUEANTE
    return ResultadoVerificacion.ADVERTENCIA


class MotivoNoVerificado(StrEnum):
    DEPENDE_DE_ITEM_1 = "DEPENDE_DE_ITEM_1"
    DEPENDE_DE_ITEM_2 = "DEPENDE_DE_ITEM_2"
    TIEMPO_AGOTADO = "TIEMPO_AGOTADO"
    CASILLA_NO_MARCADA = "CASILLA_NO_MARCADA"


def curso_puede_pasar_a_activo(resultados: dict[str, ResultadoVerificacion]) -> bool:
    """S4.3.2, S4.7 regla 5: ACTIVO solo con cero items BLOQUEANTE en rojo."""
    return not any(r == ResultadoVerificacion.BLOQUEANTE for r in resultados.values())
