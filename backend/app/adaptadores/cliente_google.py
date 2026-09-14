"""Cliente de Google OpenID Connect (SPEC 02 S2.2.1-S2.2.2). Authorization Code + PKCE.

Solo se piden los alcances `openid email profile`; nunca se guarda `id_token`,
`access_token` ni `refresh_token` (S2.2.1).
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
import jwt
from jwt import PyJWKClient

_AUTORIZACION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
_ISSUERS_VALIDOS = {"accounts.google.com", "https://accounts.google.com"}
_TIMEOUT_SEGUNDOS = 10.0
# Margen para desfase de reloj con Google al validar `iat`/`exp` del id_token: con
# tolerancia 0, un reloj local apenas 1 s atrasado rechaza todo acceso como
# "token aun no valido". 60 s, el mismo margen por desfase de relojes que usa SPEC 09.
_TOLERANCIA_RELOJ_SEGUNDOS = 60

_jwks_client = PyJWKClient(_JWKS_URL)


@dataclass(frozen=True)
class ParPkce:
    code_verifier: str
    code_challenge: str


def generar_pkce() -> ParPkce:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    )
    return ParPkce(code_verifier=verifier, code_challenge=challenge)


def construir_url_autorizacion(
    *, client_id: str, redirect_uri: str, state: str, nonce: str, code_challenge: str
) -> str:
    parametros = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        # A-018 regla 2: siempre, en todo acceso.
        "prompt": "select_account",
    }
    return f"{_AUTORIZACION_URL}?{urlencode(parametros)}"


@dataclass(frozen=True)
class ReclamacionesIdToken:
    sub: str
    email: str
    email_verified: bool
    name: str
    picture: str | None
    hd: str | None


class FalloProveedorGoogle(Exception):
    """5xx o timeout del proveedor (S2.2.7 motivo 8): nunca se traduce a 500 propio."""


def intercambiar_codigo(
    *,
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code_verifier: str,
    nonce_esperado: str,
) -> ReclamacionesIdToken:
    try:
        respuesta = httpx.post(
            _TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "code_verifier": code_verifier,
            },
            timeout=_TIMEOUT_SEGUNDOS,
        )
    except httpx.TimeoutException as exc:
        raise FalloProveedorGoogle("tiempo de espera agotado") from exc

    if respuesta.status_code >= 500:
        raise FalloProveedorGoogle(f"Google respondio {respuesta.status_code}")
    respuesta.raise_for_status()

    id_token = respuesta.json()["id_token"]
    clave_firmante = _jwks_client.get_signing_key_from_jwt(id_token)
    reclamaciones = jwt.decode(
        id_token,
        clave_firmante.key,
        algorithms=["RS256"],
        audience=client_id,
        leeway=_TOLERANCIA_RELOJ_SEGUNDOS,
        options={"require": ["exp", "iat", "sub"]},
    )
    if reclamaciones.get("iss") not in _ISSUERS_VALIDOS:
        raise ValueError("iss invalido en id_token")
    if reclamaciones.get("nonce") != nonce_esperado:
        raise ValueError("nonce no coincide")

    return ReclamacionesIdToken(
        sub=reclamaciones["sub"],
        email=reclamaciones["email"],
        email_verified=bool(reclamaciones.get("email_verified", False)),
        name=reclamaciones.get("name", ""),
        picture=reclamaciones.get("picture"),
        hd=reclamaciones.get("hd"),
    )
