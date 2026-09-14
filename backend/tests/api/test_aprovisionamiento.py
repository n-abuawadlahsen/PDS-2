"""SPEC 08 S8.5-S8.10 (Etapa P8): aprovisionamiento automatico de punta a punta,
con Canvas y GitHub en modo doble. Es el flujo que la entrega parcial demuestra:
tarea activada -> repositorios que se crean solos -> invitacion -> aviso por
Canvas -> aceptacion -> OPERATIVO, y un mapeo tardio que crea el suyo despues."""

from __future__ import annotations

import secrets
import uuid

from fastapi.testclient import TestClient

from app.adaptadores import outbox_repo, trabajos_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_github import aceptar_invitacion_doble
from app.adaptadores.modelos_aprovisionamiento import MensajeSaliente, Repositorio
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.adaptadores.modelos_infraestructura import TrabajoPeriodico
from app.adaptadores.modelos_padron import Estudiante
from app.api.dependencias import hash_token
from app.trabajos import (  # noqa: F401 (registra los manejadores)
    aprovisionar_repositorios,
    despachar_outbox,
    materializar_sujetos,
    recolector_mapeos,
    reconciliar_accesos,
    registro,
    sync_grupos,
    sync_roster,
    sync_tareas_y_fechas,
)
from tests.apoyo import fabrica_bd

_BASE_URL_DOBLE = "https://canvas-doble.local"
_ORG = "org-valida"


def _crear_usuario_con_sesion(*, email: str) -> str:
    with fabrica_bd()() as bd:
        ahora = ahora_utc()
        usuario = Usuario(
            google_sub=secrets.token_hex(8),
            email=email,
            email_canonico=email,
            nombre="Profesora",
            activo=True,
            creado_en=ahora,
            actualizado_en=ahora,
        )
        bd.add(usuario)
        bd.flush()
        token = secrets.token_urlsafe(32)
        bd.add(
            Sesion(
                usuario_id=usuario.id,
                token_hash=hash_token(token),
                jti_oidc=secrets.token_urlsafe(16),
                creada_en=ahora,
                expira_en=ahora.replace(year=ahora.year + 1),
            )
        )
        bd.commit()
        return token


def _sesion_autenticada(cliente: TestClient, token: str) -> None:
    cliente.cookies.set("sesion", token)
    csrf = secrets.token_urlsafe(16)
    cliente.cookies.set("csrf_token", csrf)
    cliente.headers.update({"X-CSRF-Token": csrf})


def _ejecutar_trabajos_pendientes() -> None:
    with fabrica_bd()() as bd:
        while True:
            trabajo = trabajos_repo.tomar_siguiente(bd, tomado_por="test")
            if trabajo is None:
                break
            manejador = registro.obtener_manejador(trabajo.tipo)
            assert manejador is not None, f"sin manejador para {trabajo.tipo}"
            manejador(bd, trabajo)
            trabajos_repo.marcar_ok(bd, trabajo)
            bd.commit()
        bd.commit()


def _encolar_y_ejecutar(tipo: str, curso_id: str) -> None:
    with fabrica_bd()() as bd:
        trabajos_repo.encolar(
            bd,
            tipo=tipo,
            clave_idempotencia=f"test:{tipo}:{curso_id}:{ahora_utc().isoformat()}",
            max_intentos=1,
            curso_id=uuid.UUID(curso_id),
        )
        bd.commit()
    _ejecutar_trabajos_pendientes()


def _despachar_outbox() -> int:
    with fabrica_bd()() as bd:
        despachados = outbox_repo.despachar_pendientes(bd, tomado_por="test")
        bd.commit()
    return despachados


def _sincronizar(cliente: TestClient, curso_id: str) -> None:
    assert cliente.post(f"/api/cursos/{curso_id}/sincronizaciones").status_code == 202
    _ejecutar_trabajos_pendientes()


