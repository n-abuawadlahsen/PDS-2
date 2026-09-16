"""Contrato HTTPS de correo aislado de la red."""

import httpx
import pytest

from app.adaptadores.proveedor_correo import (
    CorreoConsola,
    CorreoResend,
    FalloCorreo,
    crear_proveedor_correo,
    motivo_bloqueo,
)
from app.infraestructura.config import obtener_configuracion


def test_correo_http_con_idempotencia_y_dos_formatos(monkeypatch):
    observado = {}

    def post(url, **kwargs):
        observado.update(url=url, **kwargs)
        return httpx.Response(200, json={"id": "mensaje-prueba"})

    monkeypatch.setattr(httpx, "post", post)
    proveedor = CorreoResend(obtener_configuracion())
    resultado = proveedor.enviar(
        destinatario="prueba@example.test",
        asunto="Invitación",
        html="<p>Prueba</p>",
        texto="Prueba",
        clave_idempotencia="prueba-1",
        reserva="MARGEN",
    )
    assert resultado.id == "mensaje-prueba"
    assert observado["timeout"] == 20
    assert observado["headers"]["Idempotency-Key"] == "prueba-1"
    assert observado["json"]["text"] == "Prueba"
    assert observado["json"]["html"] == "<p>Prueba</p>"


@pytest.mark.parametrize(
    "status,reintentable", [(429, True), (503, True), (422, False), (401, False)]
)
def test_correo_clasifica_sin_filtrar_cuerpo_del_proveedor(monkeypatch, status, reintentable):
    monkeypatch.setattr(
        httpx, "post", lambda *a, **kw: httpx.Response(status, text="secreto-que-no-debe-salir")
    )
    with pytest.raises(FalloCorreo) as error:
        CorreoResend(obtener_configuracion()).enviar(
            destinatario="prueba@example.test",
            asunto="Prueba",
            html="Prueba",
            texto="Prueba",
            clave_idempotencia="prueba",
            reserva="MARGEN",
        )
    assert error.value.reintentable is reintentable
    assert "secreto-que-no-debe-salir" not in str(error.value)


def test_fuera_de_produccion_no_sale_correo_y_produccion_exige_config():
    settings = obtener_configuracion()
    assert isinstance(crear_proveedor_correo(settings), CorreoConsola)
    settings = settings.model_copy(
        update={"entorno": "produccion", "comunicaciones_salientes": "activadas"}
    )
    assert motivo_bloqueo(settings, "prueba@example.test") == "CORREO_SIN_CONFIGURAR"
    settings = settings.model_copy(
        update={"email_proveedor": "resend", "destinatarios_permitidos": "otra@example.test"}
    )
    assert motivo_bloqueo(settings, "prueba@example.test") == "DESTINATARIO_NO_PERMITIDO"
