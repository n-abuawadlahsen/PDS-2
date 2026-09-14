"""SPEC 07 S7.4-S7.8 (Etapa P6): mapeo estudiante <-> GitHub y Pendientes,
con Canvas y GitHub en modo doble (backend/.env: CANVAS_MODO=doble,
GITHUB_MODO=doble)."""

from __future__ import annotations

import secrets
import uuid

from fastapi.testclient import TestClient

from app.adaptadores import trabajos_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.adaptadores.modelos_mapeo import MapeoGithub
from app.adaptadores.modelos_padron import Estudiante
from app.api.dependencias import hash_token
from app.dominio.estados import EstadoMapeoGithub
from app.trabajos import (  # noqa: F401 (registra los manejadores)
    aprovisionar_repositorios,
    materializar_sujetos,
    recolector_mapeos,
    registro,
    sync_grupos,
    sync_roster,
    sync_tareas_y_fechas,
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


def _sincronizar_ahora(cliente: TestClient, curso_id: str) -> None:
    respuesta = cliente.post(f"/api/cursos/{curso_id}/sincronizaciones")
    assert respuesta.status_code == 202, respuesta.text
    _ejecutar_trabajos_pendientes()


def _preparar_curso_con_roster(cliente: TestClient, *, slug: str, email: str) -> dict:
    token = _crear_usuario_con_sesion(email=email)
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug=slug)
    _vincular_canvas(cliente, curso["id"])
    _sincronizar_ahora(cliente, curso["id"])
    return curso


def _ejecutar_recolector_mapeos(curso_id: str) -> None:
    with fabrica_bd()() as bd:
        trabajos_repo.encolar(
            bd,
            tipo="recolector_mapeos",
            clave_idempotencia=f"recolector:{curso_id}:{ahora_utc().isoformat()}",
            max_intentos=1,
            curso_id=uuid.UUID(curso_id),
        )
        bd.commit()
    _ejecutar_trabajos_pendientes()


def _estudiante_por_nombre(bd, curso_id: str, nombre: str) -> Estudiante:
    return (
        bd.query(Estudiante)
        .filter(Estudiante.curso_id == uuid.UUID(curso_id), Estudiante.nombre == nombre)
        .one()
    )


def test_recolector_mapeos_procesa_las_cuatro_entregas_fijas(cliente: TestClient):
    """S7.4.1, S7.6.1: el fixture del doble cubre VIGENTE x2 (cuentas
    distintas), NO_EXISTE, NO_RESUELTO y SIN_DATO (quien no entrega nada)."""
    curso = _preparar_curso_con_roster(cliente, slug="pds-mapeo-1", email="profe.mapeo1@gmail.com")
    respuesta = cliente.post(f"/api/cursos/{curso['id']}/registro-github")
    assert respuesta.status_code == 200, respuesta.text

    _ejecutar_recolector_mapeos(curso["id"])

    personas = cliente.get(f"/api/cursos/{curso['id']}/personas")
    assert personas.status_code == 200, personas.text
    por_nombre = {e["nombre"]: e for e in personas.json()["estudiantes"]}

    assert por_nombre["Ana Soto"]["mapeo"]["estado"] == EstadoMapeoGithub.VIGENTE.value
    assert por_nombre["Ana Soto"]["mapeo"]["cuenta_login"] == "Estudiante-Valido"
    assert por_nombre["Bruno Diaz"]["mapeo"]["estado"] == EstadoMapeoGithub.VIGENTE.value
    assert por_nombre["Bruno Diaz"]["mapeo"]["cuenta_login"] == "Estudiante-Valido-2"
    assert por_nombre["Carla Reyes"]["mapeo"]["estado"] == EstadoMapeoGithub.NO_EXISTE.value
    assert por_nombre["Diego Vera"]["mapeo"]["estado"] == EstadoMapeoGithub.NO_RESUELTO.value
    assert por_nombre["Elena Rojas"]["mapeo"]["estado"] == EstadoMapeoGithub.SIN_DATO.value

    cabecera = cliente.get(f"/api/cursos/{curso['id']}/personas/cabecera")
    assert cabecera.json() == {"con_cuenta_verificada": 2, "total": 5}