def _preparar_curso_con_tarea_activa(
    cliente: TestClient, *, slug: str, email: str
) -> tuple[str, str]:
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
    callback = cliente.post(
        "/api/vinculacion/github/callback",
        json={"state": state, "installation_id": 8001, "setup_action": "install"},
    )
    assert callback.status_code == 200, callback.text
    _sincronizar(cliente, curso_id)

    # P6: tarea de registro y recolector -> Ana Soto (2001) y Bruno Diaz (2002) VIGENTE.
    assert cliente.post(f"/api/cursos/{curso_id}/registro-github").status_code == 200
    _encolar_y_ejecutar("recolector_mapeos", curso_id)

    tarea = cliente.post(
        f"/api/cursos/{curso_id}/tareas",
        json={"nombre": "Tarea 1: Ordenamiento", "slug": "t1", "canvas_assignment_id": 9101},
    )
    assert tarea.status_code == 200, tarea.text
    tarea_id = tarea.json()["id"]
    _sincronizar(cliente, curso_id)  # fechas y visibilidad de la entrega recien vinculada

    activada = cliente.post(f"/api/cursos/{curso_id}/tareas/{tarea_id}/activar")
    assert activada.status_code == 200, activada.text
    _ejecutar_trabajos_pendientes()  # materializar -> aprovisionar (sin pulsar nada mas)
    return curso_id, tarea_id


def _repositorios(cliente: TestClient, curso_id: str, tarea_id: str) -> dict:
    respuesta = cliente.get(f"/api/cursos/{curso_id}/tareas/{tarea_id}/repositorios")
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def test_activar_crea_los_repositorios_de_quien_tiene_cuenta_y_explica_a_los_demas(
    cliente: TestClient,
):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-p8-a", email="profe.p8a@gmail.com"
    )
    datos = _repositorios(cliente, curso_id, tarea_id)
    resumen = datos["resumen"]
    # CA-8.9-01: contadores separados; DEGRADADO nunca suma a problemas.
    assert resumen["sujetos_activos"] == 5
    assert resumen["degradados"] == 2
    assert resumen["esperando_informacion"] == 3
    assert resumen["operativos"] == 0
    assert resumen["error_transitorio"] + resumen["error_permanente"] + resumen["bloqueados"] == 0

    por_sujeto = {f["sujeto"]: f for f in datos["filas"]}
    ana = por_sujeto["Ana Soto"]
    assert ana["nombre"] == "pds-p8-a-t1-e2001-ana-soto"
    assert ana["estado"] == "DEGRADADO"
    assert ana["motivo"] == "FALTA_ACEPTAR_INVITACION_GITHUB"
    assert ana["acceso_estado"] == "INVITADO"
    assert ana["acceso_docente"] == "CONCEDIDO"
    assert ana["url_html"] == f"https://github.com/{_ORG}/pds-p8-a-t1-e2001-ana-soto"
    # CA-8.5-05: quien espera siempre dice por que.
    assert por_sujeto["Elena Rojas"]["estado"] == "ESPERANDO_INFORMACION"
    assert por_sujeto["Elena Rojas"]["motivo"] == "SIN_MAPEO_GITHUB"

    # R2.3.10: activar programo los barridos del curso.
    with fabrica_bd()() as bd:
        tipos = {
            p.tipo
            for p in bd.query(TrabajoPeriodico).filter(
                TrabajoPeriodico.curso_id == uuid.UUID(curso_id)
            )
        }
    assert {"materializar_sujetos", "aprovisionar_repositorios", "reconciliar_accesos"} <= tipos


def test_el_aviso_por_canvas_es_por_persona_y_sale_por_el_outbox(cliente: TestClient):
    curso_id, _tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-p8-b", email="profe.p8b@gmail.com"
    )
    with fabrica_bd()() as bd:
        pendientes = (
            bd.query(MensajeSaliente).filter(MensajeSaliente.curso_id == uuid.UUID(curso_id)).all()
        )
        assert len(pendientes) == 2
        assert {m.evento for m in pendientes} == {"repositorio_disponible"}
        assert all(m.estado == "PENDIENTE" for m in pendientes)

    assert _despachar_outbox() == 2
    with fabrica_bd()() as bd:
        enviados = (
            bd.query(MensajeSaliente).filter(MensajeSaliente.curso_id == uuid.UUID(curso_id)).all()
        )
        assert all(m.estado == "ENVIADO" for m in enviados)
        cuerpo = next(m.cuerpo_renderizado for m in enviados if m.destinatario == "Ana Soto")
    assert cuerpo is not None
    assert "https://github.com/org-valida/pds-p8-b-t1-e2001-ana-soto" in cuerpo
    assert "no encontrado" in cuerpo
    assert "(America/Santiago)" in cuerpo

    # Repetir la materializacion no crea repositorios ni mensajes nuevos.
    _encolar_y_ejecutar("materializar_sujetos", curso_id)
    _encolar_y_ejecutar("reconciliar_accesos", curso_id)
    with fabrica_bd()() as bd:
        assert (
            bd.query(Repositorio).filter(Repositorio.curso_id == uuid.UUID(curso_id)).count() == 5
        )
        assert (
            bd.query(MensajeSaliente)
            .filter(MensajeSaliente.curso_id == uuid.UUID(curso_id))
            .count()
            == 2
        )


