"""Etapa F11 (SPEC 12 S12.3-S12.8, S12.15): asignacion, bandeja, pantalla y
reclamos, de punta a punta con Canvas y GitHub en modo doble."""

from __future__ import annotations

import uuid
from datetime import timedelta

from fastapi.testclient import TestClient

from app.adaptadores import cliente_canvas, cursos_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_aprovisionamiento import FechaEfectiva, Sujeto
from app.adaptadores.modelos_correccion import AsignacionCorreccion, Correccion
from app.adaptadores.modelos_curso import MembresiaCurso
from app.adaptadores.modelos_identidad import Usuario
from app.adaptadores.modelos_infraestructura import Bitacora, Incidencia
from app.adaptadores.modelos_padron import Estudiante
from app.adaptadores.modelos_tarea import Entrega
from app.trabajos import ejecutor  # noqa: F401 (registra manejadores)
from tests.api.test_aprovisionamiento import _preparar_curso_con_tarea_activa, _sesion_autenticada
from tests.api.test_archivado import _vencer_todo
from tests.api.test_informe import _miembro
from tests.api.test_versiones import _capturar_todo
from tests.apoyo import fabrica_bd


def _entrega_id(tarea_id: str) -> str:
    with fabrica_bd()() as bd:
        return str(
            bd.query(Entrega.id)
            .filter(Entrega.tarea_id == uuid.UUID(tarea_id))
            .order_by(Entrega.orden)
            .first()[0]
        )  # type: ignore[index]


def _sujeto_de(curso_id: str, tarea_id: str, canvas_user_id: int) -> str:
    with fabrica_bd()() as bd:
        est = (
            bd.query(Estudiante)
            .filter(
                Estudiante.curso_id == uuid.UUID(curso_id),
                Estudiante.canvas_user_id == canvas_user_id,
            )
            .one()
        )
        return str(
            bd.query(Sujeto.id)
            .filter(Sujeto.tarea_id == uuid.UUID(tarea_id), Sujeto.estudiante_id == est.id)
            .one()[0]
        )


def _correcciones(entrega_id: str) -> dict[str, tuple[str, str | None]]:
    with fabrica_bd()() as bd:
        return {
            str(c.sujeto_id): (c.estado, str(a.membresia_id) if a.membresia_id else None)
            for c, a in bd.query(Correccion, AsignacionCorreccion)
            .join(
                AsignacionCorreccion,
                (AsignacionCorreccion.entrega_id == Correccion.entrega_id)
                & (AsignacionCorreccion.sujeto_id == Correccion.sujeto_id),
            )
            .filter(Correccion.entrega_id == uuid.UUID(entrega_id))
        }


def _preparar(cliente: TestClient, slug: str):
    """Profesor, dos ayudantes que corrigen (uno con `correccion.asignar`)."""
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug=slug, email=f"{slug}@gmail.com"
    )
    profesor = cliente.cookies.get("sesion")
    token_a, membresia_a = _miembro(curso_id, permisos=["correccion.asignar"])
    token_b, membresia_b = _miembro(curso_id)
    return (
        curso_id,
        tarea_id,
        _entrega_id(tarea_id),
        profesor,
        (token_a, membresia_a),
        (token_b, membresia_b),
    )


def test_reparto_equitativo_previsualiza_sin_escribir_y_aplica_una_vez(cliente: TestClient):
    curso_id, tarea_id, entrega_id, _, (_, m_a), (token_b, m_b) = _preparar(cliente, "pds-f11-a")
    base = f"/api/cursos/{curso_id}/correccion/{entrega_id}/reparto"
    vista = cliente.post(f"{base}/previsualizar", json={"criterio": "EQUITATIVO"})
    assert vista.status_code == 200, vista.text
    filas = vista.json()["filas"]
    assert filas and all(f["propuesto"] for f in filas)
    assert {v for k, v in _correcciones(entrega_id).values()} == {None}  # nada escrito
    assert cliente.post(f"{base}/aplicar", json={"criterio": "EQUITATIVO"}).json()[
        "cambios"
    ] == len(filas)
    estados = _correcciones(entrega_id)
    asignados = [m for _, m in estados.values()]
    assert set(asignados) == {str(m_a), str(m_b)}  # el profesor tiene peso 0
    assert abs(asignados.count(str(m_a)) - asignados.count(str(m_b))) <= 1
    assert {e for e, _ in estados.values()} == {"ASIGNADA"}
    # Una segunda ejecucion no asigna nada dos veces (CA-12.5-06).
    assert cliente.post(f"{base}/aplicar", json={"criterio": "EQUITATIVO"}).json()["cambios"] == 0
    # El ayudante sin `correccion.asignar` ve la matriz completa pero no reparte.
    _sesion_autenticada(cliente, token_b)
    matriz = cliente.get(f"/api/cursos/{curso_id}/tareas/{tarea_id}/correccion/estado")
    assert matriz.status_code == 200 and matriz.headers["X-Llamadas-Externas"] == "0"
    assert len(matriz.json()["sujetos"]) == len(filas)  # CA-12.4-01
    assert matriz.json()["contador"]["total"] == len(filas)
    assert cliente.post(f"{base}/previsualizar", json={"criterio": "EQUITATIVO"}).status_code == 403
    bandeja = cliente.get(f"/api/cursos/{curso_id}/correccion").json()
    assert not bandeja["puede_repartir"]
    assert bandeja["mis_asignaciones"] and all(x["nueva"] for x in bandeja["mis_asignaciones"])
    assert all(
        x["nueva"] is False
        for x in cliente.get(f"/api/cursos/{curso_id}/correccion").json()["mis_asignaciones"]
    )


