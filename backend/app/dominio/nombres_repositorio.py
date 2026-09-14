"""Convencion de nombres de repositorios y slugs (SPEC 08 S8.4; A-107, A-108,
A-069, A-172).

Una sola funcion de dominio para todo nombre: la vista previa de la pantalla de
tareas, el repositorio base (Etapa P7) y los repositorios de sujeto (Etapa P8)
llaman a `nombre_repositorio`, nunca a una copia.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

LONGITUD_COMPONENTE = 24
LONGITUD_MAXIMA_NOMBRE = 90
TOPIC_APLICACION = "gestor-tareas"

_PATRON_SLUG = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")


def normalizar(texto: str) -> str:
    """A-108, los siete pasos en orden, aplicados por componente."""
    # 1. NFKD y descarte de marcas diacriticas (ñ -> n, tildes fuera).
    descompuesto = unicodedata.normalize("NFKD", texto)
    sin_marcas = "".join(c for c in descompuesto if not unicodedata.combining(c))
    # 2. Minusculas.
    minusculas = sin_marcas.lower()
    # 3. Todo lo que no sea [a-z0-9] pasa a guion.
    guiones = re.sub(r"[^a-z0-9]", "-", minusculas)
    # 4. Colapsar guiones consecutivos.
    colapsado = re.sub(r"-{2,}", "-", guiones)
    # 5. Recortar guiones de los extremos.
    recortado = colapsado.strip("-")
    # 6. Truncar a 24 caracteres.
    truncado = recortado[:LONGITUD_COMPONENTE]
    # 7. Volver a recortar: el truncado pudo caer justo sobre un guion.
    return truncado.strip("-")


def es_slug_valido(slug: str) -> bool:
    """Forma de `curso.slug` y `tarea.slug` (S8.4.2): <= 24, sin guion en los extremos."""
    return len(slug) <= LONGITUD_COMPONENTE and bool(_PATRON_SLUG.match(slug))


@dataclass(frozen=True)
class SujetoNombre:
    """`e<canvas_user_id>-<apellido-nombre>` o `g<canvas_group_id>-<slug-grupo>`."""

    tipo: Literal["e", "g"]
    canvas_id: int
    texto_legible: str


def _ensamblar(componentes: list[str]) -> str:
    # Paso 10: unir con guion y recortar los extremos del nombre completo.
    return "-".join(c for c in componentes if c).strip("-")


def nombre_repositorio(
    *, curso_slug: str, tarea_slug: str, sujeto: SujetoNombre | Literal["base"]
) -> str:
    """A-107/A-108 pasos 8-11. Los identificadores numericos nunca se truncan
    ni se normalizan; la parte legible vacia se omite con su guion; nunca se
    añade un sufijo."""
    if sujeto == "base":
        return _ensamblar([curso_slug, tarea_slug, "base"])

    identificador = f"{sujeto.tipo}{sujeto.canvas_id}"
    legible = normalizar(sujeto.texto_legible)
    nombre = _ensamblar([curso_slug, tarea_slug, identificador, legible])
    # Paso 11: si aun asi supera la cota, se recorta la parte legible hasta
    # que quepa; si no cabe, se omite entera (paso 9).
    while len(nombre) > LONGITUD_MAXIMA_NOMBRE and legible:
        legible = legible[:-1].strip("-")
        nombre = _ensamblar([curso_slug, tarea_slug, identificador, legible])
    return nombre


def marcador_descripcion(*, curso_slug: str, tarea_slug: str, sujeto: str) -> str:
    """A-069: sufijo estructurado que hace segura la adopcion de A-097
    (`sujeto` es `base`, `e5310` o `g8842`)."""
    return f"[gestor:{curso_slug}/{tarea_slug}/{sujeto}]"


def topics_repositorio(*, curso_slug: str, tarea_slug: str) -> list[str]:
    """A-069: exactamente tres topics."""
    return [TOPIC_APLICACION, f"curso-{curso_slug}", f"tarea-{tarea_slug}"]


def slug_entrega(*, nombre: str, orden: int, slugs_ocupados: set[str]) -> str:
    """A-172: del nombre con `normalizar`; vacio -> `e<orden>`; colision dentro
    de la misma tarea -> `-<orden>` una sola vez, y si aun colisiona, `e<orden>`."""
    base = normalizar(nombre) or f"e{orden}"
    if base not in slugs_ocupados:
        return base
    sufijo = f"-{orden}"
    # Se recorta la base antes de anexar, para que el tope de 24 no se coma el sufijo.
    con_orden = base[: LONGITUD_COMPONENTE - len(sufijo)].strip("-") + sufijo
    if con_orden not in slugs_ocupados:
        return con_orden
    return f"e{orden}"
