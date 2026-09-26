"""Etapa F10 (SPEC 11 S11.2, S11.6-S11.8, S11.10): comunicaciones ampliadas,
de punta a punta con Canvas y GitHub en modo doble."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.adaptadores import cliente_canvas, comunicaciones_repo, outbox_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_aprovisionamiento import FechaEfectiva, MensajeSaliente, Sujeto
from app.adaptadores.modelos_comunicacion import CambioFecha, ReglaComunicacion
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_padron import Estudiante, Grupo
from app.adaptadores.modelos_tarea import Entrega
from app.trabajos import ejecutor  # noqa: F401 (registra manejadores)
from tests.api.test_aprovisionamiento import (
    _preparar_curso_con_tarea_activa,
    _sesion_autenticada,
)
from tests.api.test_aprovisionamiento_grupal import _preparar_tarea_grupal
from tests.api.test_informe import _miembro
from tests.apoyo import fabrica_bd

ZONA = ZoneInfo("America/Santiago")


@pytest.fixture(autouse=True)
def _dobles_limpios():
    cliente_canvas.conversaciones_doble.clear()
    cliente_canvas.anuncios_doble.clear()
    cliente_canvas.anuncios_borrados_doble.clear()


def _mensajes(curso_id: str, **filtros) -> list[MensajeSaliente]:
    with fabrica_bd()() as bd:
        consulta = bd.query(MensajeSaliente).filter(MensajeSaliente.curso_id == uuid.UUID(curso_id))
        for campo, valor in filtros.items():
            consulta = consulta.filter(getattr(MensajeSaliente, campo) == valor)
        filas = consulta.order_by(MensajeSaliente.creado_en).all()
        for f in filas:
            bd.expunge(f)
        return filas


def _estudiante(curso_id: str, canvas_user_id: int) -> Estudiante:
    with fabrica_bd()() as bd:
        e = (
            bd.query(Estudiante)
            .filter(
                Estudiante.curso_id == uuid.UUID(curso_id),
                Estudiante.canvas_user_id == canvas_user_id,
            )
            .one()
        )
        bd.expunge(e)
        return e


def _despachar(ahora: datetime | None = None) -> None:
    with fabrica_bd()() as bd:
        outbox_repo.despachar_pendientes(bd, tomado_por="test", limite=200, ahora=ahora)
        bd.commit()


def test_apagar_y_encender_repositorio_disponible(cliente: TestClient):
    # CA-11.6-04 y CA-11.6-05: apagado no sale; al encender sale lo retenido.
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f10-a", email="f10a@gmail.com"
    )
    antes = _mensajes(curso_id, evento="repositorio_disponible")
    assert antes and {m.estado for m in antes} == {"PENDIENTE"}
    base = f"/api/cursos/{curso_id}/tareas/{tarea_id}/comunicaciones"
    reglas = cliente.get(base).json()
    assert len(reglas) == 6 and "recordatorio_mapeo" not in {r["evento"] for r in reglas}
    regla = next(r for r in reglas if r["evento"] == "repositorio_disponible")
    assert regla["activa"] and "tendrás que dársela tú" in regla["advertencia_al_apagar"]
    apagado = cliente.put(f"{base}/repositorio_disponible", json={"activa": False}).json()
    assert apagado["cancelados"] == len(antes)
    _despachar()
    assert cliente_canvas.conversaciones_doble == []
    assert {
        (m.estado, m.motivo_estado) for m in _mensajes(curso_id, evento="repositorio_disponible")
    } == {("SUPRIMIDO", "REGLA_DESACTIVADA")}
    encendido = cliente.put(f"{base}/repositorio_disponible", json={"activa": True}).json()
    assert encendido["programados"] == len(antes)
    _despachar()
    nuevos = [m for m in _mensajes(curso_id, evento="repositorio_disponible") if m.generacion == 2]
    assert len(nuevos) == len(antes) and all(m.reemplaza_a_id for m in nuevos)
    assert {m.estado for m in nuevos} == {"ENVIADO"}
    assert all(
        c["group_conversation"] is False and len(c["recipients"]) == 1
        for c in cliente_canvas.conversaciones_doble
    )
    assert cliente.put(f"{base}/salida_de_grupo", json={"activa": False}).status_code == 404


def test_mensaje_manual_a_un_grupo_es_uno_por_integrante(cliente: TestClient):
    # CA-11.7-01
    curso_id, tarea_id = _preparar_tarea_grupal(cliente, slug="pds-f10-b", email="f10b@gmail.com")
    with fabrica_bd()() as bd:
        grupo = (
            bd.query(Grupo)
            .filter(Grupo.curso_id == uuid.UUID(curso_id), Grupo.canvas_group_id == 601)
            .one()
        )
        grupo_id = str(grupo.id)
    respuesta = cliente.post(
        f"/api/cursos/{curso_id}/comunicaciones/mensajes",
        json={
            "grupo_id": grupo_id,
            "asunto": "Consulta de actividad",
            "cuerpo": "Hola, ¿cómo va la tarea?",
        },
    )
    assert respuesta.status_code == 202, respuesta.text
    assert respuesta.json()["encolados"] == 2
    _despachar()
    manuales = _mensajes(curso_id, evento="MANUAL")
    assert len(manuales) == 2 and {m.estado for m in manuales} == {"ENVIADO"}
    assert len(cliente_canvas.conversaciones_doble) == 2
    for c in cliente_canvas.conversaciones_doble:
        assert c["group_conversation"] is False and len(c["recipients"]) == 1
        assert c["subject"] == "[ICC4201] Consulta de actividad"
        assert c["body"].startswith("[ICC4201] Consulta de actividad")  # CA-11.7-04
        assert "Escrito por" in c["body"]
    html = cliente.post(
        f"/api/cursos/{curso_id}/comunicaciones/mensajes",
        json={"grupo_id": grupo_id, "asunto": "x", "cuerpo": "<p>hola</p>"},
    )
    assert html.status_code == 422


def test_bandeja_reintentar_reenviar_cancelar_y_permisos(cliente: TestClient):
    curso_id, _ = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f10-c", email="f10c@gmail.com"
    )
    ana = _estudiante(curso_id, 2001)
    cliente.post(
        f"/api/cursos/{curso_id}/comunicaciones/mensajes",
        json={"estudiante_ids": [str(ana.id)], "asunto": "Aviso", "cuerpo": "Texto"},
    )
    _despachar()
    enviado = _mensajes(curso_id, evento="MANUAL")[0]
    base = f"/api/cursos/{curso_id}/comunicaciones/{enviado.id}"
    assert cliente.post(f"{base}/reintentar").status_code == 409  # CA-11.10-02
    reenvio = cliente.post(f"{base}/reenviar")
    assert reenvio.status_code == 200, reenvio.text
    assert reenvio.json()["generacion"] == 2 and reenvio.json()["reemplaza_a_id"] == str(
        enviado.id
    )  # CA-11.10-03
    with fabrica_bd()() as bd:
        fila = bd.get(MensajeSaliente, enviado.id)
        fila.estado = "FALLIDO"  # type: ignore[union-attr]
        bd.commit()
    reintento = cliente.post(f"{base}/reintentar").json()
    assert reintento["estado"] == "PENDIENTE"
    assert _mensajes(curso_id, id=enviado.id)[0].clave_idempotencia == enviado.clave_idempotencia
    assert cliente.post(f"{base}/cancelar").json()["estado"] == "CANCELADO"
    bandeja = cliente.get(f"/api/cursos/{curso_id}/comunicaciones", params={"evento": "MANUAL"})
    assert bandeja.headers["X-Llamadas-Externas"] == "0"
    assert all(
        m["cuerpo"] is not None for m in bandeja.json()["mensajes"] if m["estado"] == "ENVIADO"
    )
    token, _ = _miembro(curso_id)  # ayudante solo con los permisos implicitos
    _sesion_autenticada(cliente, token)
    assert cliente.get(f"/api/cursos/{curso_id}/comunicaciones").status_code == 200  # CA-11.10-01
    assert cliente.post(f"{base}/cancelar").status_code == 403


def _preparar_fecha(
    curso_id: str, tarea_id: str, canvas_user_id: int, due: datetime
) -> tuple[uuid.UUID, uuid.UUID]:
    """La entrega publicada y la fecha vigente del sujeto de ese estudiante."""
    with fabrica_bd()() as bd:
        entrega = bd.query(Entrega).filter(Entrega.tarea_id == uuid.UUID(tarea_id)).first()
        entrega.publicada = True  # type: ignore[union-attr]
        est = (
            bd.query(Estudiante)
            .filter(
                Estudiante.curso_id == uuid.UUID(curso_id),
                Estudiante.canvas_user_id == canvas_user_id,
            )
            .one()
        )
        sujeto = (
            bd.query(Sujeto)
            .filter(Sujeto.tarea_id == uuid.UUID(tarea_id), Sujeto.estudiante_id == est.id)
            .one()
        )
        fecha = (
            bd.query(FechaEfectiva)
            .filter(
                FechaEfectiva.entrega_id == entrega.id,  # type: ignore[union-attr]
                FechaEfectiva.sujeto_id == sujeto.id,
                FechaEfectiva.estado == "VIGENTE",
            )
            .one()
        )
        fecha.due_at_utc = due
        fecha.origen = "BASE"
        bd.commit()
        return entrega.id, sujeto.id  # type: ignore[union-attr]


def _cambiar(entrega_id: uuid.UUID, sujeto_id: uuid.UUID, nueva: datetime, ahora: datetime) -> None:
    with fabrica_bd()() as bd:
        fecha = (
            bd.query(FechaEfectiva)
            .filter(
                FechaEfectiva.entrega_id == entrega_id,
                FechaEfectiva.sujeto_id == sujeto_id,
                FechaEfectiva.estado == "VIGENTE",
            )
            .one()
        )
        anterior = fecha.due_at_utc
        fecha.due_at_utc = nueva
        comunicaciones_repo.al_cambiar_fecha(
            bd,
            entrega=bd.get(Entrega, entrega_id),  # type: ignore[arg-type]
            sujeto=bd.get(Sujeto, sujeto_id),  # type: ignore[arg-type]
            anterior=anterior,
            nueva=nueva,
            origen="BASE",
            ahora=ahora,
        )
        bd.commit()


def _programar(curso_id: str, ahora: datetime) -> dict:
    with fabrica_bd()() as bd:
        resumen = comunicaciones_repo.programar(bd, bd.get(Curso, uuid.UUID(curso_id)), ahora=ahora)  # type: ignore[arg-type]
        bd.commit()
        return resumen


def test_tres_ediciones_de_fecha_un_solo_anuncio_y_un_cambio_chico_ninguno(cliente: TestClient):
    # CA-11.8-03 y CA-11.8-02
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f10-d", email="f10d@gmail.com"
    )
    ahora = ahora_utc()
    base = ahora + timedelta(days=5)
    entrega_id, sujeto_id = _preparar_fecha(curso_id, tarea_id, 2001, base)
    for i, horas in enumerate((24, 48, 72)):
        _cambiar(
            entrega_id, sujeto_id, base + timedelta(hours=horas), ahora + timedelta(minutes=5 * i)
        )
    with fabrica_bd()() as bd:
        assert bd.query(CambioFecha).filter(CambioFecha.entrega_id == entrega_id).count() == 1
    assert (
        _programar(curso_id, ahora + timedelta(minutes=10))["cambio_de_fecha"] == 0
    )  # ventana abierta
    assert _programar(curso_id, ahora + timedelta(minutes=21))["cambio_de_fecha"] == 1
    anuncios = _mensajes(curso_id, canal="CANVAS_ANUNCIO")
    assert len(anuncios) == 1
    _despachar()
    assert len(cliente_canvas.anuncios_doble) == 1
    publicado = cliente_canvas.anuncios_doble[0]
    assert publicado["title"].startswith("Cambio de fecha — ")
    esperado = (base + timedelta(hours=72)).astimezone(ZONA).strftime("%d-%m-%Y")
    assert esperado in publicado["message"] and "published" not in publicado
    # Un cambio de 40 minutos se aplica pero no se anuncia.
    ahora2 = ahora + timedelta(hours=1)
    _cambiar(entrega_id, sujeto_id, base + timedelta(hours=72, minutes=40), ahora2)
    _programar(curso_id, ahora2 + timedelta(minutes=21))
    assert len(_mensajes(curso_id, canal="CANVAS_ANUNCIO")) == 1


def test_aviso_de_cierre_y_tope_de_tres_al_dia(cliente: TestClient):
    # CA-11.6-07
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f10-e", email="f10e@gmail.com"
    )
    ahora = ahora_utc()
    _preparar_fecha(curso_id, tarea_id, 2001, ahora + timedelta(hours=30))
    assert _programar(curso_id, ahora)["proximidad_cierre"] >= 1
    ana = _estudiante(curso_id, 2001)
    aviso = [
        m for m in _mensajes(curso_id, evento="proximidad_cierre") if m.estudiante_id == ana.id
    ]
    assert len(aviso) == 1 and aviso[0].referencia["ventana"] == "H48"
    assert _programar(curso_id, ahora)["proximidad_cierre"] == 0  # idempotente
    # Tres automaticos ya enviados hoy a Ana.
    with fabrica_bd()() as bd:
        curso = bd.get(Curso, uuid.UUID(curso_id))
        est = bd.get(Estudiante, ana.id)
        for n in range(3):
            m = comunicaciones_repo.encolar_a_estudiante(
                bd,
                curso=curso,
                estudiante=est,
                evento="recordatorio_mapeo",  # type: ignore[arg-type]
                plantilla="recordatorio_mapeo",
                entidad=f"tope:{n}",
            )
            m.estado, m.enviado_en = "ENVIADO", ahora  # type: ignore[union-attr]
        bd.flush()
        # Lo demas de Ana ya salio, para que solo quede el aviso de cierre.
        for m in bd.query(MensajeSaliente).filter(
            MensajeSaliente.estudiante_id == ana.id,
            MensajeSaliente.estado == "PENDIENTE",
            MensajeSaliente.evento != "proximidad_cierre",
        ):
            m.estado = "CANCELADO"
            m.motivo_estado = "ACCION_DOCENTE"
        bd.commit()
    _despachar(ahora)
    aviso = _mensajes(curso_id, id=aviso[0].id)[0]
    assert aviso.estado == "PROGRAMADO"
    manana_8 = (ahora.astimezone(ZONA) + timedelta(days=1)).replace(
        hour=8, minute=0, second=0, microsecond=0
    )
    assert aviso.programado_para == manana_8


def test_suspension_difiere_canvas_y_la_purga_lo_caduca(cliente: TestClient):
    curso_id, _ = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f10-f", email="f10f@gmail.com"
    )
    assert (
        cliente.patch(
            f"/api/cursos/{curso_id}/comunicaciones", json={"suspendidas": True}
        ).status_code
        == 422
    )
    r = cliente.patch(
        f"/api/cursos/{curso_id}/comunicaciones",
        json={"suspendidas": True, "motivo": "Revisión del curso"},
    )
    assert r.status_code == 200 and r.json()["comunicaciones_salientes"] == "SUSPENDIDAS"
    _despachar()
    pendientes = _mensajes(curso_id, evento="repositorio_disponible")
    assert {(m.estado, m.motivo_estado) for m in pendientes} == {
        ("DIFERIDO", "SUSPENSION_DE_CURSO")
    }
    with fabrica_bd()() as bd:
        assert comunicaciones_repo.purgar(bd, ahora=ahora_utc() + timedelta(days=8)) == len(
            pendientes
        )
        bd.commit()
    assert {
        (m.estado, m.motivo_estado) for m in _mensajes(curso_id, evento="repositorio_disponible")
    } == {("CADUCADO", "SUSPENSION_PROLONGADA")}


def test_franja_horaria_manda_a_las_ocho(cliente: TestClient, monkeypatch):
    # CA-11.6-08: aprovisionado de madrugada, nada sale antes de las 08:00.
    curso_id, _ = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f10-g", email="f10g@gmail.com"
    )
    monkeypatch.setattr(outbox_repo, "FRANJA_ACTIVA", True)
    madrugada = (ahora_utc().astimezone(ZONA) + timedelta(days=1)).replace(
        hour=3, minute=0, second=0, microsecond=0
    )
    _despachar(madrugada.astimezone(ZoneInfo("UTC")))
    mensajes = _mensajes(curso_id, evento="repositorio_disponible")
    assert {m.estado for m in mensajes} == {"PROGRAMADO"}
    assert {m.programado_para for m in mensajes} == {madrugada.replace(hour=8)}
    assert cliente_canvas.conversaciones_doble == []


def test_supresion_por_estudiante_solo_frena_lo_automatico(cliente: TestClient):
    curso_id, _ = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f10-h", email="f10h@gmail.com"
    )
    ana = _estudiante(curso_id, 2001)
    ruta = f"/api/cursos/{curso_id}/estudiantes/{ana.id}/supresion"
    assert (
        cliente.post(
            ruta, json={"alcance": "TODAS_AUTOMATICAS", "motivo": "Lo pidió por correo"}
        ).status_code
        == 200
    )
    assert (
        cliente.post(ruta, json={"alcance": "TODAS_AUTOMATICAS", "motivo": "otra vez"}).status_code
        == 409
    )
    cliente.post(
        f"/api/cursos/{curso_id}/comunicaciones/mensajes",
        json={"estudiante_ids": [str(ana.id)], "asunto": "Aviso", "cuerpo": "Texto"},
    )
    _despachar()
    de_ana = {
        m.evento: (m.estado, m.motivo_estado) for m in _mensajes(curso_id, estudiante_id=ana.id)
    }
    assert de_ana["repositorio_disponible"] == ("SUPRIMIDO", "SUPRESION_POR_ESTUDIANTE")
    assert de_ana["MANUAL"][0] == "ENVIADO"
    assert cliente.delete(ruta).status_code == 200


def test_anuncio_manual_con_confirmacion_reforzada_y_retractacion(cliente: TestClient):
    curso_id, _ = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f10-i", email="f10i@gmail.com"
    )
    ruta = f"/api/cursos/{curso_id}/comunicaciones/anuncios"
    cuerpo = {
        "titulo": "Bienvenida",
        "cuerpo_html": "<p>Revisa tu correo: llegará una invitación de GitHub.</p>",
    }
    sin_confirmar = cliente.post(ruta, json=cuerpo)
    assert sin_confirmar.status_code == 409  # CA-11.8-08
    n = sin_confirmar.json()["detail"]["destinatarios"]
    assert (
        cliente.post(
            ruta,
            json={**cuerpo, "cuerpo_html": "<script>x</script>", "confirmacion_destinatarios": n},
        ).status_code
        == 422
    )
    publicado = cliente.post(ruta, json={**cuerpo, "confirmacion_destinatarios": n})
    assert publicado.status_code == 202, publicado.text
    _despachar()
    anuncio = _mensajes(curso_id, canal="CANVAS_ANUNCIO")[0]
    assert anuncio.estado == "ENVIADO" and anuncio.canvas_html_url
    assert cliente_canvas.anuncios_doble[0]["locked"] is True
    retirar = cliente.post(f"/api/cursos/{curso_id}/comunicaciones/{anuncio.id}/retractar")
    assert retirar.status_code == 200
    _despachar()
    assert _mensajes(curso_id, id=anuncio.id)[0].estado == "RETRACTADO"
    assert cliente_canvas.anuncios_borrados_doble == [
        anuncio.canvas_id_resultante["discussion_topic_id"]
    ]  # type: ignore[index]


def test_regla_de_curso_solo_para_recordatorio_de_mapeo(cliente: TestClient):
    # CA-11.6-02
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f10-j", email="f10j@gmail.com"
    )
    r = cliente.put(
        f"/api/cursos/{curso_id}/comunicaciones-curso/recordatorio-mapeo", json={"activa": False}
    )
    assert r.status_code == 200
    assert (
        cliente.get(f"/api/cursos/{curso_id}/comunicaciones-curso/recordatorio-mapeo").json()[
            "activa"
        ]
        is False
    )
    with fabrica_bd()() as bd:
        bd.add(
            ReglaComunicacion(
                curso_id=uuid.UUID(curso_id),
                tarea_id=None,
                alcance="CURSO",
                evento="proximidad_cierre",
                activa=False,
                actualizada_en=ahora_utc(),
            )
        )
        with pytest.raises(IntegrityError):
            bd.flush()
        bd.rollback()
