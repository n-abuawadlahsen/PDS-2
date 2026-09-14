"""SPEC 04 S4.7 (Etapa P4): checklist de verificacion, con Canvas y GitHub en
modo doble (backend/.env: CANVAS_MODO=doble, GITHUB_MODO=doble)."""

from __future__ import annotations

import secrets

from fastapi.testclient import TestClient

from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.api.dependencias import hash_token
from app.trabajos import (  # noqa: F401 (registra el manejador)
    ejecutar_checklist_vinculacion,
    registro,
)
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


def _vincular_canvas(cliente: TestClient, curso_id: str) -> None:
    respuesta = cliente.post(
        f"/api/cursos/{curso_id}/vinculacion/canvas",
        json={"token": "valido", "canvas_base_url": _BASE_URL_DOBLE, "canvas_course_id": 5001},
    )
    assert respuesta.status_code == 200, respuesta.text


def _vincular_github(cliente: TestClient, curso_id: str) -> None:
    inicio = cliente.post(f"/api/cursos/{curso_id}/vinculacion/github/iniciar", json={})
    assert inicio.status_code == 200, inicio.text
    state = inicio.json()["instalar_url"].split("state=", 1)[1]
    callback = cliente.post(
        "/api/vinculacion/github/callback",
        json={"state": state, "installation_id": 8001, "setup_action": "install"},
    )
    assert callback.status_code == 200, callback.text


def _ejecutar_trabajos_pendientes() -> None:
    """Simula un tick del ejecutor (app/trabajos/ejecutor.py) sin el proceso
    en segundo plano: toma y corre cada trabajo pendiente en la misma sesion."""
    with fabrica_bd()() as bd:
        from app.adaptadores import trabajos_repo

        while True:
            trabajo = trabajos_repo.tomar_siguiente(bd, tomado_por="test")
            if trabajo is None:
                break
            manejador = registro.obtener_manejador(trabajo.tipo)
            assert manejador is not None, f"sin manejador para {trabajo.tipo}"
            manejador(bd, trabajo)
            trabajos_repo.marcar_ok(bd, trabajo)
        bd.commit()


