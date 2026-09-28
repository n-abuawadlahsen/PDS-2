"""Contraste con Canvas y reglas de publicacion (SPEC 12 S12.10, S12.14;
A-139..A-143, A-206; Etapas F11-F12).

`contraste_canvas` es una funcion pura y nunca se persiste: guardar su
resultado seria tener dos verdades del mismo hecho (A-206).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

TOLERANCIA = 0.001


def _num(valor: Any) -> float | None:
    return None if valor is None else float(valor)


def contraste_canvas(publicaciones: list[Any], filas_canvas: list[Any]) -> str:
    """Por integrante congelado: NO_COMPROBADO (el espejo nunca se leyo),
    CONCUERDA, DIVERGE (otra nota o calificado despues de lo publicado) o
    SOLO_EN_CANVAS (hay nota en Canvas sin publicacion propia que la
    explique). En un grupo, basta un integrante para marcar la diferencia."""
    if not filas_canvas or all(f is None for f in filas_canvas):
        return "NO_COMPROBADO"
    resultado = "CONCUERDA"
    for publicacion, fila in zip(publicaciones, filas_canvas, strict=False):
        if fila is None:
            continue
        con_nota = fila.graded_at is not None and fila.score is not None
        if publicacion is None:
            if con_nota:
                resultado = "SOLO_EN_CANVAS" if resultado == "CONCUERDA" else resultado
            continue
        propio = _num(publicacion.score_devuelto)
        canvas = _num(fila.score)
        if (
            canvas is None
            or propio is None
            or abs(canvas - propio) > TOLERANCIA
            or (fila.graded_at is not None and fila.graded_at > publicacion.intentada_en)
        ):
            return "DIVERGE"
    if resultado == "CONCUERDA" and all(p is None for p in publicaciones):
        return (
            "SOLO_EN_CANVAS"
            if any(
                f is not None and f.graded_at is not None and f.score is not None
                for f in filas_canvas
            )
            else "CONCUERDA"
        )
    return resultado


@dataclass(frozen=True)
class Conflicto:
    estudiante: str
    nota_canvas: float | None
    calificada_en: datetime | None
    nota_propia: float | None


def hay_conflicto(publicacion: Any, fila: Any) -> bool:
    """S12.14.2: Canvas tiene nota y (no hay publicacion propia, o la de
    Canvas es posterior, o difiere en mas de la tolerancia). La relectura de
    la propia publicacion nunca cuenta como conflicto (CA-12.14-05)."""
    if fila is None or fila.graded_at is None or fila.score is None:
        return False
    if publicacion is None:
        return True
    if fila.graded_at > publicacion.intentada_en:
        return True
    propio = _num(publicacion.score_devuelto)
    return propio is None or abs(float(fila.score) - propio) > TOLERANCIA


def resultado_verificacion(
    *,
    enviado: float | None,
    devuelto_score: float | None,
    devuelto_entered: float | None,
    points_deducted: float | None,
    calificado: bool,
) -> str:
    """S12.10.5: PUBLICADA si Canvas guardo exactamente lo enviado sin
    descuentos; si no, PUBLICADA_CON_ADVERTENCIA (nunca un error silencioso)."""
    if not calificado or devuelto_score is None:
        return "PUBLICADA_CON_ADVERTENCIA"
    if points_deducted not in (None, 0, 0.0):
        return "PUBLICADA_CON_ADVERTENCIA"
    if enviado is not None and abs(float(devuelto_score) - enviado) > TOLERANCIA:
        return "PUBLICADA_CON_ADVERTENCIA"
    if (
        devuelto_entered is not None
        and abs(float(devuelto_entered) - float(devuelto_score)) > TOLERANCIA
    ):
        return "PUBLICADA_CON_ADVERTENCIA"
    return "PUBLICADA"


def pie_comentario(
    *,
    texto: str,
    entrega: str,
    cierre: str,
    sha: str | None,
    repositorio_full_name: str | None,
    corrector: str,
    rol: str,
) -> str:
    """S12.10.2: el pie va siempre, en texto plano."""
    if sha and repositorio_full_name:
        version = (
            f"Versión revisada: {sha[:7]} · https://github.com/{repositorio_full_name}/tree/{sha}"
        )
    else:
        version = (
            "Versión revisada: no se registró ninguna confirmación anterior a la fecha de cierre"
        )
    return (
        f"{texto.strip()}\n\n—\nEntrega: {entrega} (cierre {cierre})\n{version}\n"
        f"Corregido por {corrector} ({rol}). Publicado por el sistema de gestión del curso."
    )
