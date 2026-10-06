"""Regresiones de archivo, roles, realineación, invitaciones y grano de notas."""

import uuid
from dataclasses import replace
from datetime import timedelta

from fastapi.testclient import TestClient

from app.adaptadores import (
    cliente_canvas,
    programacion_repo,
    realineacion_repo,
    tareas_repo,
    trabajos_repo,
)
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_aprovisionamiento import (
    AccesoRepositorio,
    MensajeSaliente,
    Repositorio,
    Sujeto,
)
from app.adaptadores.modelos_correccion import AsignacionCorreccion, Correccion
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Bitacora, Trabajo, TrabajoPeriodico
from app.adaptadores.modelos_padron import Matricula, Seccion
from app.adaptadores.modelos_tarea import Entrega
from app.trabajos.ejecutor import _procesar_un_trabajo
from tests.api.test_correccion import _preparar
from tests.api.test_cursos import _sesion_autenticada
from tests.api.test_limitaciones_frontend import preparar
from tests.apoyo import fabrica_bd


def test_roles_adicionales_se_paginan_y_nunca_incluyen_docentes(monkeypatch):
    import httpx

    llamadas = []

    def get(_cliente, url, **kwargs):
        params = httpx.URL(url).params
        llamadas.append(params)
        base = {
            "id": 11,
            "user_id": 2001,
            "course_section_id": 101,
            "type": "StudentEnrollment",
            "enrollment_state": "active",
            "user": {"name": "Ana"},
        }
        items = [base]
        if "role_id[]" in params:
            items.extend(
                [
                    {**base, "id": 12, "user_id": 2002, "role_id": 42},
                    {**base, "id": 13, "user_id": 2003, "type": "TeacherEnrollment", "role_id": 43},
                ]
            )
        return httpx.Response(200, json=items, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.Client, "get", get)
    resultado = cliente_canvas.ClienteCanvasReal(
        "https://canvas.example.test"
    ).obtener_roster_paginado("token-ensayo", 5001, roles_extra=[42, 43])
    assert [m.canvas_user_id for m in resultado.items] == [2001, 2002]
    assert llamadas[0]["type[]"] == "StudentEnrollment"
    assert llamadas[1].get_list("role_id[]") == ["42", "43"]


def test_sincronizar_refleja_el_ajuste_individual_cambiado_en_canvas(
    cliente: TestClient, monkeypatch
):
    cid, eid, _ = _grupal(cliente)
    ruta = f"/api/cursos/{cid}/entregas/{eid}/calificacion-individual"
    assert not cliente.get(ruta).json()["individual"]
    original = cliente_canvas.ClienteCanvasDoble.obtener_assignments_paginado

    def leer_ajuste_canvas(self, token, canvas_course_id):
        resultado = original(self, token, canvas_course_id)
        return replace(
            resultado,
            items=[
                replace(a, payload={**a.payload, "grade_group_students_individually": True})
                if a.canvas_assignment_id == 9102
                else a
                for a in resultado.items
            ],
        )

    monkeypatch.setattr(
        cliente_canvas.ClienteCanvasDoble, "obtener_assignments_paginado", leer_ajuste_canvas
    )
    with fabrica_bd()() as bd:
        curso = bd.get(Curso, uuid.UUID(cid))
        tareas_repo.sincronizar_tareas(
            bd, cliente_canvas.ClienteCanvasDoble(), curso=curso, token="valido"
        )
        bd.commit()
    assert cliente.get(ruta).json()["individual"]


