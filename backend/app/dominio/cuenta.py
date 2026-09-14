"""Reglas puras de administracion de la propia cuenta (SPEC 02 S2.10.3).

`puede_cerrar_cuenta` es una funcion de dominio: recibe los cursos donde el
usuario ya se sabe que es la unica profesora ACTIVA de un curso ACTIVO (la
consulta la hace la capa de adaptadores, que si conoce el ORM) y decide.

Nota de alcance (Etapa P1): hasta que exista `curso`/`membresia_curso` (Etapa
P2), la lista de cursos bloqueantes que la API le pasa a esta funcion es siempre
vacia -- no hay todavia ningun curso que bloquee nada. La funcion ya queda
correcta para cuando esas tablas existan, sin tener que reescribirla.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CursoBloqueante:
    curso_id: int
    nombre: str


def puede_cerrar_cuenta(
    cursos_donde_es_unica_profesora_activa: list[CursoBloqueante],
) -> list[CursoBloqueante]:
    """Devuelve la lista de cursos que bloquean el cierre (vacia = se puede cerrar)."""
    return list(cursos_donde_es_unica_profesora_activa)
