"""Regresiones de invitaciones, cierre atomico, identidad y arranque del login."""

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

from fastapi.testclient import TestClient

from app.adaptadores import invitaciones_correo, outbox_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_aprovisionamiento import MensajeSaliente
from app.adaptadores.modelos_curso import Curso, InvitacionEquipo, MembresiaCurso
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.adaptadores.modelos_infraestructura import Trabajo
from app.adaptadores.proveedor_correo import FalloCorreo, ResultadoCorreo
from app.infraestructura.config import obtener_configuracion
from app.main import app
from app.trabajos import sincronizar_acceso_docente
from tests.api.test_cursos import _crear_curso, _crear_usuario_con_sesion, _sesion_autenticada
from tests.api.test_vinculacion_github import _iniciar_y_extraer_state
from tests.apoyo import fabrica_bd


def curso_autenticado(cliente):
    uid, token = _crear_usuario_con_sesion(email="profe.correcciones@gmail.com")
    _sesion_autenticada(cliente, token)
    return uuid.UUID(uid), _crear_curso(cliente, slug="correcciones")


def invitar(cliente, curso, email="ayudantecorrecciones@gmail.com", rol="AYUDANTE"):
    r = cliente.post(
        f"/api/cursos/{curso['id']}/equipo/invitaciones",
        json={"email": email, "rol": rol, "permisos": []},
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_arranque_recupera_get_sin_iniciar_oauth_y_conserva_post(cliente):
    for path in ("/auth/google/inicio", "/auth/confirmar"):
        r = cliente.get(path, follow_redirects=False)
        assert r.status_code == 302
        assert r.headers["location"].endswith("/acceso?motivo=SERVICIO_REINICIADO")
        assert r.headers["cache-control"] == "no-store"
        assert "set-cookie" not in r.headers
    r = cliente.post("/auth/google/inicio", data={"destino": "/cursos"}, follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"].startswith("https://accounts.google.com/")
    assert "oidc_txn=" in r.headers["set-cookie"]
    assert cliente.get("/api/salud").json()["servicio"] == "api"


def test_invitacion_persistente_token_cifrado_reenvio_y_tope(cliente):
    _, curso = curso_autenticado(cliente)
    base = f"/api/cursos/{curso['id']}/equipo/invitaciones"
    i = invitar(cliente, curso)
    token = i["enlace"].rsplit("/", 1)[1]
    with fabrica_bd()() as bd:
        m = bd.query(MensajeSaliente).one()
        assert token not in json.dumps(m.referencia)
        assert token not in bd.query(InvitacionEquipo).one().token_hash
        assert m.estado == "PENDIENTE"
    r = cliente.get(base)
    assert r.headers["cache-control"] == "no-store"
    assert r.json()[0]["enlace"] == i["enlace"]
    for _ in range(3):
        old = i
        r = cliente.post(f"{base}/{i['id']}/reenviar")
        assert r.status_code == 200, r.text
        i = r.json()
        assert i["enlace"] != old["enlace"]
        assert (
            cliente.get("/api/invitaciones/" + old["enlace"].rsplit("/", 1)[1]).json()["estado"]
            == "REVOCADA"
        )
    assert i["reenvios_restantes"] == 0
    assert cliente.post(f"{base}/{i['id']}/reenviar").status_code == 409
    assert (
        cliente.get("/api/invitaciones/" + i["enlace"].rsplit("/", 1)[1]).json()["estado"]
        == "PENDIENTE"
    )


def test_aceptacion_no_permite_cuenta_distinta_ni_repeticion(cliente):
    _, curso = curso_autenticado(cliente)
    i = invitar(cliente, curso)
    ruta = "/api/invitaciones/" + i["enlace"].rsplit("/", 1)[1] + "/aceptar"
    assert cliente.post(ruta).status_code == 409
    _, token = _crear_usuario_con_sesion(email="ayudantecorrecciones@gmail.com")
    _sesion_autenticada(cliente, token)
    assert cliente.post(ruta).status_code == 200
    assert cliente.post(ruta).status_code == 409
    assert cliente.get(f"/api/cursos/{curso['id']}/equipo/invitaciones").status_code == 403
    with fabrica_bd()() as bd:
        assert bd.query(MembresiaCurso).count() == 2
        assert bd.query(Trabajo).filter_by(tipo="sincronizar_acceso_docente").count() == 1


def test_outbox_reintenta_sin_duplicar_y_respeta_revocacion(cliente, monkeypatch):
    _, curso = curso_autenticado(cliente)
    i = invitar(cliente, curso)
    settings = obtener_configuracion().model_copy(update={"comunicaciones_salientes": "activadas"})
    monkeypatch.setattr(invitaciones_correo, "obtener_configuracion", lambda: settings)
    envios = []

    class Proveedor:
        def enviar(self, **kwargs):
            envios.append(kwargs)
            if len(envios) == 1:
                raise FalloCorreo("temporal", reintentable=True)
            return ResultadoCorreo("correo-1")

    monkeypatch.setattr(invitaciones_correo, "crear_proveedor_correo", lambda _: Proveedor())
    with fabrica_bd()() as bd:
        assert outbox_repo.despachar_pendientes(bd, tomado_por="test") == 1
        m = bd.query(MensajeSaliente).one()
        assert m.estado == "REINTENTAR"
        m.programado_para = ahora_utc() - timedelta(seconds=1)
        bd.commit()
        assert outbox_repo.despachar_pendientes(bd, tomado_por="test") == 1
        assert m.estado == "ENVIADO"
        bd.commit()
        assert outbox_repo.despachar_pendientes(bd, tomado_por="test") == 0
    assert envios[0] == envios[1]
    assert i["enlace"] in envios[0]["texto"]
    assert "<table" in envios[0]["html"]
    i2 = invitar(cliente, curso, email="otro@gmail.com")
    assert (
        cliente.delete(f"/api/cursos/{curso['id']}/equipo/invitaciones/{i2['id']}").status_code
        == 200
    )
    with fabrica_bd()() as bd:
        outbox_repo.despachar_pendientes(bd, tomado_por="test")
        assert len(envios) == 2


def test_correo_pausado_y_cuota_de_diez_no_descartan_invitacion(cliente, monkeypatch):
    _, curso = curso_autenticado(cliente)
    invitar(cliente, curso)
    with fabrica_bd()() as bd:
        outbox_repo.despachar_pendientes(bd, tomado_por="test")
        assert bd.query(MensajeSaliente).one().motivo_estado == "COMUNICACIONES_PAUSADAS"
        bd.commit()
    for n in range(10):
        invitar(cliente, curso, email=f"cuota{n}@gmail.com")
    settings = obtener_configuracion().model_copy(update={"comunicaciones_salientes": "activadas"})
    monkeypatch.setattr(invitaciones_correo, "obtener_configuracion", lambda: settings)

    class Proveedor:
        def enviar(self, **kwargs):
            return ResultadoCorreo(kwargs["clave_idempotencia"])

    monkeypatch.setattr(invitaciones_correo, "crear_proveedor_correo", lambda _: Proveedor())
    with fabrica_bd()() as bd:
        bd.query(MensajeSaliente).update({"programado_para": None})
        outbox_repo.despachar_pendientes(bd, tomado_por="test")
        assert bd.query(MensajeSaliente).filter_by(estado="ENVIADO").count() == 10
        assert (
            bd.query(MensajeSaliente)
            .filter_by(estado="DIFERIDO", motivo_estado="CUOTA_AGOTADA")
            .count()
            == 1
        )
        bd.commit()


def test_cierre_ultimo_profesor_no_revoca_sesion(cliente):
    uid, curso = curso_autenticado(cliente)
    with fabrica_bd()() as bd:
        bd.get(Curso, uuid.UUID(curso["id"])).estado = "ACTIVO"
        bd.commit()
    assert cliente.get("/api/perfil/cierre").json()["puede_cerrar"] is False
    r = cliente.delete("/api/perfil")
    assert r.status_code == 409
    assert r.json()["detail"]["cursos"][0]["curso_id"] == curso["id"]
    assert cliente.get("/api/perfil").status_code == 200
    with fabrica_bd()() as bd:
        assert bd.get(Usuario, uid).activo
        assert bd.query(MembresiaCurso).one().estado == "ACTIVA"


def test_dos_cierres_simultaneos_conservan_un_profesor(cliente):
    _, curso = curso_autenticado(cliente)
    uid2, token2 = _crear_usuario_con_sesion(email="profe.segundo@gmail.com")
    token1 = cliente.cookies.get("sesion")
    with fabrica_bd()() as bd:
        bd.get(Curso, uuid.UUID(curso["id"])).estado = "ACTIVO"
        bd.add(
            MembresiaCurso(
                curso_id=uuid.UUID(curso["id"]),
                usuario_id=uuid.UUID(uid2),
                rol="PROFESOR",
                permisos=[],
                estado="ACTIVA",
                version=1,
                creada_en=ahora_utc(),
            )
        )
        bd.commit()
    barrera = Barrier(2)

    def cerrar(token):
        with TestClient(app) as c:
            _sesion_autenticada(c, token)
            barrera.wait(timeout=5)
            return c.delete("/api/perfil").status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(cerrar, [token1, token2])) == [200, 409]
    with fabrica_bd()() as bd:
        assert bd.query(Usuario).filter_by(activo=True).count() == 1
        assert bd.query(MembresiaCurso).filter_by(estado="ACTIVA", rol="PROFESOR").count() == 1
        assert bd.query(Sesion).filter(Sesion.revocada_en.is_not(None)).count() == 1


def test_github_declarado_despues_de_vincular_y_retiro_de_cuenta_anterior(cliente):
    uid, curso = curso_autenticado(cliente)
    state = _iniciar_y_extraer_state(cliente, curso["id"])
    assert (
        cliente.post(
            "/api/vinculacion/github/callback",
            json={"state": state, "installation_id": 8001, "setup_action": "install"},
        ).status_code
        == 200
    )
    assert (
        cliente.put(
            "/api/perfil/cuenta-github", json={"login": "cuenta-personal", "consiento": False}
        ).status_code
        == 422
    )
    assert (
        cliente.put(
            "/api/perfil/cuenta-github", json={"login": "cuenta-personal", "consiento": True}
        ).status_code
        == 200
    )
    with fabrica_bd()() as bd:
        trabajo = bd.query(Trabajo).filter_by(tipo="sincronizar_acceso_docente").one()
        sincronizar_acceso_docente.ejecutar(bd, trabajo)
        assert bd.get(Usuario, uid).cuenta_github_id == 90002
        assert bd.query(MembresiaCurso).one().org_github_estado in {"ACTIVA", "PENDIENTE"}
        trabajo.estado = "OK"
        bd.commit()
    assert cliente.delete("/api/perfil/cuenta-github").status_code == 200
    with fabrica_bd()() as bd:
        trabajo = (
            bd.query(Trabajo).filter_by(tipo="sincronizar_acceso_docente", estado="PENDIENTE").one()
        )
        assert trabajo.payload["login_anterior"] == "cuenta-personal"
        sincronizar_acceso_docente.ejecutar(bd, trabajo)
        assert bd.query(MembresiaCurso).one().org_github_estado == "NO_APLICA"
        bd.commit()


def test_cuenta_github_no_puede_ser_de_otro_docente(cliente):
    curso_autenticado(cliente)
    assert (
        cliente.put(
            "/api/perfil/cuenta-github", json={"login": "cuenta-personal", "consiento": True}
        ).status_code
        == 200
    )
    _, token = _crear_usuario_con_sesion(email="competidor@gmail.com")
    _sesion_autenticada(cliente, token)
    assert (
        cliente.put(
            "/api/perfil/cuenta-github", json={"login": "cuenta-personal", "consiento": True}
        ).status_code
        == 422
    )


def test_cerrar_retira_canvas_y_promueve_respaldo(cliente):
    from app.adaptadores.modelos_canvas import CredencialCanvas

    uid, curso = curso_autenticado(cliente)
    uid2, _ = _crear_usuario_con_sesion(email="respaldo@gmail.com")
    with fabrica_bd()() as bd:
        bd.add(
            MembresiaCurso(
                curso_id=uuid.UUID(curso["id"]),
                usuario_id=uuid.UUID(uid2),
                rol="PROFESOR",
                permisos=[],
                estado="ACTIVA",
                version=1,
                creada_en=ahora_utc(),
            )
        )
        for pos, usuario_id in enumerate([uid, uuid.UUID(uid2)]):
            bd.add(
                CredencialCanvas(
                    curso_id=uuid.UUID(curso["id"]),
                    usuario_id=usuario_id,
                    token_cifrado=b"cifrado-prueba",
                    nonce=b"nonce-prueba",
                    huella=f"huella-{pos}",
                    canvas_user_id=100 + pos,
                    estado="VALIDA",
                    orden_respaldo=pos,
                    version_clave=1,
                    consentimiento_en=ahora_utc(),
                )
            )
        bd.commit()
    assert cliente.delete("/api/perfil").status_code == 200
    with fabrica_bd()() as bd:
        retirada = bd.query(CredencialCanvas).filter_by(usuario_id=uid).one()
        assert retirada.estado == "RETIRADA" and retirada.token_cifrado == b""
        assert (
            bd.query(CredencialCanvas).filter_by(usuario_id=uuid.UUID(uid2)).one().orden_respaldo
            == 0
        )
        assert bd.query(Trabajo).filter_by(tipo="revocar_acceso_docente").count() == 1
    assert cliente.get("/api/perfil").status_code == 401


def test_cerrar_sin_respaldo_degrada_canvas_y_registra_incidencia(cliente):
    from app.adaptadores.modelos_canvas import CredencialCanvas
    from app.adaptadores.modelos_infraestructura import Incidencia

    _, curso = curso_autenticado(cliente)
    assert (
        cliente.post(
            f"/api/cursos/{curso['id']}/vinculacion/canvas",
            json={
                "token": "valido",
                "canvas_base_url": "https://canvas-doble.local",
                "canvas_course_id": 5001,
            },
        ).status_code
        == 200
    )
    assert cliente.delete("/api/perfil").status_code == 200
    with fabrica_bd()() as bd:
        assert bd.query(CredencialCanvas).one().estado == "RETIRADA"
        assert bd.get(Curso, uuid.UUID(curso["id"])).estado == "CANVAS_DESVINCULADO"
        assert bd.query(Incidencia).filter_by(tipo="CANVAS_CREDENCIAL_INVALIDA").count() == 1


def test_github_no_admite_cuenta_de_estudiante_en_otro_curso(cliente):
    from tests.api.test_personas_mapeo import _preparar_curso_con_roster

    curso = _preparar_curso_con_roster(cliente, slug="elegibilidad", email="origen@gmail.com")
    persona = cliente.get(f"/api/cursos/{curso['id']}/personas").json()["estudiantes"][0]
    r = cliente.post(
        f"/api/cursos/{curso['id']}/personas/{persona['id']}/mapeo",
        json={"login": "estudiante-valido"},
    )
    assert r.status_code == 200, r.text
    _, token = _crear_usuario_con_sesion(email="otrocurso@gmail.com")
    _sesion_autenticada(cliente, token)
    r = cliente.put(
        "/api/perfil/cuenta-github", json={"login": "estudiante-valido", "consiento": True}
    )
    assert r.status_code == 422, r.text
    assert "estudiante" in r.json()["detail"]


def test_retiro_no_expulsa_membresia_github_preexistente(cliente, monkeypatch):
    from app.adaptadores.cliente_github import ClienteGitHubDoble

    _, curso = curso_autenticado(cliente)
    state = _iniciar_y_extraer_state(cliente, curso["id"])
    cliente.post(
        "/api/vinculacion/github/callback",
        json={"state": state, "installation_id": 8001, "setup_action": "install"},
    )
    quitados = []

    class GitHubPreexistente(ClienteGitHubDoble):
        def obtener_membresia_organizacion(self, *args):
            return "active"

        def quitar_miembro_organizacion(self, *args):
            quitados.append(args)

    monkeypatch.setattr(
        sincronizar_acceso_docente,
        "crear_cliente_github_desde_config",
        lambda _: GitHubPreexistente(),
    )
    cliente.put("/api/perfil/cuenta-github", json={"login": "cuenta-personal", "consiento": True})
    with fabrica_bd()() as bd:
        trabajo = bd.query(Trabajo).filter_by(tipo="sincronizar_acceso_docente").one()
        sincronizar_acceso_docente.ejecutar(bd, trabajo)
        assert not bd.query(MembresiaCurso).one().org_github_alta_por_app
        trabajo.estado = "OK"
        bd.commit()
    cliente.delete("/api/perfil/cuenta-github")
    with fabrica_bd()() as bd:
        trabajo = (
            bd.query(Trabajo).filter_by(tipo="sincronizar_acceso_docente", estado="PENDIENTE").one()
        )
        sincronizar_acceso_docente.ejecutar(bd, trabajo)
        bd.commit()
    assert quitados == []
