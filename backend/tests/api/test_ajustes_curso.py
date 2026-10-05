"""Ajustes, renovación e impacto calculados desde PostgreSQL aislado y proveedores dobles."""

import secrets
import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_aprovisionamiento import MensajeSaliente, Repositorio
from app.adaptadores.modelos_canvas import CredencialCanvas
from app.adaptadores.modelos_correccion import AsignacionCorreccion, Correccion
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_github import AccesoDocenteRepositorio, VerificacionVinculacion
from app.adaptadores.modelos_identidad import Sesion
from app.adaptadores.modelos_infraestructura import Bitacora, Trabajo
from tests.api.test_correccion import _preparar
from tests.api.test_cursos import _crear_curso, _crear_usuario_con_sesion, _sesion_autenticada
from tests.api.test_informe import _miembro
from tests.apoyo import fabrica_bd


def _curso(cliente: TestClient, slug: str = "ajustes") -> dict:
    _, token = _crear_usuario_con_sesion(email=f"{slug}@gmail.com")
    _sesion_autenticada(cliente, token)
    return _crear_curso(cliente, slug=slug)


def test_ajustes_parciales_validan_y_auditan_sin_renombrar_identificadores(cliente: TestClient):
    curso = _curso(cliente)
    ruta = f"/api/cursos/{curso['id']}"
    respuesta = cliente.patch(ruta, json={"nombre": "  Nuevo nombre  ", "zona_horaria": "UTC",
        "umbral_dias_sin_actividad": 12, "umbral_desbalance_pct": 80})
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["nombre"] == "Nuevo nombre"
    assert respuesta.json()["slug"] == curso["slug"]
    assert respuesta.json()["umbral_dias_sin_actividad"] == 12
    assert cliente.get("/api/cursos").json()[0]["zona_horaria"] == "UTC"
    with fabrica_bd()() as bd:
        audit = bd.query(Bitacora).filter_by(accion="CURSO_AJUSTES_ACTUALIZADOS").one()
        assert audit.antes["zona_horaria"] == "America/Santiago"
        assert audit.despues["zona_horaria"] == "UTC"
        assert bd.query(Trabajo).filter_by(tipo="agregar_metricas").count() == 1
    # Un PATCH idéntico no duplica el recálculo ni la auditoría.
    assert cliente.patch(ruta, json={"zona_horaria": "UTC"}).status_code == 200
    with fabrica_bd()() as bd:
        assert bd.query(Trabajo).filter_by(tipo="agregar_metricas").count() == 1
    cliente.headers.pop("X-CSRF-Token")
    assert cliente.patch(ruta, json={"nombre": "No autorizado"}).status_code == 403


@pytest.mark.parametrize("datos", [
    {}, {"nombre": None}, {"nombre": "  "}, {"zona_horaria": "No/Existe"},
    {"umbral_dias_sin_actividad": 0}, {"umbral_dias_sin_actividad": 31},
    {"umbral_desbalance_pct": 49}, {"umbral_desbalance_pct": 96},
    {"umbral_desbalance_pct": True}, {"slug": "nuevo"},
])
def test_ajustes_rechazan_valores_invalidos(cliente: TestClient, datos: dict):
    curso = _curso(cliente)
    assert cliente.patch(f"/api/cursos/{curso['id']}", json=datos).status_code == 422
    assert cliente.get("/api/cursos").json()[0]["nombre"] == curso["nombre"]


def test_ajustes_exigen_profesor_y_exponen_via_compartida(cliente: TestClient):
    curso = _curso(cliente)
    token, mid = _miembro(curso["id"])
    with fabrica_bd()() as bd:
        bd.get(MembresiaCurso, mid).es_via_compartida = True
        bd.commit()
    equipo = cliente.get(f"/api/cursos/{curso['id']}/equipo").json()
    assert next(m for m in equipo if m["membresia_id"] == str(mid))["es_via_compartida"]
    _sesion_autenticada(cliente, token)
    assert cliente.get(f"/api/cursos/{curso['id']}/contexto").json()["es_via_compartida"]
    assert cliente.patch(f"/api/cursos/{curso['id']}", json={"nombre": "No"}).status_code == 403


