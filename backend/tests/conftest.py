from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from tests.apoyo import fabrica_bd


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def limpiar_tablas_identidad():
    yield
    with fabrica_bd()() as sesion:
        # Orden que respeta las FK RESTRICT: lo que referencia primero.
        sesion.execute(text("DELETE FROM bitacora"))
        # Etapa P8: lo que referencia repositorio, sujeto y regla_fecha primero.
        sesion.execute(text("DELETE FROM mensaje_saliente"))
        sesion.execute(text("DELETE FROM fecha_efectiva"))
        sesion.execute(text("DELETE FROM regla_fecha"))
        sesion.execute(text("DELETE FROM acceso_repositorio"))
        sesion.execute(text("DELETE FROM acceso_docente_repositorio"))
        sesion.execute(text("UPDATE repositorio SET reemplaza_a_id = NULL"))
        sesion.execute(text("DELETE FROM repositorio"))
        sesion.execute(text("DELETE FROM sujeto"))
        sesion.execute(text("DELETE FROM trabajo_periodico"))
        # Etapa P7: el ciclo tarea <-> repositorio_base se rompe antes de borrar.
        sesion.execute(text("DELETE FROM visibilidad_entrega"))
        sesion.execute(text("DELETE FROM archivo_repositorio_base"))
        sesion.execute(text("UPDATE tarea SET repositorio_base_id = NULL"))
        sesion.execute(text("DELETE FROM repositorio_base"))
        sesion.execute(text("DELETE FROM entrega"))
        sesion.execute(text("DELETE FROM tarea"))
        sesion.execute(text("DELETE FROM assignment_canvas"))
        sesion.execute(text("DELETE FROM acceso_docente_repositorio"))
        sesion.execute(text("DELETE FROM sesion_membresia"))
        sesion.execute(text("DELETE FROM invitacion_equipo"))
        sesion.execute(text("DELETE FROM membresia_curso"))
        sesion.execute(text("DELETE FROM credencial_canvas"))
        sesion.execute(text("DELETE FROM identidad_canvas_usuario"))
        sesion.execute(text("DELETE FROM verificacion_vinculacion"))
        sesion.execute(text("DELETE FROM verificacion_canal"))
        sesion.execute(text("DELETE FROM equipo_github_curso"))
        sesion.execute(text("DELETE FROM intento_instalacion_github"))
        sesion.execute(text("DELETE FROM instalacion_github"))
        sesion.execute(text("DELETE FROM mapeo_github"))
        sesion.execute(text("DELETE FROM cuenta_github"))
        sesion.execute(text("DELETE FROM pertenencia_grupo"))
        sesion.execute(text("DELETE FROM grupo"))
        sesion.execute(text("DELETE FROM conjunto_grupos"))
        sesion.execute(text("DELETE FROM matricula"))
        sesion.execute(text("DELETE FROM estudiante"))
        sesion.execute(text("DELETE FROM seccion"))
        sesion.execute(text("DELETE FROM incidencia"))
        sesion.execute(text("DELETE FROM sincronizacion"))
        sesion.execute(text("DELETE FROM cursor_sincronizacion"))
        sesion.execute(text("DELETE FROM sesion"))
        sesion.execute(text("DELETE FROM trabajo"))
        # `curso.registro_creado_por` referencia `usuario` (RESTRICT, Etapa
        # P6): el curso debe borrarse antes que el usuario que lo creo.
        sesion.execute(text("DELETE FROM curso"))
        sesion.execute(text("DELETE FROM usuario"))
        sesion.commit()
