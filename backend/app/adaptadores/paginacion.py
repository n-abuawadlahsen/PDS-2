"""Paginador propio compartido por Canvas y GitHub (SPEC 05 S5.4.2).

Sigue siempre el header `Link`, nunca calcula paginas. Nunca asume que
`per_page=100` significa 100: el llamador mide `len(pagina)` en la primera
que reciba. Tope de seguridad de 50 paginas: al alcanzarlo, no falla -- el
generador simplemente termina, y `paginas_leidas`/`truncado` del ultimo
`EstadoPaginacion` le dicen al llamador si hubo que cortar.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import httpx

_TOPE_PAGINAS = 50


class BuclePaginacionDetectado(Exception):
    """La URL de `next` se repite, o una pagina vuelve vacia con `next` presente."""


@dataclass(frozen=True)
class Pagina:
    items: list[dict[str, Any]]
    numero: int
    es_ultima: bool
    truncada: bool  # True si esta es la ultima porque se alcanzo el tope de 50


def paginas(
    *, cliente_http: httpx.Client, url_inicial: str, encabezados: dict[str, str]
) -> Iterator[Pagina]:
    """Recorre todas las paginas de un listado de Canvas/GitHub via header `Link`."""
    urls_vistas: set[str] = set()
    url: str | None = url_inicial
    numero = 0

    while url:
        if url in urls_vistas:
            raise BuclePaginacionDetectado(f"la URL de next se repitio: {url}")
        urls_vistas.add(url)

        respuesta = cliente_http.get(url, headers=encabezados)
        respuesta.raise_for_status()
        items = respuesta.json()
        numero += 1

        siguiente = respuesta.links.get("next", {}).get("url")
        if not items and siguiente:
            raise BuclePaginacionDetectado("pagina vacia con next presente")

        truncada = numero >= _TOPE_PAGINAS
        yield Pagina(
            items=items, numero=numero, es_ultima=(not siguiente or truncada), truncada=truncada
        )

        if truncada:
            return
        url = siguiente