def test_renovar_distingue_curso_por_id_y_recupera_operativa_sin_borrar_historial(cliente: TestClient):
    curso = _curso(cliente)
    ruta = f"/api/cursos/{curso['id']}/vinculacion/canvas"
    credencial = {"token": "valido", "canvas_base_url": "https://canvas-doble.local", "canvas_course_id": 5001}
    assert cliente.post(ruta, json=credencial).status_code == 200
    disponible = cliente.post(f"{ruta}/cursos-disponibles", json=credencial).json()[0]
    assert disponible["ya_vinculado_a_id"] == curso["id"] and disponible["es_vinculo_actual"]
    otro = _crear_curso(cliente, slug="otro-igual-nombre")
    ajeno = cliente.post(f"/api/cursos/{otro['id']}/vinculacion/canvas/cursos-disponibles", json=credencial).json()[0]
    assert ajeno["ya_vinculado_a"] == curso["nombre"] and not ajeno["es_vinculo_actual"]
    assert cliente.post(f"/api/cursos/{otro['id']}/vinculacion/canvas", json=credencial).status_code == 422
    with fabrica_bd()() as bd:
        cid = uuid.UUID(curso["id"])
        token = bd.query(CredencialCanvas).filter_by(curso_id=cid).one()
        token.estado, token.orden_respaldo = "RETIRADA", 4
        bd.get(Curso, cid).estado = "CANVAS_DESVINCULADO"
        for item in ("4", "5-bis", "14", "18"):
            bd.add(VerificacionVinculacion(curso_id=cid, ejecucion_id=uuid.uuid4(), item=item,
                origen="CHECKLIST", resultado="CORRECTO", detalle={}, ejecutada_en=ahora_utc()))
        bd.add(Trabajo(curso_id=cid, tipo="sync_roster", clave_idempotencia="espera",
            estado="ESPERANDO_CREDENCIAL", max_intentos=4, creado_en=ahora_utc()))
        bd.add(MensajeSaliente(curso_id=cid, canal="CANVAS_CONVERSACION", evento="recordatorio",
            clave_idempotencia="mensaje-espera", destinatario="2001", plantilla="recordatorio",
            estado="ESPERANDO_CREDENCIAL", creado_en=ahora_utc()))
        bd.commit()
    renovada = cliente.post(ruta, json=credencial)
    assert renovada.status_code == 200, renovada.text
    assert renovada.json()["orden_respaldo"] == 0
    with fabrica_bd()() as bd:
        assert bd.query(CredencialCanvas).filter_by(curso_id=cid).one().estado == "VALIDA"
        assert bd.query(Trabajo).filter_by(clave_idempotencia="espera").one().estado == "PENDIENTE"
        assert bd.query(MensajeSaliente).one().estado == "PENDIENTE"
        assert bd.query(VerificacionVinculacion).filter_by(curso_id=cid, resultado="CORRECTO").count() == 4
        assert bd.query(VerificacionVinculacion).filter_by(curso_id=cid, resultado="NO_VERIFICADO").count() == 19
        trabajo = bd.query(Trabajo).filter_by(tipo="ejecutar_checklist_vinculacion").one()
        assert len(trabajo.payload["solo_items"]) == 17
        assert not {"14", "18", "5-bis", "17-bis"} & set(trabajo.payload["solo_items"])
    assert cliente.post(ruta, json={**credencial, "canvas_course_id": 999}).status_code == 409


def test_renovar_libera_orden_cero_invalido_sin_desplazar_valida(cliente: TestClient):
    curso = _curso(cliente)
    ruta = f"/api/cursos/{curso['id']}/vinculacion/canvas"
    datos = {"token": "valido", "canvas_base_url": "https://canvas-doble.local", "canvas_course_id": 5001}
    assert cliente.post(ruta, json=datos).status_code == 200
    _, otro_mid = _miembro(curso["id"], rol="PROFESOR")
    with fabrica_bd()() as bd:
        cid = uuid.UUID(curso["id"])
        propia = bd.query(CredencialCanvas).filter_by(curso_id=cid).one()
        propia.orden_respaldo = 2
        bd.flush()
        bd.add(CredencialCanvas(curso_id=cid, usuario_id=bd.get(MembresiaCurso, otro_mid).usuario_id,
            token_cifrado=b"", nonce=b"", huella="invalidada", canvas_user_id=1002,
            estado="INVALIDA", orden_respaldo=0, consentimiento_en=ahora_utc()))
        bd.commit()
    assert cliente.post(ruta, json=datos).json()["orden_respaldo"] == 0
    with fabrica_bd()() as bd:
        assert bd.query(CredencialCanvas).filter_by(curso_id=cid, orden_respaldo=0).one().estado == "VALIDA"


def test_impacto_retiro_coincide_con_asignaciones_y_accesos_locales(cliente: TestClient):
    curso, _, entrega, _, (_, mid), _ = _preparar(cliente, "impacto-real")
    reparto = cliente.post(f"/api/cursos/{curso}/correccion/{entrega}/reparto/aplicar", json={"criterio": "EQUITATIVO"})
    assert reparto.status_code == 200, reparto.text
    with fabrica_bd()() as bd:
        miembro = bd.get(MembresiaCurso, mid)
        miembro.org_github_estado = "ACTIVA"
        # Sesiones expiradas no tienen acceso que revocar.
        bd.add(Sesion(usuario_id=miembro.usuario_id, token_hash=secrets.token_hex(32),
            jti_oidc=secrets.token_hex(16), creada_en=ahora_utc()-timedelta(days=9),
            expira_en=ahora_utc()-timedelta(days=1)))
        repos = bd.query(Repositorio).filter_by(curso_id=uuid.UUID(curso)).all()
        bd.query(AccesoDocenteRepositorio).filter(AccesoDocenteRepositorio.repositorio_id.in_([r.id for r in repos])).delete()
        # Mismo repositorio por dos vías se cuenta una sola vez.
        bd.add_all([AccesoDocenteRepositorio(repositorio_id=repos[0].id, via="TEAM", estado="CONCEDIDO"),
            AccesoDocenteRepositorio(repositorio_id=repos[0].id, membresia_id=mid, via="COLABORADOR", estado="CONCEDIDO")])
        asignadas = bd.query(AsignacionCorreccion).filter_by(membresia_id=mid).all()
        assert len(asignadas) >= 2
        publicada = bd.query(Correccion).filter_by(entrega_id=asignadas[0].entrega_id, sujeto_id=asignadas[0].sujeto_id).one()
        publicada.estado = "PUBLICADA"
        esperadas = len(asignadas)-1
        bd.commit()
    ruta = f"/api/cursos/{curso}/miembros/{mid}/impacto-retiro"
    impacto = cliente.get(ruta)
    assert impacto.status_code == 200, impacto.text
    assert impacto.json() == {"sesiones_a_cerrar": 1, "repositorios_perdidos": 1,
        "entregas_sin_corrector": 1, "asignaciones_sin_corrector": esperadas, "es_profesor": False}
    retirada = cliente.post(f"/api/cursos/{curso}/equipo/{mid}/retiro")
    assert retirada.status_code == 200, retirada.text
    with fabrica_bd()() as bd:
        assert bd.query(AsignacionCorreccion).filter_by(membresia_id=mid).count() == 1
    assert cliente.get(ruta).json()["asignaciones_sin_corrector"] == 0
