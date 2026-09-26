"""Etapa F7 (SPEC 10 S10.9): timeline de un repositorio de punta a punta, con
Canvas y GitHub en modo doble."""

from __future__ import annotations

import uuid
from datetime import timedelta
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_github import agregar_commit_doble, reescribir_historia_doble
from app.adaptadores.modelos_github import AccesoDocenteRepositorio
from app.trabajos import agregar_metricas, barrido_completo_actividad  # noqa: F401
from tests.api.test_actividad import _cabeza, _enviar, _push, _trabajar
from tests.api.test_aprovisionamiento import (
    _encolar_y_ejecutar,
    _preparar_curso_con_tarea_activa,
    _sesion_autenticada,
)
from tests.api.test_aprovisionamiento_grupal import _activar, _preparar_tarea_grupal
from tests.api.test_tablero import _aceptar, _metricas, _retrodatar
from tests.api.test_versiones import _ayudante_con_tarea_administrar
from tests.apoyo import fabrica_bd

_ORG = "org-valida"
_ANA, _BRUNO = 70001, 70002


def _timeline(cliente: TestClient, curso_id: str, tarea_id: str, repo_id: uuid.UUID, **params):
    respuesta = cliente.get(
        f"/api/cursos/{curso_id}/tareas/{tarea_id}/repos/{repo_id}/timeline", params=params
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta


def _commits(datos: dict) -> list[dict]:
    return [c for d in datos["dias"] for c in d["commits"]]


def test_ca_10_9_01_historia_reescrita_huerfanos_y_evento(cliente: TestClient):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f7-a", email="f7a@gmail.com"
    )
    repos = _retrodatar(curso_id)
    ana = repos[2001]
    for i in range(3):
        agregar_commit_doble(
            _ORG,
            ana.nombre,
            fecha=ahora_utc() - timedelta(hours=3 - i),
            mensaje=f"c{i}",
            autor_github_user_id=_ANA,
        )
    _metricas(curso_id)
    vieja = _cabeza(ana)
    reescribir_historia_doble(_ORG, ana.nombre, quitar=2)
    nueva = agregar_commit_doble(
        _ORG, ana.nombre, fecha=ahora_utc(), mensaje="rehecho", autor_github_user_id=_ANA
    )
    _enviar(cliente, "push", _push(ana, before=vieja, after=nueva, commits=[], forced=True))
    _trabajar()
    datos = _timeline(cliente, curso_id, tarea_id, ana.id, periodo="todo").json()
    huerfanos = [c for c in _commits(datos) if c["etiqueta_exclusion"] == "HUERFANO"]
    assert len(huerfanos) == 2  # se muestran, con su etiqueta
    reescrita = [e for e in datos["ciclo_de_vida"] if e["tipo"] == "HISTORIA_REESCRITA"]
    assert reescrita and reescrita[0]["detalle"]["n_commits_huerfanos"] == 2
    assert reescrita[0]["detalle"]["before"] == vieja
    # El commit inicial se muestra con su etiqueta y no cuenta.
    assert any(c["etiqueta_exclusion"] == "COMMIT_INICIAL" for c in _commits(datos))


def test_ca_10_9_02_tramos_sin_actividad_se_colapsan_sin_perder_commits(cliente: TestClient):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f7-b", email="f7b@gmail.com"
    )
    repos = _retrodatar(curso_id, dias=12)
    ana = repos[2001]
    ahora = ahora_utc()
    agregar_commit_doble(
        _ORG,
        ana.nombre,
        fecha=ahora - timedelta(days=10),
        mensaje="antes",
        autor_github_user_id=_ANA,
    )
    agregar_commit_doble(
        _ORG,
        ana.nombre,
        fecha=ahora - timedelta(days=1),
        mensaje="despues",
        autor_github_user_id=_ANA,
    )
    _metricas(curso_id)
    datos = _timeline(cliente, curso_id, tarea_id, ana.id, periodo="todo").json()
    colapsados = [d for d in datos["dias"] if d["colapsado"]]
    assert any(d["n_dias"] >= 3 for d in colapsados)
    todos = {c["mensaje"] for c in _commits(datos)}
    assert {"antes", "despues"} <= todos  # nada se pierde al colapsar
    vuelta = next(c for c in _commits(datos) if c["mensaje"] == "despues")
    assert vuelta["destacado"].startswith("vuelta al trabajo tras")
    primera = next(c for c in _commits(datos) if c["mensaje"] == "antes")
    assert primera["destacado"] == "primera participación de Ana Soto"


