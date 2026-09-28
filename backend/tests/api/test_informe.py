"""Etapa F9 (SPEC 11 S11.3-S11.5): informe docente diario y suscripcion, de
punta a punta con Canvas y GitHub en modo doble y el correo por consola."""

from __future__ import annotations

import secrets
import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.adaptadores import cursos_repo, outbox_repo, suscripciones_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_aprovisionamiento import MensajeSaliente
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.adaptadores.modelos_informe import InformeDiario, SuscripcionInforme
from app.adaptadores.modelos_infraestructura import Incidencia
from app.adaptadores.modelos_padron import Estudiante
from app.adaptadores.modelos_tarea import Tarea
from app.adaptadores.proveedor_correo import correos_consola
from app.api.dependencias import hash_token
from app.dominio import informe as dominio_informe
from app.infraestructura.config import obtener_configuracion
from app.main import crear_app
from app.trabajos import ejecutor, informe_diario  # noqa: F401 (registra manejadores)
from tests.api.test_aprovisionamiento import (
    _despachar_outbox,
    _encolar_y_ejecutar,
    _preparar_curso_con_tarea_activa,
    _sesion_autenticada,
)
from tests.apoyo import fabrica_bd


@pytest.fixture(autouse=True)
def _siempre_en_horario(monkeypatch):
    monkeypatch.setattr(informe_diario, "en_horario", lambda curso, ahora: True)
    # Como las pruebas de invitaciones de main: el .env local deja las
    # comunicaciones pausadas y el despacho respeta ese bloqueo.
    activadas = obtener_configuracion().model_copy(update={"comunicaciones_salientes": "activadas"})
    monkeypatch.setattr(outbox_repo, "obtener_configuracion", lambda: activadas)
    correos_consola.clear()


def _curso_activo(cliente: TestClient, slug: str) -> tuple[str, str]:
    curso_id, tarea_id = _preparar_curso_con_tarea_activa(
        cliente, slug=slug, email=f"{slug}@gmail.com"
    )
    with fabrica_bd()() as bd:
        bd.get(Curso, uuid.UUID(curso_id)).estado = "ACTIVO"  # type: ignore[union-attr]
        bd.commit()
    return curso_id, tarea_id


def _informes(curso_id: str) -> list[InformeDiario]:
    with fabrica_bd()() as bd:
        filas = bd.query(InformeDiario).filter(InformeDiario.curso_id == uuid.UUID(curso_id)).all()
        for f in filas:
            bd.expunge(f)
        return filas


def _correos(curso_id: str) -> list[MensajeSaliente]:
    with fabrica_bd()() as bd:
        filas = (
            bd.query(MensajeSaliente)
            .filter(
                MensajeSaliente.curso_id == uuid.UUID(curso_id), MensajeSaliente.canal == "CORREO"
            )
            .order_by(MensajeSaliente.creado_en)
            .all()
        )
        for f in filas:
            bd.expunge(f)
        return filas


def _miembro(
    curso_id: str, *, rol: str = "AYUDANTE", permisos: list[str] | None = None
) -> tuple[str, uuid.UUID]:
    """Un miembro activo con sesion, suscrito como si hubiera aceptado."""
    with fabrica_bd()() as bd:
        ahora = ahora_utc()
        correo = f"miembro.{secrets.token_hex(3)}@gmail.com"
        usuario = Usuario(
            google_sub=secrets.token_hex(8),
            email=correo,
            email_canonico=correo,
            nombre="Ayudante Uno",
            activo=True,
            creado_en=ahora,
            actualizado_en=ahora,
        )
        bd.add(usuario)
        bd.flush()
        membresia = MembresiaCurso(
            curso_id=uuid.UUID(curso_id),
            usuario_id=usuario.id,
            rol=rol,
            permisos=permisos or [],
            estado="ACTIVA",
            creada_en=ahora,
        )
        bd.add(membresia)
        bd.flush()
        suscripciones_repo.al_entrar(bd, curso_id=uuid.UUID(curso_id), usuario_id=usuario.id)
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
        return token, membresia.id


