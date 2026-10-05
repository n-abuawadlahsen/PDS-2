"""Sesiones e identidades son operaciones del titular y conservan evidencia."""

from __future__ import annotations

import secrets
import uuid
from datetime import timedelta

from fastapi.testclient import TestClient

from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_canvas import CredencialCanvas, IdentidadCanvasUsuario
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_identidad import Sesion
from app.adaptadores.modelos_infraestructura import Bitacora
from app.api.dependencias import hash_token
from tests.api.test_cursos import _crear_curso, _crear_usuario_con_sesion, _sesion_autenticada
from tests.apoyo import fabrica_bd


def test_cerrar_sesion_individual_no_revoca_las_demas(cliente: TestClient):
    uid, token = _crear_usuario_con_sesion(email="sesion.propia@gmail.com")
    ajeno, otro_token = _crear_usuario_con_sesion(email="sesion.ajena@gmail.com")
    token_extra = secrets.token_urlsafe(32)
    with fabrica_bd()() as bd:
        extra = Sesion(
            usuario_id=uuid.UUID(uid),
            token_hash=hash_token(token_extra),
            jti_oidc=secrets.token_hex(16),
            creada_en=ahora_utc(),
            expira_en=ahora_utc() + timedelta(days=1),
        )
        bd.add(extra)
        bd.flush()
        extra_id = str(extra.id)
        ajena_id = str(bd.query(Sesion).filter_by(usuario_id=uuid.UUID(ajeno)).one().id)
        bd.commit()
    _sesion_autenticada(cliente, token)
    assert cliente.delete(f"/api/perfil/sesiones/{ajena_id}").status_code == 404
    r = cliente.delete(f"/api/perfil/sesiones/{extra_id}")
    assert r.status_code == 200 and not r.json()["es_la_actual"]
    assert cliente.get("/api/perfil").status_code == 200
    _sesion_autenticada(cliente, token_extra)
    assert cliente.get("/api/perfil").status_code == 401
    _sesion_autenticada(cliente, otro_token)
    assert cliente.get("/api/perfil").status_code == 200
    _sesion_autenticada(cliente, token)
    actual_id = cliente.get("/api/perfil/sesiones").json()[0]["id"]
    assert cliente.delete(f"/api/perfil/sesiones/{actual_id}").json()["es_la_actual"]
    assert cliente.get("/api/perfil").status_code == 401


def test_cerrar_sesion_exige_csrf(cliente: TestClient):
    _, token = _crear_usuario_con_sesion(email="sesion.csrf@gmail.com")
    cliente.cookies.set("sesion", token)
    actual_id = cliente.get("/api/perfil/sesiones").json()[0]["id"]
    assert cliente.delete(f"/api/perfil/sesiones/{actual_id}").status_code == 403
    assert cliente.get("/api/perfil").status_code == 200


def _vincular(cliente: TestClient):
    uid, token = _crear_usuario_con_sesion(email="identidad.propia@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="identidad-canvas")
    r = cliente.post(
        f"/api/cursos/{curso['id']}/vinculacion/canvas",
        json={
            "token": "valido",
            "canvas_base_url": "https://canvas-doble.local",
            "canvas_course_id": 5001,
        },
    )
    assert r.status_code == 200, r.text
    return uid, token, curso


def test_desvincular_identidad_conserva_curso_credencial_auditada_y_privacidad(cliente: TestClient):
    uid, token, curso = _vincular(cliente)
    r = cliente.get("/api/perfil/identidades-canvas")
    assert r.status_code == 200
    identidad = r.json()[0]
    assert identidad["cursos"][0]["id"] == curso["id"]
    assert "token" not in r.text.lower()
    _, ajeno = _crear_usuario_con_sesion(email="identidad.ajena@gmail.com")
    _sesion_autenticada(cliente, ajeno)
    assert cliente.get("/api/perfil/identidades-canvas").json() == []
    path = f"/api/perfil/identidades-canvas/{identidad['id']}"
    assert cliente.delete(path).status_code == 404
    _sesion_autenticada(cliente, token)
    assert cliente.delete(path).json() == {"credenciales_retiradas": 1}
    assert cliente.get("/api/perfil/identidades-canvas").json() == []
    with fabrica_bd()() as bd:
        credencial = bd.query(CredencialCanvas).filter_by(usuario_id=uuid.UUID(uid)).one()
        assert credencial.estado == "RETIRADA" and credencial.token_cifrado == b""
        assert bd.get(Curso, uuid.UUID(curso["id"])).estado == "CANVAS_DESVINCULADO"
        assert (
            bd.query(MembresiaCurso).filter_by(usuario_id=uuid.UUID(uid)).one().estado == "ACTIVA"
        )
        assert bd.query(Bitacora).filter_by(accion="IDENTIDAD_CANVAS_DESVINCULADA").count() == 1


def test_desvincular_promueve_respaldo_y_respeta_otra_instancia(cliente: TestClient):
    uid, _, curso = _vincular(cliente)
    uid_respaldo, _ = _crear_usuario_con_sesion(email="respaldo@gmail.com")
    with fabrica_bd()() as bd:
        ahora = ahora_utc()
        bd.add(
            MembresiaCurso(
                curso_id=uuid.UUID(curso["id"]),
                usuario_id=uuid.UUID(uid_respaldo),
                rol="PROFESOR",
                estado="ACTIVA",
                permisos=[],
                version=1,
                creada_en=ahora,
            )
        )
        bd.add(
            CredencialCanvas(
                curso_id=uuid.UUID(curso["id"]),
                usuario_id=uuid.UUID(uid_respaldo),
                token_cifrado=b"ensayo",
                nonce=b"ensayo",
                huella="ensayo",
                canvas_user_id=202,
                estado="VALIDA",
                orden_respaldo=1,
                version_clave=1,
                consentimiento_en=ahora,
            )
        )
        bd.add(
            IdentidadCanvasUsuario(
                usuario_id=uuid.UUID(uid),
                canvas_base_url="https://otra.test",
                canvas_user_id=303,
                verificada_en=ahora,
            )
        )
        bd.commit()
    identidades = cliente.get("/api/perfil/identidades-canvas").json()
    identidad = next(i for i in identidades if i["canvas_base_url"] == "https://canvas-doble.local")
    assert cliente.delete(f"/api/perfil/identidades-canvas/{identidad['id']}").status_code == 200
    assert [i["canvas_base_url"] for i in cliente.get("/api/perfil/identidades-canvas").json()] == [
        "https://otra.test"
    ]
    with fabrica_bd()() as bd:
        assert (
            bd.query(CredencialCanvas)
            .filter_by(usuario_id=uuid.UUID(uid_respaldo))
            .one()
            .orden_respaldo
            == 0
        )
        assert bd.get(Curso, uuid.UUID(curso["id"])).estado != "CANVAS_DESVINCULADO"
