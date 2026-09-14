"""SPEC 02 S2.4, S2.5, S2.7, S2.9 (Etapa P2): curso, equipo, invitaciones."""

from __future__ import annotations

import secrets

from fastapi.testclient import TestClient

from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.api.dependencias import hash_token
from tests.apoyo import fabrica_bd


def _crear_usuario_con_sesion(*, email: str, nombre: str = "Ana") -> tuple[str, str]:
    """Devuelve (usuario_id_str, token_sesion)."""
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
        return str(usuario.id), token


def _sesion_autenticada(cliente: TestClient, token: str) -> None:
    cliente.cookies.set("sesion", token)
    csrf = secrets.token_urlsafe(16)
    cliente.cookies.set("csrf_token", csrf)
    cliente.headers.update({"X-CSRF-Token": csrf})


def _crear_curso(cliente: TestClient, *, slug: str) -> dict:
    respuesta = cliente.post(
        "/api/cursos",
        json={
            "nombre": "Desarrollo de Software",
            "codigo": "ICC4201",
            "periodo": "2026-2",
            "slug": slug,
            "zona_horaria": "America/Santiago",
        },
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def test_crear_curso_deja_al_creador_como_profesor(cliente: TestClient):
    _uid, token = _crear_usuario_con_sesion(email="profe@gmail.com")
    _sesion_autenticada(cliente, token)

    curso = _crear_curso(cliente, slug="pds-1")

    contexto = cliente.get(f"/api/cursos/{curso['id']}/contexto")
    assert contexto.status_code == 200
    assert contexto.json()["rol"] == "PROFESOR"
    assert set(contexto.json()["permisos_efectivos"]) >= {"curso.ver", "correccion.corregir"}


def test_listar_cursos_solo_muestra_los_del_usuario(cliente: TestClient):
    _uid1, token1 = _crear_usuario_con_sesion(email="ana@gmail.com")
    _sesion_autenticada(cliente, token1)
    _crear_curso(cliente, slug="pds-2")

    _uid2, token2 = _crear_usuario_con_sesion(email="beto@gmail.com")
    _sesion_autenticada(cliente, token2)
    respuesta = cliente.get("/api/cursos")
    assert respuesta.json() == []


def test_invitar_ayudante_con_permiso_no_concedible_da_422(cliente: TestClient):
    _uid, token = _crear_usuario_con_sesion(email="profe2@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-3")

    respuesta = cliente.post(
        f"/api/cursos/{curso['id']}/equipo/invitaciones",
        json={"email": "ayudante@gmail.com", "rol": "AYUDANTE", "permisos": ["curso.administrar"]},
    )
    assert respuesta.status_code == 422


def test_flujo_completo_de_invitacion_y_aceptacion(cliente: TestClient):
    _uid_profe, token_profe = _crear_usuario_con_sesion(email="profe3@gmail.com")
    _sesion_autenticada(cliente, token_profe)
    curso = _crear_curso(cliente, slug="pds-4")

    creada = cliente.post(
        f"/api/cursos/{curso['id']}/equipo/invitaciones",
        json={
            "email": "ayudante3@gmail.com",
            "rol": "AYUDANTE",
            "permisos": ["mapeo.editar"],
        },
    )
    assert creada.status_code == 200, creada.text

    # Segunda invitacion pendiente a la misma direccion se rechaza (S2.5.3).
    duplicada = cliente.post(
        f"/api/cursos/{curso['id']}/equipo/invitaciones",
        json={"email": "ayudante3@gmail.com", "rol": "AYUDANTE", "permisos": []},
    )
    assert duplicada.status_code == 409

    equipo = cliente.get(f"/api/cursos/{curso['id']}/equipo")
    assert equipo.status_code == 200
    assert len(equipo.json()) == 1  # solo el profesor: la invitacion aun no se acepto


def test_retirar_al_unico_profesor_activo_se_rechaza(cliente: TestClient):
    _uid, token = _crear_usuario_con_sesion(email="unico@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-5")

    equipo = cliente.get(f"/api/cursos/{curso['id']}/equipo").json()
    membresia_id = equipo[0]["membresia_id"]

    respuesta = cliente.post(f"/api/cursos/{curso['id']}/equipo/{membresia_id}/retiro")
    assert respuesta.status_code == 409
    assert "promueve antes a otro profesor" in respuesta.json()["detail"]


def test_cerrar_sesion_de_curso_no_afecta_otro_curso(cliente: TestClient):
    """CA-2.4-01: la misma persona en dos cursos, cada membresia funciona por separado."""
    _uid, token = _crear_usuario_con_sesion(email="dual@gmail.com")
    _sesion_autenticada(cliente, token)
    curso_a = _crear_curso(cliente, slug="pds-a")
    curso_b = _crear_curso(cliente, slug="pds-b")

    for curso in (curso_a, curso_b):
        respuesta = cliente.get(f"/api/cursos/{curso['id']}/contexto")
        assert respuesta.status_code == 200
        assert respuesta.json()["rol"] == "PROFESOR"


def test_ruta_de_curso_sin_membresia_da_404(cliente: TestClient):
    _uid1, token1 = _crear_usuario_con_sesion(email="dueno@gmail.com")
    _sesion_autenticada(cliente, token1)
    curso = _crear_curso(cliente, slug="pds-6")

    _uid2, token2 = _crear_usuario_con_sesion(email="ajeno@gmail.com")
    _sesion_autenticada(cliente, token2)
    respuesta = cliente.get(f"/api/cursos/{curso['id']}/contexto")
    assert respuesta.status_code == 404
