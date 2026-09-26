"""Etapa F6 (SPEC 10 S10.4-S10.8, S10.10): tablero, alertas y comparacion de
punta a punta, con Canvas y GitHub en modo doble."""

from __future__ import annotations

import uuid
from datetime import timedelta

from fastapi.testclient import TestClient

from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_github import agregar_commit_doble, retrodatar_repo_doble
from app.adaptadores.modelos_aprovisionamiento import AccesoRepositorio, Repositorio, Sujeto
from app.adaptadores.modelos_infraestructura import Bitacora, Incidencia
from app.adaptadores.modelos_metricas import (
    MetricaRepositorioDia,
    ParticipacionEntrega,
    ResumenTarea,
)
from app.adaptadores.modelos_padron import Estudiante, Grupo, PertenenciaGrupo
from app.trabajos import (  # noqa: F401 (registra los manejadores)
    agregar_metricas,
    barrido_completo_actividad,
    reconciliar_actividad,
)
from tests.api.test_aprovisionamiento import (
    _encolar_y_ejecutar,
    _preparar_curso_con_tarea_activa,
)
from tests.api.test_aprovisionamiento_grupal import _activar, _preparar_tarea_grupal
from tests.apoyo import fabrica_bd

_ORG = "org-valida"
_ANA, _BRUNO = 70001, 70002


def _retrodatar(curso_id: str, dias: int = 10) -> dict[int | str, Repositorio]:
    """Los repositorios del curso existen desde hace `dias` dias."""
    hace = ahora_utc() - timedelta(days=dias)
    claves: dict[uuid.UUID, int | str] = {}
    with fabrica_bd()() as bd:
        for repo in bd.query(Repositorio).filter(Repositorio.curso_id == uuid.UUID(curso_id)):
            sujeto = bd.get(Sujeto, repo.sujeto_id)
            assert sujeto is not None
            sujeto.creado_en = hace
            repo.creado_en = hace
            if repo.github_repo_id is not None:
                repo.listo_en = hace
                retrodatar_repo_doble(_ORG, repo.nombre, hace)
                if sujeto.estudiante_id:
                    claves[repo.id] = bd.get(Estudiante, sujeto.estudiante_id).canvas_user_id  # type: ignore[union-attr]
                else:
                    claves[repo.id] = bd.get(Grupo, sujeto.grupo_id).nombre  # type: ignore[union-attr]
        for pg in (
            bd.query(PertenenciaGrupo)
            .join(Grupo, Grupo.id == PertenenciaGrupo.grupo_id)
            .filter(Grupo.curso_id == uuid.UUID(curso_id))
        ):
            pg.activa_desde = hace
        bd.commit()
    with fabrica_bd()() as bd:
        salida: dict[int | str, Repositorio] = {}
        for repo in bd.query(Repositorio).filter(Repositorio.id.in_(list(claves))):
            bd.expunge(repo)
            salida[claves[repo.id]] = repo
        return salida


def _metricas(curso_id: str) -> None:
    _encolar_y_ejecutar("barrido_completo_actividad", curso_id)
    _encolar_y_ejecutar("agregar_metricas", curso_id)


def _aceptar(repo: Repositorio) -> None:
    with fabrica_bd()() as bd:
        for a in bd.query(AccesoRepositorio).filter(AccesoRepositorio.repositorio_id == repo.id):
            a.estado = "ACEPTADO"
        bd.commit()


def _incidencias(curso_id: str, tipo: str) -> list[Incidencia]:
    with fabrica_bd()() as bd:
        filas = (
            bd.query(Incidencia)
            .filter(Incidencia.curso_id == uuid.UUID(curso_id), Incidencia.tipo == tipo)
            .all()
        )
        for f in filas:
            bd.expunge(f)
        return filas


def _foto(curso_id: str) -> list[tuple]:
    with fabrica_bd()() as bd:
        return sorted(
            [
                ("dia", str(m.id), m.commits, m.dias_activos_acumulados)
                for m in bd.query(MetricaRepositorioDia)
            ]
            + [
                ("part", str(p.id), p.commits, p.dias_activos)
                for p in bd.query(ParticipacionEntrega)
            ]
            + [("res", str(r.id), str(r.calculado_en)) for r in bd.query(ResumenTarea)]
            + [("inc", str(i.id), i.abierta, str(i.detalle)) for i in bd.query(Incidencia)]
        )


