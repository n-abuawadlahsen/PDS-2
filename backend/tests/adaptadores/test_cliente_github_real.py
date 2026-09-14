"""`ClienteGitHubReal`: consultas de cuentas publicas (SPEC 06 S6.2.4), sin red.

Regresion del 14-sep-2026, vista en produccion: `/users/{login}` y
`/orgs/{login}` se consultaban con el JWT de la App, que GitHub rechaza con 401
fuera de las rutas `/app/...`. Toda organizacion real quedaba como
`CUENTA_PERSONAL` y todo login de estudiante como inexistente. El doble no lo
mostraba porque no pasa por HTTP.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from app.adaptadores import cliente_github
from app.adaptadores.cliente_github import ClienteGitHubReal, FalloProveedorGithub

_TOKEN_INSTALACION = "ghs_token_de_instalacion"


class _GitHubFalso:
    """Imita lo que GitHub hace de verdad: el JWT de la App no sirve en `/users`
    ni en `/orgs` (401), y una organizacion existe en los dos endpoints."""

    def __init__(self, cuentas: dict[str, int], *, instalaciones: bool = True) -> None:
        self.cuentas = cuentas
        self.instalaciones = instalaciones
        self.tokens_emitidos = 0
        self.autorizaciones: list[str | None] = []

    def __call__(
        self, metodo: str, url: str, *, headers: dict[str, str], **_: Any
    ) -> httpx.Response:
        peticion = httpx.Request(metodo, url)
        autorizacion = headers.get("Authorization")
        if url.endswith("/app/installations?per_page=100"):
            cuerpo = (
                [{"id": 161736234, "account": {"login": "PDS-2", "id": 1}, "suspended_at": None}]
                if self.instalaciones
                else []
            )
            return httpx.Response(200, json=cuerpo, request=peticion)
        if url.endswith("/access_tokens"):
            self.tokens_emitidos += 1
            cuerpo = {"token": _TOKEN_INSTALACION, "expires_at": "2999-01-01T00:00:00Z"}
            return httpx.Response(201, json=cuerpo, request=peticion)

        self.autorizaciones.append(autorizacion)
        estado = self.cuentas[url.removeprefix("https://api.github.com")]
        if autorizacion == "Bearer jwt-de-la-app":
            estado = 401
        cuerpo = {"id": 4242, "login": "Estudiante-Valido"} if estado == 200 else {"message": "x"}
        return httpx.Response(estado, json=cuerpo, request=peticion)


@pytest.fixture
def cliente(monkeypatch: pytest.MonkeyPatch) -> ClienteGitHubReal:
    cliente_github._tokens_consulta.clear()
    monkeypatch.setattr(ClienteGitHubReal, "_jwt_app", lambda self: "jwt-de-la-app")
    return ClienteGitHubReal(app_id="4943358", private_key_pem_base64="no-se-usa")


def _instalar(monkeypatch: pytest.MonkeyPatch, github: _GitHubFalso) -> _GitHubFalso:
    monkeypatch.setattr(httpx, "request", github)
    return github


def test_organizacion_real_se_detecta_con_token_de_instalacion(cliente, monkeypatch):
    github = _instalar(monkeypatch, _GitHubFalso({"/users/PDS-2": 200, "/orgs/PDS-2": 200}))

    assert cliente.existe_como_organizacion("PDS-2") is True
    assert cliente.existe_como_usuario("PDS-2") is True  # igual que en GitHub real
    assert github.autorizaciones == [f"Bearer {_TOKEN_INSTALACION}"] * 2


def test_cuenta_personal_no_es_organizacion_y_devuelve_su_identificador(cliente, monkeypatch):
    _instalar(
        monkeypatch,
        _GitHubFalso({"/users/estudiante-valido": 200, "/orgs/estudiante-valido": 404}),
    )

    assert cliente.existe_como_organizacion("estudiante-valido") is False
    cuenta = cliente.obtener_cuenta_usuario("estudiante-valido")
    assert cuenta is not None
    assert (cuenta.github_user_id, cuenta.login) == (4242, "Estudiante-Valido")


def test_login_inexistente_es_none_no_un_error(cliente, monkeypatch):
    _instalar(monkeypatch, _GitHubFalso({"/users/no-existe": 404}))

    assert cliente.obtener_cuenta_usuario("no-existe") is None
    assert cliente.existe_como_usuario("no-existe") is False


def test_el_token_de_instalacion_se_reutiliza_entre_consultas(cliente, monkeypatch):
    github = _instalar(monkeypatch, _GitHubFalso({"/users/PDS-2": 200, "/orgs/PDS-2": 200}))

    cliente.existe_como_usuario("PDS-2")
    cliente.existe_como_organizacion("PDS-2")
    ClienteGitHubReal(app_id="4943358", private_key_pem_base64="no-se-usa").existe_como_usuario(
        "PDS-2"
    )

    assert github.tokens_emitidos == 1


def test_limite_de_peticiones_es_fallo_del_proveedor_no_cuenta_inexistente(cliente, monkeypatch):
    _instalar(monkeypatch, _GitHubFalso({"/users/alguien": 403}))

    with pytest.raises(FalloProveedorGithub):
        cliente.existe_como_usuario("alguien")


def test_sin_instalaciones_consulta_sin_autenticar(cliente, monkeypatch):
    github = _instalar(monkeypatch, _GitHubFalso({"/orgs/PDS-2": 200}, instalaciones=False))

    assert cliente.existe_como_organizacion("PDS-2") is True
    assert github.autorizaciones == [None]
