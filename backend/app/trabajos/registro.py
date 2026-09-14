"""Registro de manejadores de trabajo implementados.

Etapa 0 solo implementa los trabajos "meta" que no dependen de Canvas/GitHub:
`vigilancia` (recuperacion de huerfanos, S14.7.6) y el propio ciclo del
planificador. El resto de los 31 (app/trabajos/catalogo.py) se implementa junto
con la etapa del plan que lo necesita (P3 en adelante) y se añade aqui.
"""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from app.adaptadores.modelos_infraestructura import Trabajo

ManejadorTrabajo = Callable[[Session, Trabajo], None]

_REGISTRO: dict[str, ManejadorTrabajo] = {}


def registrar(tipo: str) -> Callable[[ManejadorTrabajo], ManejadorTrabajo]:
    def decorador(func: ManejadorTrabajo) -> ManejadorTrabajo:
        _REGISTRO[tipo] = func
        return func

    return decorador


def obtener_manejador(tipo: str) -> ManejadorTrabajo | None:
    return _REGISTRO.get(tipo)


def tipos_implementados() -> frozenset[str]:
    return frozenset(_REGISTRO.keys())
