"""Contrato HTTPS de correo aislado de la red."""

import smtplib

import httpx
import pytest

from app.adaptadores.proveedor_correo import (
    CorreoConsola,
    CorreoGmailApi,
    CorreoResend,
    CorreoSmtp,
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


class _SmtpFalso:
    """Doble de smtplib.SMTP: registra la conversacion y puede fallar a pedido."""

    instancias: list["_SmtpFalso"] = []
    fallo: Exception | None = None

    def __init__(self, host, port, timeout):
        self.host, self.port, self.timeout = host, port, timeout
        self.pasos: list[str] = []
        self.mensaje = None
        _SmtpFalso.instancias.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.pasos.append("quit")

    def starttls(self, context=None):
        self.pasos.append("starttls")

    def login(self, usuario, contrasena):
        self.pasos.append(f"login:{usuario}")
        if isinstance(_SmtpFalso.fallo, smtplib.SMTPAuthenticationError):
            raise _SmtpFalso.fallo

    def send_message(self, mensaje):
        if _SmtpFalso.fallo is not None:
            raise _SmtpFalso.fallo
        self.mensaje = mensaje
        self.pasos.append("send")


def _settings_smtp():
    return obtener_configuracion().model_copy(
        update={
            "entorno": "produccion",
            "comunicaciones_salientes": "activadas",
            "destinatarios_permitidos": "",
            "email_proveedor": "smtp",
            "email_from": "proyecto2pds@gmail.com",
            "email_from_nombre": "Proyecto 2",
            "email_reply_to": "contacto@gmail.com",
            "email_dominio_verificado": "gmail.com",
            "smtp_usuario": "proyecto2pds@gmail.com",
            "smtp_contrasena": "abcd efgh ijkl mnop",
        }
    )


@pytest.fixture
def smtp_falso(monkeypatch):
    _SmtpFalso.instancias.clear()
    _SmtpFalso.fallo = None
    monkeypatch.setattr(smtplib, "SMTP", _SmtpFalso)
    return _SmtpFalso


def test_smtp_envia_con_starttls_login_y_dos_formatos(smtp_falso):
    settings = _settings_smtp()
    proveedor = crear_proveedor_correo(settings)
    assert isinstance(proveedor, CorreoSmtp)
    resultado = proveedor.enviar(
        destinatario="docente@miuandes.cl",
        asunto="Informe diario",
        html="<p>Hola</p>",
        texto="Hola",
        clave_idempotencia="informe-1",
        reserva="MARGEN",
        cabeceras={"List-Unsubscribe": "<https://app/baja>"},
    )
    conexion = smtp_falso.instancias[0]
    assert (conexion.host, conexion.port, conexion.timeout) == ("smtp.gmail.com", 587, 20)
    assert conexion.pasos == ["starttls", "login:proyecto2pds@gmail.com", "send", "quit"]
    m = conexion.mensaje
    assert m["To"] == "docente@miuandes.cl"
    assert m["From"] == "Proyecto 2 <proyecto2pds@gmail.com>"
    assert m["Reply-To"] == "contacto@gmail.com"
    assert m["Subject"] == "Informe diario"
    assert m["List-Unsubscribe"] == "<https://app/baja>"
    tipos = [p.get_content_type() for p in m.iter_parts()]
    assert tipos == ["text/plain", "text/html"]
    assert resultado.id == m["Message-ID"] and not resultado.simulado


@pytest.mark.parametrize(
    "fallo,reintentable",
    [
        (smtplib.SMTPAuthenticationError(535, b"bad credentials"), False),
        (smtplib.SMTPServerDisconnected("se corto"), True),
        (smtplib.SMTPResponseException(421, b"intenta luego"), True),
        (smtplib.SMTPResponseException(550, b"buzon inexistente"), False),
        (smtplib.SMTPRecipientsRefused({"x@y": (550, b"no")}), False),
        (TimeoutError("lento"), True),
    ],
)
def test_smtp_clasifica_errores_sin_filtrar_credenciales(smtp_falso, fallo, reintentable):
    smtp_falso.fallo = fallo
    with pytest.raises(FalloCorreo) as error:
        CorreoSmtp(_settings_smtp()).enviar(
            destinatario="docente@miuandes.cl",
            asunto="Prueba",
            html="Prueba",
            texto="Prueba",
            clave_idempotencia="prueba",
            reserva="MARGEN",
        )
    assert error.value.reintentable is reintentable
    assert "abcd efgh" not in str(error.value)


def test_produccion_con_smtp_exige_usuario_y_contrasena():
    settings = _settings_smtp()
    assert motivo_bloqueo(settings, "docente@miuandes.cl") is None
    sin_clave = settings.model_copy(update={"smtp_contrasena": None})
    assert motivo_bloqueo(sin_clave, "docente@miuandes.cl") == "CORREO_SIN_CONFIGURAR"
    otro_dominio = settings.model_copy(update={"email_dominio_verificado": "otro.cl"})
    assert motivo_bloqueo(otro_dominio, "docente@miuandes.cl") == "CORREO_SIN_CONFIGURAR"


def _settings_gmail_api():
    return _settings_smtp().model_copy(
        update={
            "email_proveedor": "gmail_api",
            "smtp_usuario": None,
            "smtp_contrasena": None,
            "gmail_client_id": "cliente-gmail",
            "gmail_client_secret": "secreto-cliente",
            "gmail_refresh_token": "refresh-secreto",
        }
    )


def _google_falso(monkeypatch, token=None, envio=None, fallo_red=False):
    llamadas = []

    def post(url, **kwargs):
        llamadas.append((url, kwargs))
        if fallo_red:
            raise httpx.ConnectError("sin red")
        if url.startswith("https://oauth2.googleapis.com/"):
            return token or httpx.Response(200, json={"access_token": "acceso-1"})
        return envio or httpx.Response(200, json={"id": "gmail-123"})

    monkeypatch.setattr(httpx, "post", post)
    return llamadas


def test_gmail_api_renueva_token_y_envia_mime_por_https(monkeypatch):
    import base64
    from email import message_from_bytes

    llamadas = _google_falso(monkeypatch)
    proveedor = crear_proveedor_correo(_settings_gmail_api())
    assert isinstance(proveedor, CorreoGmailApi)
    resultado = proveedor.enviar(
        destinatario="docente@miuandes.cl",
        asunto="Informe diario",
        html="<p>Hola</p>",
        texto="Hola",
        clave_idempotencia="informe-1",
        reserva="MARGEN",
        cabeceras={"List-Unsubscribe": "<https://app/baja>"},
    )
    (url_token, token), (url_envio, envio) = llamadas
    assert url_token == "https://oauth2.googleapis.com/token"
    assert token["data"] == {
        "client_id": "cliente-gmail",
        "client_secret": "secreto-cliente",
        "refresh_token": "refresh-secreto",
        "grant_type": "refresh_token",
    }
    assert url_envio == "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
    assert envio["headers"]["Authorization"] == "Bearer acceso-1"
    m = message_from_bytes(base64.urlsafe_b64decode(envio["json"]["raw"]))
    assert m["To"] == "docente@miuandes.cl"
    assert m["From"] == "Proyecto 2 <proyecto2pds@gmail.com>"
    assert m["List-Unsubscribe"] == "<https://app/baja>"
    assert [p.get_content_type() for p in m.get_payload()] == ["text/plain", "text/html"]
    assert resultado.id == "gmail-123" and not resultado.simulado


def test_gmail_api_sin_client_id_propio_usa_el_del_login(monkeypatch):
    llamadas = _google_falso(monkeypatch)
    settings = _settings_gmail_api().model_copy(
        update={"gmail_client_id": None, "gmail_client_secret": None}
    )
    CorreoGmailApi(settings).enviar(
        destinatario="docente@miuandes.cl",
        asunto="Prueba",
        html="Prueba",
        texto="Prueba",
        clave_idempotencia="prueba",
        reserva="MARGEN",
    )
    assert llamadas[0][1]["data"]["client_id"] == settings.google_client_id
    assert llamadas[0][1]["data"]["client_secret"] == settings.google_client_secret


@pytest.mark.parametrize(
    "token,envio,fallo_red,reintentable",
    [
        (httpx.Response(400, text="invalid_grant refresh-secreto"), None, False, False),
        (httpx.Response(503, text="caido"), None, False, True),
        (httpx.Response(200, json={}), None, False, True),
        (None, httpx.Response(403, text="refresh-secreto"), False, False),
        (None, httpx.Response(429, text="cuota"), False, True),
        (None, httpx.Response(200, json={}), False, True),
        (None, None, True, True),
    ],
)
def test_gmail_api_clasifica_errores_sin_filtrar_credenciales(
    monkeypatch, token, envio, fallo_red, reintentable
):
    _google_falso(monkeypatch, token=token, envio=envio, fallo_red=fallo_red)
    with pytest.raises(FalloCorreo) as error:
        CorreoGmailApi(_settings_gmail_api()).enviar(
            destinatario="docente@miuandes.cl",
            asunto="Prueba",
            html="Prueba",
            texto="Prueba",
            clave_idempotencia="prueba",
            reserva="MARGEN",
        )
    assert error.value.reintentable is reintentable
    assert "refresh-secreto" not in str(error.value)
    assert "secreto-cliente" not in str(error.value)


def test_produccion_con_gmail_api_exige_refresh_token():
    settings = _settings_gmail_api()
    assert motivo_bloqueo(settings, "docente@miuandes.cl") is None
    sin_token = settings.model_copy(update={"gmail_refresh_token": " "})
    assert motivo_bloqueo(sin_token, "docente@miuandes.cl") == "CORREO_SIN_CONFIGURAR"
