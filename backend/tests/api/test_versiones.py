"""Etapa F4 (SPEC 09 S9.6-S9.9, S9.12): captura y versiones de entrega de punta
a punta, con Canvas y GitHub en modo doble.

Las fechas de cierre se simulan con overrides de la entrega 9101 relativos a
ahora; los repositorios del doble se retrodatan para que existan antes del
corte. Los trabajos corren con el ciclo real del trabajador
(`_procesar_un_trabajo`), que clasifica errores y pospone igual que en
produccion."""

from __future__ import annotations

import re
import secrets
import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.adaptadores import versiones_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_canvas import ClienteCanvasDoble
from app.adaptadores.cliente_github import (
    ClienteGitHubDoble,
    FalloProveedorGithub,
    RechazoProveedorGithub,
    agregar_commit_doble,
    retrodatar_repo_doble,
    tags_doble,
)
from app.adaptadores.modelos_aprovisionamiento import Repositorio, Sujeto
from app.adaptadores.modelos_curso import MembresiaCurso
from app.adaptadores.modelos_github import AccesoDocenteRepositorio
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.adaptadores.modelos_infraestructura import Bitacora, Incidencia, Trabajo
from app.adaptadores.modelos_tarea import Entrega
from app.adaptadores.modelos_version import VersionEntrega
from app.api.dependencias import hash_token
from app.dominio.tareas_canvas import OverrideCanvasCrudo
from app.dominio.versiones import VersionInmutable
from app.trabajos import (  # noqa: F401 (registra los manejadores)
    barrido_completo_actividad,
    crear_etiqueta,
    resolver_sha,
)
from app.trabajos.ejecutor import _procesar_un_trabajo
from tests.api.test_aprovisionamiento import (
    _encolar_y_ejecutar,
    _preparar_curso_con_tarea_activa,
    _sesion_autenticada,
)
from tests.apoyo import fabrica_bd

_ORG = "org-valida"


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


def _override(oid, due_at, estudiantes):
    return OverrideCanvasCrudo(
        canvas_override_id=oid,
        student_ids=estudiantes,
        course_section_id=None,
        group_id=None,
        due_at=due_at,
        titulo="Cierre anticipado",
    )


def _trabajar() -> None:
    """El bucle del trabajador hasta que no quede nada listo para tomar."""
    fabrica = fabrica_bd()
    while True:
        with fabrica() as bd:
            if not _procesar_un_trabajo(bd, tomado_por="test"):
                return


def _encolar(tipo: str, curso_id: str | None) -> None:
    from app.adaptadores import trabajos_repo

    with fabrica_bd()() as bd:
        trabajos_repo.encolar(
            bd,
            tipo=tipo,
            clave_idempotencia=f"test:{tipo}:{secrets.token_hex(4)}",
            max_intentos=8,
            curso_id=uuid.UUID(curso_id) if curso_id else None,
        )
        bd.commit()


def _repos(curso_id: str) -> dict[str, str]:
    """Nombre del repositorio por login del estudiante (Ana y Bruno)."""
    with fabrica_bd()() as bd:
        return {
            re.search(r"-e(\d+)-", r.nombre).group(1): r.nombre  # type: ignore[union-attr]
            for r in bd.query(Repositorio).filter(
                Repositorio.curso_id == uuid.UUID(curso_id), Repositorio.github_repo_id.isnot(None)
            )
        }


def _preparar(cliente, overrides, *, slug, email, hace=timedelta(minutes=10)):
    """Ana (2001) y Bruno (2002) con repositorio creado hace tres dias; la
    entrega 9101 cierra para ellos y para Carla (2003, sin repositorio) hace
    `hace`. Ana hizo un commit antes del cierre y otro despues."""
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(cliente, slug=slug, email=email)
    ahora = ahora_utc().replace(microsecond=0)
    corte = ahora - hace
    hace_tres_dias = ahora - timedelta(days=3)
    with fabrica_bd()() as bd:
        for repo in bd.query(Repositorio).filter(Repositorio.curso_id == uuid.UUID(curso_id)):
            bd.get(Sujeto, repo.sujeto_id).creado_en = hace_tres_dias  # type: ignore[union-attr]
            if repo.github_repo_id is not None:
                repo.listo_en = hace_tres_dias
                retrodatar_repo_doble(_ORG, repo.nombre, hace_tres_dias)
        bd.commit()
    repos = _repos(curso_id)
    sha_ana = agregar_commit_doble(
        _ORG, repos["2001"], fecha=corte - timedelta(hours=1), mensaje="implementa quicksort"
    )
    agregar_commit_doble(_ORG, repos["2001"], fecha=corte + timedelta(minutes=1), mensaje="tarde")
    overrides.append(_override(1, corte, [2001, 2002, 2003]))
    _encolar_y_ejecutar("sync_tareas_y_fechas", curso_id)
    return curso_id, tarea_id, corte, repos, sha_ana


