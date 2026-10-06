"""Etapa F12 (SPEC 12 S12.10, S12.13-S12.15): publicacion de notas en Canvas
y reconciliacion, de punta a punta con Canvas y GitHub en modo doble."""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.adaptadores import cliente_canvas, outbox_repo, publicacion_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_aprovisionamiento import FechaEfectiva, MensajeSaliente
from app.adaptadores.modelos_correccion import Correccion, PublicacionNota
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Incidencia, Trabajo
from app.adaptadores.modelos_padron import Grupo
from app.adaptadores.modelos_tarea import Entrega
from app.trabajos import ejecutor  # noqa: F401 (registra manejadores)
from tests.api.test_aprovisionamiento import _sesion_autenticada
from tests.api.test_aprovisionamiento_grupal import _activar, _preparar_tarea_grupal
from tests.api.test_archivado import _vencer_todo
from tests.api.test_correccion import _entrega_id, _preparar, _sujeto_de
from tests.api.test_versiones import _capturar_todo
from tests.apoyo import fabrica_bd


@pytest.fixture(autouse=True)
def _doble_limpio():
    cliente_canvas.calificaciones_doble.clear()
    cliente_canvas.publicaciones_doble.clear()
    cliente_canvas.no_calificables_doble.clear()


def _dejar_lista(
    cliente: TestClient,
    curso_id: str,
    tarea_id: str,
    entrega_id: str,
    sujeto_id: str,
    nota: str = "85",
    rubrica: bool = True,
) -> str:
    _vencer_todo(tarea_id)
    _capturar_todo()
    ruta = f"/api/cursos/{curso_id}/correccion/{entrega_id}/{sujeto_id}"
    pantalla = cliente.get(ruta).json()
    guardado = cliente.put(
        f"{ruta}/borrador",
        json={
            "nota": nota,
            "rubrica": {"c1": {"points": 60, "rating_id": "r11"}, "c2": {"points": 25}}
            if rubrica
            else None,
            "comentario": "Buen trabajo; falta documentar.",
            "version": pantalla["borrador"]["version"],
        },
    )
    assert guardado.status_code == 200, guardado.text
    lista = cliente.post(f"{ruta}/lista")
    assert lista.status_code == 200, lista.text
    return ruta


def _correccion(ruta_entrega: str, sujeto_id: str) -> Correccion:
    with fabrica_bd()() as bd:
        c = (
            bd.query(Correccion)
            .filter(
                Correccion.entrega_id == uuid.UUID(ruta_entrega),
                Correccion.sujeto_id == uuid.UUID(sujeto_id),
            )
            .one()
        )
        bd.expunge(c)
        return c


def test_publicar_verifica_contra_canvas_y_deja_evidencia(cliente: TestClient):
    curso_id, tarea_id, entrega_id, _, _, _ = _preparar(cliente, "pds-f12-a")
    ana = _sujeto_de(curso_id, tarea_id, 2001)
    ruta = _dejar_lista(cliente, curso_id, tarea_id, entrega_id, ana)
    respuesta = cliente.post(f"{ruta}/publicar", json={})
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["estado"] == "PUBLICADA"
    assert len(cliente_canvas.publicaciones_doble) == 1
    enviado = cliente_canvas.publicaciones_doble[0]
    assert enviado["user_id"] == 2001
    assert enviado["submission"] == {"posted_grade": "85", "late_policy_status": "none"}
    texto = enviado["comment"]["text_comment"]
    assert (
        texto.startswith("Buen trabajo")
        and "Versión revisada:" in texto
        and "Corregido por" in texto
    )  # CA-12.10-03
    assert "group_comment" not in enviado["comment"]
    assert enviado["rubric_assessment"] == {
        "c1": {"points": 60, "rating_id": "r11"},
        "c2": {"points": 25},
    }
    assert "as_user_id" not in str(enviado)
    with fabrica_bd()() as bd:
        evidencia = bd.query(PublicacionNota).all()
        assert [
            (p.intento, float(p.score_devuelto), p.late_policy_status_enviado) for p in evidencia
        ] == [(1, 85.0, "none")]
        # El aviso al estudiante nace con la publicacion verificada (apagado por defecto).
        assert (
            bd.query(MensajeSaliente)
            .filter(MensajeSaliente.evento == "correccion_publicada")
            .count()
            == 1
        )
        # Reconciliacion inmediata (CA-12.13-02).
        assert bd.query(Trabajo).filter(Trabajo.tipo == "reconciliar_notas_canvas").count() == 1
        outbox_repo.despachar_pendientes(bd, tomado_por="test", limite=200)
        aviso = (
            bd.query(MensajeSaliente).filter(MensajeSaliente.evento == "correccion_publicada").one()
        )
        assert (aviso.estado, aviso.motivo_estado) == ("SUPRIMIDO", "REGLA_DESACTIVADA")
        bd.rollback()
    matriz = cliente.get(f"/api/cursos/{curso_id}/tareas/{tarea_id}/correccion/estado").json()
    fila = next(s for s in matriz["sujetos"] if s["sujeto_id"] == ana)
    assert fila["celdas"][entrega_id]["contraste"] == "CONCUERDA"
    assert matriz["contador"]["con_nota_en_canvas"] == 1