def test_ca_8_6_03_aceptar_la_invitacion_lleva_a_operativo(cliente: TestClient):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-p8-c", email="profe.p8c@gmail.com"
    )
    aceptar_invitacion_doble(_ORG, "pds-p8-c-t1-e2001-ana-soto", "Estudiante-Valido")
    _encolar_y_ejecutar("reconciliar_accesos", curso_id)

    por_sujeto = {f["sujeto"]: f for f in _repositorios(cliente, curso_id, tarea_id)["filas"]}
    assert por_sujeto["Ana Soto"]["estado"] == "OPERATIVO"
    assert por_sujeto["Ana Soto"]["acceso_estado"] == "ACEPTADO"
    assert por_sujeto["Bruno Diaz"]["estado"] == "DEGRADADO"

    with fabrica_bd()() as bd:
        eventos = [
            m.evento
            for m in bd.query(MensajeSaliente).filter(
                MensajeSaliente.curso_id == uuid.UUID(curso_id),
                MensajeSaliente.destinatario == "Ana Soto",
            )
        ]
    assert sorted(eventos) == ["invitacion_aceptada", "repositorio_disponible"]

    pendientes = cliente.get(f"/api/cursos/{curso_id}/pendientes").json()
    assert [f["nombre"] for f in pendientes["bloque_4_invitaciones_sin_aceptar"]] == ["Bruno Diaz"]


def test_ca_8_5_02_un_mapeo_tardio_crea_su_repositorio_sin_tocar_los_demas(cliente: TestClient):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-p8-d", email="profe.p8d@gmail.com"
    )
    with fabrica_bd()() as bd:
        elena = (
            bd.query(Estudiante)
            .filter(Estudiante.curso_id == uuid.UUID(curso_id), Estudiante.nombre == "Elena Rojas")
            .one()
        )
        antes = {
            r.id: r.actualizado_en
            for r in bd.query(Repositorio).filter(
                Repositorio.curso_id == uuid.UUID(curso_id), Repositorio.github_repo_id.is_not(None)
            )
        }
    declarado = cliente.post(
        f"/api/cursos/{curso_id}/personas/{elena.id}/mapeo", json={"login": "cuenta-personal"}
    )
    assert declarado.status_code == 200, declarado.text
    _ejecutar_trabajos_pendientes()

    datos = _repositorios(cliente, curso_id, tarea_id)
    por_sujeto = {f["sujeto"]: f for f in datos["filas"]}
    assert por_sujeto["Elena Rojas"]["estado"] == "DEGRADADO"
    assert datos["resumen"]["creados"] == 3
    with fabrica_bd()() as bd:
        for repositorio_id, actualizado in antes.items():
            assert bd.get(Repositorio, repositorio_id).actualizado_en == actualizado


def test_fechas_de_la_entrega_en_modo_lectura(cliente: TestClient):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-p8-e", email="profe.p8e@gmail.com"
    )
    respuesta = cliente.get(f"/api/cursos/{curso_id}/tareas/{tarea_id}/entregas/fechas")
    assert respuesta.status_code == 200, respuesta.text
    [entrega] = respuesta.json()
    assert entrega["cierre_base"] == "01-10-2026 20:59 (America/Santiago)"
    assert entrega["sujetos_con_fecha"] == 5
    assert entrega["excepciones"] == []


def test_reintentar_y_sustituir_solo_donde_corresponde(cliente: TestClient):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-p8-f", email="profe.p8f@gmail.com"
    )
    fila = next(
        f for f in _repositorios(cliente, curso_id, tarea_id)["filas"] if f["sujeto"] == "Ana Soto"
    )
    base = f"/api/cursos/{curso_id}/tareas/{tarea_id}/repositorios/{fila['repositorio_id']}"
    assert cliente.post(f"{base}/reintentar").status_code == 409
    sustituir = cliente.post(f"{base}/sustituir", json={"confirmacion": "otro-nombre"})
    assert sustituir.status_code == 422
    sustituir = cliente.post(f"{base}/sustituir", json={"confirmacion": fila["nombre"]})
    assert sustituir.status_code == 409  # solo desde INACCESIBLE (S8.11.2)
