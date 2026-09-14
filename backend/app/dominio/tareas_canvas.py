"""DTOs de las tareas de Canvas y de sus overrides (SPEC 05 S5.3 endpoints 12-14;
SPEC 08 S8.2; A-164). Sin I/O: `app/adaptadores/cliente_canvas.py` mapea el
JSON de Canvas a estos tipos."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AssignmentCanvasCrudo:
    """Una fila de `GET /courses/:id/assignments?include[]=assignment_visibility`.

    `assignment_visibility` es `None` cuando la instancia no lo devolvio (A-164
    paso 1 lo distingue de una lista vacia: no es lo mismo "nadie" que "no se").
    """

    canvas_assignment_id: int
    nombre: str
    puntos_posibles: float | None
    grading_type: str | None
    publicada: bool
    moderated_grading: bool
    anonymous_grading: bool
    group_category_id: int | None
    only_visible_to_overrides: bool
    due_at: datetime | None
    all_day: bool
    canvas_updated_at: datetime | None
    assignment_visibility: list[int] | None
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def es_grupal(self) -> bool:
        """En Canvas una tarea es grupal si y solo si tiene `group_category_id`."""
        return self.group_category_id is not None


@dataclass(frozen=True)
class OverrideCanvasCrudo:
    """Una fila de `GET /courses/:id/assignments/:aid/overrides` (endpoint 14).
    Exactamente uno de los tres alcances viene poblado."""

    canvas_override_id: int
    student_ids: list[int] | None
    course_section_id: int | None
    group_id: int | None
    due_at: datetime | None
    titulo: str | None
