"""Etapa F8 (A-168, A-197): archivar y desarchivar los repositorios de una
tarea, de punta a punta con Canvas y GitHub en modo doble."""

from __future__ import annotations

import uuid
from datetime import timedelta

from fastapi.testclient import TestClient

from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_github import repo_archivado_doble
from app.adaptadores.modelos_aprovisionamiento import (
    AccesoRepositorio,
    FechaEfectiva,
    MensajeSaliente,
    Repositorio,
)
from app.adaptadores.modelos_github import AccesoDocenteRepositorio
from app.adaptadores.modelos_infraestructura import Bitacora
from app.adaptadores.modelos_tarea import Entrega, Tarea
from app.adaptadores.modelos_version import VersionEntrega
from app.trabajos import archivar_repositorios  # noqa: F401
from tests.api.test_aprovisionamiento import (
    _despachar_outbox,
    _preparar_curso_con_tarea_activa,
    _sesion_autenticada,
)
from tests.api.test_tablero import _aceptar, _retrodatar
from tests.api.test_versiones import _ayudante_con_tarea_administrar, _capturar_todo, _trabajar
from tests.apoyo import fabrica_bd

_ORG = "org-valida"


def _base(curso_id: str, tarea_id: str) -> str:
    return f"/api/cursos/{curso_id}/tareas/{tarea_id}"


def _vencer_todo(tarea_id: str, *, hace: timedelta = timedelta(days=2)) -> None:
    with fabrica_bd()() as bd:
        for f in (
            bd.query(FechaEfectiva)
            .join(Entrega, Entrega.id == FechaEfectiva.entrega_id)
            .filter(Entrega.tarea_id == uuid.UUID(tarea_id), FechaEfectiva.estado == "VIGENTE")
        ):
            f.due_at_utc = ahora_utc() - hace
        bd.commit()


def _tarea_lista_para_archivar(cliente: TestClient, *, slug: str, email: str):
    """Ana y Bruno con repositorio, invitaciones aceptadas, todas las entregas
    vencidas y capturadas. Falta solo el aviso previo."""
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(cliente, slug=slug, email=email)
    repos = _retrodatar(curso_id, dias=30)
    for repo in repos.values():
        _aceptar(repo)
    _vencer_todo(tarea_id)
    _capturar_todo()
    return curso_id, tarea_id, repos


def _avisar_hace(
    cliente: TestClient, curso_id: str, tarea_id: str, dias: int = 15, *, enviar: bool = True
) -> None:
    if enviar:
        respuesta = cliente.post(f"{_base(curso_id, tarea_id)}/archivar/aviso")
        assert respuesta.status_code == 202, respuesta.text
        assert respuesta.json()["encolados"] == 2
        _despachar_outbox()
    with fabrica_bd()() as bd:
        for m in bd.query(MensajeSaliente).filter(
            MensajeSaliente.tarea_id == uuid.UUID(tarea_id),
            MensajeSaliente.evento == "aviso_archivado_previo",
        ):
            assert m.estado == "ENVIADO"
            m.enviado_en = ahora_utc() - timedelta(days=dias)
        bd.commit()


def _estado(cliente: TestClient, curso_id: str, tarea_id: str) -> dict:
    respuesta = cliente.get(f"{_base(curso_id, tarea_id)}/archivado")
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.headers["X-Llamadas-Externas"] == "0"
    return respuesta.json()


def _guarda(estado: dict, numero: int) -> dict:
    return next(g for g in estado["guardas"] if g["numero"] == numero)


def _foto_versiones(tarea_id: str) -> list[tuple]:
    with fabrica_bd()() as bd:
        return sorted(
            (str(v.id), v.commit_sha, v.estado, v.vigente, v.intento)
            for v in bd.query(VersionEntrega)
            .join(Entrega, Entrega.id == VersionEntrega.entrega_id)
            .filter(Entrega.tarea_id == uuid.UUID(tarea_id))
        )


def _acciones(curso_id: str, accion: str) -> list[Bitacora]:
    with fabrica_bd()() as bd:
        filas = (
            bd.query(Bitacora)
            .filter(Bitacora.curso_id == uuid.UUID(curso_id), Bitacora.accion == accion)
            .all()
        )
        for f in filas:
            bd.expunge(f)
        return filas