def test_pantalla_abre_en_curso_borrador_propio_y_lista_con_version(cliente: TestClient):
    curso_id, tarea_id, entrega_id, profesor, (token_a, m_a), (token_b, _) = _preparar(
        cliente, "pds-f11-b"
    )
    ana = _sujeto_de(curso_id, tarea_id, 2001)
    cliente.post(
        f"/api/cursos/{curso_id}/correccion/{entrega_id}/reparto/aplicar",
        json={"criterio": "MANUAL", "manual": {ana: str(m_a)}},
    )
    ruta = f"/api/cursos/{curso_id}/correccion/{entrega_id}/{ana}"
    _sesion_autenticada(cliente, token_a)
    pantalla = cliente.get(ruta).json()
    assert pantalla["estado"] == "EN_CURSO" and pantalla["es_propietario"]  # CA-12.3-04
    assert pantalla["rubrica"]["criterios"][0]["id"] == "c1"
    antes = len(cliente_canvas.conversaciones_doble)
    guardado = cliente.put(
        f"{ruta}/borrador",
        json={
            "nota": "85",
            "rubrica": {"c1": {"points": 60, "rating_id": "r11"}, "c2": {"points": 25}},
            "comentario": "Bien",
            "version": pantalla["borrador"]["version"],
        },
    )
    assert guardado.status_code == 200, guardado.text
    assert len(cliente_canvas.conversaciones_doble) == antes  # el borrador no llama a Canvas
    malo = cliente.put(f"{ruta}/borrador", json={"nota": "85", "rubrica": {"c9": {"points": 1}}})
    assert malo.status_code == 422
    viejo = cliente.put(f"{ruta}/borrador", json={"nota": "86", "version": 1})
    assert viejo.status_code == 409  # concurrencia optimista
    assert cliente.post(f"{ruta}/lista").status_code == 409  # sin version registrada
    # La otra persona ve la fila pero no su borrador ni puede escribirlo (CA-12.4-02).
    _sesion_autenticada(cliente, token_b)
    ajena = cliente.get(ruta).json()
    assert (
        ajena["borrador"] is None and not ajena["es_propietario"] and ajena["banderas"] is not None
    )
    assert cliente.put(f"{ruta}/borrador", json={"nota": "10"}).status_code == 403
    # Con la version capturada, «lista» normaliza la nota.
    _vencer_todo(tarea_id)
    _capturar_todo()
    _sesion_autenticada(cliente, token_a)
    lista = cliente.post(f"{ruta}/lista")
    assert lista.status_code == 200, lista.text
    assert lista.json() == {"estado": "LISTA_PARA_PUBLICAR", "nota": "85"}
    with fabrica_bd()() as bd:
        transiciones = bd.query(Bitacora).filter(Bitacora.accion == "CORRECCION_ESTADO").count()
    assert transiciones >= 4  # alta, asignada, en curso, lista