def _capturar_todo() -> None:
    _encolar("resolver_sha", None)
    _trabajar()


def _entrega_id(curso_id: str) -> str:
    with fabrica_bd()() as bd:
        return str(
            bd.query(Entrega.id)
            .filter(Entrega.curso_id == uuid.UUID(curso_id), Entrega.canvas_assignment_id == 9101)
            .scalar()
        )


def _versiones(curso_id: str) -> dict[str, list[VersionEntrega]]:
    """Versiones por etiqueta del sujeto, en orden de intento."""
    with fabrica_bd()() as bd:
        salida: dict[str, list[VersionEntrega]] = {}
        for v in (
            bd.query(VersionEntrega)
            .join(Entrega, Entrega.id == VersionEntrega.entrega_id)
            .filter(Entrega.curso_id == uuid.UUID(curso_id))
            .order_by(VersionEntrega.intento)
        ):
            bd.expunge(v)
            salida.setdefault(v.sujeto_etiqueta, []).append(v)
        return salida


def test_ca_9_6_01_captura_al_cierre_y_etiqueta(cliente: TestClient, overrides_9101):
    curso_id, _, corte, repos, sha_ana = _preparar(
        cliente, overrides_9101, slug="pds-f4-a", email="f4a@gmail.com"
    )
    _capturar_todo()
    versiones = _versiones(curso_id)
    # CA-9.6-01: nadie cuya fecha no vencio tiene fila (Diego, Elena: fecha base futura).
    assert set(versiones) == {"Ana Soto", "Bruno Diaz", "Carla Reyes"}

    ana = versiones["Ana Soto"][0]
    assert (ana.estado, ana.commit_sha, ana.fecha_corte_utc) == ("CAPTURADA", sha_ana, corte)
    assert ana.tag_nombre == "entrega/1-tarea-1-ordenamiento/v1"
    assert tags_doble(_ORG, repos["2001"])[ana.tag_nombre] == sha_ana
    assert ana.integrantes[0]["github_login"] == "Estudiante-Valido"
    assert ana.fecha_origen == "ADHOC" and ana.canvas_override_id == 1

    # CA-9.6-04: solo el commit inicial -> SIN_COMMITS, nunca error, sin etiqueta.
    bruno = versiones["Bruno Diaz"][0]
    assert (bruno.estado, bruno.tag_estado, bruno.tag_motivo) == (
        "SIN_COMMITS",
        "NO_APLICA",
        "SIN_COMMITS",
    )
    assert bruno.verificacion["motivo_sin_commits"] == "SOLO_COMMIT_INICIAL"
    assert repos["2002"] not in {k for k in tags_doble(_ORG, repos["2002"])}

    # S9.6.6: sin repositorio al cierre, nunca «sin entrega» y sin llamar a GitHub.
    carla = versiones["Carla Reyes"][0]
    assert (carla.estado, carla.motivo, carla.repositorio_id) == (
        "SIN_REPOSITORIO",
        "SIN_REPOSITORIO_AL_CIERRE",
        None,
    )

    # Pantalla: progreso sobre fechas vencidas y ficha del sujeto.
    progreso = cliente.get(
        f"/api/cursos/{curso_id}/entregas/{_entrega_id(curso_id)}/progreso-captura"
    ).json()
    assert (progreso["vencidas"], progreso["registradas"]) == (3, 3)
    filas = {f["sujeto"]: f for f in progreso["filas"]}
    assert filas["Ana Soto"]["estado_captura"] == "CAPTURADA"
    assert filas["Diego Vera"]["estado_captura"] == "PENDIENTE_DE_CIERRE"
    ficha = cliente.get(
        f"/api/cursos/{curso_id}/entregas/{_entrega_id(curso_id)}/sujetos/{ana.sujeto_id}/version"
    ).json()
    assert ficha["vigente"]["commit_sha"] == sha_ana
    assert "(America/Santiago)" in ficha["vigente"]["fecha_corte"]
    assert ficha["vigente"]["enlaces"]["arbol"].endswith("/abrir?destino=arbol")
    assert ficha["vigente"]["comparacion_base"] == "desde el inicio del repositorio"


