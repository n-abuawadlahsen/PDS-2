"""SPEC 07 S7.2-S7.3 (Etapa P5): espejo de estudiantes, secciones y grupos,
con Canvas en modo doble (backend/.env: CANVAS_MODO=doble)."""

from __future__ import annotations

import secrets
import uuid
from datetime import timedelta

from fastapi.testclient import TestClient

from app.adaptadores import trabajos_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.adaptadores.modelos_infraestructura import Incidencia
from app.adaptadores.modelos_padron import Estudiante, Seccion
from app.api.dependencias import hash_token
from app.dominio.estados import EstadoEstudiante, EstadoSeccion
from app.trabajos import (  # noqa: F401 (registra los manejadores)
    aprovisionar_repositorios,
    materializar_sujetos,
    registro,
    sync_grupos,
    sync_roster,
    sync_tareas_y_fechas,
)
from tests.apoyo import fabrica_bd

_BASE_URL_DOBLE = "https://canvas-doble.local"


def _crear_usuario_con_sesion(*, email: str, nombre: str = "Profesora") -> str:
    with fabrica_bd()() as bd:
        ahora = ahora_utc()
        usuario = Usuario(
            google_sub=secrets.token_hex(8),
            email=email,
            email_canonico=email,
            nombre=nombre,
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
                expira_en=ahora_utc().replace(year=ahora.year + 1),
            )
        )
        bd.commit()
        return token


def _sesion_autenticada(cliente: TestClient, token: str) -> None:
    cliente.cookies.set("sesion", token)
    csrf = secrets.token_urlsafe(16)
    cliente.cookies.set("csrf_token", csrf)
    cliente.headers.update({"X-CSRF-Token": csrf})