def test_reclamo_se_registra_sin_incidencia_y_exige_desenlace(cliente: TestClient):
    curso_id, tarea_id, entrega_id, _, _, (token_b, _) = _preparar(cliente, "pds-f11-c")
    ana = _sujeto_de(curso_id, tarea_id, 2001)
    cliente.get(
        f"/api/cursos/{curso_id}/tareas/{tarea_id}/correccion/estado"
    )  # materializa las filas
    ruta = f"/api/cursos/{curso_id}/correccion/{entrega_id}/{ana}/reclamos"
    _sesion_autenticada(cliente, token_b)
    with fabrica_bd()() as bd:
        antes = bd.query(Incidencia).count()
    assert (
        cliente.post(
            ruta, json={"texto": "El estudiante dice que su último commit no se consideró"}
        ).status_code
        == 200
    )
    with fabrica_bd()() as bd:
        assert bd.query(Incidencia).count() == antes  # CA-12.15-01
    assert (
        cliente.post(f"{ruta}/cerrar", json={"texto": "Revisado"}).status_code == 422
    )  # CA-12.15-02
    assert (
        cliente.post(
            f"{ruta}/cerrar", json={"texto": "Se corrige", "desenlace": "NOTA_CORREGIDA"}
        ).status_code
        == 403
    )
    assert cliente.post(
        f"{ruta}/cerrar", json={"texto": "Se revisó", "desenlace": "SIN_CAMBIO"}
    ).json() == {"reclamo_abierto": False}


def test_sujeto_tardio_queda_sin_corrector_con_incidencia(cliente: TestClient):
    # CA-12.5-03
    curso_id, tarea_id, entrega_id, _, _, _ = _preparar(cliente, "pds-f11-d")
    cliente.post(
        f"/api/cursos/{curso_id}/correccion/{entrega_id}/reparto/aplicar",
        json={"criterio": "EQUITATIVO"},
    )
    antes = _correcciones(entrega_id)
    with fabrica_bd()() as bd:
        ahora = ahora_utc()
        est = Estudiante(
            curso_id=uuid.UUID(curso_id),
            canvas_user_id=2099,
            nombre="Tardío Pérez",
            nombre_ordenable="Pérez, Tardío",
            estado="ACTIVO",
            ciclos_ausente=0,
            primera_vista_en=ahora,
            ultima_vista_en=ahora,
        )
        bd.add(est)
        bd.flush()
        sujeto = Sujeto(
            tarea_id=uuid.UUID(tarea_id),
            tipo="ESTUDIANTE",
            estudiante_id=est.id,
            activo=True,
            creado_en=ahora,
        )
        bd.add(sujeto)
        bd.flush()
        bd.add(
            FechaEfectiva(
                entrega_id=uuid.UUID(entrega_id),
                sujeto_id=sujeto.id,
                due_at_utc=ahora + timedelta(days=3),
                origen="BASE",
                ambigua=False,
                calculada_en=ahora,
                estado="VIGENTE",
            )
        )
        bd.commit()
        nuevo = str(sujeto.id)
    cliente.get(f"/api/cursos/{curso_id}/tareas/{tarea_id}/correccion/estado")
    despues = _correcciones(entrega_id)
    assert despues[nuevo] == ("SIN_CORRECTOR", None)
    assert {k: v for k, v in despues.items() if k != nuevo} == antes  # nada mas cambia
    with fabrica_bd()() as bd:
        assert (
            bd.query(Incidencia)
            .filter(Incidencia.tipo == "CORRECCION_SIN_CORRECTOR", Incidencia.abierta.is_(True))
            .count()
            == 1
        )


def test_retirar_a_un_ayudante_devuelve_sus_filas_con_el_borrador(cliente: TestClient):
    # CA-12.5-05
    curso_id, tarea_id, entrega_id, _, (token_a, m_a), _ = _preparar(cliente, "pds-f11-e")
    ana = _sujeto_de(curso_id, tarea_id, 2001)
    cliente.post(
        f"/api/cursos/{curso_id}/correccion/{entrega_id}/reparto/aplicar",
        json={"criterio": "MANUAL", "manual": {ana: str(m_a)}},
    )
    _sesion_autenticada(cliente, token_a)
    ruta = f"/api/cursos/{curso_id}/correccion/{entrega_id}/{ana}"
    cliente.get(ruta)
    cliente.put(f"{ruta}/borrador", json={"nota": "70", "comentario": "Falta el README"})
    with fabrica_bd()() as bd:
        membresia = bd.get(MembresiaCurso, m_a)
        actor = bd.query(Usuario).filter(Usuario.email == "pds-f11-e@gmail.com").one()
        cursos_repo.retirar_membresia(bd, membresia, actor=actor, curso_activo=False)  # type: ignore[arg-type]
        bd.commit()
        c = (
            bd.query(Correccion)
            .filter(
                Correccion.entrega_id == uuid.UUID(entrega_id),
                Correccion.sujeto_id == uuid.UUID(ana),
            )
            .one()
        )
        assert (c.estado, c.nota_local, c.comentario) == ("SIN_CORRECTOR", "70", "Falta el README")
        assert (
            bd.query(Incidencia).filter(Incidencia.tipo == "CORRECCION_SIN_CORRECTOR").count() == 1
        )