def test_ca_9_6_06_un_limite_al_etiquetar_no_impide_la_evidencia(
    cliente: TestClient, overrides_9101, monkeypatch
):
    def _limite(*_args, **_kwargs):
        raise RechazoProveedorGithub(403, "API rate limit exceeded for installation")

    monkeypatch.setattr(ClienteGitHubDoble, "crear_ref_tag", _limite)
    curso_id, _, _, _, sha_ana = _preparar(
        cliente, overrides_9101, slug="pds-f4-b", email="f4b@gmail.com"
    )
    _capturar_todo()
    ana = _versiones(curso_id)["Ana Soto"][0]
    assert (ana.estado, ana.commit_sha) == ("CAPTURADA_SIN_TAG", sha_ana)
    assert (ana.tag_estado, ana.tag_motivo) == ("PENDIENTE", "LIMITE_API")
    with fabrica_bd()() as bd:
        pendiente = bd.query(Trabajo).filter(Trabajo.tipo == "crear_etiqueta").one()
        assert pendiente.estado == "REINTENTAR"  # se reintenta: no se abandona


def test_ca_9_8_01_la_evidencia_no_se_puede_modificar_ni_borrar(
    cliente: TestClient, overrides_9101
):
    curso_id, _, _, _, _ = _preparar(
        cliente, overrides_9101, slug="pds-f4-c", email="f4c@gmail.com"
    )
    _capturar_todo()
    ana = _versiones(curso_id)["Ana Soto"][0]
    for sentencia in (
        "UPDATE version_entrega SET commit_sha = 'x' WHERE id = :id",
        "UPDATE version_entrega SET fecha_corte_utc = now() WHERE id = :id",
        "UPDATE version_entrega SET commit_fecha_committer = now() WHERE id = :id",
        "DELETE FROM version_entrega WHERE id = :id",
    ):
        with fabrica_bd()() as bd, pytest.raises(DBAPIError):
            bd.execute(text(sentencia), {"id": ana.id})
            bd.flush()
    with fabrica_bd()() as bd:
        fila = bd.get(VersionEntrega, ana.id)
        assert fila is not None
        with pytest.raises(VersionInmutable):
            versiones_repo.transicionar(bd, fila, commit_sha="b" * 40)
        with pytest.raises(VersionInmutable):
            versiones_repo.transicionar(bd, fila, estado="SIN_COMMITS")


def test_ca_9_8_02_adelantar_la_fecha_recaptura_y_conserva_la_anterior(
    cliente: TestClient, overrides_9101
):
    curso_id, _, corte, repos, sha_ana = _preparar(
        cliente, overrides_9101, slug="pds-f4-d", email="f4d@gmail.com", hace=timedelta(minutes=10)
    )
    sha_antes = agregar_commit_doble(
        _ORG, repos["2001"], fecha=corte - timedelta(hours=3), mensaje="primer avance"
    )
    _capturar_todo()
    overrides_9101[0] = _override(1, corte - timedelta(hours=2), [2001, 2002, 2003])
    _encolar_y_ejecutar("sync_tareas_y_fechas", curso_id)
    _capturar_todo()

    v1, v2 = _versiones(curso_id)["Ana Soto"]
    assert (v1.intento, v1.vigente, v1.motivo, v1.commit_sha) == (
        1,
        False,
        "FECHA_ADELANTADA",
        sha_ana,
    )
    assert (v2.intento, v2.vigente, v2.commit_sha, v2.reemplaza_a_id) == (
        2,
        True,
        sha_antes,
        None,
    )
    tags = tags_doble(_ORG, repos["2001"])
    assert tags["entrega/1-tarea-1-ordenamiento/v1"] == sha_ana  # el v1 sigue ahi
    assert tags["entrega/1-tarea-1-ordenamiento/v2"] == sha_antes
    ficha = cliente.get(
        f"/api/cursos/{curso_id}/entregas/{_entrega_id(curso_id)}/sujetos/{v2.sujeto_id}/version"
    ).json()
    assert ficha["vigente"]["intento"] == 2
    assert [a["intento"] for a in ficha["anteriores"]] == [1]


