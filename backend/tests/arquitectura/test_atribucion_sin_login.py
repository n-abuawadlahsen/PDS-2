"""SPEC 10 S10.3.1 regla 2 (CA-10.3-09): la atribucion nunca compara por
`login` de GitHub, siempre por `github_user_id` numerico."""

from __future__ import annotations

import re
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2] / "app"
_MODULOS = [
    _RAIZ / "dominio" / "actividad.py",
    _RAIZ / "adaptadores" / "actividad_repo.py",
]
_PATRONES = [
    re.compile(r"\.login\s*=="),
    re.compile(r"==\s*\w*\.login\b"),
    re.compile(r"login\)\s*=="),
]


def test_la_ingesta_no_une_por_login():
    ofensores = [
        f"{m.name}: {linea.strip()}"
        for m in _MODULOS
        for linea in m.read_text(encoding="utf-8").splitlines()
        if any(p.search(linea) for p in _PATRONES)
    ]
    assert not ofensores, f"comparacion por login en la ingesta: {ofensores}"
