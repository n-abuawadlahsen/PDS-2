"""SPEC 04 S4.5 / SPEC 05 S5.2 (Etapa P3): paso 2 del asistente, con Canvas en
modo doble (backend/.env: CANVAS_MODO=doble)."""

from __future__ import annotations

import secrets
import uuid

from fastapi.testclient import TestClient

from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_curso import MembresiaCurso
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.api.dependencias import hash_token
from tests.apoyo import fabrica_bd

_BASE_URL_DOBLE = "https://canvas-doble.local"


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


def test_listar_instancias_permitidas(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="ve.instancias@gmail.com")
    _sesion_autenticada(cliente, token)
    respuesta = cliente.get("/api/canvas/instancias")
    assert respuesta.status_code == 200
    assert any(i["base_url"] == _BASE_URL_DOBLE for i in respuesta.json())


def test_cursos_disponibles_con_token_valido(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.canvas1@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-canvas-1")

    respuesta = cliente.post(
        f"/api/cursos/{curso['id']}/vinculacion/canvas/cursos-disponibles",
        json={"token": "valido", "canvas_base_url": _BASE_URL_DOBLE},
    )
    assert respuesta.status_code == 200, respuesta.text
    cursos = respuesta.json()
    assert len(cursos) == 1
    assert cursos[0]["canvas_course_id"] == 5001
    assert cursos[0]["ya_vinculado_a"] is None


def test_cursos_disponibles_con_token_invalido_da_lista_vacia(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.canvas2@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-canvas-2")

    respuesta = cliente.post(
        f"/api/cursos/{curso['id']}/vinculacion/canvas/cursos-disponibles",
        json={"token": "invalido", "canvas_base_url": _BASE_URL_DOBLE},
    )
    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_vincular_canvas_completa_y_cambia_estado_del_curso(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.canvas3@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-canvas-3")
    assert curso["estado"] == "BORRADOR"

    respuesta = cliente.post(
        f"/api/cursos/{curso['id']}/vinculacion/canvas",
        json={"token": "valido", "canvas_base_url": _BASE_URL_DOBLE, "canvas_course_id": 5001},
    )
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["orden_respaldo"] == 0
    assert cuerpo["curso_estado"] == "VINCULANDO"

    estado = cliente.get(f"/api/cursos/{curso['id']}/vinculacion/canvas")
    assert estado.status_code == 200
    assert len(estado.json()) == 1
    assert estado.json()[0]["estado"] == "VALIDA"
    # Nunca se devuelve el token, ni cifrado ni descifrado (A-034).
    assert "token" not in estado.text.lower().replace("token_cifrado", "").replace(
        "vinculacion/canvas", ""
    )


def test_repetir_el_pegado_es_upsert_no_crea_segunda_fila(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.canvas4@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-canvas-4")

    for _ in range(2):
        respuesta = cliente.post(
            f"/api/cursos/{curso['id']}/vinculacion/canvas",
            json={"token": "valido", "canvas_base_url": _BASE_URL_DOBLE, "canvas_course_id": 5001},
        )
        assert respuesta.status_code == 200

    estado = cliente.get(f"/api/cursos/{curso['id']}/vinculacion/canvas")
    assert len(estado.json()) == 1


def test_vincular_sin_matricula_de_profesor_se_rechaza(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.canvas5@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-canvas-5")

    respuesta = cliente.post(
        f"/api/cursos/{curso['id']}/vinculacion/canvas",
        json={"token": "valido", "canvas_base_url": _BASE_URL_DOBLE, "canvas_course_id": 9999},
    )
    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == "SIN_MATRICULA_PROFESOR"


def test_vincular_a_curso_ya_vinculado_nombra_al_ocupante(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.canvas6@gmail.com")
    _sesion_autenticada(cliente, token)
    curso_a = _crear_curso(cliente, slug="pds-canvas-6a")
    curso_b = _crear_curso(cliente, slug="pds-canvas-6b")

    primero = cliente.post(
        f"/api/cursos/{curso_a['id']}/vinculacion/canvas",
        json={"token": "valido", "canvas_base_url": _BASE_URL_DOBLE, "canvas_course_id": 5001},
    )
    assert primero.status_code == 200

    segundo = cliente.post(
        f"/api/cursos/{curso_b['id']}/vinculacion/canvas",
        json={"token": "valido", "canvas_base_url": _BASE_URL_DOBLE, "canvas_course_id": 5001},
    )
    assert segundo.status_code == 422
    assert segundo.json()["detail"]["motivo"] == "CURSO_YA_VINCULADO"
    assert segundo.json()["detail"]["curso_ocupante"] == "Curso de prueba"


def test_instancia_no_reconocida_se_rechaza(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.canvas7@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-canvas-7")

    respuesta = cliente.post(
        f"/api/cursos/{curso['id']}/vinculacion/canvas/cursos-disponibles",
        json={"token": "valido", "canvas_base_url": "https://otra-instancia.example"},
    )
    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == "INSTANCIA_NO_RECONOCIDA"


def test_ayudante_no_puede_vincular(cliente: TestClient):
    """S4.3.1: curso.administrar NO CONCEDIBLE a un ayudante."""
    token_profe = _crear_usuario_con_sesion(email="profe.canvas8@gmail.com")
    _sesion_autenticada(cliente, token_profe)
    curso = _crear_curso(cliente, slug="pds-canvas-8")

    token_ayudante = _crear_usuario_con_sesion(email="ayudante.canvas8@gmail.com")
    with fabrica_bd()() as bd:
        usuario_ayudante = (
            bd.query(Usuario).filter(Usuario.email == "ayudante.canvas8@gmail.com").one()
        )
        ahora = ahora_utc()
        bd.add(
            MembresiaCurso(
                curso_id=uuid.UUID(curso["id"]),
                usuario_id=usuario_ayudante.id,
                rol="AYUDANTE",
                permisos=["mapeo.editar"],
                estado="ACTIVA",
                version=1,
                creada_en=ahora,
            )
        )
        bd.commit()

    _sesion_autenticada(cliente, token_ayudante)
    respuesta = cliente.post(
        f"/api/cursos/{curso['id']}/vinculacion/canvas/cursos-disponibles",
        json={"token": "valido", "canvas_base_url": _BASE_URL_DOBLE},
    )
    assert respuesta.status_code == 403
    assert respuesta.json()["detail"]["codigo"] == "PERMISO_INSUFICIENTE"
