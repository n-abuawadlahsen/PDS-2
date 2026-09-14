"""DTOs de los datos crudos de Canvas para el espejo del padron (SPEC 07 S7.2).

Sin I/O: los adaptadores de `app/adaptadores/cliente_canvas.py` mapean el
JSON de Canvas a estos tipos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

_T = TypeVar("_T")


@dataclass(frozen=True)
class ResultadoPaginado(Generic[_T]):
    """S5.4.2: `per_page_medido` nunca se asume, se mide; `truncado` es
    verdadero cuando el tope de 50 paginas cerro el ciclo (S14.7.5 patron,
    no falla, solo dice "no llegue a la ultima pagina")."""

    items: list[_T]
    per_page_medido: int
    truncado: bool


@dataclass(frozen=True)
class MatriculaCruda:
    """Una fila de `GET /courses/:id/enrollments?type[]=StudentEnrollment`,
    con los campos del `user` embebido (S7.2.4: solo si la instancia los
    entrega)."""

    canvas_enrollment_id: int
    canvas_user_id: int
    canvas_section_id: int
    tipo: str
    role_id: int | None
    workflow_state: str
    limitada_a_seccion: bool
    nombre: str
    nombre_ordenable: str | None
    login_id: str | None
    sis_user_id: str | None
    email: str | None
    uuid: str | None
    past_uuid: str | None


@dataclass(frozen=True)
class SeccionCruda:
    """Una fila de `GET /courses/:id/sections`."""

    canvas_section_id: int
    nombre: str
    sis_section_id: str | None
    nonxlist_course_id: int | None


@dataclass(frozen=True)
class ConjuntoGruposCrudo:
    """Una fila de `GET /courses/:id/group_categories`."""

    canvas_group_category_id: int
    nombre: str
    no_colaborativo: bool
    self_signup: str | None
    group_limit: int | None
    auto_leader: str | None


@dataclass(frozen=True)
class GrupoCrudo:
    """Una fila de `GET /group_categories/:id/groups`. `slug` no viene de
    Canvas (su API no expone uno): lo deriva la aplicacion del nombre al
    insertar (`app/dominio/padron.py::slug_desde_nombre`), para uso propio
    (p. ej. nombrar el repositorio del grupo en una etapa posterior)."""

    canvas_group_id: int
    canvas_group_category_id: int
    nombre: str
    is_full: bool


@dataclass(frozen=True)
class PertenenciaCruda:
    """Una fila de `GET /groups/:id/memberships`."""

    canvas_user_id: int
    workflow_state: str
