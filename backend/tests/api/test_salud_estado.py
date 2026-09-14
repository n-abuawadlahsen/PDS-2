from __future__ import annotations

from fastapi.testclient import TestClient


def test_salud_no_requiere_sesion_ni_toca_bd(cliente: TestClient):
    respuesta = cliente.get("/salud")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "ok"
    assert "version" in cuerpo


def test_estado_forma_anonima(cliente: TestClient):
    respuesta = cliente.get("/estado")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["base_de_datos"]["alcanzable"] is True
    assert cuerpo["esquema"]["revision_actual"] == cuerpo["esquema"]["revision_esperada"]


def test_capacidades_perfil_parcial_sin_banderas(cliente: TestClient):
    respuesta = cliente.get("/api/capacidades")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["perfil"] == "parcial"
    assert cuerpo["banderas"] == []