def test_recolector_mapeos_es_idempotente_entre_ciclos(cliente: TestClient):
    """S7.4.1: reenviar la misma entrega sin cambios no crea una fila nueva."""
    curso = _preparar_curso_con_roster(cliente, slug="pds-mapeo-2", email="profe.mapeo2@gmail.com")
    cliente.post(f"/api/cursos/{curso['id']}/registro-github")
    _ejecutar_recolector_mapeos(curso["id"])
    _ejecutar_recolector_mapeos(curso["id"])

    with fabrica_bd()() as bd:
        ana = _estudiante_por_nombre(bd, curso["id"], "Ana Soto")
        cantidad = bd.query(MapeoGithub).filter(MapeoGithub.estudiante_id == ana.id).count()
        assert cantidad == 1


def test_declarar_mapeo_manual_camino_feliz(cliente: TestClient):
    """Via 2 (S7.4.3)."""
    curso = _preparar_curso_con_roster(cliente, slug="pds-mapeo-3", email="profe.mapeo3@gmail.com")
    with fabrica_bd()() as bd:
        elena = _estudiante_por_nombre(bd, curso["id"], "Elena Rojas")

    respuesta = cliente.post(
        f"/api/cursos/{curso['id']}/personas/{elena.id}/mapeo",
        json={"login": "estudiante-valido"},
    )
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == EstadoMapeoGithub.VIGENTE.value
    assert cuerpo["cuenta_login"] == "Estudiante-Valido"


def test_declarar_mapeo_manual_rechaza_organizacion(cliente: TestClient):
    """S7.5.3 "puerta del docente": rechazo inmediato, 422, sin persistir."""
    curso = _preparar_curso_con_roster(cliente, slug="pds-mapeo-4", email="profe.mapeo4@gmail.com")
    with fabrica_bd()() as bd:
        elena = _estudiante_por_nombre(bd, curso["id"], "Elena Rojas")

    respuesta = cliente.post(
        f"/api/cursos/{curso['id']}/personas/{elena.id}/mapeo",
        json={"login": "org-valida"},
    )
    assert respuesta.status_code == 422, respuesta.text
    assert respuesta.json()["detail"]["motivo"] == "ES_ORGANIZACION"

    with fabrica_bd()() as bd:
        mapeo = (
            bd.query(MapeoGithub)
            .filter(MapeoGithub.estudiante_id == elena.id, MapeoGithub.estado != "SUPERSEDIDO")
            .one()
        )
        assert mapeo.estado == EstadoMapeoGithub.SIN_DATO.value


def test_declarar_mapeo_manual_rechaza_cuenta_ya_asignada(cliente: TestClient):
    """S7.6.3: la puerta del docente rechaza de inmediato una cuenta que ya
    esta VIGENTE para otro estudiante del mismo curso."""
    curso = _preparar_curso_con_roster(cliente, slug="pds-mapeo-5", email="profe.mapeo5@gmail.com")
    with fabrica_bd()() as bd:
        ana = _estudiante_por_nombre(bd, curso["id"], "Ana Soto")
        elena = _estudiante_por_nombre(bd, curso["id"], "Elena Rojas")

    primero = cliente.post(
        f"/api/cursos/{curso['id']}/personas/{ana.id}/mapeo",
        json={"login": "estudiante-valido"},
    )
    assert primero.status_code == 200, primero.text

    segundo = cliente.post(
        f"/api/cursos/{curso['id']}/personas/{elena.id}/mapeo",
        json={"login": "estudiante-valido"},
    )
    assert segundo.status_code == 422, segundo.text
    assert segundo.json()["detail"]["motivo"] == "CUENTA_YA_ASIGNADA"


def test_importar_csv_preview_no_escribe_nada(cliente: TestClient):
    curso = _preparar_curso_con_roster(cliente, slug="pds-mapeo-6", email="profe.mapeo6@gmail.com")
    with fabrica_bd()() as bd:
        ana = _estudiante_por_nombre(bd, curso["id"], "Ana Soto")

    csv_texto = f"canvas_user_id,github_login\n{ana.canvas_user_id},estudiante-valido\n"
    respuesta = cliente.post(
        f"/api/cursos/{curso['id']}/mapeo/importar-csv",
        json={"csv": csv_texto},
    )
    assert respuesta.status_code == 200, respuesta.text
    filas = respuesta.json()["filas"]
    assert len(filas) == 1
    assert filas[0]["resultado"] == "SE_APLICARIA"

    with fabrica_bd()() as bd:
        mapeo = (
            bd.query(MapeoGithub)
            .filter(MapeoGithub.estudiante_id == ana.id, MapeoGithub.estado != "SUPERSEDIDO")
            .one()
        )
        assert mapeo.estado == EstadoMapeoGithub.SIN_DATO.value


