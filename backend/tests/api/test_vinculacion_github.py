"""SPEC 04 S4.6 (Etapa P4): paso 3 del asistente, con GitHub en modo doble
(backend/.env: GITHUB_MODO=doble)."""

from __future__ import annotations

import secrets

from fastapi.testclient import TestClient

from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.api.dependencias import hash_token
from tests.apoyo import fabrica_bd


def _crear_usuario_con_sesion(*, email: str, nombre: str = "Profesora") -> str:
    with fabrica_bd()() as bd:
        ahora = ahora_utc()
        usuario = Usuario(
            google_sub=secrets.token_hex(8),
            email=email,
            email_canonico=email,
            nombre=nombre,
            activo=True,
            creado_en=ahora,
            actualizado_en=ahora,
        )
        bd.add(usuario)
        bd.flush()
        token = secrets.token_urlsafe(32)
        bd.add(
            Sesion(
                usuario_id=usuario.id,
                token_hash=hash_token(token),
                jti_oidc=secrets.token_urlsafe(16),
                creada_en=ahora,
                expira_en=ahora_utc().replace(year=ahora.year + 1),
            )
        )
        bd.commit()
        return token


def _sesion_autenticada(cliente: TestClient, token: str) -> None:
    cliente.cookies.set("sesion", token)
    csrf = secrets.token_urlsafe(16)
    cliente.cookies.set("csrf_token", csrf)
    cliente.headers.update({"X-CSRF-Token": csrf})


def _crear_curso(cliente: TestClient, *, slug: str) -> dict:
    respuesta = cliente.post(
        "/api/cursos",
        json={
            "nombre": "Curso de prueba",
            "codigo": "ICC4201",
            "periodo": "2026-2",
            "slug": slug,
            "zona_horaria": "America/Santiago",
        },
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def _iniciar_y_extraer_state(cliente: TestClient, curso_id: str) -> str:
    respuesta = cliente.post(f"/api/cursos/{curso_id}/vinculacion/github/iniciar", json={})
    assert respuesta.status_code == 200, respuesta.text
    url = respuesta.json()["instalar_url"]
    assert url.startswith(
        "https://github.com/apps/proyecto2-icc4201-doble/installations/new?state="
    )
    return url.split("state=", 1)[1]


def test_iniciar_instalacion_devuelve_url_de_github(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.gh1@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-gh-1")
    _iniciar_y_extraer_state(cliente, curso["id"])


def test_callback_con_installation_id_valido_vincula_y_crea_equipo(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.gh2@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-gh-2")
    state = _iniciar_y_extraer_state(cliente, curso["id"])

    respuesta = cliente.post(
        "/api/vinculacion/github/callback",
        json={"state": state, "installation_id": 8001, "setup_action": "install"},
    )
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["resultado"] == "VINCULADO"
    assert cuerpo["org_login"] == "org-valida"
    assert cuerpo["equipo_docentes_slug"] == "docentes"
    assert cuerpo["curso_estado"] == "VINCULANDO"

    estado = cliente.get(f"/api/cursos/{curso['id']}/vinculacion/github")
    assert estado.status_code == 200
    assert estado.json()["org_login"] == "org-valida"
    assert estado.json()["installation_id"] == 8001


def test_callback_con_state_invalido_no_vincula(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.gh3@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-gh-3")
    _iniciar_y_extraer_state(cliente, curso["id"])

    respuesta = cliente.post(
        "/api/vinculacion/github/callback",
        json={"state": "no-es-un-jwt", "installation_id": 8001, "setup_action": "install"},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["resultado"] == "STATE_INVALIDO"


def test_callback_en_cuenta_personal_se_rechaza(cliente: TestClient):
    """S4.6.3: R2.1.5 exige una organizacion, nunca una cuenta personal."""
    token = _crear_usuario_con_sesion(email="profe.gh4@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-gh-4")
    state = _iniciar_y_extraer_state(cliente, curso["id"])

    respuesta = cliente.post(
        "/api/vinculacion/github/callback",
        json={"state": state, "installation_id": 8002, "setup_action": "install"},
    )
    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == "CUENTA_PERSONAL"


def test_callback_organizacion_ya_vinculada_nombra_al_ocupante(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.gh5@gmail.com")
    _sesion_autenticada(cliente, token)
    curso_a = _crear_curso(cliente, slug="pds-gh-5a")
    curso_b = _crear_curso(cliente, slug="pds-gh-5b")

    state_a = _iniciar_y_extraer_state(cliente, curso_a["id"])
    primero = cliente.post(
        "/api/vinculacion/github/callback",
        json={"state": state_a, "installation_id": 8001, "setup_action": "install"},
    )
    assert primero.status_code == 200

    state_b = _iniciar_y_extraer_state(cliente, curso_b["id"])
    segundo = cliente.post(
        "/api/vinculacion/github/callback",
        json={"state": state_b, "installation_id": 8001, "setup_action": "install"},
    )
    assert segundo.status_code == 422
    assert segundo.json()["detail"]["motivo"] == "ORGANIZACION_YA_VINCULADA"
    assert segundo.json()["detail"]["curso_ocupante"] == "Curso de prueba"


def test_callback_sin_installation_id_deja_el_curso_vinculando(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.gh6@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-gh-6")
    state = _iniciar_y_extraer_state(cliente, curso["id"])

    respuesta = cliente.post(
        "/api/vinculacion/github/callback",
        json={"state": state, "setup_action": "request"},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["resultado"] == "SOLICITUD_PENDIENTE"
