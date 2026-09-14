"""SPEC 08 S8.2-S8.3 (Etapa P7): tarea individual, entrega unica y repositorio
base, con Canvas y GitHub en modo doble."""

from __future__ import annotations

import base64
import secrets

from fastapi.testclient import TestClient

from app.adaptadores import trabajos_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.adaptadores.modelos_infraestructura import Bitacora
from app.adaptadores.modelos_tarea import Entrega, VisibilidadEntrega
from app.api.dependencias import hash_token
from app.trabajos import (  # noqa: F401 (registra los manejadores)
    aprovisionar_repositorios,
    materializar_sujetos,
    registro,
    sync_grupos,
    sync_roster,
    sync_tareas_y_fechas,
)
from tests.apoyo import fabrica_bd

_BASE_URL_DOBLE = "https://canvas-doble.local"


def _crear_usuario_con_sesion(*, email: str) -> str:
    with fabrica_bd()() as bd:
        ahora = ahora_utc()
        usuario = Usuario(
            google_sub=secrets.token_hex(8),
            email=email,
            email_canonico=email,
            nombre="Profesora",
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
                expira_en=ahora.replace(year=ahora.year + 1),
            )
        )
        bd.commit()
        return token


def _sesion_autenticada(cliente: TestClient, token: str) -> None:
    cliente.cookies.set("sesion", token)
    csrf = secrets.token_urlsafe(16)
    cliente.cookies.set("csrf_token", csrf)
    cliente.headers.update({"X-CSRF-Token": csrf})


def _ejecutar_trabajos_pendientes() -> None:
    with fabrica_bd()() as bd:
        while True:
            trabajo = trabajos_repo.tomar_siguiente(bd, tomado_por="test")
            if trabajo is None:
                break
            manejador = registro.obtener_manejador(trabajo.tipo)
            assert manejador is not None, f"sin manejador para {trabajo.tipo}"
            manejador(bd, trabajo)
            trabajos_repo.marcar_ok(bd, trabajo)
        bd.commit()


def _preparar_curso(cliente: TestClient, *, slug: str, email: str, con_github: bool = True) -> str:
    _sesion_autenticada(cliente, _crear_usuario_con_sesion(email=email))
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
    curso_id = respuesta.json()["id"]
    respuesta = cliente.post(
        f"/api/cursos/{curso_id}/vinculacion/canvas",
        json={"token": "valido", "canvas_base_url": _BASE_URL_DOBLE, "canvas_course_id": 5001},
    )
    assert respuesta.status_code == 200, respuesta.text
    if con_github:
        iniciar = cliente.post(f"/api/cursos/{curso_id}/vinculacion/github/iniciar", json={})
        assert iniciar.status_code == 200, iniciar.text
        state = iniciar.json()["instalar_url"].split("state=", 1)[1]
        callback = cliente.post(
            "/api/vinculacion/github/callback",
            json={"state": state, "installation_id": 8001, "setup_action": "install"},
        )
        assert callback.status_code == 200, callback.text
    assert cliente.post(f"/api/cursos/{curso_id}/sincronizaciones").status_code == 202
    _ejecutar_trabajos_pendientes()
    return curso_id


def _crear_tarea(cliente: TestClient, curso_id: str, **cambios: object) -> dict:
    cuerpo: dict[str, object] = {
        "nombre": "Tarea 1: Ordenamiento",
        "slug": "t1-ordenamiento",
        "canvas_assignment_id": 9101,
    }
    cuerpo.update(cambios)
    respuesta = cliente.post(f"/api/cursos/{curso_id}/tareas", json=cuerpo)
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


# --- Espejo y seleccion ---


def test_sincronizar_espeja_las_tareas_de_canvas_con_su_motivo(cliente: TestClient):
    curso_id = _preparar_curso(cliente, slug="pds-t7-a", email="profe.t7a@gmail.com")
    respuesta = cliente.get(f"/api/cursos/{curso_id}/tareas/assignments-canvas")
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    por_id = {a["canvas_assignment_id"]: a for a in cuerpo["assignments"]}
    assert {9101, 9102, 9103, 9104} <= set(por_id)
    assert por_id[9101]["seleccionable"] is True
    assert por_id[9102]["seleccionable"] is False
    assert "23 de septiembre" in por_id[9102]["motivo"]
    assert cuerpo["sincronizado_en"] is not None