def test_archivo_difiere_outbox_antes_de_contactar_al_proveedor(cliente: TestClient, monkeypatch):
    from app.adaptadores import invitaciones_correo, outbox_repo

    _, _, c = preparar(cliente)
    cid = uuid.UUID(c["id"])
    assert (
        cliente.post(
            f"/api/cursos/{cid}/archivar", json={"confirmar": True, "slug": c["slug"]}
        ).status_code
        == 200
    )

    def no_despachar(*args, **kwargs):
        raise AssertionError("Un curso archivado no puede contactar al proveedor")

    monkeypatch.setattr(invitaciones_correo, "despachar", no_despachar)
    with fabrica_bd()() as bd:
        m = MensajeSaliente(
            curso_id=cid,
            canal="CORREO",
            evento="invitacion_equipo",
            clave_idempotencia="correo-archivo",
            destinatario="ensayo@gmail.com",
            plantilla="invitacion_equipo",
            plantilla_version=1,
            origen="MANUAL",
            estado="PENDIENTE",
            intentos=0,
            creado_en=ahora_utc(),
        )
        bd.add(m)
        bd.flush()
        outbox_repo._despachar_uno(bd, m, tomado_por="ensayo", ahora=ahora_utc())
        assert m.estado == "DIFERIDO" and m.motivo_estado == "CURSO_ARCHIVADO"


def test_reenvio_dirigido_no_duplica_invitacion_y_conserva_otros_accesos(cliente: TestClient):
    from app.adaptadores import cliente_github
    from app.adaptadores.modelos_mapeo import CuentaGithub
    from app.trabajos import reconciliar_accesos

    cid, _, _, _, _, _ = _preparar(cliente, "reenvio-dirigido")
    with fabrica_bd()() as bd:
        a, r = (
            bd.query(AccesoRepositorio, Repositorio)
            .join(Repositorio, Repositorio.id == AccesoRepositorio.repositorio_id)
            .filter(Repositorio.curso_id == uuid.UUID(cid), AccesoRepositorio.estado == "INVITADO")
            .first()
        )
        aid, eid = a.id, a.estudiante_id
        cuenta = bd.get(CuentaGithub, a.cuenta_github_id)
        cliente_github._invitaciones[("org-valida", r.nombre)].pop(cuenta.login.lower())
        otros = [
            (a.id, a.estado, a.reenvios)
            for a in bd.query(AccesoRepositorio)
            .filter(AccesoRepositorio.id != aid)
            .order_by(AccesoRepositorio.id)
        ]
    respuesta = cliente.post(f"/api/cursos/{cid}/personas/{eid}/invitaciones-github/{aid}/reenviar")
    assert respuesta.status_code == 202, respuesta.text
    with fabrica_bd()() as bd:
        t = bd.get(Trabajo, uuid.UUID(respuesta.json()["trabajo_id"]))
        reconciliar_accesos.ejecutar(bd, t)
        assert bd.get(AccesoRepositorio, aid).reenvios == 1
        assert bd.get(AccesoRepositorio, aid).estado == "INVITADO"
        reconciliar_accesos.ejecutar(bd, t)
        assert bd.get(AccesoRepositorio, aid).reenvios == 1
        assert [
            (a.id, a.estado, a.reenvios)
            for a in bd.query(AccesoRepositorio)
            .filter(AccesoRepositorio.id != aid)
            .order_by(AccesoRepositorio.id)
        ] == otros


