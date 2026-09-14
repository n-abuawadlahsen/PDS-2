"""Logs estructurados con redaccion central (SPEC 14 S14.6.1.6).

Un filtro central redacta la cabecera Authorization, el token cifrado, cualquier
clave de correo, la clave privada de la GitHub App y la cadena de conexion; no se
confia en la disciplina de quien escribe cada linea de log.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping, MutableMapping
from typing import Any, cast

import structlog

_PATRONES_SECRETOS: list[re.Pattern[str]] = [
    re.compile(r"(?i)(authorization\"?\s*[:=]\s*\"?)(bearer\s+\S+|\S+)"),
    re.compile(r"(-----BEGIN [A-Z ]*PRIVATE KEY-----)[\s\S]+?(-----END [A-Z ]*PRIVATE KEY-----)"),
    re.compile(r"(?i)(postgres(?:ql)?:\/\/)[^@\s]+@"),
    re.compile(r"(?i)((?:api|secret|token|key)[\"']?\s*[:=]\s*[\"']?)([A-Za-z0-9_\-./+=]{12,})"),
]

_MASCARA = "[REDACTADO]"


def redactar_texto(texto: str) -> str:
    resultado = texto
    resultado = _PATRONES_SECRETOS[0].sub(rf"\1{_MASCARA}", resultado)
    resultado = _PATRONES_SECRETOS[1].sub(rf"\1{_MASCARA}\2", resultado)
    resultado = _PATRONES_SECRETOS[2].sub(rf"\1{_MASCARA}@", resultado)
    resultado = _PATRONES_SECRETOS[3].sub(rf"\1{_MASCARA}", resultado)
    return resultado


def _procesador_redaccion(
    logger: Any, nombre_metodo: str, event_dict: MutableMapping[str, Any]
) -> Mapping[str, Any]:
    for clave, valor in list(event_dict.items()):
        if isinstance(valor, str):
            event_dict[clave] = redactar_texto(valor)
    return event_dict


def configurar_logs(*, entorno: str, version: str) -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _procesador_redaccion,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    structlog.contextvars.bind_contextvars(entorno=entorno, version=version)


def obtener_logger(nombre: str) -> structlog.stdlib.BoundLogger:
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(nombre))