def test_ca_9_8_04_etiqueta_borrada_se_recrea_y_movida_nunca_se_sobrescribe(
    cliente: TestClient, overrides_9101
):
    curso_id, _, _, repos, sha_ana = _preparar(
        cliente, overrides_9101, slug="pds-f4-e", email="f4e@gmail.com"
    )
    _capturar_todo()
    nombre = "entrega/1-tarea-1-ordenamiento/v1"
    del tags_doble(_ORG, repos["2001"])[nombre]
    _encolar("barrido_completo_actividad", curso_id)
    _trabajar()
    ana = _versiones(curso_id)["Ana Soto"][0]
    assert (ana.estado, ana.tag_estado) == ("CAPTURADA", "CREADO")
    assert tags_doble(_ORG, repos["2001"])[nombre] == sha_ana
    with fabrica_bd()() as bd:
        assert bd.query(Incidencia).filter(Incidencia.tipo == "TAG_ALTERADO").count() == 1

    tags_doble(_ORG, repos["2001"])[nombre] = "f" * 40  # alguien la movio
    _encolar("barrido_completo_actividad", curso_id)
    _trabajar()
    ana = _versiones(curso_id)["Ana Soto"][0]
    assert (ana.estado, ana.tag_estado, ana.tag_motivo) == (
        "CAPTURADA_SIN_TAG",
        "CONFLICTO",
        "SHA_DISTINTO",
    )
    assert ana.commit_sha == sha_ana  # la evidencia no se toca
    assert tags_doble(_ORG, repos["2001"])[nombre] == "f" * 40


def _ayudante_con_tarea_administrar(curso_id: str) -> str:
    with fabrica_bd()() as bd:
        ahora = ahora_utc()
        usuario = Usuario(
            google_sub=secrets.token_hex(8),
            email=f"ayudante.{secrets.token_hex(3)}@gmail.com",
            email_canonico=f"ayudante.{secrets.token_hex(3)}@gmail.com",
            nombre="Ayudante",
            activo=True,
            creado_en=ahora,
            actualizado_en=ahora,
        )
        bd.add(usuario)
        bd.flush()
        bd.add(
            MembresiaCurso(
                curso_id=uuid.UUID(curso_id),
                usuario_id=usuario.id,
                rol="AYUDANTE",
                permisos=["tarea.administrar"],
                estado="ACTIVA",
                creada_en=ahora,
            )
        )
        token = secrets.token_urlsafe(32)
        bd.add(
            Sesion(
                usuario_id=usuario.id,
                token_hash=hash_token(token),
                jti_oidc=secrets.token_urlsafe(16),
                creada_en=ahora,
                expira_en=ahora + timedelta(days=1),
            )
        )
        bd.commit()
        return token


def test_ca_9_8_05_y_9_12_02_fijar_un_sha(cliente: TestClient, overrides_9101):
    curso_id, _, corte, repos, sha_ana = _preparar(
        cliente, overrides_9101, slug="pds-f4-f", email="f4f@gmail.com"
    )
    _capturar_todo()
    ana = _versiones(curso_id)["Ana Soto"][0]
    base = f"/api/cursos/{curso_id}/entregas/{_entrega_id(curso_id)}/sujetos/{ana.sujeto_id}"
    otro_repo = agregar_commit_doble(
        _ORG, repos["2002"], fecha=corte - timedelta(hours=1), mensaje="de otro"
    )
    ajeno = cliente.post(
        f"{base}/version/fijar-sha",
        json={"sha": otro_repo, "motivo_manual": "El estudiante pidió corregir esta versión."},
    )
    assert ajeno.status_code == 422, ajeno.text
    assert ajeno.json()["detail"]["motivo"] == "SHA_AJENO"
    assert len(_versiones(curso_id)["Ana Soto"]) == 1  # rechazada antes de escribir nada

    corto = cliente.post(f"{base}/version/fijar-sha", json={"sha": sha_ana, "motivo_manual": "x"})
    assert corto.status_code == 422
    assert corto.json()["detail"]["motivo"] == "MOTIVO_INSUFICIENTE"

    sha_nuevo = agregar_commit_doble(
        _ORG, repos["2001"], fecha=corte - timedelta(minutes=30), mensaje="arreglo"
    )
    ok = cliente.post(
        f"{base}/version/fijar-sha",
        json={"sha": sha_nuevo, "motivo_manual": "Commit correcto acordado en clase."},
    )
    assert ok.status_code == 200, ok.text
    v1, v2 = _versiones(curso_id)["Ana Soto"]
    assert (v1.vigente, v2.vigente, v2.intento, v2.origen_captura) == (
        False,
        True,
        2,
        "MANUAL_SHA",
    )
    assert v2.commit_sha == sha_nuevo and v2.reemplaza_a_id == v1.id

    # CA-9.12-02: un ayudante con `tarea.administrar` no puede fijar ni recapturar.
    _sesion_autenticada(cliente, _ayudante_con_tarea_administrar(curso_id))
    for accion, cuerpo in (
        ("fijar-sha", {"sha": sha_ana, "motivo_manual": "Intento del ayudante a mano."}),
        (
            "recapturar",
            {"fecha_corte": corte.isoformat(), "motivo_manual": "Intento del ayudante a mano."},
        ),
    ):
        assert cliente.post(f"{base}/version/{accion}", json=cuerpo).status_code == 403