def _identidad_nueva(cliente: TestClient, *, capturar: bool = False):
    from app.adaptadores import fusion_canvas_repo, mapeo_github_repo
    from app.adaptadores.modelos_padron import Estudiante

    cid, tid, eid, profesor, _, ayudante = _preparar(cliente, "fusion-canvas")
    if capturar:
        from tests.api.test_archivado import _vencer_todo
        from tests.api.test_versiones import _capturar_todo

        _vencer_todo(tid)
        _capturar_todo()
    with fabrica_bd()() as bd:
        anterior = (
            bd.query(Estudiante).filter_by(curso_id=uuid.UUID(cid), canvas_user_id=2001).one()
        )
        anterior.login_id = "ana.institucional"
        anterior.estado, anterior.retirado_en = "RETIRADO", ahora_utc()
        mapeo_github_repo.invalidar_por_retiro(
            bd, curso_id=uuid.UUID(cid), estudiante_id=anterior.id
        )
        nuevo = Estudiante(
            curso_id=uuid.UUID(cid),
            canvas_user_id=4001,
            nombre="Ana Soto nueva",
            login_id=anterior.login_id,
            estado="ACTIVO",
            group_ids_canvas=[],
            ciclos_ausente=0,
            primera_vista_en=ahora_utc(),
            ultima_vista_en=ahora_utc(),
        )
        bd.add(nuevo)
        bd.flush()
        mapeo_github_repo.crear_mapeo_sin_dato(bd, curso_id=uuid.UUID(cid), estudiante_id=nuevo.id)
        seccion = bd.query(Seccion).filter_by(curso_id=uuid.UUID(cid)).first()
        bd.add(
            Matricula(
                curso_id=uuid.UUID(cid),
                estudiante_id=nuevo.id,
                seccion_id=seccion.id,
                canvas_enrollment_id=99999,
                tipo="StudentEnrollment",
                estado="active",
                activa=True,
                limitada_a_seccion=False,
                sincronizado_en=ahora_utc(),
            )
        )
        bd.add(
            Sujeto(
                tarea_id=uuid.UUID(tid),
                tipo="ESTUDIANTE",
                estudiante_id=nuevo.id,
                activo=True,
                creado_en=ahora_utc(),
            )
        )
        bd.flush()
        assert fusion_canvas_repo.detectar(bd, bd.get(Curso, uuid.UUID(cid))) == 1
        ids = anterior.id, nuevo.id
        bd.commit()
    return cid, tid, eid, profesor, ayudante, ids


def test_fusion_detectada_no_es_automatica_y_preserva_identidad_e_historial(cliente: TestClient):
    from app.adaptadores.modelos_mapeo import MapeoGithub
    from app.adaptadores.modelos_padron import Estudiante
    from app.adaptadores.modelos_version import VersionEntrega

    cid, _, _, _, _, (anterior, nuevo) = _identidad_nueva(cliente, capturar=True)
    ruta = f"/api/cursos/{cid}/personas/fusiones-canvas"
    f = cliente.get(ruta).json()["pendientes"][0]
    assert f["candidatos"][0]["coincidencias"] == ["login_id"]
    with fabrica_bd()() as bd:
        assert bd.get(Estudiante, anterior).canvas_user_id == 2001
        repos = [
            (r.id, r.sujeto_id, r.github_repo_id)
            for r in bd.query(Repositorio).filter_by(curso_id=uuid.UUID(cid))
        ]
        mapeos = [
            (m.id, m.estado, m.cuenta_github_id)
            for m in bd.query(MapeoGithub).filter_by(estudiante_id=anterior)
        ]
        versiones = [
            (v.id, v.commit_sha, v.fecha_corte_utc, v.integrantes)
            for v in bd.query(VersionEntrega).order_by(VersionEntrega.id)
        ]
        assert versiones
    datos = {"anterior_id": str(anterior), "confirmar": True}
    r = cliente.post(f"{ruta}/{f['incidencia_id']}/confirmar", json=datos)
    assert r.status_code == 200 and r.json()["estudiante_id"] == str(anterior), r.text
    assert r.json()["canvas_user_id"] == 4001
    assert cliente.post(f"{ruta}/{f['incidencia_id']}/confirmar", json=datos).status_code == 200
    with fabrica_bd()() as bd:
        assert bd.get(Estudiante, nuevo).fusionada_en_id == anterior
        assert bd.get(Estudiante, nuevo).estado == "RETIRADO"
        assert bd.get(Estudiante, anterior).estado == "ACTIVO"
        assert [
            (r.id, r.sujeto_id, r.github_repo_id)
            for r in bd.query(Repositorio).filter_by(curso_id=uuid.UUID(cid))
        ] == repos
        assert [
            (m.id, m.estado, m.cuenta_github_id)
            for m in bd.query(MapeoGithub).filter_by(estudiante_id=anterior)
        ] == mapeos
        assert bd.query(Bitacora).filter_by(accion="FUSION_CANVAS_CONFIRMADA").count() == 1
        assert [
            (v.id, v.commit_sha, v.fecha_corte_utc, v.integrantes)
            for v in bd.query(VersionEntrega).order_by(VersionEntrega.id)
        ] == versiones
        assert (
            bd.query(Matricula).filter_by(canvas_enrollment_id=99999).one().estudiante_id
            == anterior
        )
    vista = cliente.get(ruta).json()
    assert vista["pendientes"] == [] and len(vista["historial"]) == 1