def test_checklist_completo_activa_el_curso_sin_bloqueantes(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.check1@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-check-1")
    _vincular_canvas(cliente, curso["id"])
    _vincular_github(cliente, curso["id"])

    encolado = cliente.post(f"/api/cursos/{curso['id']}/verificacion")
    assert encolado.status_code == 202, encolado.text
    ejecucion_id = encolado.json()["ejecucion_id"]

    _ejecutar_trabajos_pendientes()

    estado = cliente.get(f"/api/cursos/{curso['id']}/verificacion/{ejecucion_id}")
    assert estado.status_code == 200
    items = {f["item"] for f in estado.json()}
    assert items == {
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
    }
    assert not any(f["resultado"] == "BLOQUEANTE" for f in estado.json())

    with fabrica_bd()() as bd:
        curso_bd = bd.query(Curso).filter(Curso.id == curso["id"]).one()
        assert curso_bd.estado == "ACTIVO"


def test_item_1_bloqueante_cascada_a_los_demas_items_de_canvas(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.check2@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-check-2")
    _vincular_canvas(cliente, curso["id"])
    _vincular_github(cliente, curso["id"])

    # Invalida la credencial operativa para que el item 1 salga BLOQUEANTE.
    from app.adaptadores.modelos_canvas import CredencialCanvas

    with fabrica_bd()() as bd:
        credencial = (
            bd.query(CredencialCanvas).filter(CredencialCanvas.curso_id == curso["id"]).one()
        )
        credencial.canvas_user_id = 999999
        bd.commit()

    encolado = cliente.post(f"/api/cursos/{curso['id']}/verificacion")
    ejecucion_id = encolado.json()["ejecucion_id"]
    _ejecutar_trabajos_pendientes()

    filas = {
        f["item"]: f
        for f in cliente.get(f"/api/cursos/{curso['id']}/verificacion/{ejecucion_id}").json()
    }
    assert filas["1"]["resultado"] == "BLOQUEANTE"
    assert filas["2"]["resultado"] == "NO_VERIFICADO"
    assert filas["2"]["detalle"]["motivo"] == "DEPENDE_DE_ITEM_1"
    # El carril de GitHub (14, 18) se ejecuta igual (CA-4.7-02).
    assert filas["14"]["resultado"] != "NO_VERIFICADO"
    assert filas["18"]["resultado"] != "NO_VERIFICADO"

    with fabrica_bd()() as bd:
        curso_bd = bd.query(Curso).filter(Curso.id == curso["id"]).one()
        assert curso_bd.estado != "ACTIVO"


def test_reejecutar_un_item_no_toca_los_demas(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.check3@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-check-3")
    _vincular_canvas(cliente, curso["id"])
    _vincular_github(cliente, curso["id"])

    cliente.post(f"/api/cursos/{curso['id']}/verificacion")
    _ejecutar_trabajos_pendientes()
    primera_pasada = {
        f["item"]: f["ejecutada_en"]
        for f in cliente.get(f"/api/cursos/{curso['id']}/verificacion/ultima").json()
    }

    reejecucion = cliente.post(f"/api/cursos/{curso['id']}/verificacion/items/9")
    assert reejecucion.status_code == 202
    _ejecutar_trabajos_pendientes()

    segunda_pasada = {
        f["item"]: f["ejecutada_en"]
        for f in cliente.get(f"/api/cursos/{curso['id']}/verificacion/ultima").json()
    }
    assert segunda_pasada["9"] != primera_pasada["9"]
    for item in primera_pasada:
        if item != "9":
            assert segunda_pasada[item] == primera_pasada[item]


def test_item_14_sin_github_vinculado_es_bloqueante(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.check4@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-check-4")
    _vincular_canvas(cliente, curso["id"])

    encolado = cliente.post(f"/api/cursos/{curso['id']}/verificacion")
    ejecucion_id = encolado.json()["ejecucion_id"]
    _ejecutar_trabajos_pendientes()

    filas = {
        f["item"]: f
        for f in cliente.get(f"/api/cursos/{curso['id']}/verificacion/{ejecucion_id}").json()
    }
    assert filas["14"]["resultado"] == "BLOQUEANTE"

    with fabrica_bd()() as bd:
        curso_bd = bd.query(Curso).filter(Curso.id == curso["id"]).one()
        assert curso_bd.estado != "ACTIVO"


def test_5bis_sin_casilla_marcada_queda_no_verificado(cliente: TestClient):
    """Regresion de enrutado: `/items/5-bis` debe ganarle a `/items/{item}`,
    registrada antes en el router (FastAPI resuelve por orden de registro)."""
    token = _crear_usuario_con_sesion(email="profe.check5@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-check-5")
    _vincular_canvas(cliente, curso["id"])

    respuesta = cliente.post(
        f"/api/cursos/{curso['id']}/verificacion/items/5-bis", json={"consiento": False}
    )
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["item"] == "5-bis"
    assert cuerpo["resultado"] == "NO_VERIFICADO"
    assert cuerpo["detalle"]["motivo"] == "CASILLA_NO_MARCADA"


def test_5bis_con_casilla_marcada_escribe_via_anuncio_seccion(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.check6@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-check-6")
    _vincular_canvas(cliente, curso["id"])

    respuesta = cliente.post(
        f"/api/cursos/{curso['id']}/verificacion/items/5-bis", json={"consiento": True}
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["detalle"]["via_anuncio_seccion"] == "SECCION"

    with fabrica_bd()() as bd:
        curso_bd = bd.query(Curso).filter(Curso.id == curso["id"]).one()
        assert curso_bd.via_anuncio_seccion == "SECCION"
