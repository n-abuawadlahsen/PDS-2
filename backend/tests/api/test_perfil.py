"""SPEC 02 S2.10 (recorte Etapa P1): /api/perfil exige sesion; CSRF en mutaciones."""

from __future__ import annotations

import secrets

from fastapi.testclient import TestClient

from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.api.dependencias import hash_token
from tests.apoyo import fabrica_bd


def _crear_usuario_con_sesion(*, email: str = "ana.perfil@gmail.com") -> tuple[int, str]:
    with fabrica_bd()() as bd:
        ahora = ahora_utc()
        usuario = Usuario(
            google_sub=secrets.token_hex(8),
            email=email,
            email_canonico=email,
            nombre="Ana",
            activo=True,
            creado_en=ahora,
            actualizado_en=ahora,
        )
        bd.add(usuario)
        bd.flush()

        token = secrets.token_urlsafe(32)
        sesion = Sesion(
            usuario_id=usuario.id,
            token_hash=hash_token(token),
            jti_oidc=secrets.token_urlsafe(16),
            creada_en=ahora,
            expira_en=ahora_utc().replace(year=ahora.year + 1),
        )
        bd.add(sesion)
        bd.commit()
        return usuario.id, token


def test_perfil_sin_sesion_da_401(cliente: TestClient):
    respuesta = cliente.get("/api/perfil")
    assert respuesta.status_code == 401


def test_perfil_con_sesion_devuelve_datos(cliente: TestClient):
    _usuario_id, token = _crear_usuario_con_sesion()
    cliente.cookies.set("sesion", token)
    respuesta = cliente.get("/api/perfil")
    assert respuesta.status_code == 200
    assert respuesta.json()["email"] == "ana.perfil@gmail.com"


def test_patch_perfil_sin_csrf_falla(cliente: TestClient):
    _usuario_id, token = _crear_usuario_con_sesion()
    cliente.cookies.set("sesion", token)
    respuesta = cliente.patch("/api/perfil", json={"nombre": "Otro nombre"})
    assert respuesta.status_code == 403


def test_patch_perfil_con_csrf_funciona(cliente: TestClient):
    _usuario_id, token = _crear_usuario_con_sesion()
    cliente.cookies.set("sesion", token)
    csrf = secrets.token_urlsafe(16)
    cliente.cookies.set("csrf_token", csrf)
    respuesta = cliente.patch(
        "/api/perfil", json={"nombre": "Otro nombre"}, headers={"X-CSRF-Token": csrf}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Otro nombre"


def test_correo_no_es_editable_por_patch(cliente: TestClient):
    """CA-2.10-01: el correo no aparece como campo editable en el esquema de entrada."""
    from app.api.rutas.perfil import PerfilEntrada

    assert "email" not in PerfilEntrada.model_fields