def test_fusion_no_admite_historia_nueva_ni_ayudante_ni_curso_archivado(cliente: TestClient):
    from app.adaptadores.modelos_padron import Estudiante

    cid, _, _, profesor, (token, _), (anterior, nuevo) = _identidad_nueva(cliente)
    ruta = f"/api/cursos/{cid}/personas/fusiones-canvas"
    f = cliente.get(ruta).json()["pendientes"][0]
    confirmar = f"{ruta}/{f['incidencia_id']}/confirmar"
    _sesion_autenticada(cliente, token)
    assert cliente.get(ruta).status_code == 403
    assert (
        cliente.post(confirmar, json={"anterior_id": str(anterior), "confirmar": True}).status_code
        == 403
    )
    _sesion_autenticada(cliente, profesor)
    with fabrica_bd()() as bd:
        s = bd.query(Sujeto).filter_by(estudiante_id=nuevo).one()
        bd.add(
            Repositorio(
                curso_id=uuid.UUID(cid),
                tarea_id=s.tarea_id,
                sujeto_id=s.id,
                nombre="evidencia-nueva",
                nombre_canonico="evidencia-nueva",
                estado="CREANDO",
                intentos=0,
                sondeos_contenido=0,
                creado_en=ahora_utc(),
                actualizado_en=ahora_utc(),
            )
        )
        bd.commit()
    assert cliente.get(ruta).json()["pendientes"][0]["candidatos"][0]["motivo_bloqueo"]
    assert (
        cliente.post(confirmar, json={"anterior_id": str(anterior), "confirmar": True}).status_code
        == 409
    )
    with fabrica_bd()() as bd:
        assert bd.get(Estudiante, anterior).canvas_user_id == 2001
        assert bd.get(Estudiante, nuevo).fusionada_en_id is None
        slug = bd.get(Curso, uuid.UUID(cid)).slug
    assert (
        cliente.post(
            f"/api/cursos/{cid}/archivar", json={"confirmar": True, "slug": slug}
        ).status_code
        == 200
    )
    assert (
        cliente.post(confirmar, json={"anterior_id": str(anterior), "confirmar": True}).status_code
        == 409
    )


def test_roles_extra_validados_auditados_y_solicitan_roster(cliente: TestClient):
    _, _, c = preparar(cliente)
    base = f"/api/cursos/{c['id']}"
    for roles in ([0], [-1], [True], ["1"], None):
        assert cliente.patch(base, json={"roles_estudiante_extra": roles}).status_code == 422
    r = cliente.patch(base, json={"roles_estudiante_extra": [42, 32, 42]})
    assert r.status_code == 200 and r.json()["roles_estudiante_extra"] == [32, 42]
    with fabrica_bd()() as bd:
        assert bd.query(Trabajo).filter_by(tipo="sync_roster").count() == 1
        assert bd.query(Bitacora).filter_by(accion="CURSO_AJUSTES_ACTUALIZADOS").one().despues[
            "roles_estudiante_extra"
        ] == [32, 42]


