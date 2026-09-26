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
        # Etapa F10: cambio_fecha referencia mensaje_saliente.
        sesion.execute(text("DELETE FROM cambio_fecha"))
        sesion.execute(text("DELETE FROM mensaje_saliente"))
        for tabla in (
            "plantilla_mensaje",
            "supresion_comunicacion",
            "regla_comunicacion",
            "ventana_supresion",
        ):
            sesion.execute(text(f"DELETE FROM {tabla}"))
        # Etapa F9: informe y suscripcion referencian curso y usuario.
        sesion.execute(text("DELETE FROM informe_diario"))
        sesion.execute(text("DELETE FROM suscripcion_informe"))
        # Etapa F4: `version_entrega` es evidencia y su disparador rechaza todo
        # DELETE; solo la limpieza de pruebas lo apaga durante la sentencia.
        sesion.execute(
            text("ALTER TABLE version_entrega DISABLE TRIGGER version_entrega_inmutable")
        )
        sesion.execute(text("DELETE FROM version_entrega"))
        # Etapa F5: la autoria y los commits referencian identidad_git y repositorio.
        sesion.execute(text("DELETE FROM metrica_repositorio_dia"))
        sesion.execute(text("DELETE FROM participacion_entrega"))
        sesion.execute(text("DELETE FROM resumen_tarea"))
        sesion.execute(text("DELETE FROM autoria_commit"))
        sesion.execute(text("DELETE FROM commit"))
        sesion.execute(text("DELETE FROM identidad_git"))
        sesion.execute(text("DELETE FROM evento_push"))
        sesion.execute(text("DELETE FROM evento_webhook"))
        sesion.execute(text("ALTER TABLE version_entrega ENABLE TRIGGER version_entrega_inmutable"))
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


@pytest.fixture(autouse=True)
def _sin_franja_horaria(monkeypatch):
    """La franja 08:00-21:00 (S11.6.5) depende del reloj real: se apaga para
    que las pruebas no cambien de resultado segun la hora. Las pruebas de la
    franja la encienden."""
    from app.adaptadores import outbox_repo

    monkeypatch.setattr(outbox_repo, "FRANJA_ACTIVA", False)