def test_ca_10_9_03_franja_coincide_con_la_comparacion_del_tablero(cliente: TestClient):
    curso_id, tarea_id = _preparar_tarea_grupal(cliente, slug="pds-f7-c", email="f7c@gmail.com")
    _activar(cliente, curso_id, tarea_id)
    repos = _retrodatar(curso_id)
    grupo = repos["Grupo 1"]
    _aceptar(grupo)
    # Los tres el mismo dia del curso, sin importar a que hora corra la prueba.
    ayer = (ahora_utc().astimezone(ZoneInfo("America/Santiago")) - timedelta(days=1)).replace(
        hour=12, minute=0, second=0, microsecond=0
    )
    for i in range(3):
        agregar_commit_doble(
            _ORG,
            grupo.nombre,
            fecha=ayer + timedelta(minutes=i),
            mensaje=f"ana {i}",
            autor_github_user_id=_ANA,
        )
    _metricas(curso_id)
    tablero = cliente.get(f"/api/cursos/{curso_id}/tareas/{tarea_id}/tablero").json()
    fila = next(f for f in tablero["filas"] if f["sujeto"] == "Grupo 1")
    comparacion = {i["nombre"]: (i["commits"], i["dias_activos"]) for i in fila["integrantes"]}
    datos = _timeline(cliente, curso_id, tarea_id, grupo.id, periodo=tablero["periodo"]).json()
    tramo = next(t for t in datos["franja"] if t["periodo"] == tablero["periodo"])
    franja = {i["nombre"]: (i["commits"], i["dias_activos"]) for i in tramo["integrantes"]}
    assert franja == comparacion == {"Ana Soto": (3, 1), "Bruno Diaz": (0, 0)}
    # CA-10.9-04: el cero va con su causa, nunca solo.
    bruno = next(i for i in tramo["integrantes"] if i["nombre"] == "Bruno Diaz")
    assert bruno["causa"] == "SIN_COMMITS"


def test_ca_10_9_05_hitos_manuales_con_permiso(cliente: TestClient):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f7-d", email="f7d@gmail.com"
    )
    repos = _retrodatar(curso_id)
    ana = repos[2001]
    sha = agregar_commit_doble(
        _ORG, ana.nombre, fecha=ahora_utc(), mensaje="entrega casi lista", autor_github_user_id=_ANA
    )
    _metricas(curso_id)
    base = f"/api/cursos/{curso_id}/tareas/{tarea_id}/repos/{ana.id}/commits/{sha}/hito"
    largo = cliente.post(base, json={"nota": "x" * 141})
    assert largo.status_code == 422
    assert cliente.post(base, json={"nota": "Primera versión funcional"}).status_code == 200
    datos = _timeline(cliente, curso_id, tarea_id, ana.id, periodo="todo").json()
    commit = next(c for c in _commits(datos) if c["sha"] == sha)
    assert commit["hito"] == "Primera versión funcional"
    assert cliente.delete(base).status_code == 200
    datos = _timeline(cliente, curso_id, tarea_id, ana.id, periodo="todo").json()
    assert next(c for c in _commits(datos) if c["sha"] == sha)["hito"] is None

    _sesion_autenticada(cliente, _ayudante_con_tarea_administrar(curso_id))
    assert cliente.post(base, json={"nota": "del ayudante"}).status_code == 200  # tiene el permiso


def test_ca_10_9_06_sin_acceso_docente_no_hay_enlace_sino_motivo(cliente: TestClient):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f7-e", email="f7e@gmail.com"
    )
    repos = _retrodatar(curso_id)
    ana = repos[2001]
    agregar_commit_doble(
        _ORG, ana.nombre, fecha=ahora_utc(), mensaje="x", autor_github_user_id=_ANA
    )
    _metricas(curso_id)
    datos = _timeline(cliente, curso_id, tarea_id, ana.id, periodo="todo").json()
    assert all(c["url"] for c in _commits(datos))
    assert datos["enlaces"]["motivo"] is None
    with fabrica_bd()() as bd:
        acceso = (
            bd.query(AccesoDocenteRepositorio)
            .filter(AccesoDocenteRepositorio.repositorio_id == ana.id)
            .one()
        )
        acceso.estado = "PENDIENTE"
        bd.commit()
    respuesta = _timeline(cliente, curso_id, tarea_id, ana.id, periodo="todo")
    assert respuesta.headers["X-Llamadas-Externas"] == "0"
    datos = respuesta.json()
    assert all(c["url"] is None for c in _commits(datos))
    assert "Preparando tu acceso" in datos["enlaces"]["motivo"]


def test_repositorio_sin_commits_muestra_la_causa(cliente: TestClient):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f7-f", email="f7f@gmail.com"
    )
    repos = _retrodatar(curso_id)
    _metricas(curso_id)
    datos = _timeline(cliente, curso_id, tarea_id, repos[2002].id).json()
    assert datos["sin_commits_contables"] is True
    assert datos["causa_vacia"] in {
        "SIN_ACCESO",
        "SIN_ATRIBUIR",
        "SIN_COMMITS",
        "SIN_DATOS_TODAVIA",
    }
    _encolar_y_ejecutar("agregar_metricas", curso_id)
