"""Etapa F5 (SPEC 10 S10.2-S10.3; SPEC 06 S6.8): ingesta de actividad de punta
a punta, con Canvas y GitHub en modo doble.

Los webhooks se firman con el secreto de la configuracion, como los firmaria
GitHub; el doble de GitHub responde `compare` y los listados por rama desde su
grafo de commits."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_canvas import ClienteCanvasDoble
from app.adaptadores.cliente_github import (
    agregar_commit_doble,
    reescribir_historia_doble,
    retrodatar_repo_doble,
)
from app.adaptadores.modelos_actividad import (
    AutoriaCommit,
    Commit,
    EventoPush,
    EventoWebhook,
    IdentidadGit,
)
from app.adaptadores.modelos_aprovisionamiento import AccesoRepositorio, Repositorio, Sujeto
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Bitacora, Incidencia, Trabajo
from app.adaptadores.modelos_padron import Estudiante
from app.adaptadores.modelos_version import VersionEntrega
from app.dominio.tareas_canvas import OverrideCanvasCrudo
from app.infraestructura.config import obtener_configuracion
from app.trabajos import (  # noqa: F401 (registra los manejadores)
    barrido_completo_actividad,
    crear_etiqueta,
    procesar_webhooks,
    reconciliar_actividad,
    resolver_sha,
)
from app.trabajos.ejecutor import _procesar_un_trabajo
from tests.api.test_aprovisionamiento import (
    _encolar_y_ejecutar,
    _preparar_curso_con_tarea_activa,
    _sesion_autenticada,
)
from tests.api.test_versiones import _ayudante_con_tarea_administrar
from tests.apoyo import fabrica_bd

_ORG = "org-valida"
_ANA_ID = 70001  # Estudiante-Valido, mapeo VIGENTE de Ana Soto (2001)


def _trabajar() -> None:
    fabrica = fabrica_bd()
    while True:
        with fabrica() as bd:
            if not _procesar_un_trabajo(bd, tomado_por="test"):
                return


def _enviar(
    cliente: TestClient,
    evento: str,
    payload: dict,
    *,
    firma: str | None = None,
    delivery: str | None = None,
):
    cuerpo = json.dumps(payload).encode()
    secreto = obtener_configuracion().github_webhook_secret
    if firma is None:
        firma = "sha256=" + hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()
    return cliente.post(
        "/webhooks/github",
        content=cuerpo,
        headers={
            "X-GitHub-Event": evento,
            "X-GitHub-Delivery": delivery or secrets.token_hex(8),
            "X-Hub-Signature-256": firma,
            "Content-Type": "application/json",
        },
    )


def _repo(curso_id: str, canvas_user_id: int) -> Repositorio:
    with fabrica_bd()() as bd:
        repo = (
            bd.query(Repositorio)
            .join(Sujeto, Sujeto.id == Repositorio.sujeto_id)
            .join(Estudiante, Estudiante.id == Sujeto.estudiante_id)
            .filter(
                Repositorio.curso_id == uuid.UUID(curso_id),
                Estudiante.canvas_user_id == canvas_user_id,
            )
            .one()
        )
        bd.expunge(repo)
        return repo


def _cabeza(repo: Repositorio) -> str:
    from app.adaptadores.cliente_github import _ramas

    return _ramas[(_ORG, repo.nombre)]["main"]


def _push(repo: Repositorio, *, before: str, after: str, commits: list[dict], forced=False):
    return {
        "ref": "refs/heads/main",
        "before": before,
        "after": after,
        "forced": forced,
        "commits": commits,
        "repository": {"id": repo.github_repo_id, "name": repo.nombre},
        "installation": {"id": 8001},
    }


def _commit_payload(sha: str, *, email: str, mensaje: str) -> dict:
    return {
        "id": sha,
        "message": mensaje,
        "timestamp": ahora_utc().isoformat(),
        "author": {"name": "Alguien", "email": email, "username": "alguien"},
        "added": ["a.py"],
        "removed": [],
        "modified": [],
    }


def _commits(repo_id: uuid.UUID) -> dict[str, Commit]:
    with fabrica_bd()() as bd:
        filas = bd.query(Commit).filter(Commit.repositorio_id == repo_id).all()
        for f in filas:
            bd.expunge(f)
        return {f.sha: f for f in filas}


def test_ca_6_8_01_firma_invalida_401_sin_ningun_efecto(cliente: TestClient):
    curso_id, _ = _preparar_curso_con_tarea_activa(cliente, slug="pds-f5-a", email="f5a@gmail.com")
    ana = _repo(curso_id, 2001)
    respuesta = _enviar(
        cliente,
        "push",
        _push(ana, before="a" * 40, after="b" * 40, commits=[]),
        firma="sha256=" + "0" * 64,
    )
    assert respuesta.status_code == 401
    with fabrica_bd()() as bd:
        fila = bd.query(EventoWebhook).one()
        assert (fila.firma_valida, fila.payload) == (False, None)
        assert bd.query(Trabajo).filter(Trabajo.tipo == "procesar_webhooks").count() == 0
        assert bd.query(EventoPush).count() == 0


def test_push_se_ingiere_se_atribuye_y_la_reentrega_no_duplica(cliente: TestClient):
    curso_id, _ = _preparar_curso_con_tarea_activa(cliente, slug="pds-f5-b", email="f5b@gmail.com")
    ana = _repo(curso_id, 2001)
    antes = _cabeza(ana)
    sha_ana = agregar_commit_doble(
        _ORG,
        ana.nombre,
        fecha=ahora_utc(),
        mensaje="quicksort",
        autor_email="ana@gmail.com",
        autor_github_user_id=_ANA_ID,
    )
    sha_otro = agregar_commit_doble(
        _ORG,
        ana.nombre,
        fecha=ahora_utc(),
        mensaje="desde otra maquina",
        autor_email="root@localhost",
    )
    payload = _push(
        ana,
        before=antes,
        after=sha_otro,
        commits=[
            _commit_payload(sha_ana, email="ana@gmail.com", mensaje="quicksort"),
            _commit_payload(sha_otro, email="root@localhost", mensaje="desde otra maquina"),
        ],
    )
    primera = _enviar(cliente, "push", payload, delivery="entrega-1")
    assert primera.status_code == 202
    _trabajar()
    commits = _commits(ana.id)
    # El payload no trae el `author.id`: lo completa `compare` (AUTOR_GITHUB).
    assert commits[sha_ana].regla_atribucion == "AUTOR_GITHUB"
    assert commits[sha_ana].n_padres == 1
    assert commits[sha_ana].archivos_tocados == 1
    assert commits[sha_otro].regla_atribucion == "SIN_ATRIBUIR"
    with fabrica_bd()() as bd:
        identidad = bd.query(IdentidadGit).filter(IdentidadGit.repositorio_id == ana.id).one()
        assert identidad.email_normalizado == "root@localhost"
        assert bd.query(AutoriaCommit).count() == 2
        push = bd.query(EventoPush).one()
        assert push.completado is True

    # CA-6.8-02: misma entrega, cero filas nuevas.
    assert _enviar(cliente, "push", payload, delivery="entrega-1").status_code == 202
    _trabajar()
    with fabrica_bd()() as bd:
        assert bd.query(EventoWebhook).count() == 1
        assert bd.query(Commit).filter(Commit.repositorio_id == ana.id).count() == len(commits)


def test_ca_10_2_5_push_force_marca_huerfanos_y_no_borra(cliente: TestClient):
    curso_id, _ = _preparar_curso_con_tarea_activa(cliente, slug="pds-f5-c", email="f5c@gmail.com")
    ana = _repo(curso_id, 2001)
    shas = [
        agregar_commit_doble(
            _ORG, ana.nombre, fecha=ahora_utc(), mensaje=f"c{i}", autor_github_user_id=_ANA_ID
        )
        for i in range(3)
    ]
    _encolar_y_ejecutar("reconciliar_actividad", curso_id)
    vieja = _cabeza(ana)
    nueva = reescribir_historia_doble(_ORG, ana.nombre, quitar=3)
    reemplazo = agregar_commit_doble(
        _ORG, ana.nombre, fecha=ahora_utc(), mensaje="rehecho", autor_github_user_id=_ANA_ID
    )
    assert nueva != vieja
    _enviar(cliente, "push", _push(ana, before=vieja, after=reemplazo, commits=[], forced=True))
    _trabajar()
    commits = _commits(ana.id)
    assert all(commits[s].huerfano and commits[s].huerfano_desde for s in shas)
    assert {commits[s].motivo_exclusion for s in shas} == {"HUERFANO"}
    assert commits[reemplazo].huerfano is False
    with fabrica_bd()() as bd:
        push = bd.query(EventoPush).one()
        assert (push.divergido, push.n_commits_huerfanos) == (True, 3)


def test_ca_6_8_05_reconciliacion_por_etag_sin_webhook(cliente: TestClient):
    curso_id, _ = _preparar_curso_con_tarea_activa(cliente, slug="pds-f5-d", email="f5d@gmail.com")
    ana = _repo(curso_id, 2001)
    sha = agregar_commit_doble(
        _ORG, ana.nombre, fecha=ahora_utc(), mensaje="sin webhook", autor_github_user_id=_ANA_ID
    )
    _encolar_y_ejecutar("reconciliar_actividad", curso_id)
    assert sha in _commits(ana.id)
    with fabrica_bd()() as bd:
        antes = bd.query(Commit).count()
    _encolar_y_ejecutar("reconciliar_actividad", curso_id)  # 304: no escribe nada
    with fabrica_bd()() as bd:
        assert bd.query(Commit).count() == antes


def test_ca_10_2_7_evento_sin_destino_se_reintenta_y_caduca_sin_incidencia(
    cliente: TestClient,
):
    _preparar_curso_con_tarea_activa(cliente, slug="pds-f5-e", email="f5e@gmail.com")
    payload = {
        "ref": "refs/heads/main",
        "before": "a" * 40,
        "after": "b" * 40,
        "commits": [],
        "repository": {"id": 999_999, "name": "no-existe"},
        "installation": {"id": 8001},
    }
    assert _enviar(cliente, "push", payload, delivery="sin-destino").status_code == 202
    _trabajar()
    with fabrica_bd()() as bd:
        evento = bd.query(EventoWebhook).one()
        assert evento.estado == "SIN_DESTINO_PENDIENTE"
        trabajo = bd.query(Trabajo).filter(Trabajo.tipo == "procesar_webhooks").one()
        assert (trabajo.estado, trabajo.intentos) == ("PENDIENTE", 0)
        evento.recibido_en = ahora_utc() - timedelta(hours=25)
        trabajo.proximo_intento_en = ahora_utc()
        bd.commit()
    _trabajar()
    with fabrica_bd()() as bd:
        assert bd.query(EventoWebhook).one().estado == "DESCARTADO_SIN_DESTINO"
        assert bd.query(Incidencia).filter(Incidencia.tipo.like("%DESTINO%")).count() == 0


def test_member_added_y_repository_archived(cliente: TestClient):
    curso_id, _ = _preparar_curso_con_tarea_activa(cliente, slug="pds-f5-f", email="f5f@gmail.com")
    ana = _repo(curso_id, 2001)
    repo_gh = {"id": ana.github_repo_id, "name": ana.nombre}
    _enviar(
        cliente,
        "member",
        {
            "action": "added",
            "member": {"id": _ANA_ID, "login": "x"},
            "repository": repo_gh,
            "installation": {"id": 8001},
        },
    )
    _enviar(
        cliente,
        "repository",
        {"action": "archived", "repository": repo_gh, "installation": {"id": 8001}},
    )
    _trabajar()
    with fabrica_bd()() as bd:
        acceso = (
            bd.query(AccesoRepositorio).filter(AccesoRepositorio.repositorio_id == ana.id).one()
        )
        assert acceso.estado == "ACEPTADO"
        assert bd.get(Repositorio, ana.id).estado == "ARCHIVADO"  # type: ignore[union-attr]
        assert any(
            (b.despues or {}).get("estado") == "ARCHIVADO"
            for b in bd.query(Bitacora).filter(
                Bitacora.accion == "REPOSITORIO_ESTADO", Bitacora.entidad_id == str(ana.id)
            )
        )


def test_identidades_resolver_propagar_y_revelar(cliente: TestClient):
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f5-g", email="f5g@gmail.com"
    )
    ana, bruno = _repo(curso_id, 2001), _repo(curso_id, 2002)
    for repo in (ana, bruno):
        agregar_commit_doble(
            _ORG,
            repo.nombre,
            fecha=ahora_utc(),
            mensaje="portatil",
            autor_email="Juan.Perez@gmail.com",
            autor_nombre="Juan P",
        )
    _encolar_y_ejecutar("reconciliar_actividad", curso_id)
    base = f"/api/cursos/{curso_id}/tareas/{tarea_id}/repos/{ana.id}/identidades"
    lista = cliente.get(base)
    assert lista.status_code == 200, lista.text
    [identidad] = lista.json()
    # S10.3.6: el correo llega ofuscado del servidor.
    assert identidad["email"] == "J•••@g•••.com"
    assert "Juan.Perez@gmail.com" not in lista.text
    assert identidad["commits_contables"] == 1

    propagacion = cliente.get(f"{base}/{identidad['id']}/propagacion").json()
    assert [c["repositorio_id"] for c in propagacion] == [str(bruno.id)]
    assert propagacion[0]["marcada"] is False  # nacen desmarcadas

    with fabrica_bd()() as bd:
        estudiante_ana = bd.query(Estudiante).filter(Estudiante.canvas_user_id == 2001).one().id
    resuelta = cliente.post(
        f"{base}/{identidad['id']}/resolver",
        json={"estudiante_id": str(estudiante_ana), "propagar_a": []},
    )
    assert resuelta.status_code == 200, resuelta.text
    commits_ana = _commits(ana.id)
    assert {
        c.regla_atribucion for c in commits_ana.values() if c.autor_email and not c.autor_es_bot
    } == {"IDENTIDAD_DOCENTE"}
    # Sin propagar: el repositorio de Bruno no cambia.
    assert {
        c.regla_atribucion
        for c in _commits(bruno.id).values()
        if c.autor_email and not c.autor_es_bot
    } == {"SIN_ATRIBUIR"}
    with fabrica_bd()() as bd:
        filas = bd.query(IdentidadGit).filter(IdentidadGit.repositorio_id == ana.id).all()
        assert sorted(f.estado for f in filas) == ["RESUELTA", "SUPERSEDIDA"]  # append-only

    revelado = cliente.post(f"{base}/{identidad['id']}/revelar")
    assert revelado.json()["email"] == "Juan.Perez@gmail.com"
    with fabrica_bd()() as bd:
        assert bd.query(Bitacora).filter(Bitacora.accion == "EMAIL_AUTOR_REVELADO").count() == 1

    # Sin `mapeo.editar`: 403.
    _sesion_autenticada(cliente, _ayudante_con_tarea_administrar(curso_id))
    assert cliente.post(f"{base}/{identidad['id']}/revelar").status_code == 403


@pytest.fixture
def overrides_9101(monkeypatch):
    lista: list[OverrideCanvasCrudo] = []
    original = ClienteCanvasDoble.obtener_overrides_assignment

    def _falso(self, token, canvas_course_id, canvas_assignment_id):
        if canvas_assignment_id == 9101:
            return list(lista)
        return original(self, token, canvas_course_id, canvas_assignment_id)

    monkeypatch.setattr(ClienteCanvasDoble, "obtener_overrides_assignment", _falso)
    return lista


def test_ca_9_6_03_discrepancia_espejo_github_deja_revisar(cliente: TestClient, overrides_9101):
    """Con el espejo fiable (relleno hecho), el commit de cierre sale del espejo
    y se contrasta con GitHub; si difieren, REVISAR con los dos SHA."""
    curso_id, _ = _preparar_curso_con_tarea_activa(cliente, slug="pds-f5-h", email="f5h@gmail.com")
    ana = _repo(curso_id, 2001)
    ahora = ahora_utc().replace(microsecond=0)
    corte = ahora - timedelta(minutes=10)
    with fabrica_bd()() as bd:
        bd.get(Repositorio, ana.id).listo_en = ahora - timedelta(days=3)  # type: ignore[union-attr]
        bd.get(Sujeto, ana.sujeto_id).creado_en = ahora - timedelta(days=3)  # type: ignore[union-attr]
        bd.commit()
    retrodatar_repo_doble(_ORG, ana.nombre, ahora - timedelta(days=3))
    sha_github = agregar_commit_doble(
        _ORG,
        ana.nombre,
        fecha=corte - timedelta(hours=2),
        mensaje="en github",
        autor_github_user_id=_ANA_ID,
    )
    _encolar_y_ejecutar("barrido_completo_actividad", curso_id)  # relleno: espejo fiable
    with fabrica_bd()() as bd:
        assert bd.get(Curso, uuid.UUID(curso_id)).ingesta_actividad_desde is not None  # type: ignore[union-attr]
        # Un commit que solo el espejo conoce, mas reciente pero anterior al corte.
        bd.add(
            Commit(
                repositorio_id=ana.id,
                sha="e" * 40,
                parent_shas=[sha_github],
                n_padres=1,
                en_rama_por_defecto=True,
                fecha_committer=corte - timedelta(hours=1),
                origen_ingesta="WEBHOOK",
                recibido_en=ahora,
                ingresado_en=ahora,
            )
        )
        bd.commit()
    overrides_9101.append(
        OverrideCanvasCrudo(
            canvas_override_id=1,
            student_ids=[2001],
            course_section_id=None,
            group_id=None,
            due_at=corte,
            titulo="x",
        )
    )
    _encolar_y_ejecutar("sync_tareas_y_fechas", curso_id)
    from tests.api.test_versiones import _capturar_todo

    _capturar_todo()
    with fabrica_bd()() as bd:
        version = bd.query(VersionEntrega).filter(VersionEntrega.sujeto_id == ana.sujeto_id).one()
        assert version.estado == "REVISAR"
        assert version.commit_sha == "e" * 40  # manda el espejo
        assert version.verificacion["github_sha"] == sha_github
        assert bd.query(Incidencia).filter(Incidencia.tipo == "VERSION_REVISAR").count() == 1
