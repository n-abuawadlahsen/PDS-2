"""Reglas puras de administracion de la propia cuenta (SPEC 02 S2.10.3).

`puede_cerrar_cuenta` es una funcion de dominio: recibe los cursos donde el
usuario ya se sabe que es la unica profesora ACTIVA de un curso ACTIVO (la
consulta la hace la capa de adaptadores, que si conoce el ORM) y decide.

"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CursoBloqueante:
    curso_id: UUID
    nombre: str


def puede_cerrar_cuenta(
    cursos_donde_es_unica_profesora_activa: list[CursoBloqueante],
) -> list[CursoBloqueante]:
    """Devuelve la lista de cursos que bloquean el cierre (vacia = se puede cerrar)."""
    return list(cursos_donde_es_unica_profesora_activa)
