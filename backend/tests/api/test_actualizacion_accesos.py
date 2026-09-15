"""Aceptacion visible sin esperar 15 minutos, con comprobaciones reales y acotadas."""

import uuid
from datetime import timedelta
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.adaptadores import aprovisionamiento_repo, programacion_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_github import (
    FalloProveedorGithub,
    aceptar_invitacion_doble,
    crear_cliente_github_desde_config,
)
from app.adaptadores.modelos_aprovisionamiento import Repositorio
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Trabajo, TrabajoPeriodico
from app.infraestructura.config import obtener_configuracion
from app.trabajos import planificador, reconciliar_accesos
from app.trabajos.ejecutor import _procesar_un_trabajo
from tests.api.test_aprovisionamiento import (
    _ejecutar_trabajos_pendientes,
    _preparar_curso_con_tarea_activa,
    _repositorios,
)
from tests.apoyo import fabrica_bd


def _preparar(cliente):
    curso, tarea = _preparar_curso_con_tarea_activa(
        cliente, slug=f"pds-accesos-{uuid.uuid4().hex[:6]}", email="accesos@gmail.com"
    )
    ruta = f"/api/cursos/{curso}/tareas/{tarea}/repositorios/verificar-accesos"
    return curso, tarea, ruta


def _aceptar(cliente, curso_id, tarea_id):
    nombre = _repositorios(cliente, curso_id, tarea_id)["filas"][0]["nombre"]
    aceptar_invitacion_doble("org-valida", nombre, "Estudiante-Valido")


def test_periodico_actualiza_curso_existente_y_detecta_aceptacion(cliente: TestClient):
    curso_id, tarea_id, _ = _preparar(cliente)
    antes = _repositorios(cliente, curso_id, tarea_id)["filas"][0]
    _aceptar(cliente, curso_id, tarea_id)
    # Refrescar HTTP no inventa comprobaciones ni consulta GitHub.
    assert _repositorios(cliente, curso_id, tarea_id)["filas"][0] == antes
    with fabrica_bd()() as bd:
        periodicos = bd.query(TrabajoPeriodico).all()
        for p in periodicos:
            p.activo = p.tipo == "reconciliar_accesos"
        p = next(p for p in periodicos if p.tipo == "reconciliar_accesos")
        p.cadencia_segundos = 900
        p.proxima_ejecucion = ahora_utc() + timedelta(minutes=14)
        programacion_repo.actualizar_cadencia_accesos(bd)
        assert p.cadencia_segundos == 60
        assert p.proxima_ejecucion <= ahora_utc() + timedelta(seconds=60)
        assert all(not x.activo for x in periodicos if x.tipo != p.tipo)
        p.proxima_ejecucion = ahora_utc() - timedelta(seconds=1)
        bd.flush()
        assert planificador.tick(bd) == 1
        # Un trabajo en cola impide acumular otro barrido del mismo curso.
        p.proxima_ejecucion = ahora_utc() - timedelta(seconds=1)
        bd.flush()
        assert planificador.tick(bd) == 0
        bd.commit()
    _ejecutar_trabajos_pendientes()
    despues = _repositorios(cliente, curso_id, tarea_id)["filas"][0]
    assert despues["estado"] == "OPERATIVO"
    assert despues["acceso_estado"] == "ACEPTADO"
    assert despues["acceso_verificado_en"] > antes["acceso_verificado_en"]
    assert despues["invitacion_url"] is None


def test_comprobacion_manual_encola_deduplica_y_respeta_csrf(cliente: TestClient):
    curso_id, tarea_id, ruta = _preparar(cliente)
    _aceptar(cliente, curso_id, tarea_id)
    primera = cliente.post(ruta)
    assert primera.status_code == 202
    assert primera.json()["estado"] == "PENDIENTE"
    assert cliente.post(ruta).json()["trabajo_id"] == primera.json()["trabajo_id"]
    assert _repositorios(cliente, curso_id, tarea_id)["filas"][0]["acceso_estado"] == "INVITADO"
    _ejecutar_trabajos_pendientes()
    resultado = _repositorios(cliente, curso_id, tarea_id)
    assert resultado["filas"][0]["acceso_estado"] == "ACEPTADO"
    assert resultado["verificacion_accesos"]["estado"] == "OK"
    assert cliente.post(ruta).json()["trabajo_id"] == primera.json()["trabajo_id"]
    with fabrica_bd()() as bd:
        trabajo = bd.get(Trabajo, uuid.UUID(primera.json()["trabajo_id"]))
        trabajo.creado_en = ahora_utc() - timedelta(seconds=61)
        bd.commit()
    assert cliente.post(ruta).json()["trabajo_id"] != primera.json()["trabajo_id"]
    csrf = cliente.headers.pop("X-CSRF-Token")
    assert cliente.post(ruta).status_code == 403
    cliente.headers["X-CSRF-Token"] = csrf
    cliente.cookies.clear()
    assert cliente.post(ruta).status_code in (401, 403)