def test_fecha_recalculada_no_rompe_pantalla_ni_publicacion(cliente: TestClient):
    """El historial de FechaEfectiva es append-only: una fila SUPERSEDIDA junto a
    la VIGENTE no debe tumbar la pantalla, el borrador ni la publicacion, y el
    pie del comentario usa la fecha VIGENTE."""
    curso_id, tarea_id, entrega_id, _, _, _ = _preparar(cliente, "pds-f12-sup")
    ana = _sujeto_de(curso_id, tarea_id, 2001)
    ruta = _dejar_lista(cliente, curso_id, tarea_id, entrega_id, ana)
    with fabrica_bd()() as bd:
        vigente = (
            bd.query(FechaEfectiva)
            .filter_by(entrega_id=uuid.UUID(entrega_id), sujeto_id=uuid.UUID(ana))
            .one()
        )
        bd.add(
            FechaEfectiva(
                entrega_id=vigente.entrega_id,
                sujeto_id=vigente.sujeto_id,
                due_at_utc=vigente.due_at_utc - timedelta(days=7),
                origen=vigente.origen,
                ambigua=False,
                calculada_en=vigente.calculada_en - timedelta(days=1),
                estado="SUPERSEDIDA",
            )
        )
        bd.commit()
    assert cliente.get(ruta).status_code == 200
    respuesta = cliente.post(f"{ruta}/publicar", json={})
    assert respuesta.status_code == 200, respuesta.text
    texto = cliente_canvas.publicaciones_doble[0]["comment"]["text_comment"]
    assert "sin fecha" not in texto


def test_sin_permiso_403_y_no_publicable_409_sin_llamar_a_canvas(cliente: TestClient):
    curso_id, tarea_id, entrega_id, profesor, (token_a, m_a), _ = _preparar(cliente, "pds-f12-b")
    ana = _sujeto_de(curso_id, tarea_id, 2001)
    cliente.post(
        f"/api/cursos/{curso_id}/correccion/{entrega_id}/reparto/aplicar",
        json={"criterio": "MANUAL", "manual": {ana: str(m_a)}},
    )
    _sesion_autenticada(cliente, token_a)
    ruta = _dejar_lista(cliente, curso_id, tarea_id, entrega_id, ana)
    sin_permiso = cliente.post(f"{ruta}/publicar", json={})
    assert (
        sin_permiso.status_code == 403
        and sin_permiso.json()["detail"]["codigo"] == "PERMISO_INSUFICIENTE"
    )
    _sesion_autenticada(cliente, profesor)
    with fabrica_bd()() as bd:
        bd.get(Entrega, uuid.UUID(entrega_id)).moderated_grading = True  # type: ignore[union-attr]
        bd.commit()
    cliente.get(ruta)  # refresca las banderas derivadas
    bloqueada = cliente.post(f"{ruta}/publicar", json={})
    assert bloqueada.status_code == 409  # CA-12.3-03
    assert cliente_canvas.publicaciones_doble == []
    # Con `publicable = false` el borrador y «lista» siguen permitidos (CA-12.3-03).
    assert cliente.put(f"{ruta}/borrador", json={"nota": "80"}).status_code == 200
    assert cliente.post(f"{ruta}/lista").status_code == 200
    assert _correccion(entrega_id, ana).estado == "LISTA_PARA_PUBLICAR"


