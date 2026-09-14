"""JWT internos firmados con `SIGNING_KEY` (SPEC 02 S2.2.2): `state` y confirmacion.

El `state` es un JWT HMAC de 10 minutos que lleva el `nonce` esperado, el
destino de vuelta y `sha256(txn_id)` -- no hay estado de servidor que perder
en una ventana privada.

El `code_verifier` de PKCE tambien viaja dentro del `state` (no en una
cookie): el camino degradado (S2.2.2 parrafo 4) exige poder canjear el codigo
e identificar la cuenta de Google *incluso cuando ninguna cookie vuelve*, y
`state` es lo unico que Google garantiza devolver intacto en la query del
callback. La cookie `oidc_txn` sigue existiendo solo como señal adicional
anti-CSRF de inicio de sesion (S2.2.2 parrafo 3), independiente del canje.

El token de "confirmacion" (camino degradado, S2.2.2 parrafo 4) no lo fija el
SPEC a nivel de mecanismo, solo el comportamiento ("pantalla que nombra la
cuenta ... con un token anti-CSRF de formulario"). Se implementa aqui como un
segundo JWT HMAC de vida corta que lleva las reclamaciones ya validadas de
Google, para no tener que volver a canjear el codigo (de un solo uso) en
`POST /auth/confirmar`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

_ALGORITMO = "HS256"
_EXPIRACION_STATE = timedelta(minutes=10)
_EXPIRACION_CONFIRMACION = timedelta(minutes=10)


@dataclass(frozen=True)
class ReclamacionesState:
    jti: str
    nonce: str
    destino: str
    txn_hash: str
    code_verifier: str
    # Presente solo cuando el acceso viene de "Aceptar la invitacion"
    # (SPEC 02 S2.5.5): la aceptacion se resuelve al final del mismo login.
    invitacion_token: str | None = None


def emitir_state(
    *,
    signing_key: str,
    nonce: str,
    destino: str,
    txn_hash: str,
    jti: str,
    code_verifier: str,
    invitacion_token: str | None = None,
) -> str:
    ahora = datetime.now(UTC)
    return jwt.encode(
        {
            "jti": jti,
            "nonce": nonce,
            "destino": destino,
            "txn_hash": txn_hash,
            "code_verifier": code_verifier,
            "invitacion_token": invitacion_token,
            "iat": ahora,
            "exp": ahora + _EXPIRACION_STATE,
        },
        signing_key,
        algorithm=_ALGORITMO,
    )


class StateInvalido(Exception):
    """S2.2.7 motivo 5: state invalido, caducado o con firma alterada."""


def verificar_state(*, signing_key: str, state: str) -> ReclamacionesState:
    try:
        payload = jwt.decode(state, signing_key, algorithms=[_ALGORITMO])
    except jwt.PyJWTError as exc:
        raise StateInvalido(str(exc)) from exc
    try:
        return ReclamacionesState(
            jti=payload["jti"],
            nonce=payload["nonce"],
            destino=payload["destino"],
            txn_hash=payload["txn_hash"],
            code_verifier=payload["code_verifier"],
            invitacion_token=payload.get("invitacion_token"),
        )
    except KeyError as exc:
        raise StateInvalido(f"falta reclamacion {exc}") from exc


@dataclass(frozen=True)
class ReclamacionesConfirmacion:
    sub: str
    email: str
    email_verified: bool
    nombre: str
    avatar_url: str | None
    hd: str | None
    jti_oidc: str
    destino: str
    invitacion_token: str | None = None


def emitir_confirmacion(*, signing_key: str, datos: ReclamacionesConfirmacion) -> str:
    ahora = datetime.now(UTC)
    payload = {
        "sub": datos.sub,
        "email": datos.email,
        "email_verified": datos.email_verified,
        "nombre": datos.nombre,
        "avatar_url": datos.avatar_url,
        "hd": datos.hd,
        "jti_oidc": datos.jti_oidc,
        "destino": datos.destino,
        "invitacion_token": datos.invitacion_token,
        "iat": ahora,
        "exp": ahora + _EXPIRACION_CONFIRMACION,
    }
    return jwt.encode(payload, signing_key, algorithm=_ALGORITMO)


def verificar_confirmacion(*, signing_key: str, token: str) -> ReclamacionesConfirmacion:
    try:
        payload = jwt.decode(token, signing_key, algorithms=[_ALGORITMO])
    except jwt.PyJWTError as exc:
        raise StateInvalido(str(exc)) from exc
    try:
        return ReclamacionesConfirmacion(
            sub=payload["sub"],
            email=payload["email"],
            email_verified=payload["email_verified"],
            nombre=payload["nombre"],
            avatar_url=payload.get("avatar_url"),
            hd=payload.get("hd"),
            jti_oidc=payload["jti_oidc"],
            destino=payload["destino"],
            invitacion_token=payload.get("invitacion_token"),
        )
    except KeyError as exc:
        raise StateInvalido(f"falta reclamacion {exc}") from exc