def test_ca_9_9_01_y_9_9_02_abrir_redirige_auditado_o_explica(cliente: TestClient, overrides_9101):
    curso_id, _, _, repos, sha_ana = _preparar(
        cliente, overrides_9101, slug="pds-f4-g", email="f4g@gmail.com"
    )
    _capturar_todo()
    ana = _versiones(curso_id)["Ana Soto"][0]
    respuesta = cliente.get(
        f"/api/cursos/{curso_id}/versiones/{ana.id}/abrir",
        params={"destino": "arbol"},
        follow_redirects=False,
    )
    assert respuesta.status_code == 307
    assert (
        respuesta.headers["location"] == f"https://github.com/{_ORG}/{repos['2001']}/tree/{sha_ana}"
    )
    with fabrica_bd()() as bd:
        assert (
            bd.query(Bitacora)
            .filter(Bitacora.accion == "VERSION_ABIERTA", Bitacora.entidad_id == str(ana.id))
            .count()
            == 1
        )
        acceso = (
            bd.query(AccesoDocenteRepositorio)
            .filter(AccesoDocenteRepositorio.repositorio_id == ana.repositorio_id)
            .one()
        )
        acceso.estado = "PENDIENTE"
        bd.commit()
    pendiente = cliente.get(
        f"/api/cursos/{curso_id}/versiones/{ana.id}/abrir",
        params={"destino": "zip"},
        follow_redirects=False,
    )
    assert pendiente.status_code == 409
    assert pendiente.json()["detail"]["motivo"] == "ACCESO_DOCENTE_PENDIENTE"


def test_ca_9_6_05_vinculada_tras_el_cierre_espera_confirmacion(cliente: TestClient, monkeypatch):
    original = ClienteCanvasDoble._assignments_doble

    def _con_9104_vencida(self):
        from dataclasses import replace

        return [
            replace(a, due_at=ahora_utc() - timedelta(days=1))
            if a.canvas_assignment_id == 9104
            else a
            for a in original(self)
        ]

    monkeypatch.setattr(ClienteCanvasDoble, "_assignments_doble", _con_9104_vencida)
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug="pds-f4-h", email="f4h@gmail.com"
    )
    vinculada = cliente.post(
        f"/api/cursos/{curso_id}/tareas/{tarea_id}/entregas",
        json={"canvas_assignment_id": 9104, "final_canvas_assignment_id": 9104},
    )
    assert vinculada.status_code == 200, vinculada.text
    e9104 = next(e for e in vinculada.json()["entregas"] if e["canvas_assignment_id"] == 9104)
    assert e9104["estado_validacion"] == "VINCULADA_TRAS_EL_CIERRE"
    _trabajar()  # sincroniza fechas de la entrega nueva
    _capturar_todo()
    with fabrica_bd()() as bd:
        assert (
            bd.query(VersionEntrega)
            .filter(VersionEntrega.entrega_id == uuid.UUID(e9104["id"]))
            .count()
            == 0
        )
    respuesta = cliente.post(f"/api/cursos/{curso_id}/entregas/{e9104['id']}/registrar-versiones")
    assert respuesta.status_code == 202, respuesta.text
    assert respuesta.json()["encoladas"] == 1  # 9104 solo es visible para Elena
    _trabajar()
    with fabrica_bd()() as bd:
        version = (
            bd.query(VersionEntrega)
            .filter(VersionEntrega.entrega_id == uuid.UUID(e9104["id"]))
            .one()
        )
        assert version.origen_captura == "MANUAL_AHORA"
        assert version.creada_por_usuario_id is not None
        entrega = bd.get(Entrega, uuid.UUID(e9104["id"]))
        assert entrega is not None and entrega.estado_validacion == "VIGENTE"