def test_ca_10_4_01_agregar_metricas_dos_veces_no_cambia_nada(cliente: TestClient):
    curso_id, _ = _preparar_curso_con_tarea_activa(cliente, slug="pds-f6-a", email="f6a@gmail.com")
    repos = _retrodatar(curso_id)
    agregar_commit_doble(
        _ORG,
        repos[2001].nombre,
        fecha=ahora_utc() - timedelta(days=1),
        mensaje="avance",
        autor_github_user_id=_ANA,
    )
    _metricas(curso_id)
    antes = _foto(curso_id)
    assert any(f[0] == "dia" for f in antes)
    _encolar_y_ejecutar("agregar_metricas", curso_id)
    assert _foto(curso_id) == antes


def test_tablero_sin_llamadas_externas_y_con_sus_cinco_bloques(cliente: TestClient):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f6-b", email="f6b@gmail.com"
    )
    repos = _retrodatar(curso_id)
    agregar_commit_doble(
        _ORG,
        repos[2001].nombre,
        fecha=ahora_utc() - timedelta(days=1),
        mensaje="avance",
        autor_github_user_id=_ANA,
    )
    _metricas(curso_id)
    respuesta = cliente.get(f"/api/cursos/{curso_id}/tareas/{tarea_id}/tablero")
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.headers["X-Llamadas-Externas"] == "0"
    datos = respuesta.json()
    assert datos["periodo"].startswith("entrega:")  # la entrega vigente, por defecto
    assert [e["estado"] for e in datos["entregas"]] == ["ABIERTA"]
    assert datos["repositorios"]["sujetos_activos"] == 5
    # Bloques 3 y 5 solo cuentan repositorios que existen en GitHub (Ana y Bruno).
    assert datos["tarjetas"]["repositorios_creados"] == 2
    assert len(datos["filas"]) == 2
    ana = next(f for f in datos["filas"] if f["sujeto"] == "Ana Soto")
    assert ana["commits_periodo"] == 1
    assert sum(ana["sparkline"]) == 1 and len(ana["sparkline"]) == 30
    assert datos["serie"] and any(d["commits"] for d in datos["serie"])
    # INDIVIDUAL: posicion frente al curso; nunca «ranking».
    assert datos["posicion_frente_al_curso"]["sujetos"] == 2
    assert "ranking" not in respuesta.text.lower()


def test_ca_10_5_03_repositorio_joven_no_se_marca_sin_actividad(cliente: TestClient):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f6-c", email="f6c@gmail.com"
    )
    _retrodatar(curso_id, dias=3)
    _metricas(curso_id)
    assert _incidencias(curso_id, "SIN_ACTIVIDAD") == []
    filas = cliente.get(f"/api/cursos/{curso_id}/tareas/{tarea_id}/tablero").json()["filas"]
    assert {f["actividad"] for f in filas} == {"SIN_DATO_SUFICIENTE"}
    assert {(f["dias_observados"], f["umbral_dias"]) for f in filas} == {(3, 7)}


def test_sin_actividad_se_abre_un_bot_no_la_cierra_y_un_estudiante_si(cliente: TestClient):
    curso_id, _ = _preparar_curso_con_tarea_activa(cliente, slug="pds-f6-d", email="f6d@gmail.com")
    repos = _retrodatar(curso_id, dias=10)
    _metricas(curso_id)
    abiertas = {i.sujeto_id for i in _incidencias(curso_id, "SIN_ACTIVIDAD") if i.abierta}
    assert abiertas == {repos[2001].id, repos[2002].id}

    # CA-10.5-02: un commit de un bot (sin atribuir a ningun estudiante) no la cierra.
    agregar_commit_doble(
        _ORG, repos[2001].nombre, fecha=ahora_utc(), mensaje="ci", autor_email="ci@example.com"
    )
    _metricas(curso_id)
    assert repos[2001].id in {
        i.sujeto_id for i in _incidencias(curso_id, "SIN_ACTIVIDAD") if i.abierta
    }

    # CA-10.4-02: el commit de la estudiante la cierra el sistema, sin borrarla.
    agregar_commit_doble(
        _ORG, repos[2001].nombre, fecha=ahora_utc(), mensaje="avance", autor_github_user_id=_ANA
    )
    _metricas(curso_id)
    ana = [i for i in _incidencias(curso_id, "SIN_ACTIVIDAD") if i.sujeto_id == repos[2001].id]
    assert len(ana) == 1 and not ana[0].abierta and ana[0].resuelta_en is not None
    assert ana[0].detalle["resuelta_por"] == "SISTEMA"


