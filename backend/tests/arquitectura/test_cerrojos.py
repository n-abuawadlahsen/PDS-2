"""SPEC 14 S14.7.3: unico punto de toma de pg_advisory_lock es infraestructura/cerrojos.py."""

from __future__ import annotations

from pathlib import Path

_RAIZ_APP = Path(__file__).resolve().parents[2] / "app"
_ARCHIVO_PERMITIDO = _RAIZ_APP / "infraestructura" / "cerrojos.py"


def test_pg_advisory_lock_solo_se_llama_desde_cerrojos():
    """Busca la invocacion SQL real (`SELECT pg_advisory...`), no menciones en
    docstrings/comentarios que citen `cerrojos.py` en prosa."""
    ofensores = []
    for archivo in _RAIZ_APP.rglob("*.py"):
        if archivo == _ARCHIVO_PERMITIDO:
            continue
        contenido = archivo.read_text(encoding="utf-8")
        if "SELECT pg_advisory_lock" in contenido or "SELECT pg_advisory_xact_lock" in contenido:
            ofensores.append(str(archivo))
    assert not ofensores, f"toma de pg_advisory_lock fuera de cerrojos.py: {ofensores}"
