"""Etapa F2 (SPEC 08 S8.2.1-S8.2.3, R2.3.1/R2.3.2/R2.3.4): varias entregas por
tarea, con Canvas y GitHub en modo doble."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.adaptadores.modelos_aprovisionamiento import FechaEfectiva, Repositorio
from app.adaptadores.modelos_infraestructura import Trabajo
from tests.api.test_aprovisionamiento import (
    _ejecutar_trabajos_pendientes,
    _preparar_curso_con_tarea_activa,
    _sincronizar,
)
from tests.apoyo import fabrica_bd


def _entregas(cliente: TestClient, curso_id: str, tarea_id: str) -> list[dict]:
    return cliente.get(f"/api/cursos/{curso_id}/tareas/{tarea_id}").json()["entregas"]


def test_f2_vincular_una_segunda_entrega_la_nueva_final_y_la_anterior_parcial(
    cliente: TestClient,
):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f2-a", email="f2a@gmail.com"
    )
    detalle = cliente.get(f"/api/cursos/{curso_id}/tareas/{tarea_id}").json()
    assert detalle["vincular_otra_entrega"]["habilitada"] is True

    # CA-8.2-04: sin decir cual es la final no se completa la operacion.
    sin_final = cliente.post(
        f"/api/cursos/{curso_id}/tareas/{tarea_id}/entregas",
        json={"canvas_assignment_id": 9104},
    )
    assert sin_final.status_code == 422  # validacion: falta un dato del formulario
    assert sin_final.json()["detail"]["motivo"] == "FINAL_NO_ELEGIDA"
    assert len(_entregas(cliente, curso_id, tarea_id)) == 1

    respuesta = cliente.post(
        f"/api/cursos/{curso_id}/tareas/{tarea_id}/entregas",
        json={"canvas_assignment_id": 9104, "final_canvas_assignment_id": 9104},
    )
    assert respuesta.status_code == 200, respuesta.text
    entregas = respuesta.json()["entregas"]
    assert [(e["canvas_assignment_id"], e["orden"], e["tipo"]) for e in entregas] == [
        (9101, 1, "PARCIAL"),
        (9104, 2, "FINAL"),
    ]
    # Vincular a una tarea activa encola la sincronizacion: nadie tiene que
    # pulsar «sincronizar ahora» para que la entrega nueva tenga fechas.
    with fabrica_bd()() as bd:
        assert (
            bd.query(Trabajo)
            .filter(
                Trabajo.tipo == "sync_tareas_y_fechas",
                Trabajo.curso_id == uuid.UUID(curso_id),
                Trabajo.estado == "PENDIENTE",
            )
            .count()
            == 1
        )


def test_f2_todas_las_entregas_comparten_los_mismos_repositorios(cliente: TestClient):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f2-b", email="f2b@gmail.com"
    )
    with fabrica_bd()() as bd:
        antes = bd.query(Repositorio).filter(Repositorio.tarea_id == uuid.UUID(tarea_id)).count()
    assert (
        cliente.post(
            f"/api/cursos/{curso_id}/tareas/{tarea_id}/entregas",
            json={"canvas_assignment_id": 9103, "final_canvas_assignment_id": 9103},
        ).status_code
        == 200
    )
    _ejecutar_trabajos_pendientes()
    _sincronizar(cliente, curso_id)
    entregas = {e["canvas_assignment_id"]: e["id"] for e in _entregas(cliente, curso_id, tarea_id)}
    with fabrica_bd()() as bd:
        # CA-8.2-05 / R2.3.4: vincular otra entrega nunca crea repositorios.
        despues = bd.query(Repositorio).filter(Repositorio.tarea_id == uuid.UUID(tarea_id)).count()
        assert despues == antes
        # Cada entrega tiene sus propias fechas sobre los mismos sujetos. 9103
        # solo es visible para la seccion 101 (3 estudiantes).
        for canvas_id, esperadas in ((9101, 5), (9103, 3)):
            vigentes = (
                bd.query(FechaEfectiva)
                .filter(
                    FechaEfectiva.entrega_id == uuid.UUID(entregas[canvas_id]),
                    FechaEfectiva.estado == "VIGENTE",
                )
                .count()
            )
            assert vigentes == esperadas, canvas_id


def test_f2_desvincular_renumera_y_excluir_conserva_la_entrega(cliente: TestClient):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f2-c", email="f2c@gmail.com"
    )
    for canvas_id in (9103, 9104):
        assert (
            cliente.post(
                f"/api/cursos/{curso_id}/tareas/{tarea_id}/entregas",
                json={"canvas_assignment_id": canvas_id, "final_canvas_assignment_id": canvas_id},
            ).status_code
            == 200
        )
    entregas = _entregas(cliente, curso_id, tarea_id)
    assert [(e["canvas_assignment_id"], e["orden"], e["tipo"]) for e in entregas] == [
        (9101, 1, "PARCIAL"),
        (9103, 2, "PARCIAL"),
        (9104, 3, "FINAL"),
    ]
    # CA-8.2-02: quitar la del medio renumera en la misma transaccion.
    medio = entregas[1]["id"]
    respuesta = cliente.delete(f"/api/cursos/{curso_id}/tareas/{tarea_id}/entregas/{medio}")
    assert respuesta.status_code == 200, respuesta.text
    assert [(e["canvas_assignment_id"], e["orden"]) for e in respuesta.json()["entregas"]] == [
        (9101, 1),
        (9104, 2),
    ]

    final, parcial = entregas[2]["id"], entregas[0]["id"]
    rechazo = cliente.post(f"/api/cursos/{curso_id}/tareas/{tarea_id}/entregas/{final}/excluir")
    assert rechazo.status_code == 409
    assert rechazo.json()["detail"]["motivo"] == "EXCLUIR_NO_PERMITIDO"

    excluida = cliente.post(f"/api/cursos/{curso_id}/tareas/{tarea_id}/entregas/{parcial}/excluir")
    assert excluida.status_code == 200, excluida.text
    por_id = {e["id"]: e for e in excluida.json()["entregas"]}
    assert por_id[parcial]["estado_validacion"] == "EXCLUIDA"
    assert por_id[parcial]["orden"] == 1  # sigue en su lugar: no desaparece


def test_f2_la_modalidad_queda_congelada_por_la_primera_entrega(cliente: TestClient):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f2-d", email="f2d@gmail.com"
    )
    # CA-8.2-01: una tarea de Canvas grupal no entra en una tarea individual.
    respuesta = cliente.post(
        f"/api/cursos/{curso_id}/tareas/{tarea_id}/entregas",
        json={"canvas_assignment_id": 9102, "final_canvas_assignment_id": 9102},
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"]["motivo"] == "MODALIDAD_INCOMPATIBLE"
    assert len(_entregas(cliente, curso_id, tarea_id)) == 1