def test_sin_tareas_activas_no_hay_correo(cliente: TestClient):
    # CA-11.3-01
    curso_id, tarea_id = _curso_activo(cliente, "pds-f9-a")
    with fabrica_bd()() as bd:
        bd.get(Tarea, uuid.UUID(tarea_id)).estado = "BORRADOR"  # type: ignore[union-attr]
        bd.commit()
    _encolar_y_ejecutar("informe_diario", curso_id)
    informes = _informes(curso_id)
    assert [i.estado for i in informes] == ["SIN_TAREAS_ACTIVAS"]
    assert informes[0].contenido_html is None
    assert _correos(curso_id) == []
    vista = cliente.get(f"/api/cursos/{curso_id}/informe-de-hoy/vista-previa").json()
    assert vista["hay_tareas_activas"] is False and "tareas activas" in vista["mensaje"]


def test_una_fila_por_dia_un_correo_por_suscriptor_y_sin_correos_de_estudiantes(
    cliente: TestClient,
):
    curso_id, _ = _curso_activo(cliente, "pds-f9-b")
    with fabrica_bd()() as bd:
        for e in bd.query(Estudiante).filter(Estudiante.curso_id == uuid.UUID(curso_id)):
            e.email = f"alumno{e.canvas_user_id}@uc.cl"
        bd.commit()
    _encolar_y_ejecutar("informe_diario", curso_id)
    _encolar_y_ejecutar("informe_diario", curso_id)
    informes = _informes(curso_id)
    assert len(informes) == 1 and informes[0].estado == "GENERADO"  # CA-11.5-02
    correos = _correos(curso_id)
    assert len(correos) == 1 and correos[0].reserva == "INFORME"
    _despachar_outbox()
    correo = _correos(curso_id)[0]
    # Fuera de produccion se simula, como las invitaciones (main).
    assert (correo.estado, correo.motivo_estado) == ("SUPRIMIDO", "SIMULADO_LOCAL")
    assert correo.proveedor_id
    enviado = correos_consola[-1]
    assert "ICC4201 · Informe docente del" in enviado.asunto  # CA-11.5-01
    assert enviado.cabeceras["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    assert "/api/baja/" in enviado.cabeceras["List-Unsubscribe"]
    with fabrica_bd()() as bd:
        correos_estudiantes = [
            e.email
            for e in bd.query(Estudiante).filter(Estudiante.curso_id == uuid.UUID(curso_id))
            if e.email
        ]
    assert correos_estudiantes  # hay de donde filtrar
    for email in correos_estudiantes:  # CA-11.5-07
        assert email not in enviado.html and email not in enviado.texto
    # El informe queda visible en la aplicacion.
    dia = informes[0].fecha.isoformat()
    vista = cliente.get(f"/api/cursos/{curso_id}/informes/{dia}")
    assert vista.status_code == 200 and vista.json()["html"]
    listado = cliente.get(f"/api/cursos/{curso_id}/informes").json()
    assert listado["se_genera_desde"] == dia


def test_enviarme_solo_a_mi_con_tope_y_enviar_a_todos_exige_administrar(cliente: TestClient):
    curso_id, _ = _curso_activo(cliente, "pds-f9-c")
    token, membresia_id = _miembro(curso_id)
    _sesion_autenticada(cliente, token)
    assert cliente.get(f"/api/cursos/{curso_id}/mis-notificaciones").status_code == 200
    for _ in range(2):
        respuesta = cliente.post(f"/api/cursos/{curso_id}/informe-de-hoy/enviarme")
        assert respuesta.status_code == 202, respuesta.text  # CA-11.5-03
    correos = _correos(curso_id)
    assert {c.membresia_id for c in correos} == {membresia_id}  # nadie mas
    assert [c.generacion for c in correos] == [1, 2] and {c.reserva for c in correos} == {"MARGEN"}
    assert cliente.post(f"/api/cursos/{curso_id}/informe-de-hoy/enviarme").status_code == 429
    assert cliente.post(f"/api/cursos/{curso_id}/informe-de-hoy/enviar").status_code == 403


def test_baja_por_enlace_get_no_cambia_post_da_de_baja_y_regenerar_invalida(
    cliente: TestClient,
):
    curso_id, _ = _curso_activo(cliente, "pds-f9-d")
    _encolar_y_ejecutar("informe_diario", curso_id)
    _despachar_outbox()
    enlace = correos_consola[-1].cabeceras["List-Unsubscribe"].strip("<>")
    token = enlace.rsplit("/", 1)[1]
    ruta = f"/api/baja/{token}"
    cliente.cookies.clear()  # el enlace no depende de ninguna sesion
    assert cliente.get(ruta).json()["activa"] is True
    assert cliente.get(ruta).json()["activa"] is True  # CA-11.4-03: el GET no cambia nada
    assert cliente.post(ruta).json()["activa"] is False
    assert cliente.post(ruta, params={"accion": "alta"}).json()["activa"] is True
    with fabrica_bd()() as bd:
        fila = (
            bd.query(SuscripcionInforme)
            .filter(SuscripcionInforme.curso_id == uuid.UUID(curso_id))
            .one()
        )
        usuario = bd.get(Usuario, fila.usuario_id)
        usuario.generacion_enlaces += 1  # type: ignore[union-attr]
        bd.commit()
    assert cliente.get(ruta).status_code == 404  # CA-11.4-04


def test_retiro_suprime_el_correo_encolado_y_reincorporacion_respeta_la_baja_propia(
    cliente: TestClient,
):
    curso_id, _ = _curso_activo(cliente, "pds-f9-e")
    _, membresia_id = _miembro(curso_id)
    _encolar_y_ejecutar("informe_diario", curso_id)
    with fabrica_bd()() as bd:
        membresia = bd.get(MembresiaCurso, membresia_id)
        actor = bd.query(Usuario).filter(Usuario.email == "pds-f9-e@gmail.com").one()
        cursos_repo.retirar_membresia(bd, membresia, actor=actor, curso_activo=False)  # type: ignore[arg-type]
        bd.commit()
    _despachar_outbox()
    del_miembro = [c for c in _correos(curso_id) if c.membresia_id == membresia_id]
    assert [(c.estado, c.motivo_estado) for c in del_miembro] == [
        ("SUPRIMIDO", "MATRICULA_NO_ACTIVA")
    ]
    with fabrica_bd()() as bd:
        membresia = bd.get(MembresiaCurso, membresia_id)
        cursos_repo.reincorporar_membresia(bd, membresia, permisos=frozenset())  # type: ignore[arg-type]
        fila = bd.get(SuscripcionInforme, (uuid.UUID(curso_id), membresia.usuario_id))  # type: ignore[union-attr]
        assert fila is not None and fila.activa  # CA-11.4-07: retirado por el profesor
        suscripciones_repo.cambiar_propia(
            bd, curso_id=fila.curso_id, usuario_id=fila.usuario_id, activa=False
        )
        cursos_repo.retirar_membresia(bd, membresia, actor=actor, curso_activo=False)  # type: ignore[arg-type]
        cursos_repo.reincorporar_membresia(bd, membresia, permisos=frozenset())  # type: ignore[arg-type]
        assert not fila.activa and fila.origen_baja == "USUARIO"  # se dio de baja el mismo
        bd.commit()


def test_cuota_agotada_difiere_sin_perder_y_abre_incidencia(cliente: TestClient, monkeypatch):
    # CA-11.5-06
    curso_id, _ = _curso_activo(cliente, "pds-f9-f")
    monkeypatch.setitem(dominio_informe.CUOTA_DIARIA, "INFORME", 0)
    monkeypatch.setitem(dominio_informe.CUOTA_DIARIA, "MARGEN", 0)
    _encolar_y_ejecutar("informe_diario", curso_id)
    _despachar_outbox()
    correo = _correos(curso_id)[0]
    assert (correo.estado, correo.motivo_estado) == ("DIFERIDO", "CUOTA_AGOTADA")
    assert correo.programado_para is not None and correo.programado_para > ahora_utc()
    with fabrica_bd()() as bd:
        assert bd.query(Incidencia).filter(Incidencia.tipo == "CUOTA_CORREO_AGOTADA").count() == 1


def test_tope_de_suscriptores(cliente: TestClient, monkeypatch):
    # CA-11.4-08 con el tope reducido a 1
    curso_id, _ = _curso_activo(cliente, "pds-f9-g")
    monkeypatch.setattr(suscripciones_repo, "TOPE_SUSCRIPTORES", 1)
    _, membresia_id = _miembro(curso_id)
    with fabrica_bd()() as bd:
        m = bd.get(MembresiaCurso, membresia_id)
        fila = bd.get(SuscripcionInforme, (uuid.UUID(curso_id), m.usuario_id))  # type: ignore[union-attr]
        assert fila is not None and not fila.activa and fila.origen_baja == "TOPE_SUSCRIPTORES"


def test_ninguna_ruta_recibe_un_usuario_destino():
    # CA-11.4-05
    rutas = [getattr(r, "path", "") for r in crear_app().routes]
    assert rutas and not [r for r in rutas if "{usuario_id}" in r]
