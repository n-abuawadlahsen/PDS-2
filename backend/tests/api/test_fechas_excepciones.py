"""Etapa F3 (SPEC 09 S9.3-S9.5): fechas efectivas con excepciones y
resincronizacion por huella, con Canvas y GitHub en modo doble.

Los overrides de la entrega 9101 se simulan reemplazando el endpoint 14 del
doble: la aplicacion no distingue esa respuesta de la de Canvas real."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_canvas import ClienteCanvasDoble
from app.adaptadores.modelos_aprovisionamiento import FechaEfectiva, Sujeto
from app.adaptadores.modelos_infraestructura import (
    Bitacora,
    Incidencia,
    Sincronizacion,
    Trabajo,
    TrabajoPeriodico,
)
from app.adaptadores.modelos_padron import Estudiante, Matricula, Seccion
from app.adaptadores.modelos_tarea import Entrega
from app.dominio.tareas_canvas import OverrideCanvasCrudo
from tests.api.test_aprovisionamiento import (
    _encolar_y_ejecutar,
    _preparar_curso_con_tarea_activa,
)
from tests.apoyo import fabrica_bd

_BASE = datetime(2026, 10, 1, 23, 59, tzinfo=UTC)  # fecha base del doble


@pytest.fixture
def overrides_9101(monkeypatch):
    """Lista mutable: lo que el endpoint 14 del doble devuelve para 9101."""
    lista: list[OverrideCanvasCrudo] = []
    original = ClienteCanvasDoble.obtener_overrides_assignment

    def _falso(self, token, canvas_course_id, canvas_assignment_id):
        if canvas_assignment_id == 9101:
            return list(lista)
        return original(self, token, canvas_course_id, canvas_assignment_id)

    monkeypatch.setattr(ClienteCanvasDoble, "obtener_overrides_assignment", _falso)
    return lista


def _override(
    oid: int,
    due_at: datetime | None,
    *,
    estudiantes: list[int] | None = None,
    seccion: int | None = None,
    titulo: str = "Extensión",
) -> OverrideCanvasCrudo:
    return OverrideCanvasCrudo(
        canvas_override_id=oid,
        student_ids=estudiantes,
        course_section_id=seccion,
        group_id=None,
        due_at=due_at,
        titulo=titulo,
    )


def _sync_tareas(curso_id: str) -> None:
    _encolar_y_ejecutar("sync_tareas_y_fechas", curso_id)


def _fecha_vigente(curso_id: str, canvas_user_id: int) -> FechaEfectiva:
    with fabrica_bd()() as bd:
        return (
            bd.query(FechaEfectiva)
            .join(Sujeto, Sujeto.id == FechaEfectiva.sujeto_id)
            .join(Estudiante, Estudiante.id == Sujeto.estudiante_id)
            .join(Entrega, Entrega.id == FechaEfectiva.entrega_id)
            .filter(
                Estudiante.canvas_user_id == canvas_user_id,
                Estudiante.curso_id == uuid.UUID(curso_id),
                Entrega.canvas_assignment_id == 9101,
                FechaEfectiva.estado == "VIGENTE",
            )
            .one()
        )


def _entrega_id(curso_id: str) -> str:
    with fabrica_bd()() as bd:
        return str(
            bd.query(Entrega.id)
            .filter(Entrega.curso_id == uuid.UUID(curso_id), Entrega.canvas_assignment_id == 9101)
            .scalar()
        )


def test_ca_9_3_01_y_9_4_01_extension_individual_gana_y_supersede(
    cliente: TestClient, overrides_9101
):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f3-a", email="f3a@gmail.com"
    )
    anterior = _fecha_vigente(curso_id, 2001)
    assert anterior.origen == "BASE"

    overrides_9101.extend(
        [
            _override(1, _BASE + timedelta(days=2), seccion=101, titulo="Sección 1"),
            _override(2, _BASE - timedelta(days=1), estudiantes=[2001]),
        ]
    )
    _sync_tareas(curso_id)
    nueva = _fecha_vigente(curso_id, 2001)
    assert (nueva.origen, nueva.due_at_utc) == ("ADHOC", _BASE - timedelta(days=1))
    assert _fecha_vigente(curso_id, 2002).origen == "SECCION"
    with fabrica_bd()() as bd:
        superseda = bd.get(FechaEfectiva, anterior.id)
        assert superseda is not None
        assert superseda.estado == "SUPERSEDIDA" and superseda.vigente_hasta is not None

    # Historial: la cadena completa de la persona, sin llamar a Canvas.
    historial = cliente.get(
        f"/api/cursos/{curso_id}/entregas/{_entrega_id(curso_id)}/historial-fechas"
    )
    assert historial.status_code == 200, historial.text
    ana = next(s for s in historial.json() if s["sujeto"] == "Ana Soto")
    assert [f["origen"] for f in ana["fechas"]] == ["BASE", "ADHOC"]
    assert ana["fechas"][1]["canvas_override_id"] == 2
    assert ana["fechas"][0]["vigente_hasta"] is not None
    assert "(America/Santiago)" in ana["fechas"][1]["fecha"]

    # Panel de excepciones: con nombre del sujeto y el override en monoespaciado.
    fechas = cliente.get(f"/api/cursos/{curso_id}/tareas/{tarea_id}/entregas/fechas").json()
    excepciones = {e["canvas_override_id"]: e for e in fechas[0]["excepciones"]}
    assert excepciones[2]["etiqueta"] == "Extensión individual"
    assert excepciones[2]["sujetos"] == ["Ana Soto"]
    assert excepciones[1]["sujetos"] == ["Ana Soto", "Bruno Diaz", "Carla Reyes"]


def test_ca_9_3_02_dos_secciones_quedan_ambiguas_con_incidencia(
    cliente: TestClient, overrides_9101
):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f3-b", email="f3b@gmail.com"
    )
    with fabrica_bd()() as bd:
        ana = (
            bd.query(Estudiante)
            .filter(Estudiante.curso_id == uuid.UUID(curso_id), Estudiante.canvas_user_id == 2001)
            .one()
        )
        s102 = (
            bd.query(Seccion)
            .filter(Seccion.curso_id == uuid.UUID(curso_id), Seccion.canvas_section_id == 102)
            .one()
        )
        bd.add(
            Matricula(
                curso_id=uuid.UUID(curso_id),
                estudiante_id=ana.id,
                seccion_id=s102.id,
                canvas_enrollment_id=999_001,
                tipo="StudentEnrollment",
                estado="active",
                activa=True,
                sincronizado_en=ahora_utc(),
            )
        )
        bd.commit()
    overrides_9101.extend(
        [
            _override(1, _BASE + timedelta(days=1), seccion=101),
            _override(2, _BASE + timedelta(days=3), seccion=102),
        ]
    )
    _sync_tareas(curso_id)
    fecha = _fecha_vigente(curso_id, 2001)
    assert (fecha.ambigua, fecha.due_at_utc) == (True, _BASE + timedelta(days=3))
    with fabrica_bd()() as bd:
        incidencia = (
            bd.query(Incidencia)
            .filter(Incidencia.tipo == "ESTUDIANTE_EN_DOS_SECCIONES", Incidencia.abierta.is_(True))
            .one()
        )
        assert incidencia.sujeto_id == fecha.sujeto_id

    fechas = cliente.get(f"/api/cursos/{curso_id}/tareas/{tarea_id}/entregas/fechas").json()
    ambigua = next(a for a in fechas[0]["ambiguas"] if a["sujeto"] == "Ana Soto")
    assert {c["canvas_override_id"] for c in ambigua["candidatas"]} >= {1, 2}


def test_ca_9_4_02_cambiar_solo_el_titulo_no_deja_rastro(cliente: TestClient, overrides_9101):
    curso_id, _ = _preparar_curso_con_tarea_activa(cliente, slug="pds-f3-c", email="f3c@gmail.com")
    overrides_9101.append(_override(2, _BASE - timedelta(days=1), estudiantes=[2001]))
    _sync_tareas(curso_id)
    with fabrica_bd()() as bd:
        filas_antes = bd.query(FechaEfectiva).count()
        bitacora_antes = (
            bd.query(Bitacora).filter(Bitacora.accion == "FECHAS_ENTREGA_CAMBIARON").count()
        )
    overrides_9101[0] = _override(
        2, _BASE - timedelta(days=1), estudiantes=[2001], titulo="Extensión médica"
    )
    _sync_tareas(curso_id)
    with fabrica_bd()() as bd:
        assert bd.query(FechaEfectiva).count() == filas_antes
        assert (
            bd.query(Bitacora).filter(Bitacora.accion == "FECHAS_ENTREGA_CAMBIARON").count()
            == bitacora_antes
        )
    # El titulo se actualiza en silencio (S9.4.3).
    historial = cliente.get(
        f"/api/cursos/{curso_id}/entregas/{_entrega_id(curso_id)}/historial-fechas"
    ).json()
    ana = next(s for s in historial if s["sujeto"] == "Ana Soto")
    assert ana["fechas"][-1]["override_titulo"] == "Extensión médica"


def test_ca_9_4_03_un_sync_de_grupos_fallido_pospone_las_fechas(
    cliente: TestClient, overrides_9101
):
    curso_id, _ = _preparar_curso_con_tarea_activa(cliente, slug="pds-f3-d", email="f3d@gmail.com")
    with fabrica_bd()() as bd:
        bd.add(
            Sincronizacion(
                curso_id=uuid.UUID(curso_id),
                recurso="grupos",
                resultado="FALLIDA",
                contadores={},
                creado_en=ahora_utc(),
            )
        )
        bd.commit()
    overrides_9101.append(_override(2, _BASE - timedelta(days=1), estudiantes=[2001]))
    _sync_tareas(curso_id)
    assert _fecha_vigente(curso_id, 2001).origen == "BASE"  # pospuesto

    _encolar_y_ejecutar("sync_grupos", curso_id)  # el ciclo siguiente sale bien
    _sync_tareas(curso_id)
    assert _fecha_vigente(curso_id, 2001).origen == "ADHOC"


def test_ca_9_4_04_sincronizar_ahora_dos_veces_encola_un_solo_ciclo(cliente: TestClient):
    curso_id, _ = _preparar_curso_con_tarea_activa(cliente, slug="pds-f3-e", email="f3e@gmail.com")
    primera = cliente.post(f"/api/cursos/{curso_id}/sincronizaciones")
    segunda = cliente.post(f"/api/cursos/{curso_id}/sincronizaciones")
    assert primera.status_code == segunda.status_code == 202
    assert primera.json()["en_curso"] is False
    assert segunda.json()["en_curso"] is True
    with fabrica_bd()() as bd:
        pendientes = (
            bd.query(Trabajo)
            .filter(
                Trabajo.curso_id == uuid.UUID(curso_id),
                Trabajo.tipo == "sync_tareas_y_fechas",
                Trabajo.estado == "PENDIENTE",
            )
            .count()
        )
    assert pendientes == 1


def test_cadencia_de_un_minuto_cerca_de_un_cierre_y_override_sucio(
    cliente: TestClient, overrides_9101
):
    curso_id, _ = _preparar_curso_con_tarea_activa(cliente, slug="pds-f3-f", email="f3f@gmail.com")
    overrides_9101.extend(
        [
            _override(2, ahora_utc() + timedelta(minutes=45), estudiantes=[2001]),
            _override(3, _BASE, seccion=555),  # seccion que el curso no tiene
        ]
    )
    _sync_tareas(curso_id)
    with fabrica_bd()() as bd:
        periodico = (
            bd.query(TrabajoPeriodico)
            .filter(
                TrabajoPeriodico.curso_id == uuid.UUID(curso_id),
                TrabajoPeriodico.tipo == "sync_tareas_y_fechas",
            )
            .one()
        )
        assert periodico.cadencia_segundos == 60
        incidencia = (
            bd.query(Incidencia)
            .filter(Incidencia.tipo == "OVERRIDE_NO_INTERPRETABLE", Incidencia.abierta.is_(True))
            .one()
        )
        assert incidencia.severidad == "ADVERTENCIA"
        assert incidencia.detalle["overrides"] == [
            {"canvas_override_id": 3, "motivo": "SECCION_DESCONOCIDA"}
        ]


def test_override_retirado_en_canvas_no_se_borra_del_historial(cliente: TestClient, overrides_9101):
    curso_id, _ = _preparar_curso_con_tarea_activa(cliente, slug="pds-f3-g", email="f3g@gmail.com")
    overrides_9101.append(_override(2, _BASE - timedelta(days=1), estudiantes=[2001]))
    _sync_tareas(curso_id)
    overrides_9101.clear()  # la extension se borra en Canvas
    _sync_tareas(curso_id)
    assert _fecha_vigente(curso_id, 2001).origen == "BASE"
    historial = cliente.get(
        f"/api/cursos/{curso_id}/entregas/{_entrega_id(curso_id)}/historial-fechas"
    ).json()
    ana = next(s for s in historial if s["sujeto"] == "Ana Soto")
    assert [f["origen"] for f in ana["fechas"]] == ["BASE", "ADHOC", "BASE"]
    adhoc = ana["fechas"][1]
    assert (adhoc["canvas_override_id"], adhoc["override_retirado"]) == (2, True)
