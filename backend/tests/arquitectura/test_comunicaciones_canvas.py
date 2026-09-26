"""Etapa F10 (S11.7, S11.8): reglas de escritura en Canvas que fallan la
construccion si se rompen."""

from __future__ import annotations

import re
from pathlib import Path

from app.infraestructura.scopes_canvas import LECTURAS

_APP = Path(__file__).resolve().parents[2] / "app"


def _codigo() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in _APP.rglob("*.py"))


def test_ningun_anuncio_se_crea_como_borrador():
    # CA-11.8-01: nunca `published=false` para simular un borrador.
    assert not re.search(r"[\"']published[\"']\s*:\s*False", _codigo())


def test_ninguna_conversacion_es_grupal_ni_masiva():
    # CA-11.7-01
    codigo = _codigo()
    assert not re.search(r"[\"']group_conversation[\"']\s*:\s*True", codigo)
    assert not re.search(r"[\"']bulk_message[\"']\s*:", codigo)


def test_la_aplicacion_nunca_lee_conversaciones():
    # S11.7.7: las respuestas de los estudiantes llegan al titular en Canvas.
    assert not [e for e in LECTURAS if "conversations" in e.plantilla]