def test_vista_previa_del_nombre_usa_un_estudiante_real(cliente: TestClient):
    curso_id = _preparar_curso(cliente, slug="pds-t7-b", email="profe.t7b@gmail.com")
    respuesta = cliente.get(
        f"/api/cursos/{curso_id}/tareas/vista-previa-nombre",
        params={"nombre": "Tarea 1: Ordenamiento"},
    )
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["slug"] == "tarea-1-ordenamiento"
    assert cuerpo["ejemplo_repositorio"].startswith("pds-t7-b-tarea-1-ordenamiento-e")
    assert cuerpo["repositorio_base"] == "pds-t7-b-tarea-1-ordenamiento-base"


# --- Crear tarea y entregas (R2.3.1-R2.3.4) ---


def test_crear_tarea_individual_con_su_entrega_final(cliente: TestClient):
    curso_id = _preparar_curso(cliente, slug="pds-t7-c", email="profe.t7c@gmail.com")
    tarea = _crear_tarea(cliente, curso_id)
    assert tarea["estado"] == "BORRADOR"
    assert tarea["modalidad"] == "INDIVIDUAL"
    assert len(tarea["entregas"]) == 1
    entrega = tarea["entregas"][0]
    assert (entrega["tipo"], entrega["orden"]) == ("FINAL", 1)
    assert entrega["slug"] == "tarea-1-ordenamiento"
    # R2.3.5: sin base, la tarea se activa sin ninguna comprobacion de base (CA-8.3-01).
    assert tarea["activar"] == {"habilitada": True, "motivo": None}
    # Bandera `tarea_multientrega`: capa 3 con fecha.
    assert tarea["vincular_otra_entrega"]["habilitada"] is False
    assert "23 de septiembre" in tarea["vincular_otra_entrega"]["motivo"]

    listado = cliente.get(f"/api/cursos/{curso_id}/tareas").json()
    assert [t["slug"] for t in listado] == ["t1-ordenamiento"]


def test_la_visibilidad_de_la_entrega_se_calcula_en_la_sincronizacion(cliente: TestClient):
    curso_id = _preparar_curso(cliente, slug="pds-t7-d", email="profe.t7d@gmail.com")
    tarea = _crear_tarea(cliente, curso_id)
    assert cliente.post(f"/api/cursos/{curso_id}/sincronizaciones").status_code == 202
    _ejecutar_trabajos_pendientes()
    with fabrica_bd()() as bd:
        filas = (
            bd.query(VisibilidadEntrega)
            .join(Entrega, Entrega.id == VisibilidadEntrega.entrega_id)
            .filter(Entrega.tarea_id == tarea["id"])
            .all()
        )
    assert len(filas) == 5
    assert all(f.visible and f.origen == "TODOS" for f in filas)


def test_tarea_grupal_se_rechaza_con_motivo_y_fecha(cliente: TestClient):
    curso_id = _preparar_curso(cliente, slug="pds-t7-e", email="profe.t7e@gmail.com")
    respuesta = cliente.post(
        f"/api/cursos/{curso_id}/tareas",
        json={"nombre": "Compilador", "canvas_assignment_id": 9102},
    )
    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["detail"]["motivo"] == "MODALIDAD_GRUPAL_NO_DISPONIBLE"
    assert cliente.get(f"/api/cursos/{curso_id}/tareas").json() == []


