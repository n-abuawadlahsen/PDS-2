"""SPEC 11 S11.2 y SPEC 08 S8.10 (Etapa P8): plantillas, clave y guardas."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.dominio.comunicaciones import (
    INVITACION_ACEPTADA,
    REPOSITORIO_DISPONIBLE,
    PlantillaInvalida,
    clave_idempotencia,
    guardas_outbox,
    instrucciones_de_acceso,
    renderizar,
)
from app.dominio.estados import EstadoMensaje

_VALORES = {
    "estudiante.nombre": "Ana Pérez",
    "tarea.nombre": "Tarea 1",
    "curso.nombre": "Desarrollo de Software",
    "organizacion.nombre": "PDS-2",
    "repositorio.nombre": "pds-2-t1-e2001-perez-ana",
    "repositorio.url": "https://github.com/PDS-2/pds-2-t1-e2001-perez-ana",
    "acceso.instrucciones": instrucciones_de_acceso(via_invitacion=True, invitacion_url=None),
    "entrega.fecha_cierre": "01-10-2026 20:59 (America/Santiago)",
    "cuenta_github.login": "ana-perez",
}


def test_repositorio_disponible_dice_lo_que_exige_a_127():
    cuerpo = renderizar(REPOSITORIO_DISPONIBLE.cuerpo, REPOSITORIO_DISPONIBLE, _VALORES)
    assert "PDS-2" in cuerpo
    assert "pds-2-t1-e2001-perez-ana" in cuerpo
    assert "https://github.com/PDS-2/pds-2-t1-e2001-perez-ana" in cuerpo
    assert "no encontrado" in cuerpo
    assert "(America/Santiago)" in cuerpo
    assert "spam" in cuerpo
    assert "{{" not in cuerpo


def test_acceso_directo_no_habla_de_invitacion_pendiente():
    texto = instrucciones_de_acceso(via_invitacion=False, invitacion_url=None)
    assert "no necesitas aceptar" in texto


def test_sin_url_del_repositorio_el_mensaje_no_se_construye():
    valores = dict(_VALORES)
    valores["repositorio.url"] = ""
    with pytest.raises(PlantillaInvalida):
        renderizar(REPOSITORIO_DISPONIBLE.cuerpo, REPOSITORIO_DISPONIBLE, valores)


def test_variable_desconocida_se_rechaza():
    with pytest.raises(PlantillaInvalida):
        renderizar("{{version.sha_corto}}", INVITACION_ACEPTADA, _VALORES)


def test_la_clave_es_por_persona():
    comun = {
        "canal": "CANVAS_CONVERSACION",
        "plantilla": "repositorio_disponible",
        "entidad": "repo-1",
    }
    ana = clave_idempotencia(destinatario="2001", **comun)
    beto = clave_idempotencia(destinatario="2002", **comun)
    assert ana != beto
    assert ana == clave_idempotencia(destinatario="2001", **comun)
    assert ana != clave_idempotencia(destinatario="2001", generacion=2, **comun)


def test_guardas_en_orden():
    ahora = datetime(2026, 9, 15, tzinfo=UTC)
    assert guardas_outbox(ahora=ahora, caduca_en=None, estado_estudiante="ACTIVO") is None
    assert guardas_outbox(
        ahora=ahora, caduca_en=ahora - timedelta(minutes=1), estado_estudiante="RETIRADO"
    ) == (
        EstadoMensaje.CADUCADO,
        "CADUCIDAD_ALCANZADA",
    )
    assert guardas_outbox(ahora=ahora, caduca_en=None, estado_estudiante="RETIRADO") == (
        EstadoMensaje.SUPRIMIDO,
        "MATRICULA_NO_ACTIVA",
    )
    assert guardas_outbox(ahora=ahora, caduca_en=None, estado_estudiante="INVITADO") is None
