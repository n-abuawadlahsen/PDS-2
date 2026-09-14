"""CA-2.9-11: nunca se borra un repositorio (ni un commit, tag o nota publicada)."""

from __future__ import annotations

from pathlib import Path

_RAIZ_ADAPTADORES = Path(__file__).resolve().parents[2] / "app" / "adaptadores"


def test_nunca_aparece_delete_repos_owner_repo():
    ofensores = []
    for archivo in _RAIZ_ADAPTADORES.rglob("*.py"):
        contenido = archivo.read_text(encoding="utf-8")
        if "DELETE /repos/{owner}/{repo}" in contenido or "DELETE /repos/{org}/{repo}" in contenido:
            ofensores.append(str(archivo))
    assert not ofensores, f"DELETE de repositorio encontrado en: {ofensores}"