def test_ca_10_5_05_las_tres_causas_de_sin_participacion(cliente: TestClient):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f6-e", email="f6e@gmail.com"
    )
    repos = _retrodatar(curso_id, dias=10)
    _metricas(curso_id)
    causas = {
        i.detalle["estudiante"]: i.detalle["causa"]
        for i in _incidencias(curso_id, "SIN_PARTICIPACION")
        if i.abierta
    }
    assert causas == {"Ana Soto": "SIN_ACCESO", "Bruno Diaz": "SIN_ACCESO"}

    _aceptar(repos[2001])
    _aceptar(repos[2002])
    agregar_commit_doble(
        _ORG,
        repos[2002].nombre,
        fecha=ahora_utc(),
        mensaje="otra maquina",
        autor_email="root@localhost",
    )
    _metricas(curso_id)
    causas = {
        i.detalle["estudiante"]: i.detalle["causa"]
        for i in _incidencias(curso_id, "SIN_PARTICIPACION")
        if i.abierta
    }
    # Con commits sin atribuir en su repositorio, Bruno no queda en SIN_COMMITS.
    assert causas == {"Ana Soto": "SIN_COMMITS", "Bruno Diaz": "SIN_ATRIBUIR"}

    # Silenciar la oculta del tablero y la conserva abierta.
    ana = next(
        i
        for i in _incidencias(curso_id, "SIN_PARTICIPACION")
        if i.abierta and i.detalle["estudiante"] == "Ana Soto"
    )
    assert cliente.post(f"/api/cursos/{curso_id}/incidencias/{ana.id}/silenciar").status_code == 200
    datos = cliente.get(f"/api/cursos/{curso_id}/tareas/{tarea_id}/tablero").json()
    assert datos["tarjetas"]["sin_participacion"] == {"SIN_ATRIBUIR": 1}
    assert next(i for i in _incidencias(curso_id, "SIN_PARTICIPACION") if i.id == ana.id).abierta


def test_ca_10_8_02_grupo_con_8_y_2_commits_da_80_por_ciento(cliente: TestClient):
    curso_id, tarea_id = _preparar_tarea_grupal(cliente, slug="pds-f6-f", email="f6f@gmail.com")
    _activar(cliente, curso_id, tarea_id)
    repos = _retrodatar(curso_id, dias=10)
    grupo1 = repos["Grupo 1"]
    _aceptar(grupo1)
    for i in range(8):
        agregar_commit_doble(
            _ORG,
            grupo1.nombre,
            fecha=ahora_utc() - timedelta(hours=i + 1),
            mensaje=f"ana {i}",
            autor_github_user_id=_ANA,
        )
    for i in range(2):
        agregar_commit_doble(
            _ORG,
            grupo1.nombre,
            fecha=ahora_utc() - timedelta(minutes=i + 1),
            mensaje=f"bruno {i}",
            autor_github_user_id=_BRUNO,
        )
    _metricas(curso_id)
    datos = cliente.get(f"/api/cursos/{curso_id}/tareas/{tarea_id}/tablero").json()
    fila = next(f for f in datos["filas"] if f["sujeto"] == "Grupo 1")
    assert {i["nombre"]: i["commits"] for i in fila["integrantes"]} == {
        "Ana Soto": 8,
        "Bruno Diaz": 2,
    }
    assert fila["indice_desequilibrio"] == 80
    assert fila["reparto_concentrado"] is True
    assert datos["posicion_frente_al_curso"] is None  # grupal: comparacion, no posicion


def test_actualizar_ahora_con_cooldown_csv_y_vista_de_curso(cliente: TestClient):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f6-g", email="f6g@gmail.com"
    )
    _retrodatar(curso_id)
    _metricas(curso_id)
    base = f"/api/cursos/{curso_id}/tareas/{tarea_id}/tablero"
    primera = cliente.post(f"{base}/actualizar").json()
    segunda = cliente.post(f"{base}/actualizar").json()
    assert primera["encolada"] is True
    assert segunda["encolada"] is False and segunda["disponible_en"]

    csv = cliente.get(f"/api/cursos/{curso_id}/tareas/{tarea_id}/tablero.csv")
    assert csv.status_code == 200
    lineas = csv.text.splitlines()
    assert lineas[0].startswith("# Commit contable")
    assert lineas[2].startswith("repositorio,sujeto")
    with fabrica_bd()() as bd:
        assert bd.query(Bitacora).filter(Bitacora.accion == "EXPORTACION_TABLERO").count() == 1

    curso = cliente.get(f"/api/cursos/{curso_id}/seguimiento")
    assert curso.headers["X-Llamadas-Externas"] == "0"
    [fila] = curso.json()
    assert fila["tarea_id"] == tarea_id and fila["sin_actividad"] == 2