def test_archivo_reversible_preserva_datos_y_pausas_previas(cliente: TestClient):
    _, _, c = preparar(cliente)
    cid = uuid.UUID(c["id"])
    with fabrica_bd()() as bd:
        programacion_repo.asegurar_periodicos_de_curso(bd, cid)
        bd.query(TrabajoPeriodico).filter_by(curso_id=cid, tipo="sync_grupos").one().activo = False
        trabajos_repo.encolar(
            bd, tipo="sync_roster", curso_id=cid, clave_idempotencia="antes-archivo", max_intentos=3
        )
        bd.commit()
    base = f"/api/cursos/{cid}"
    assert cliente.get(f"{base}/archivo/previsualizar").json() == {
        "repositorios": 0,
        "sin_capturar": 0,
        "capturas_pendientes": [],
        "repositorios_por_archivar": 0,
        "bloqueos": [],
        "trabajos_archivado": [],
    }
    assert (
        cliente.post(f"{base}/archivar", json={"confirmar": True, "slug": "otro"}).status_code
        == 422
    )
    r = cliente.post(f"{base}/archivar", json={"confirmar": True, "slug": c["slug"]})
    assert r.status_code == 200 and r.json()["estado"] == "ARCHIVADO", r.text
    assert cliente.patch(base, json={"nombre": "No debe cambiar"}).status_code == 409
    assert cliente.post(f"{base}/sincronizar-ahora").status_code in (404, 409)
    assert cliente.get(f"{base}/personas").status_code == 200
    with fabrica_bd()() as bd:
        assert (
            bd.query(Trabajo).filter_by(clave_idempotencia="antes-archivo").one().estado
            == "CANCELADO"
        )
        assert not bd.query(TrabajoPeriodico).filter_by(curso_id=cid, activo=True).count()
        programacion_repo.asegurar_periodicos_de_cursos_activos(bd)
        assert not bd.query(TrabajoPeriodico).filter_by(curso_id=cid, activo=True).count()
        assert bd.get(Curso, cid).nombre == c["nombre"]
    assert (
        cliente.post(f"{base}/desarchivar", json={"confirmar": True}).json()["estado"]
        == c["estado"]
    )
    with fabrica_bd()() as bd:
        assert (
            not bd.query(TrabajoPeriodico).filter_by(curso_id=cid, tipo="sync_grupos").one().activo
        )
        assert bd.query(TrabajoPeriodico).filter_by(curso_id=cid, tipo="sync_roster").one().activo


def test_trabajador_cancela_un_trabajo_tardio_del_curso_archivado(cliente: TestClient):
    _, _, c = preparar(cliente)
    cid = uuid.UUID(c["id"])
    assert (
        cliente.post(
            f"/api/cursos/{cid}/archivar", json={"confirmar": True, "slug": c["slug"]}
        ).status_code
        == 200
    )
    with fabrica_bd()() as bd:
        t = trabajos_repo.encolar(
            bd, tipo="sin_manejador", curso_id=cid, clave_idempotencia="tardio", max_intentos=1
        )
        tid = t.id
        bd.commit()
        assert _procesar_un_trabajo(bd, tomado_por="ensayo")
        t = bd.get(Trabajo, tid)
        assert t.estado == "CANCELADO" and t.motivo_cancelacion == "CURSO_ARCHIVADO"


def _archivo_remoto(cliente: TestClient, slug: str):
    from tests.api.test_archivado import _avisar_hace, _tarea_lista_para_archivar

    cid, tid, repos = _tarea_lista_para_archivar(cliente, slug=slug, email=f"{slug}@gmail.com")
    _avisar_hace(cliente, cid, tid)
    return cid, tid, repos


