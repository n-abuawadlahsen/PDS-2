"""SPEC 14 S14.1: `dominio/` no importa I/O, ORM ni framework HTTP."""

from __future__ import annotations

import ast
from pathlib import Path

_PROHIBIDOS = {"httpx", "sqlalchemy", "fastapi", "psycopg", "alembic", "requests"}
_RAIZ_DOMINIO = Path(__file__).resolve().parents[2] / "app" / "dominio"


def _modulos_importados(ruta: Path) -> set[str]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    modulos: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos.update(alias.name.split(".")[0] for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.add(nodo.module.split(".")[0])
    return modulos


def test_dominio_no_importa_infraestructura():
    violaciones = []
    for archivo in _RAIZ_DOMINIO.glob("*.py"):
        importados = _modulos_importados(archivo)
        prohibidos_encontrados = importados & _PROHIBIDOS
        if prohibidos_encontrados:
            violaciones.append((archivo.name, prohibidos_encontrados))
    assert not violaciones, f"dominio/ importa infraestructura: {violaciones}"