def _crear_curso(cliente: TestClient, *, slug: str) -> dict:
    respuesta = cliente.post(
        "/api/cursos",
        json={
            "nombre": "Curso de prueba",
            "codigo": "ICC4201",
            "periodo": "2026-2",
            "slug": slug,
            "zona_horaria": "America/Santiago",
        },
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def _vincular_canvas(cliente: TestClient, curso_id: str) -> None:
    respuesta = cliente.post(
        f"/api/cursos/{curso_id}/vinculacion/canvas",
        json={"token": "valido", "canvas_base_url": _BASE_URL_DOBLE, "canvas_course_id": 5001},
    )
    assert respuesta.status_code == 200, respuesta.text


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


def _sincronizar_ahora(cliente: TestClient, curso_id: str) -> None:
    respuesta = cliente.post(f"/api/cursos/{curso_id}/sincronizaciones")
    assert respuesta.status_code == 202, respuesta.text
    _ejecutar_trabajos_pendientes()


def test_sincronizar_ahora_puebla_estudiantes_secciones_y_grupos(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.padron1@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-padron-1")
    _vincular_canvas(cliente, curso["id"])

    _sincronizar_ahora(cliente, curso["id"])

    personas = cliente.get(f"/api/cursos/{curso['id']}/personas")
    assert personas.status_code == 200, personas.text
    cuerpo = personas.json()
    assert len(cuerpo["estudiantes"]) == 5
    assert {e["estado"] for e in cuerpo["estudiantes"]} == {"ACTIVO"}
    assert len(cuerpo["secciones"]) == 2
    assert len(cuerpo["grupos"]) == 2
    assert cuerpo["roster_sincronizado_en"] is not None
    assert cuerpo["grupos_sincronizado_en"] is not None

    grupo_1 = next(g for g in cuerpo["grupos"] if g["nombre"] == "Grupo 1")
    assert sorted(grupo_1["integrantes"]) == ["Ana Soto", "Bruno Diaz"]
    ana = next(e for e in cuerpo["estudiantes"] if e["nombre"] == "Ana Soto")
    assert ana["secciones"] == ["Sección 1"]
    assert ana["grupos"] == ["Grupo 1"]

    elena = next(e for e in cuerpo["estudiantes"] if e["nombre"] == "Elena Rojas")
    assert elena["grupos"] == []  # a proposito, sin grupo (fixture doble)


def test_sincronizar_ahora_es_idempotente_entre_ciclos(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.padron2@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-padron-2")
    _vincular_canvas(cliente, curso["id"])

    _sincronizar_ahora(cliente, curso["id"])
    _sincronizar_ahora(cliente, curso["id"])

    with fabrica_bd()() as bd:
        cantidad = (
            bd.query(Estudiante).filter(Estudiante.curso_id == uuid.UUID(curso["id"])).count()
        )
        assert cantidad == 5


def test_cabecera_excluye_estados_no_activos(cliente: TestClient):
    token = _crear_usuario_con_sesion(email="profe.padron3@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-padron-3")
    _vincular_canvas(cliente, curso["id"])
    _sincronizar_ahora(cliente, curso["id"])

    cabecera = cliente.get(f"/api/cursos/{curso['id']}/personas/cabecera")
    assert cabecera.status_code == 200
    assert cabecera.json() == {"con_cuenta_verificada": 0, "total": 5}


def test_seccion_ausente_se_elimina_tras_dos_ciclos(cliente: TestClient):
    """S7.3.2: CA-7.3-01."""
    token = _crear_usuario_con_sesion(email="profe.padron4@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-padron-4")
    _vincular_canvas(cliente, curso["id"])
    _sincronizar_ahora(cliente, curso["id"])

    with fabrica_bd()() as bd:
        bd.add(
            Seccion(
                curso_id=uuid.UUID(curso["id"]),
                canvas_section_id=999,
                nombre="Sección fantasma",
                sis_section_id=None,
                nonxlist_course_id=None,
                estado=EstadoSeccion.ACTIVA.value,
                ciclos_ausente=0,
                sincronizado_en=ahora_utc(),
            )
        )
        bd.commit()

    _sincronizar_ahora(cliente, curso["id"])
    with fabrica_bd()() as bd:
        fantasma = (
            bd.query(Seccion)
            .filter(Seccion.curso_id == uuid.UUID(curso["id"]), Seccion.canvas_section_id == 999)
            .one()
        )
        assert fantasma.estado == EstadoSeccion.ACTIVA.value
        assert fantasma.ciclos_ausente == 1

    _sincronizar_ahora(cliente, curso["id"])
    with fabrica_bd()() as bd:
        fantasma = (
            bd.query(Seccion)
            .filter(Seccion.curso_id == uuid.UUID(curso["id"]), Seccion.canvas_section_id == 999)
            .one()
        )
        assert fantasma.estado == EstadoSeccion.ELIMINADA.value


def test_roster_sospechoso_no_da_de_baja_a_nadie(cliente: TestClient):
    """S7.3.8/S7.9.10 (A-045): CA resumido "un roster que cae de 200 a 40 no
    da de baja a nadie". Se simula sembrando 10 estudiantes ACTIVOS de mas,
    de forma que el roster fijo de 5 del doble caiga bajo el 60%."""
    token = _crear_usuario_con_sesion(email="profe.padron5@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-padron-5")
    _vincular_canvas(cliente, curso["id"])

    with fabrica_bd()() as bd:
        ahora = ahora_utc()
        for i in range(10):
            bd.add(
                Estudiante(
                    curso_id=uuid.UUID(curso["id"]),
                    canvas_user_id=9000 + i,
                    nombre=f"Fantasma {i}",
                    estado=EstadoEstudiante.ACTIVO.value,
                    ciclos_ausente=0,
                    primera_vista_en=ahora,
                    ultima_vista_en=ahora,
                )
            )
        bd.commit()

    _sincronizar_ahora(cliente, curso["id"])

    with fabrica_bd()() as bd:
        cantidad_activos = (
            bd.query(Estudiante)
            .filter(
                Estudiante.curso_id == uuid.UUID(curso["id"]),
                Estudiante.estado != EstadoEstudiante.RETIRADO.value,
            )
            .count()
        )
        # Los 10 fantasmas siguen sin retirar y los 5 reales del doble no se
        # llegaron a espejar: la guarda corto la sincronizacion entera.
        assert cantidad_activos == 10
        incidencia = (
            bd.query(Incidencia)
            .filter(
                Incidencia.curso_id == uuid.UUID(curso["id"]),
                Incidencia.tipo == "ROSTER_SOSPECHOSO",
            )
            .one_or_none()
        )
        assert incidencia is not None
        assert incidencia.abierta


def test_estudiante_ausente_se_retira_tras_dos_ciclos(cliente: TestClient):
    """S7.9.1: CA-7.9-01 (la mitad: aqui solo el retiro, no la reincorporacion)."""
    token = _crear_usuario_con_sesion(email="profe.padron6@gmail.com")
    _sesion_autenticada(cliente, token)
    curso = _crear_curso(cliente, slug="pds-padron-6")
    _vincular_canvas(cliente, curso["id"])
    _sincronizar_ahora(cliente, curso["id"])

    with fabrica_bd()() as bd:
        ahora = ahora_utc()
        bd.add(
            Estudiante(
                curso_id=uuid.UUID(curso["id"]),
                canvas_user_id=8001,
                nombre="Se va del curso",
                estado=EstadoEstudiante.ACTIVO.value,
                ciclos_ausente=0,
                primera_vista_en=ahora - timedelta(days=10),
                ultima_vista_en=ahora - timedelta(days=10),
            )
        )
        bd.commit()

    _sincronizar_ahora(cliente, curso["id"])
    _sincronizar_ahora(cliente, curso["id"])

    with fabrica_bd()() as bd:
        fantasma = (
            bd.query(Estudiante)
            .filter(
                Estudiante.curso_id == uuid.UUID(curso["id"]), Estudiante.canvas_user_id == 8001
            )
            .one()
        )
        assert fantasma.estado == EstadoEstudiante.RETIRADO.value
        assert fantasma.retirado_en is not None