def test_archivo_remoto_del_curso_respeta_correcciones_y_conserva_versiones(cliente: TestClient):
    from app.adaptadores import correccion_repo
    from app.adaptadores.cliente_github import repo_archivado_doble
    from tests.api.test_archivado import _foto_versiones
    from tests.api.test_versiones import _trabajar

    cid, tid, repos = _archivo_remoto(cliente, "archivo-remoto")
    base = f"/api/cursos/{cid}"
    with fabrica_bd()() as bd:
        entrega = bd.query(Entrega).filter_by(tarea_id=uuid.UUID(tid)).first()
        correccion_repo.asegurar_filas(bd, entrega)
        for c in bd.query(Correccion):
            c.estado = "PUBLICADA"
        c = bd.query(Correccion).first()
        c.estado = "ASIGNADA"
        pendiente = c.id
        bd.commit()
    datos = {"confirmar": True, "slug": "archivo-remoto", "archivar_repositorios": True}
    vista = cliente.get(f"{base}/archivo/previsualizar").json()
    assert vista["bloqueos"] and "correcciones" in vista["bloqueos"][0]["motivo"]
    assert cliente.post(f"{base}/archivar", json=datos).status_code == 409
    with fabrica_bd()() as bd:
        assert bd.get(Curso, uuid.UUID(cid)).estado != "ARCHIVADO"
        bd.get(Correccion, pendiente).estado = "PUBLICADA"
        bd.commit()
    antes = _foto_versiones(tid)
    respuesta = cliente.post(f"{base}/archivar", json=datos)
    assert respuesta.status_code == 200, respuesta.text
    assert len(cliente.get(f"{base}/archivo/previsualizar").json()["trabajos_archivado"]) == 2
    _trabajar()
    with fabrica_bd()() as bd:
        assert bd.get(Curso, uuid.UUID(cid)).estado == "ARCHIVADO"
        assert all(bd.get(Repositorio, r.id).estado == "ARCHIVADO" for r in repos.values())
    assert all(repo_archivado_doble("org-valida", r.nombre) for r in repos.values())
    assert _foto_versiones(tid) == antes


def test_archivo_remoto_reevalua_guardas_y_rechaza_trabajos_sin_consentimiento(cliente: TestClient):
    from app.adaptadores import archivado_repo, correccion_repo
    from tests.api.test_versiones import _trabajar

    cid, tid, repos = _archivo_remoto(cliente, "archivo-guardas")
    base = f"/api/cursos/{cid}"
    assert (
        cliente.post(
            f"{base}/archivar",
            json={
                "confirmar": True,
                "slug": "archivo-guardas",
                "archivar_repositorios": True,
            },
        ).status_code
        == 200
    )
    with fabrica_bd()() as bd:
        entrega = bd.query(Entrega).filter_by(tarea_id=uuid.UUID(tid)).first()
        correccion_repo.asegurar_filas(bd, entrega)
        curso = bd.get(Curso, uuid.UUID(cid))
        actor = bd.query(Bitacora).filter_by(accion="CURSO_ARCHIVADO").one().actor_usuario_id
        t = trabajos_repo.encolar(
            bd,
            tipo=archivado_repo.TIPO_TRABAJO,
            curso_id=curso.id,
            clave_idempotencia="archivo-no-autorizado",
            max_intentos=1,
            payload={
                "accion": "archivar",
                "tarea_id": tid,
                "repositorio_id": str(next(iter(repos.values())).id),
                "actor_usuario_id": str(actor),
                "archivo_curso": "no-concedido",
            },
        )
        no_autorizado = t.id
        bd.commit()
    _trabajar()
    with fabrica_bd()() as bd:
        assert all(bd.get(Repositorio, r.id).estado != "ARCHIVADO" for r in repos.values())
        assert bd.get(Trabajo, no_autorizado).estado == "CANCELADO"
        assert bd.query(Bitacora).filter_by(accion="ARCHIVADO_OMITIDO").count() == 2


def test_reactivar_cancela_el_archivo_remoto_pendiente(cliente: TestClient):
    from tests.api.test_versiones import _trabajar

    cid, _, repos = _archivo_remoto(cliente, "archivo-cancelado")
    base = f"/api/cursos/{cid}"
    assert (
        cliente.post(
            f"{base}/archivar",
            json={
                "confirmar": True,
                "slug": "archivo-cancelado",
                "archivar_repositorios": True,
            },
        ).status_code
        == 200
    )
    trabajos = cliente.get(f"{base}/archivo/previsualizar").json()["trabajos_archivado"]
    assert trabajos
    assert cliente.post(f"{base}/desarchivar", json={"confirmar": True}).status_code == 200
    _trabajar()
    with fabrica_bd()() as bd:
        assert all(bd.get(Trabajo, uuid.UUID(t)).estado == "CANCELADO" for t in trabajos)
        assert all(bd.get(Repositorio, r.id).estado != "ARCHIVADO" for r in repos.values())


