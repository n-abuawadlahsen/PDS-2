"""Etapa F12 (S12.4.5, A-206): reglas que fallan la construccion si se rompen."""

from __future__ import annotations

from pathlib import Path

_APP = Path(__file__).resolve().parents[2] / "app"


def _codigo() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in _APP.rglob("*.py"))


def test_nunca_se_escribe_a_nombre_de_otra_persona():
    # Toda escritura usa la credencial operativa; `as_user_id` no se envia.
    assert '"as_user_id"' not in _codigo() and "'as_user_id'" not in _codigo()


def test_nunca_se_usa_el_resumen_de_entregas_de_canvas():
    # CA-12.11-02: lo que Canvas tiene sale de `estado_canvas_submission`.
    codigo = _codigo()
    assert '"submission_summary"' not in codigo and "include[]=submission_summary" not in codigo


def test_correccion_no_tiene_columnas_espejo_de_canvas():
    # CA-12.2.8-4
    from app.adaptadores.modelos_correccion import AsignacionCorreccion, Correccion

    columnas = {c.name for c in Correccion.__table__.columns}
    assert not [
        c
        for c in columnas
        if c.startswith("canvas_") or c in ("contraste_canvas", "canvas_verificado_en")
    ]
    assert "estado" not in {c.name for c in AsignacionCorreccion.__table__.columns}
