"""SPEC 05 S5.3 CA-1: ninguna llamada real de `ClienteCanvasReal` usa un
endpoint fuera del catalogo cerrado `SCOPES_CANVAS`."""

from __future__ import annotations

import httpx
import pytest

from app.adaptadores import cliente_canvas
from app.infraestructura.scopes_canvas import SCOPES_CANVAS


class _RespuestaFalsa:
    status_code = 200

    def __init__(self, cuerpo: object) -> None:
        self._cuerpo = cuerpo

    def json(self) -> object:
        return self._cuerpo

    def raise_for_status(self) -> None:
        return None


@pytest.fixture(autouse=True)
def _limpiar_registro():
    cliente_canvas.LLAMADAS_REGISTRADAS.clear()
    yield
    cliente_canvas.LLAMADAS_REGISTRADAS.clear()


def test_todas_las_llamadas_reales_estan_en_el_catalogo(monkeypatch: pytest.MonkeyPatch):
    def _get_falso(url: str, **_kwargs: object) -> _RespuestaFalsa:
        if url.endswith("/users/self"):
            return _RespuestaFalsa({"id": 1, "name": "x"})
        if "/assignments/" in url:
            return _RespuestaFalsa({"id": 456, "name": "Tarea"})
        return _RespuestaFalsa([])

    monkeypatch.setattr(httpx, "get", _get_falso)

    real = cliente_canvas.ClienteCanvasReal("https://canvas.example")
    real.obtener_usuario_actual("token")
    real.listar_cursos_profesor("token")
    real.obtener_matriculas_profesor("token", 123)
    real.obtener_assignment("token", 123, 456)

    assert cliente_canvas.LLAMADAS_REGISTRADAS, "la prueba no registro ninguna llamada"
    for llamada in cliente_canvas.LLAMADAS_REGISTRADAS:
        assert llamada in SCOPES_CANVAS, f"endpoint fuera del catalogo: {llamada}"