def test_reparto_guarda_seccion_y_realinea_solo_marcados_con_borrador(cliente: TestClient):
    cid, _, eid, _, (_, ma), (_, mb) = _preparar(cliente, "reparto-realinea")
    with fabrica_bd()() as bd:
        secciones = {
            s.canvas_section_id: str(s.id)
            for s in bd.query(Seccion).filter_by(curso_id=uuid.UUID(cid))
        }
    base = f"/api/cursos/{cid}/correccion/{eid}/reparto"
    cuerpo = {
        "criterio": "SECCION",
        "por_seccion": {secciones[101]: str(ma), secciones[102]: str(mb)},
    }
    assert cliente.post(f"{base}/aplicar", json=cuerpo).status_code == 200
    with fabrica_bd()() as bd:
        a, s = (
            bd.query(AsignacionCorreccion, Sujeto)
            .join(Sujeto, Sujeto.id == AsignacionCorreccion.sujeto_id)
            .filter(
                AsignacionCorreccion.entrega_id == uuid.UUID(eid),
                AsignacionCorreccion.criterio_seccion_id == uuid.UUID(secciones[101]),
            )
            .first()
        )
        aid, sid = a.id, s.id
        assert a.membresia_id == ma
        c = bd.query(Correccion).filter_by(entrega_id=uuid.UUID(eid), sujeto_id=sid).one()
        c.nota_local, c.comentario = "42", "Conservar borrador"
        for m in bd.query(Matricula).filter_by(estudiante_id=s.estudiante_id, activa=True):
            m.seccion_id = uuid.UUID(secciones[102])
        assert realineacion_repo.revisar(bd, bd.get(Entrega, uuid.UUID(eid))) == 1
        bd.commit()
    vista = cliente.post(f"{base}/previsualizar", json={"criterio": "MANUAL", "realinear": True})
    assert vista.status_code == 200 and len(vista.json()["filas"]) == 1, vista.text
    with fabrica_bd()() as bd:
        assert bd.get(AsignacionCorreccion, aid).membresia_id == ma
    r = cliente.post(f"{base}/aplicar", json={"criterio": "MANUAL", "realinear": True})
    assert r.status_code == 200 and r.json()["cambios"] == 1, r.text
    with fabrica_bd()() as bd:
        assert bd.get(AsignacionCorreccion, aid).membresia_id == mb
        assert bd.get(AsignacionCorreccion, aid).desalineada_motivo is None
        c = bd.query(Correccion).filter_by(entrega_id=uuid.UUID(eid), sujeto_id=sid).one()
        assert c.nota_local == "42" and c.comentario == "Conservar borrador"
    assert (
        cliente.post(f"{base}/aplicar", json={"criterio": "MANUAL", "realinear": True}).json()[
            "cambios"
        ]
        == 0
    )


def test_ayudante_avisa_por_outbox_y_no_duplica_en_24_horas(cliente: TestClient):
    cid, _, eid, _, _, (token, _) = _preparar(cliente, "aviso-corrector")
    cliente.post(
        f"/api/cursos/{cid}/correccion/{eid}/reparto/previsualizar", json={"criterio": "EQUITATIVO"}
    )
    _sesion_autenticada(cliente, token)
    ruta = f"/api/cursos/{cid}/correccion/avisar-profesores"
    r = cliente.post(ruta)
    assert r.status_code == 202 and r.json()["encolados"] == 1, r.text
    bandeja = cliente.get(f"/api/cursos/{cid}/comunicaciones?canal=CORREO").json()
    assert len(bandeja["mensajes"]) == 1
    assert bandeja["mensajes"][0]["evento"] == "aviso_sin_corrector"
    assert "no tiene enlace en Canvas" in bandeja["mensajes"][0]["motivo_sin_enlace"]
    assert cliente.post(ruta).status_code == 429
    with fabrica_bd()() as bd:
        m = bd.query(MensajeSaliente).filter_by(evento="aviso_sin_corrector").one()
        assert m.estado == "PENDIENTE" and m.enviado_en is None