def test_ca_8_2_03_con_versiones_no_se_desvincula(cliente: TestClient, overrides_9101):
    curso_id, tarea_id, _, _, _ = _preparar(
        cliente, overrides_9101, slug="pds-f4-i", email="f4i@gmail.com"
    )
    _capturar_todo()
    assert (
        cliente.post(
            f"/api/cursos/{curso_id}/tareas/{tarea_id}/entregas",
            json={"canvas_assignment_id": 9104, "final_canvas_assignment_id": 9104},
        ).status_code
        == 200
    )
    respuesta = cliente.delete(
        f"/api/cursos/{curso_id}/tareas/{tarea_id}/entregas/{_entrega_id(curso_id)}"
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"]["motivo"] == "DESVINCULAR_NO_PERMITIDO"


def test_ca_9_10_02_github_sin_acceso_pospone_sin_consumir_intentos(
    cliente: TestClient, overrides_9101, monkeypatch
):
    curso_id, _, _, _, _ = _preparar(
        cliente, overrides_9101, slug="pds-f4-j", email="f4j@gmail.com"
    )

    def _sin_acceso(self, installation_id):
        raise FalloProveedorGithub("instalación suspendida")

    monkeypatch.setattr(ClienteGitHubDoble, "obtener_token_instalacion", _sin_acceso)
    _capturar_todo()
    with fabrica_bd()() as bd:
        pospuestos = (
            bd.query(Trabajo)
            .filter(Trabajo.tipo == "resolver_sha", Trabajo.payload["entrega_id"].isnot(None))
            .all()
        )
        con_repositorio = [t for t in pospuestos if t.estado == "PENDIENTE"]
        assert con_repositorio, "Ana y Bruno quedan pospuestos"
        for t in con_repositorio:
            assert t.intentos == 0
            assert t.proximo_intento_en > ahora_utc() + timedelta(minutes=25)
            assert (t.ultimo_error or "").startswith("GITHUB_SIN_ACCESO")
    assert set(_versiones(curso_id)) == {"Carla Reyes"}  # sin repositorio no necesita GitHub


def test_ca_9_6_06_sujeto_que_nace_despues_del_cierre(cliente: TestClient, overrides_9101):
    """A-204 punto 5: `SIN_REPOSITORIO` con `SUJETO_MATERIALIZADO_TRAS_EL_CIERRE`,
    y cuando el repositorio aparece no se captura solo: se abre VERSION_REVISAR."""
    curso_id, _ = _preparar_curso_con_tarea_activa(cliente, slug="pds-f4-k", email="f4k@gmail.com")
    corte = ahora_utc().replace(microsecond=0) - timedelta(hours=1)
    overrides_9101.append(_override(1, corte, [2005]))  # Elena: sujeto de hoy, sin repositorio
    _encolar_y_ejecutar("sync_tareas_y_fechas", curso_id)
    _capturar_todo()
    elena = _versiones(curso_id)["Elena Rojas"][0]
    assert (elena.estado, elena.motivo) == (
        "SIN_REPOSITORIO",
        "SUJETO_MATERIALIZADO_TRAS_EL_CIERRE",
    )
    with fabrica_bd()() as bd:
        repo = bd.query(Repositorio).filter(Repositorio.sujeto_id == elena.sujeto_id).one()
        versiones_repo.al_quedar_listo_el_repositorio(bd, repo)
        bd.commit()
        incidencia = bd.query(Incidencia).filter(Incidencia.tipo == "VERSION_REVISAR").one()
        assert incidencia.detalle["accion_sugerida"].startswith("captura ahora")
    assert len(_versiones(curso_id)["Elena Rojas"]) == 1  # nada se capturo solo
