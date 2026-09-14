"""Clasificacion de errores de proveedores externos en tres familias (SPEC 14 S14.7.5).

Identica para Canvas y GitHub. Un limite de una API externa jamas se pinta como
error propio (Ley 5): todo 403 no reconocido se clasifica BLOQUEANTE, nunca
PERMANENTE.
"""

from __future__ import annotations

from app.dominio.estados import FamiliaError

_CODIGOS_TRANSITORIOS = {429, 500, 502, 503, 504}


def clasificar_error_http(
    *, codigo_estado: int, cuerpo_reconocido_como_permanente: bool = False
) -> FamiliaError:
    """Clasifica una respuesta HTTP de Canvas o GitHub.

    `cuerpo_reconocido_como_permanente` la fija el adaptador de cada proveedor
    cuando reconoce explicitamente el cuerpo de un 4xx de validacion (p. ej. un
    422). Un 403 sin reconocer nunca llega aqui como PERMANENTE.
    """
    if codigo_estado in _CODIGOS_TRANSITORIOS:
        return FamiliaError.TRANSITORIO
    if codigo_estado == 403:
        return FamiliaError.BLOQUEANTE
    if codigo_estado == 401:
        return FamiliaError.BLOQUEANTE
    if 400 <= codigo_estado < 500:
        if cuerpo_reconocido_como_permanente:
            return FamiliaError.PERMANENTE
        return FamiliaError.BLOQUEANTE
    return FamiliaError.BLOQUEANTE


def clasificar_tiempo_de_espera_agotado() -> FamiliaError:
    return FamiliaError.TRANSITORIO
