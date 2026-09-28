"""Etapa F1 (SPEC 08 S8.5, S8.8.2-S8.8.3; SPEC 09 S9.3.3): modalidad grupal de
punta a punta, con Canvas y GitHub en modo doble.

El padron del doble: Grupo 1 (601) = Ana Soto (2001) y Bruno Diaz (2002), los
dos con mapeo VIGENTE tras el recolector; Grupo 2 (602) = Carla Reyes (2003) y
Diego Vera (2004), sin mapeo; Elena Rojas (2005) sin grupo."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_github import aceptar_invitacion_doble
from app.adaptadores.modelos_aprovisionamiento import (
    AccesoRepositorio,
    FechaEfectiva,
    Repositorio,
    Sujeto,
)
from app.adaptadores.modelos_padron import Estudiante, Grupo, PertenenciaGrupo
from app.adaptadores.modelos_tarea import Tarea
from tests.api.test_aprovisionamiento import (
    _crear_usuario_con_sesion,
    _ejecutar_trabajos_pendientes,
    _encolar_y_ejecutar,
    _sesion_autenticada,
    _sincronizar,
)
from tests.apoyo import fabrica_bd

_BASE_URL_DOBLE = "https://canvas-doble.local"
_ORG = "org-valida"


def _preparar_tarea_grupal(cliente: TestClient, *, slug: str, email: str) -> tuple[str, str]:
    _sesion_autenticada(cliente, _crear_usuario_con_sesion(email=email))
    curso = cliente.post(
        "/api/cursos",
        json={
            "nombre": "Desarrollo de Software",
            "codigo": "ICC4201",
            "periodo": "2026-2",
            "slug": slug,
            "zona_horaria": "America/Santiago",
        },
    )
    assert curso.status_code == 200, curso.text
    curso_id = curso.json()["id"]
    assert (
        cliente.post(
            f"/api/cursos/{curso_id}/vinculacion/canvas",
            json={"token": "valido", "canvas_base_url": _BASE_URL_DOBLE, "canvas_course_id": 5001},
        ).status_code
        == 200
    )
    iniciar = cliente.post(f"/api/cursos/{curso_id}/vinculacion/github/iniciar", json={})
    state = iniciar.json()["instalar_url"].split("state=", 1)[1]
    assert (
        cliente.post(
            "/api/vinculacion/github/callback",
            json={"state": state, "installation_id": 8001, "setup_action": "install"},
        ).status_code
        == 200
    )
    _sincronizar(cliente, curso_id)
    assert cliente.post(f"/api/cursos/{curso_id}/registro-github").status_code == 200
    _encolar_y_ejecutar("recolector_mapeos", curso_id)

    tarea = cliente.post(
        f"/api/cursos/{curso_id}/tareas",
        json={"nombre": "Compilador", "slug": "t2", "canvas_assignment_id": 9102},
    )
    assert tarea.status_code == 200, tarea.text
    assert tarea.json()["modalidad"] == "GRUPAL"
    tarea_id = tarea.json()["id"]
    _sincronizar(cliente, curso_id)
    return curso_id, tarea_id


def _activar(cliente: TestClient, curso_id: str, tarea_id: str) -> None:
    activada = cliente.post(f"/api/cursos/{curso_id}/tareas/{tarea_id}/activar")
    assert activada.status_code == 200, activada.text
    _ejecutar_trabajos_pendientes()


def _filas(cliente: TestClient, curso_id: str, tarea_id: str) -> dict[str, dict]:
    respuesta = cliente.get(f"/api/cursos/{curso_id}/tareas/{tarea_id}/repositorios")
    assert respuesta.status_code == 200, respuesta.text
    return {f["sujeto"]: f for f in respuesta.json()["filas"]}


def test_f1_la_tarea_grupal_ya_no_esta_deshabilitada(cliente: TestClient):
    curso_id, tarea_id = _preparar_tarea_grupal(cliente, slug="pds-f1-a", email="f1a@gmail.com")
    with fabrica_bd()() as bd:
        tarea = bd.get(Tarea, uuid.UUID(tarea_id))
        assert tarea is not None and tarea.conjunto_grupos_id is not None
    detalle = cliente.get(f"/api/cursos/{curso_id}/tareas/{tarea_id}").json()
    assert detalle["activar"]["motivo"] is None


def test_f1_repositorio_de_grupo_con_todos_sus_integrantes_llega_a_operativo(cliente: TestClient):
    curso_id, tarea_id = _preparar_tarea_grupal(cliente, slug="pds-f1-b", email="f1b@gmail.com")
    _activar(cliente, curso_id, tarea_id)

    filas = _filas(cliente, curso_id, tarea_id)
    assert set(filas) == {"Grupo 1", "Grupo 2"}
    grupo1 = filas["Grupo 1"]
    assert grupo1["sujeto_tipo"] == "GRUPO"
    assert grupo1["nombre"] == "pds-f1-b-t2-g601-grupo-1"
    assert grupo1["estado"] == "DEGRADADO"
    assert grupo1["motivo"] == "FALTA_ACEPTAR_INVITACION_GITHUB"
    integrantes = {i["nombre"]: i for i in grupo1["integrantes"]}
    assert set(integrantes) == {"Ana Soto", "Bruno Diaz"}
    assert {i["acceso_estado"] for i in integrantes.values()} == {"INVITADO"}
    # Grupo 2: nadie tiene cuenta -> espera con motivo, sin repositorio.
    assert filas["Grupo 2"]["estado"] == "ESPERANDO_INFORMACION"
    assert filas["Grupo 2"]["motivo"] == "SIN_MAPEO_GITHUB"

    # La fecha del sujeto grupal quedo materializada (S9.3.3): sin ella no sale
    # el aviso de R2.3.12.
    with fabrica_bd()() as bd:
        repo = bd.query(Repositorio).filter(Repositorio.id == grupo1["repositorio_id"]).one()
        assert bd.query(FechaEfectiva).filter(FechaEfectiva.sujeto_id == repo.sujeto_id).count()

    aceptar_invitacion_doble(_ORG, grupo1["nombre"], "Estudiante-Valido")
    aceptar_invitacion_doble(_ORG, grupo1["nombre"], "Estudiante-Valido-2")
    _encolar_y_ejecutar("reconciliar_accesos", curso_id)
    grupo1 = _filas(cliente, curso_id, tarea_id)["Grupo 1"]
    assert grupo1["estado"] == "OPERATIVO"
    assert {i["acceso_estado"] for i in grupo1["integrantes"]} == {"ACEPTADO"}


def test_f1_basta_un_integrante_mapeado_y_los_demas_se_incorporan(cliente: TestClient):
    curso_id, tarea_id = _preparar_tarea_grupal(cliente, slug="pds-f1-c", email="f1c@gmail.com")
    # Elena Rojas (sin cuenta) entra a Grupo 1: 2 de 3 con mapeo vigente.
    with fabrica_bd()() as bd:
        elena = bd.query(Estudiante).filter(Estudiante.canvas_user_id == 2005).one()
        grupo1 = bd.query(Grupo).filter(Grupo.canvas_group_id == 601).one()
        bd.add(
            PertenenciaGrupo(
                grupo_id=grupo1.id,
                estudiante_id=elena.id,
                workflow_state="accepted",
                activa=True,
                activa_desde=ahora_utc(),
                ciclos_ausente=0,
                sincronizado_en=ahora_utc(),
            )
        )
        bd.commit()
    _activar(cliente, curso_id, tarea_id)
    grupo1 = _filas(cliente, curso_id, tarea_id)["Grupo 1"]
    assert grupo1["url_html"] is not None  # CA-8.5-01: el repositorio existe
    integrantes = {i["nombre"]: i["acceso_estado"] for i in grupo1["integrantes"]}
    assert integrantes == {
        "Ana Soto": "INVITADO",
        "Bruno Diaz": "INVITADO",
        "Elena Rojas": "SIN_MAPEO",
    }


def test_f1_estudiante_en_dos_grupos_no_frena_a_los_demas(cliente: TestClient):
    curso_id, tarea_id = _preparar_tarea_grupal(cliente, slug="pds-f1-d", email="f1d@gmail.com")
    # Diego Vera (2004) tambien aparece en un tercer grupo del mismo conjunto.
    with fabrica_bd()() as bd:
        grupo2 = bd.query(Grupo).filter(Grupo.canvas_group_id == 602).one()
        diego = bd.query(Estudiante).filter(Estudiante.canvas_user_id == 2004).one()
        grupo3 = Grupo(
            curso_id=grupo2.curso_id,
            conjunto_grupos_id=grupo2.conjunto_grupos_id,
            canvas_group_id=603,
            nombre="Grupo 3",
            slug="grupo-3",
            sincronizado_en=ahora_utc(),
        )
        bd.add(grupo3)
        bd.flush()
        bd.add(
            PertenenciaGrupo(
                grupo_id=grupo3.id,
                estudiante_id=diego.id,
                workflow_state="accepted",
                activa=True,
                activa_desde=ahora_utc(),
                ciclos_ausente=0,
                sincronizado_en=ahora_utc(),
            )
        )
        bd.commit()
    _activar(cliente, curso_id, tarea_id)
    filas = _filas(cliente, curso_id, tarea_id)
    assert filas["Grupo 1"]["url_html"] is not None
    assert filas["Grupo 2"]["motivo"] == "ESTUDIANTE_EN_DOS_GRUPOS"
    assert filas["Grupo 3"]["motivo"] == "ESTUDIANTE_EN_DOS_GRUPOS"


def test_f1_salida_de_un_integrante_no_revoca_su_acceso(cliente: TestClient, monkeypatch):
    from app.adaptadores.cliente_github import ClienteGitHubDoble

    def _prohibido(*_args, **_kwargs):
        raise AssertionError("la revocacion nunca se ejecuta sola (A-212)")

    monkeypatch.setattr(ClienteGitHubDoble, "quitar_colaborador_repo", _prohibido)
    curso_id, tarea_id = _preparar_tarea_grupal(cliente, slug="pds-f1-e", email="f1e@gmail.com")
    _activar(cliente, curso_id, tarea_id)
    nombre = _filas(cliente, curso_id, tarea_id)["Grupo 1"]["nombre"]
    aceptar_invitacion_doble(_ORG, nombre, "Estudiante-Valido")
    aceptar_invitacion_doble(_ORG, nombre, "Estudiante-Valido-2")
    _encolar_y_ejecutar("reconciliar_accesos", curso_id)

    # sync_grupos ya confirmo en dos ciclos que Bruno salio del grupo.
    with fabrica_bd()() as bd:
        bruno = bd.query(Estudiante).filter(Estudiante.canvas_user_id == 2002).one()
        pertenencia = (
            bd.query(PertenenciaGrupo).filter(PertenenciaGrupo.estudiante_id == bruno.id).one()
        )
        pertenencia.activa = False
        pertenencia.activa_hasta = ahora_utc()
        bd.commit()
    _encolar_y_ejecutar("materializar_sujetos", curso_id)
    _encolar_y_ejecutar("reconciliar_accesos", curso_id)

    grupo1 = _filas(cliente, curso_id, tarea_id)["Grupo 1"]
    with fabrica_bd()() as bd:
        accesos = {
            a.estudiante_id: a.estado
            for a in bd.query(AccesoRepositorio).filter(
                AccesoRepositorio.repositorio_id == uuid.UUID(grupo1["repositorio_id"])
            )
        }
        assert accesos[bruno.id] == "REVOCACION_PROPUESTA"
        sujeto = bd.query(Sujeto).filter(Sujeto.grupo_id.isnot(None)).first()
        assert sujeto is not None
    # El predicado solo mira a los integrantes actuales: Ana sigue con acceso.
    assert grupo1["estado"] == "OPERATIVO"
    assert [i["nombre"] for i in grupo1["integrantes"]] == ["Ana Soto"]


def test_f1_integrante_invitado_en_canvas_degrada_hasta_que_desaparece(cliente: TestClient):
    curso_id, tarea_id = _preparar_tarea_grupal(cliente, slug="pds-f1-f", email="f1f@gmail.com")
    with fabrica_bd()() as bd:
        elena = bd.query(Estudiante).filter(Estudiante.canvas_user_id == 2005).one()
        grupo1 = bd.query(Grupo).filter(Grupo.canvas_group_id == 601).one()
        bd.add(
            PertenenciaGrupo(
                grupo_id=grupo1.id,
                estudiante_id=elena.id,
                workflow_state="invited",
                activa=False,
                activa_desde=ahora_utc(),
                ciclos_ausente=0,
                sincronizado_en=ahora_utc(),
            )
        )
        bd.commit()
    _activar(cliente, curso_id, tarea_id)
    nombre = _filas(cliente, curso_id, tarea_id)["Grupo 1"]["nombre"]
    aceptar_invitacion_doble(_ORG, nombre, "Estudiante-Valido")
    aceptar_invitacion_doble(_ORG, nombre, "Estudiante-Valido-2")
    _encolar_y_ejecutar("reconciliar_accesos", curso_id)
    grupo1 = _filas(cliente, curso_id, tarea_id)["Grupo 1"]
    assert grupo1["motivo"] == "INTEGRANTE_PENDIENTE_EN_CANVAS"

    # Canvas ya no la trae como invitada: sync_grupos la envejece y deja de pesar.
    _encolar_y_ejecutar("sync_grupos", curso_id)
    _encolar_y_ejecutar("reconciliar_accesos", curso_id)
    assert _filas(cliente, curso_id, tarea_id)["Grupo 1"]["estado"] == "OPERATIVO"
