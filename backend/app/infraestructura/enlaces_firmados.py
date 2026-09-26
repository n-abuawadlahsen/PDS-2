"""Enlaces firmados con `SIGNING_KEY` (SPEC 11 S11.4.4, S11.5.3; S14.6.2).

HMAC-SHA256 sobre la carga JSON, comparado en tiempo constante. No es un JWT:
el algoritmo es fijo y el token no puede declarar otro. Durante la rotacion
se aceptan la clave vigente y la anterior (se pasan en ese orden).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime
from typing import Any


def _b64(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode()


def _desde_b64(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def _firma(cuerpo: str, clave: str) -> str:
    return _b64(hmac.new(clave.encode(), cuerpo.encode(), hashlib.sha256).digest())


def firmar(carga: dict[str, Any], clave: str, *, expira_en: datetime) -> str:
    cuerpo = _b64(json.dumps({**carga, "exp": int(expira_en.timestamp())}, sort_keys=True).encode())
    return f"{cuerpo}.{_firma(cuerpo, clave)}"


def verificar(token: str, claves: list[str], *, ahora: datetime) -> dict[str, Any] | None:
    """La carga sin `exp`, o `None` si la firma no cuadra con ninguna clave o
    el enlace vencio."""
    cuerpo, _, firma = token.partition(".")
    if not cuerpo or not firma:
        return None
    if not any(hmac.compare_digest(_firma(cuerpo, c), firma) for c in claves if c):
        return None
    try:
        carga = json.loads(_desde_b64(cuerpo))
    except ValueError:
        return None
    if not isinstance(carga, dict) or int(carga.pop("exp", 0)) < ahora.timestamp():
        return None
    return carga