def _grupal(cliente: TestClient):
    cid, _, eid, _, _, ayudante = _preparar(cliente, "notas-individuales")
    with fabrica_bd()() as bd:
        entrega = bd.get(Entrega, uuid.UUID(eid))
        entrega.canvas_assignment_id = 9102
        bd.commit()
    return cid, eid, ayudante


def test_configuracion_grupal_solo_lectura_con_enlace_a_canvas(cliente: TestClient):
    cid, eid, (token, _) = _grupal(cliente)
    ruta = f"/api/cursos/{cid}/entregas/{eid}/calificacion-individual"
    vista = cliente.get(ruta)
    assert vista.json()["es_grupal"] and vista.json()["puede_cambiar"], vista.text
    assert not vista.json()["individual"]
    assert vista.headers["X-Llamadas-Externas"] == "0"
    assert vista.json()["enlace_canvas"].endswith("/courses/5001/assignments/9102/edit")
    assert cliente.post(ruta, json={"confirmar": True}).status_code == 405
    assert not cliente.get(ruta).json()["individual"]
    _sesion_autenticada(cliente, token)
    assert cliente.get(ruta).status_code == 200
    assert cliente.post(ruta, json={"confirmar": True}).status_code == 405


def test_no_propone_cambiar_grano_despues_de_intentar_publicar(cliente: TestClient):
    cid, eid, _ = _grupal(cliente)
    cliente.post(
        f"/api/cursos/{cid}/correccion/{eid}/reparto/previsualizar", json={"criterio": "EQUITATIVO"}
    )
    with fabrica_bd()() as bd:
        bd.query(Correccion).filter_by(entrega_id=uuid.UUID(eid)).first().intentos = 1
        bd.commit()
    ruta = f"/api/cursos/{cid}/entregas/{eid}/calificacion-individual"
    vista = cliente.get(ruta).json()
    assert not vista["puede_cambiar"]
    assert "intento de publicación" in vista["motivo"]
    assert not vista["individual"]
    assert cliente.post(ruta, json={"confirmar": True}).status_code == 405


def test_reenvio_estudiante_respeta_maximo_cooldown_y_scope(cliente: TestClient):
    cid, _, _, _, _, _ = _preparar(cliente, "invitacion-manual")
    with fabrica_bd()() as bd:
        a = (
            bd.query(AccesoRepositorio)
            .join(Repositorio, Repositorio.id == AccesoRepositorio.repositorio_id)
            .filter(Repositorio.curso_id == uuid.UUID(cid), AccesoRepositorio.estado == "INVITADO")
            .first()
        )
        aid, estudiante = a.id, a.estudiante_id
    ruta = f"/api/cursos/{cid}/personas/{estudiante}/invitaciones-github/{aid}/reenviar"
    r = cliente.post(ruta)
    assert r.status_code == 202, r.text
    assert cliente.post(ruta).json()["trabajo_id"] == r.json()["trabajo_id"]
    with fabrica_bd()() as bd:
        a = bd.get(AccesoRepositorio, aid)
        a.ultimo_reenvio_en = ahora_utc()
        bd.commit()
    r = cliente.post(ruta)
    assert r.status_code == 429 and int(r.headers["Retry-After"]) > 0
    with fabrica_bd()() as bd:
        a = bd.get(AccesoRepositorio, aid)
        a.ultimo_reenvio_en = ahora_utc() - timedelta(days=2)
        a.reenvios = 3
        bd.commit()
    assert cliente.post(ruta).status_code == 409
    assert cliente.post(ruta.replace(str(estudiante), str(uuid.uuid4()))).status_code == 404