def test_importar_csv_aplica_validas_y_reporta_la_invalida(cliente: TestClient):
    """CA-7.7-03 (resumido en la vista): "una fila invalida entre validas
    aplica las validas y reporta la invalida, nunca rechaza el archivo entero"."""
    curso = _preparar_curso_con_roster(cliente, slug="pds-mapeo-7", email="profe.mapeo7@gmail.com")
    with fabrica_bd()() as bd:
        ana = _estudiante_por_nombre(bd, curso["id"], "Ana Soto")

    csv_texto = (
        "canvas_user_id,github_login\n"
        f"{ana.canvas_user_id},estudiante-valido\n"
        "999999,estudiante-valido-2\n"
    )
    respuesta = cliente.post(
        f"/api/cursos/{curso['id']}/mapeo/importar-csv",
        json={"csv": csv_texto, "aplicar": "true"},
    )
    assert respuesta.status_code == 200, respuesta.text
    filas = respuesta.json()["filas"]
    assert {f["resultado"] for f in filas} == {"APLICADA", "INVALIDA"}

    with fabrica_bd()() as bd:
        mapeo = (
            bd.query(MapeoGithub)
            .filter(MapeoGithub.estudiante_id == ana.id, MapeoGithub.estado != "SUPERSEDIDO")
            .one()
        )
        assert mapeo.estado == EstadoMapeoGithub.VIGENTE.value


def test_pendientes_bloque_1_incluye_todo_lo_no_vigente(cliente: TestClient):
    """CA-7.8-01: "sin excepcion"."""
    curso = _preparar_curso_con_roster(cliente, slug="pds-mapeo-8", email="profe.mapeo8@gmail.com")
    cliente.post(f"/api/cursos/{curso['id']}/registro-github")
    _ejecutar_recolector_mapeos(curso["id"])

    pendientes = cliente.get(f"/api/cursos/{curso['id']}/pendientes")
    assert pendientes.status_code == 200, pendientes.text
    cuerpo = pendientes.json()

    nombres_bloque_1 = {f["nombre"] for f in cuerpo["bloque_1_sin_cuenta"]}
    # Carla (NO_EXISTE), Diego (NO_RESUELTO) y Elena (SIN_DATO) no estan VIGENTE.
    assert nombres_bloque_1 == {"Carla Reyes", "Diego Vera", "Elena Rojas"}
    assert cuerpo["bloque_4_invitaciones_sin_aceptar"] == []


def test_pendientes_bloque_2_incluye_conflicto(cliente: TestClient):
    curso = _preparar_curso_con_roster(cliente, slug="pds-mapeo-9", email="profe.mapeo9@gmail.com")
    with fabrica_bd()() as bd:
        ana = _estudiante_por_nombre(bd, curso["id"], "Ana Soto")
        elena = _estudiante_por_nombre(bd, curso["id"], "Elena Rojas")

    cliente.post(
        f"/api/cursos/{curso['id']}/personas/{ana.id}/mapeo",
        json={"login": "estudiante-valido"},
    )
    # Via la ingesta (recolector), no la puerta del docente: no lanza, persiste EN_CONFLICTO.
    with fabrica_bd()() as bd:
        from app.adaptadores import mapeo_github_repo
        from app.adaptadores.cliente_github import ClienteGitHubDoble
        from app.adaptadores.modelos_padron import Estudiante as EstudianteModelo

        elena_bd = bd.query(EstudianteModelo).filter(EstudianteModelo.id == elena.id).one()
        mapeo_github_repo.procesar_candidato(
            bd,
            ClienteGitHubDoble(),
            curso_id=uuid.UUID(curso["id"]),
            estudiante=elena_bd,
            login="estudiante-valido",
            texto_crudo="@estudiante-valido",
            origen="AUTOSERVICIO_CANVAS",
            es_puerta_docente=False,
        )
        bd.commit()

    pendientes = cliente.get(f"/api/cursos/{curso['id']}/pendientes")
    nombres_bloque_2 = {f["nombre"] for f in pendientes.json()["bloque_2_en_conflicto"]}
    assert nombres_bloque_2 == {"Ana Soto", "Elena Rojas"}