def test_archivar_deja_archivado_con_la_captura_intacta_y_desarchivar_lo_revierte(
    cliente: TestClient,
):
    curso_id, tarea_id, repos = _tarea_lista_para_archivar(
        cliente, slug="pds-f8-a", email="f8a@gmail.com"
    )
    estado = _estado(cliente, curso_id, tarea_id)
    assert [g["numero"] for g in estado["guardas"]] == [1, 2, 3, 4, 5]
    assert not estado["permitido"] and not _guarda(estado, 4)["cumple"]
    bloqueado = cliente.post(f"{_base(curso_id, tarea_id)}/archivar", json={})
    assert bloqueado.status_code == 409
    assert bloqueado.json()["detail"]["codigo"] == "ARCHIVADO_BLOQUEADO"

    _avisar_hace(cliente, curso_id, tarea_id, dias=5)
    assert "Faltan 9 días" in _guarda(_estado(cliente, curso_id, tarea_id), 4)["motivo"]
    _avisar_hace(cliente, curso_id, tarea_id, dias=15, enviar=False)
    estado = _estado(cliente, curso_id, tarea_id)
    assert estado["permitido"], estado["guardas"]

    antes = _foto_versiones(tarea_id)
    assert antes  # hay evidencia capturada
    respuesta = cliente.post(f"{_base(curso_id, tarea_id)}/archivar", json={})
    assert respuesta.status_code == 202, respuesta.text
    assert respuesta.json()["repositorios"] == 2
    _trabajar()

    with fabrica_bd()() as bd:
        for repo in repos.values():
            assert bd.get(Repositorio, repo.id).estado == "ARCHIVADO"  # type: ignore[union-attr]
            assert repo_archivado_doble(_ORG, repo.nombre)
        assert bd.get(Tarea, uuid.UUID(tarea_id)).estado == "ARCHIVADA"  # type: ignore[union-attr]
        avisos = (
            bd.query(MensajeSaliente)
            .filter(
                MensajeSaliente.tarea_id == uuid.UUID(tarea_id),
                MensajeSaliente.evento == "aviso_archivado",
            )
            .count()
        )
    assert avisos == 2  # el segundo aviso, al ejecutar
    assert _foto_versiones(tarea_id) == antes  # la captura previa no se toca
    assert len(_acciones(curso_id, "TAREA_ARCHIVADA")) == 1
    assert _estado(cliente, curso_id, tarea_id)["puede_desarchivar"]

    respuesta = cliente.post(f"{_base(curso_id, tarea_id)}/desarchivar")
    assert respuesta.status_code == 202, respuesta.text
    _trabajar()
    with fabrica_bd()() as bd:
        for repo in repos.values():
            assert bd.get(Repositorio, repo.id).estado == "DEGRADADO"  # type: ignore[union-attr]
            assert not repo_archivado_doble(_ORG, repo.nombre)
        assert bd.get(Tarea, uuid.UUID(tarea_id)).estado == "ACTIVA"  # type: ignore[union-attr]
    assert len(_acciones(curso_id, "REPOSITORIO_DESARCHIVADO")) == 2
    assert _foto_versiones(tarea_id) == antes


def test_ayudante_con_tarea_administrar_recibe_403_con_motivo(cliente: TestClient):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f8-b", email="f8b@gmail.com"
    )
    _sesion_autenticada(cliente, _ayudante_con_tarea_administrar(curso_id))
    for ruta in ("archivar", "desarchivar", "archivar/aviso"):
        respuesta = cliente.post(f"{_base(curso_id, tarea_id)}/{ruta}", json={})
        assert respuesta.status_code == 403, ruta
        assert respuesta.json()["detail"]["codigo"] == "PERMISO_INSUFICIENTE"
        assert "profesor" in respuesta.json()["detail"]["motivo"]
    # Ver las guardas si puede: no es una accion.
    assert cliente.get(f"{_base(curso_id, tarea_id)}/archivado").status_code == 200