def test_una_tarea_de_canvas_no_se_vincula_dos_veces(cliente: TestClient):
    curso_id = _preparar_curso(cliente, slug="pds-t7-f", email="profe.t7f@gmail.com")
    _crear_tarea(cliente, curso_id)
    respuesta = cliente.post(
        f"/api/cursos/{curso_id}/tareas",
        json={"nombre": "Otra", "slug": "otra", "canvas_assignment_id": 9101},
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"]["motivo"] == "ASSIGNMENT_YA_VINCULADO"


def test_slug_repetido_no_se_sufija(cliente: TestClient):
    curso_id = _preparar_curso(cliente, slug="pds-t7-g", email="profe.t7g@gmail.com")
    _crear_tarea(cliente, curso_id)
    respuesta = cliente.post(
        f"/api/cursos/{curso_id}/tareas",
        json={"nombre": "Otra", "slug": "t1-ordenamiento", "canvas_assignment_id": 9104},
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"]["motivo"] == "SLUG_OCUPADO"


def test_segunda_entrega_rechazada_en_la_parcial(cliente: TestClient):
    curso_id = _preparar_curso(cliente, slug="pds-t7-h", email="profe.t7h@gmail.com")
    tarea = _crear_tarea(cliente, curso_id)
    respuesta = cliente.post(
        f"/api/cursos/{curso_id}/tareas/{tarea['id']}/entregas",
        json={"canvas_assignment_id": 9104, "final_canvas_assignment_id": 9104},
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"]["motivo"] == "MULTIENTREGA_NO_DISPONIBLE"


def test_tarea_sin_sincronizar_pide_sincronizar(cliente: TestClient):
    _sesion_autenticada(cliente, _crear_usuario_con_sesion(email="profe.t7i@gmail.com"))
    curso = cliente.post(
        "/api/cursos",
        json={
            "nombre": "Curso",
            "codigo": "ICC4201",
            "periodo": "2026-2",
            "slug": "pds-t7-i",
            "zona_horaria": "America/Santiago",
        },
    ).json()
    cliente.post(
        f"/api/cursos/{curso['id']}/vinculacion/canvas",
        json={"token": "valido", "canvas_base_url": _BASE_URL_DOBLE, "canvas_course_id": 5001},
    )
    respuesta = cliente.post(
        f"/api/cursos/{curso['id']}/tareas",
        json={"nombre": "T1", "canvas_assignment_id": 9101},
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"]["motivo"] == "ASSIGNMENT_NO_SINCRONIZADO"


# --- Repositorio base y activacion (R2.3.5, R2.3.6, A-208) ---


def _b64(texto: str) -> str:
    return base64.b64encode(texto.encode()).decode()


def test_repositorio_base_de_punta_a_punta(cliente: TestClient):
    curso_id = _preparar_curso(cliente, slug="pds-t7-j", email="profe.t7j@gmail.com")
    tarea = _crear_tarea(cliente, curso_id)
    base_url = f"/api/cursos/{curso_id}/tareas/{tarea['id']}"

    creada = cliente.post(f"{base_url}/repositorio-base")
    assert creada.status_code == 200, creada.text
    detalle = creada.json()
    base = detalle["repositorio_base"]
    assert base["nombre"] == "pds-t7-j-t1-ordenamiento-base"
    assert base["estado"] == "CREADO_VACIO"
    assert base["rama_por_defecto"] == "main"
    assert [a["ruta"] for a in base["archivos"]] == ["README.md"]
    # CA-8.3-02: con el base vacio, activar queda deshabilitado con el motivo literal.
    assert detalle["activar"] == {
        "habilitada": False,
        "motivo": "El repositorio base no tiene contenido.",
    }
    assert cliente.post(f"{base_url}/activar").status_code == 409

    subida = cliente.put(
        f"{base_url}/repositorio-base/archivos/src/main.py",
        json={"contenido_base64": _b64("print('hola')\n")},
    )
    assert subida.status_code == 200, subida.text
    detalle = subida.json()
    assert detalle["repositorio_base"]["estado"] == "LISTO"
    assert detalle["activar"]["habilitada"] is True

    reemplazo = cliente.put(
        f"{base_url}/repositorio-base/archivos/src/main.py",
        json={"contenido_base64": _b64("print('chao')\n")},
    )
    assert reemplazo.status_code == 200, reemplazo.text

    vista = cliente.get(f"{base_url}/repositorio-base/archivos/src/main.py")
    assert vista.status_code == 200, vista.text
    assert vista.json()["texto"] == "print('chao')\n"

    renombrado = cliente.post(
        f"{base_url}/repositorio-base/renombrar", json={"desde": "src/main.py", "hacia": "main.py"}
    )
    assert renombrado.status_code == 200, renombrado.text
    rutas = [a["ruta"] for a in renombrado.json()["repositorio_base"]["archivos"]]
    assert rutas == ["README.md", "main.py"]

    borrado = cliente.delete(f"{base_url}/repositorio-base/archivos/main.py")
    assert borrado.status_code == 200, borrado.text
    assert borrado.json()["repositorio_base"]["estado"] == "CREADO_VACIO"

    cliente.put(
        f"{base_url}/repositorio-base/archivos/enunciado.md",
        json={"contenido_base64": _b64("# Enunciado\n")},
    )
    activada = cliente.post(f"{base_url}/activar")
    assert activada.status_code == 200, activada.text
    assert activada.json()["estado"] == "ACTIVA"

    with fabrica_bd()() as bd:
        acciones = {b.accion for b in bd.query(Bitacora).filter(Bitacora.curso_id == curso_id)}
    assert {
        "REPOSITORIO_BASE_CREACION_SOLICITADA",
        "REPOSITORIO_BASE_CREADO",
        "ARCHIVO_BASE_SUBIDO",
        "ARCHIVO_BASE_REEMPLAZADO",
        "ARCHIVO_BASE_RENOMBRADO",
        "ARCHIVO_BASE_BORRADO",
        "TAREA_ACTIVADA",
    } <= acciones


def test_crear_el_base_dos_veces_no_crea_dos_repositorios(cliente: TestClient):
    curso_id = _preparar_curso(cliente, slug="pds-t7-k", email="profe.t7k@gmail.com")
    tarea = _crear_tarea(cliente, curso_id)
    url = f"/api/cursos/{curso_id}/tareas/{tarea['id']}/repositorio-base"
    assert cliente.post(url).status_code == 200
    segunda = cliente.post(url)
    assert segunda.status_code == 409
    assert segunda.json()["detail"]["motivo"] == "REPOSITORIO_BASE_YA_EXISTE"


def test_no_se_suben_workflows_al_base(cliente: TestClient):
    curso_id = _preparar_curso(cliente, slug="pds-t7-l", email="profe.t7l@gmail.com")
    tarea = _crear_tarea(cliente, curso_id)
    base_url = f"/api/cursos/{curso_id}/tareas/{tarea['id']}"
    assert cliente.post(f"{base_url}/repositorio-base").status_code == 200
    respuesta = cliente.put(
        f"{base_url}/repositorio-base/archivos/.github/workflows/ci.yml",
        json={"contenido_base64": _b64("on: push\n")},
    )
    assert respuesta.status_code == 422
    assert respuesta.json()["detail"]["motivo"] == "RUTA_INVALIDA"


def test_sin_github_no_se_crea_base_ni_se_activa(cliente: TestClient):
    curso_id = _preparar_curso(
        cliente, slug="pds-t7-m", email="profe.t7m@gmail.com", con_github=False
    )
    tarea = _crear_tarea(cliente, curso_id)
    assert tarea["activar"]["motivo"] == "El curso todavía no tiene GitHub vinculado."
    assert tarea["crear_repositorio_base"]["habilitada"] is False
    respuesta = cliente.post(f"/api/cursos/{curso_id}/tareas/{tarea['id']}/repositorio-base")
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"]["motivo"] == "GITHUB_NO_VINCULADO"


def test_desvincular_la_unica_entrega_de_una_tarea_en_borrador(cliente: TestClient):
    curso_id = _preparar_curso(cliente, slug="pds-t7-n", email="profe.t7n@gmail.com")
    tarea = _crear_tarea(cliente, curso_id)
    entrega_id = tarea["entregas"][0]["id"]
    respuesta = cliente.delete(f"/api/cursos/{curso_id}/tareas/{tarea['id']}/entregas/{entrega_id}")
    assert respuesta.status_code == 200, respuesta.text
    detalle = respuesta.json()
    assert detalle["entregas"] == []
    assert detalle["activar"]["habilitada"] is False
