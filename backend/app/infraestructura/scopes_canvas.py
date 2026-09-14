"""Catalogo cerrado de los 25 endpoints de Canvas que `ClienteCanvas` invoca,
y ninguno mas (SPEC 05 S5.3). Una prueba de arquitectura contrasta cada
llamada real del cliente contra esta lista.

Solo el metodo y la plantilla de ruta (sin dominio): coincide con como
`ClienteCanvasReal` compone la URL a partir de `canvas_base_url`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EndpointCanvas:
    metodo: str
    plantilla: str


LECTURAS: tuple[EndpointCanvas, ...] = (
    EndpointCanvas("GET", "/api/v1/users/self"),
    EndpointCanvas("GET", "/api/v1/courses"),
    EndpointCanvas("GET", "/api/v1/courses/{course_id}"),
    EndpointCanvas("GET", "/api/v1/courses/{course_id}/permissions"),
    EndpointCanvas("GET", "/api/v1/courses/{course_id}/enrollments"),
    EndpointCanvas("GET", "/api/v1/courses/{course_id}/sections"),
    EndpointCanvas("GET", "/api/v1/courses/{course_id}/group_categories"),
    EndpointCanvas("GET", "/api/v1/group_categories/{group_category_id}/groups"),
    EndpointCanvas("GET", "/api/v1/groups/{group_id}/memberships"),
    EndpointCanvas("GET", "/api/v1/courses/{course_id}/late_policy"),
    EndpointCanvas("GET", "/api/v1/courses/{course_id}/grading_periods"),
    EndpointCanvas("GET", "/api/v1/courses/{course_id}/assignments"),
    EndpointCanvas("GET", "/api/v1/courses/{course_id}/assignments/{id}"),
    EndpointCanvas("GET", "/api/v1/courses/{course_id}/assignments/{assignment_id}/overrides"),
    EndpointCanvas(
        "GET", "/api/v1/courses/{course_id}/assignments/{assignment_id}/gradeable_students"
    ),
    EndpointCanvas("GET", "/api/v1/courses/{course_id}/students/submissions"),
    EndpointCanvas("GET", "/api/v1/courses/{course_id}/rubrics/{id}"),
    EndpointCanvas("GET", "/api/v1/search/recipients"),
    EndpointCanvas("GET", "/api/v1/courses/{course_id}/discussion_topics"),
)

ESCRITURAS: tuple[EndpointCanvas, ...] = (
    EndpointCanvas("POST", "/api/v1/courses/{course_id}/assignments"),
    EndpointCanvas("PUT", "/api/v1/courses/{course_id}/assignments/{id}"),
    EndpointCanvas("POST", "/api/v1/courses/{course_id}/discussion_topics"),
    EndpointCanvas("DELETE", "/api/v1/courses/{course_id}/discussion_topics/{topic_id}"),
    EndpointCanvas("POST", "/api/v1/conversations"),
    EndpointCanvas(
        "PUT", "/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    ),
)

SCOPES_CANVAS: tuple[EndpointCanvas, ...] = LECTURAS + ESCRITURAS

assert len(SCOPES_CANVAS) == 25, "el catalogo de Canvas debe tener exactamente 25 endpoints (S5.3)"