def test_fallo_github_no_inventa_verificacion_y_queda_visible(cliente: TestClient, monkeypatch):
    curso_id, tarea_id, ruta = _preparar(cliente)
    antes = _repositorios(cliente, curso_id, tarea_id)["filas"][0]
    github = Mock(wraps=crear_cliente_github_desde_config(obtener_configuracion()))
    github.es_colaborador.side_effect = FalloProveedorGithub("Temporal")
    monkeypatch.setattr(reconciliar_accesos, "crear_cliente_github_desde_config", lambda _: github)
    assert cliente.post(ruta).status_code == 202
    with fabrica_bd()() as bd:
        assert _procesar_un_trabajo(bd, tomado_por="test-accesos")
    resultado = _repositorios(cliente, curso_id, tarea_id)
    assert resultado["verificacion_accesos"]["estado"] == "REINTENTAR"
    despues = resultado["filas"][0]
    assert despues["acceso_estado"] == "INVITADO"
    assert despues["acceso_verificado_en"] == antes["acceso_verificado_en"]
    assert "No se pudo comprobar" in despues["error_mensaje_literal"]


def test_lotes_rotan_y_no_revisan_operativos_recientes(cliente: TestClient, monkeypatch):
    curso_id, tarea_id, _ = _preparar(cliente)
    monkeypatch.setattr(aprovisionamiento_repo, "MAX_REPOSITORIOS_POR_RECONCILIACION", 1)
    github = Mock(wraps=crear_cliente_github_desde_config(obtener_configuracion()))
    with fabrica_bd()() as bd:
        curso = bd.get(Curso, uuid.UUID(curso_id))
        for _ in range(2):
            assert (
                aprovisionamiento_repo.reconciliar_accesos(bd, github, curso=curso, periodico=True)
                == 1
            )
        logins = [llamada.args[2] for llamada in github.es_colaborador.call_args_list]
        assert set(logins) == {"Estudiante-Valido", "Estudiante-Valido-2"}
        bd.commit()
    _aceptar(cliente, curso_id, tarea_id)
    with fabrica_bd()() as bd:
        curso = bd.get(Curso, uuid.UUID(curso_id))
        for _ in range(2):
            aprovisionamiento_repo.reconciliar_accesos(bd, github, curso=curso, periodico=True)
        bd.commit()
    assert _repositorios(cliente, curso_id, tarea_id)["filas"][0]["estado"] == "OPERATIVO"
    github.es_colaborador.reset_mock()
    with fabrica_bd()() as bd:
        curso = bd.get(Curso, uuid.UUID(curso_id))
        aprovisionamiento_repo.reconciliar_accesos(bd, github, curso=curso, periodico=True)
        bd.commit()
    assert github.es_colaborador.call_args.args[2] == "Estudiante-Valido-2"


def test_pendientes_no_postergan_indefinidamente_el_resto(cliente: TestClient, monkeypatch):
    curso_id, tarea_id, _ = _preparar(cliente)
    _aceptar(cliente, curso_id, tarea_id)
    github = crear_cliente_github_desde_config(obtener_configuracion())
    with fabrica_bd()() as bd:
        curso = bd.get(Curso, uuid.UUID(curso_id))
        aprovisionamiento_repo.reconciliar_accesos(bd, github, curso=curso)
        operativo = (
            bd.query(Repositorio)
            .filter(Repositorio.curso_id == curso.id, Repositorio.estado == "OPERATIVO")
            .one()
        )
        vencido = ahora_utc() - timedelta(minutes=16)
        operativo.actualizado_en = vencido
        bd.flush()
        monkeypatch.setattr(aprovisionamiento_repo, "MAX_REPOSITORIOS_POR_RECONCILIACION", 1)
        aprovisionamiento_repo.reconciliar_accesos(bd, github, curso=curso, periodico=True)
        assert operativo.actualizado_en > vencido
        bd.commit()