def test_guarda_1_cierre_futuro_bloquea_y_vencida_sin_captura_pide_confirmacion(
    cliente: TestClient,
):
    curso_id, tarea_id, repos = _tarea_lista_para_archivar(
        cliente, slug="pds-f8-c", email="f8c@gmail.com"
    )
    _avisar_hace(cliente, curso_id, tarea_id)
    # Una entrega vence para Ana dentro de tres dias.
    ana = repos[2001]
    with fabrica_bd()() as bd:
        sujeto_ana = bd.get(Repositorio, ana.id).sujeto_id  # type: ignore[union-attr]
        fecha = (
            bd.query(FechaEfectiva)
            .filter(FechaEfectiva.sujeto_id == sujeto_ana, FechaEfectiva.estado == "VIGENTE")
            .first()
        )
        assert fecha is not None
        for v in bd.query(VersionEntrega).filter(
            VersionEntrega.sujeto_id == sujeto_ana, VersionEntrega.entrega_id == fecha.entrega_id
        ):
            v.vigente = False  # el disparador permite cambiar `vigente`
        fecha.due_at_utc = ahora_utc() + timedelta(days=3)
        bd.commit()
    g1 = _guarda(_estado(cliente, curso_id, tarea_id), 1)
    assert not g1["cumple"] and g1["confirmacion"] is None
    respuesta = cliente.post(
        f"{_base(curso_id, tarea_id)}/archivar",
        json={"confirmacion_sin_captura": "archivo igual, ya lo sé"},
    )
    assert respuesta.status_code == 409

    # Ya vencida, pero sin capturar: basta una confirmacion escrita.
    with fabrica_bd()() as bd:
        bd.get(FechaEfectiva, fecha.id).due_at_utc = ahora_utc() - timedelta(hours=1)  # type: ignore[union-attr]
        bd.commit()
    g1 = _guarda(_estado(cliente, curso_id, tarea_id), 1)
    assert not g1["cumple"] and g1["confirmacion"] == "SIN_CAPTURA"
    assert cliente.post(f"{_base(curso_id, tarea_id)}/archivar", json={}).status_code == 409
    respuesta = cliente.post(
        f"{_base(curso_id, tarea_id)}/archivar",
        json={"confirmacion_sin_captura": "Ana no entregó a tiempo; se revisa aparte"},
    )
    assert respuesta.status_code == 202, respuesta.text
    solicitud = _acciones(curso_id, "ARCHIVADO_SOLICITADO")
    assert "Ana no entregó" in solicitud[0].despues["confirmacion_sin_captura"]  # type: ignore[index]


def test_guardas_2_y_3_y_el_trabajo_reevalua_antes_de_cada_repositorio(cliente: TestClient):
    curso_id, tarea_id, repos = _tarea_lista_para_archivar(
        cliente, slug="pds-f8-d", email="f8d@gmail.com"
    )
    _avisar_hace(cliente, curso_id, tarea_id)
    ana, bruno = repos[2001], repos[2002]
    with fabrica_bd()() as bd:
        acceso = (
            bd.query(AccesoDocenteRepositorio)
            .filter(AccesoDocenteRepositorio.repositorio_id == ana.id)
            .first()
        )
        assert acceso is not None
        acceso.estado = "PENDIENTE"
        bd.commit()
    estado = _estado(cliente, curso_id, tarea_id)
    assert not _guarda(estado, 2)["cumple"]
    assert ana.nombre in _guarda(estado, 2)["detalle"]
    with fabrica_bd()() as bd:
        bd.get(AccesoDocenteRepositorio, acceso.id).estado = "CONCEDIDO"  # type: ignore[union-attr]
        bd.commit()
    assert _estado(cliente, curso_id, tarea_id)["permitido"]

    assert cliente.post(f"{_base(curso_id, tarea_id)}/archivar", json={}).status_code == 202
    # Antes de que corra el trabajo, a Bruno le queda una invitacion pendiente.
    with fabrica_bd()() as bd:
        for a in bd.query(AccesoRepositorio).filter(AccesoRepositorio.repositorio_id == bruno.id):
            a.estado = "INVITADO"
        bd.commit()
    _trabajar()
    with fabrica_bd()() as bd:
        assert bd.get(Repositorio, ana.id).estado == "ARCHIVADO"  # type: ignore[union-attr]
        assert bd.get(Repositorio, bruno.id).estado != "ARCHIVADO"  # type: ignore[union-attr]
        # Mientras quede uno sin archivar, la tarea no pasa a ARCHIVADA.
        assert bd.get(Tarea, uuid.UUID(tarea_id)).estado == "ACTIVA"  # type: ignore[union-attr]
    omitido = _acciones(curso_id, "ARCHIVADO_OMITIDO")
    assert omitido and omitido[0].despues["guarda"] == 3  # type: ignore[index]
    assert not repo_archivado_doble(_ORG, bruno.nombre)
    assert not _guarda(_estado(cliente, curso_id, tarea_id), 3)["cumple"]