def test_periodo_cerrado_marca_no_publicable_sin_escribir(cliente: TestClient, monkeypatch):
    # CA-12.10-05
    curso_id, tarea_id, entrega_id, _, _, _ = _preparar(cliente, "pds-f12-c")
    ana = _sujeto_de(curso_id, tarea_id, 2001)
    ruta = _dejar_lista(cliente, curso_id, tarea_id, entrega_id, ana)
    monkeypatch.setattr(cliente_canvas, "periodo_cerrado_doble", True)
    respuesta = cliente.post(f"{ruta}/publicar", json={})
    assert respuesta.status_code == 409
    assert cliente_canvas.publicaciones_doble == []
    c = _correccion(entrega_id, ana)
    assert (c.publicable, c.motivo_no_publicable, c.estado) == (
        False,
        "PERIODO_CERRADO",
        "LISTA_PARA_PUBLICAR",
    )


def test_conflicto_con_canvas_bloquea_y_ofrece_tres_salidas(cliente: TestClient):
    # CA-12.14-03, CA-12.14-04
    curso_id, tarea_id, entrega_id, _, _, _ = _preparar(cliente, "pds-f12-d")
    ana = _sujeto_de(curso_id, tarea_id, 2001)
    ruta = _dejar_lista(cliente, curso_id, tarea_id, entrega_id, ana)
    cliente_canvas.calificar_en_canvas_doble(9101, 2001, 70.0, ahora_utc() - timedelta(hours=1))
    conflicto = cliente.post(f"{ruta}/publicar", json={})
    assert conflicto.status_code == 409
    detalle = conflicto.json()["detail"]
    assert detalle["codigo"] == "CONFLICTO" and detalle["conflictos"][0]["nota_canvas"] == 70.0
    assert cliente_canvas.publicaciones_doble == []  # ningun PUT hasta elegir
    with fabrica_bd()() as bd:
        assert (
            bd.query(Incidencia)
            .filter(Incidencia.tipo == "NOTA_DIVERGENTE_EN_CANVAS", Incidencia.abierta.is_(True))
            .count()
            == 1
        )
    adoptada = cliente.post(f"{ruta}/adoptar-canvas", json={})
    assert adoptada.status_code == 200 and adoptada.json()["nota"] == "70"
    assert cliente_canvas.publicaciones_doble == []
    with fabrica_bd()() as bd:
        assert (
            bd.query(Incidencia)
            .filter(Incidencia.tipo == "NOTA_DIVERGENTE_EN_CANVAS", Incidencia.abierta.is_(True))
            .count()
            == 0
        )
    mia = cliente.post(f"{ruta}/publicar", json={"resolucion": "PUBLICAR_MIA"})
    assert mia.status_code == 200 and mia.json()["estado"] == "PUBLICADA"
    assert cliente_canvas.publicaciones_doble[0]["submission"]["posted_grade"] == "70"


def test_descuento_de_canvas_deja_publicada_con_advertencia_y_reabrir_exige_motivo(
    cliente: TestClient, monkeypatch
):
    # CA-12.10-06, CA-12.15-03
    curso_id, tarea_id, entrega_id, _, _, _ = _preparar(cliente, "pds-f12-e")
    ana = _sujeto_de(curso_id, tarea_id, 2001)
    ruta = _dejar_lista(cliente, curso_id, tarea_id, entrega_id, ana)
    monkeypatch.setattr(cliente_canvas, "descuento_doble", 5.0)
    assert cliente.post(f"{ruta}/publicar", json={}).json()["estado"] == "PUBLICADA_CON_ADVERTENCIA"
    assert cliente.post(f"{ruta}/reabrir", json={"motivo": ""}).status_code == 422
    reabierta = cliente.post(f"{ruta}/reabrir", json={"motivo": "El estudiante pidió revisión"})
    assert reabierta.status_code == 200 and reabierta.json()["estado"] == "EN_CURSO"
    with fabrica_bd()() as bd:
        assert bd.query(PublicacionNota).count() == 1  # la evidencia anterior queda


def test_grupo_sin_calificacion_individual_es_una_llamada_con_comentario_de_grupo(
    cliente: TestClient,
):
    # CA-12.10-04
    curso_id, tarea_id = _preparar_tarea_grupal(cliente, slug="pds-f12-f", email="f12f@gmail.com")
    _activar(cliente, curso_id, tarea_id)
    with fabrica_bd()() as bd:
        curso = bd.get(Curso, uuid.UUID(curso_id))
        grupo = (
            bd.query(Grupo).filter(Grupo.curso_id == curso.id, Grupo.canvas_group_id == 601).one()
        )  # type: ignore[union-attr]
        from app.adaptadores.modelos_aprovisionamiento import Sujeto

        sujeto = str(
            bd.query(Sujeto.id)
            .filter(Sujeto.tarea_id == uuid.UUID(tarea_id), Sujeto.grupo_id == grupo.id)
            .one()[0]
        )
    entrega_id = _entrega_id(tarea_id)
    ruta = _dejar_lista(cliente, curso_id, tarea_id, entrega_id, sujeto, nota="90", rubrica=False)
    respuesta = cliente.post(f"{ruta}/publicar", json={})
    assert respuesta.status_code == 200, respuesta.text
    assert len(cliente_canvas.publicaciones_doble) == 1
    llamada = cliente_canvas.publicaciones_doble[0]
    assert llamada["user_id"] == 2001 and llamada["comment"]["group_comment"] is True
    with fabrica_bd()() as bd:
        assert bd.query(PublicacionNota).count() == 2  # una fila por integrante
    assert respuesta.json()["estado"] == "PUBLICADA"


def test_reconciliacion_detecta_una_nota_cambiada_en_speedgrader(cliente: TestClient):
    # CA-12.14-02
    curso_id, tarea_id, entrega_id, _, _, _ = _preparar(cliente, "pds-f12-g")
    ana = _sujeto_de(curso_id, tarea_id, 2001)
    ruta = _dejar_lista(cliente, curso_id, tarea_id, entrega_id, ana)
    cliente.post(f"{ruta}/publicar", json={})
    cliente_canvas.calificar_en_canvas_doble(9101, 2001, 50.0, ahora_utc() + timedelta(minutes=5))
    with fabrica_bd()() as bd:
        curso = bd.get(Curso, uuid.UUID(curso_id))
        entrega = bd.get(Entrega, uuid.UUID(entrega_id))
        assert publicacion_repo.reconciliar(bd, curso, entrega) == 1  # type: ignore[arg-type]
        bd.commit()
        inc = bd.query(Incidencia).filter(Incidencia.tipo == "NOTA_DIVERGENTE_EN_CANVAS").one()
        assert inc.detalle["canvas"][0]["nota"] == 50.0 and inc.detalle["aplicacion"] == "85"
    matriz = cliente.get(f"/api/cursos/{curso_id}/tareas/{tarea_id}/correccion/estado").json()
    fila = next(s for s in matriz["sujetos"] if s["sujeto_id"] == ana)
    assert fila["celdas"][entrega_id]["contraste"] == "DIVERGE"
    assert _correccion(entrega_id, ana).estado == "PUBLICADA"  # el estado local nunca se pisa
    assert (
        cliente.post(f"/api/cursos/{curso_id}/correccion/{entrega_id}/comprobar").status_code == 202
    )
