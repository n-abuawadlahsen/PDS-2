"""Las cinco comprobaciones al pegar un token de Canvas (SPEC 05 S5.2.3,
version canonica; SPEC 04 S4.5.2 la repite palabra por palabra).

Reglas puras: reciben datos ya obtenidos de la API de Canvas (DTOs, sin I/O)
y deciden. La llamada HTTP real es de `app/adaptadores/cliente_canvas.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MotivoRechazoVinculacion(StrEnum):
    """Catalogo cerrado de desenlaces del pegado de token (S4.5.5)."""

    TOKEN_INVALIDO = "TOKEN_INVALIDO"
    SIN_MATRICULA_PROFESOR = "SIN_MATRICULA_PROFESOR"
    IDENTIDAD_YA_VINCULADA_A_OTRO_USUARIO = "IDENTIDAD_YA_VINCULADA_A_OTRO_USUARIO"
    IDENTIDAD_NO_COINCIDE = "IDENTIDAD_NO_COINCIDE"
    CURSO_YA_VINCULADO = "CURSO_YA_VINCULADO"
    LIMITADO_A_SECCION = "LIMITADO_A_SECCION"
    INSTANCIA_NO_RECONOCIDA = "INSTANCIA_NO_RECONOCIDA"


class RechazoVinculacion(Exception):
    def __init__(self, motivo: MotivoRechazoVinculacion, detalle: str = "") -> None:
        self.motivo = motivo
        self.detalle = detalle
        super().__init__(motivo.value)


@dataclass(frozen=True)
class UsuarioCanvas:
    """Respuesta de `GET /api/v1/users/self` (comprobacion 2.a)."""

    canvas_user_id: int
    nombre: str


@dataclass(frozen=True)
class CursoCanvas:
    """Una tarjeta de `GET /courses?enrollment_type=teacher...` (S4.5.3)."""

    canvas_course_id: int
    nombre: str
    codigo: str
    termino: str | None
    total_estudiantes: int | None


@dataclass(frozen=True)
class MatriculaCanvas:
    """Una fila de `GET /courses/:id/enrollments` (S5.3 endpoint 5)."""

    tipo: str  # "TeacherEnrollment", etc.
    workflow_state: str  # "active", "invited", "completed", ...
    limitada_a_seccion: bool  # limit_privileges_to_course_section


def tiene_matricula_profesor_activa(matriculas: list[MatriculaCanvas]) -> bool:
    """Comprobacion 2.b: matricula de profesor ACTIVA en el curso que se vincula."""
    return any(m.tipo == "TeacherEnrollment" and m.workflow_state == "active" for m in matriculas)


def todas_las_matriculas_profesor_limitadas_a_seccion(matriculas: list[MatriculaCanvas]) -> bool:
    """A-052: si TODAS las matriculas de profesor activas estan limitadas, se bloquea."""
    matriculas_profesor_activas = [
        m for m in matriculas if m.tipo == "TeacherEnrollment" and m.workflow_state == "active"
    ]
    if not matriculas_profesor_activas:
        return False
    return all(m.limitada_a_seccion for m in matriculas_profesor_activas)


@dataclass(frozen=True)
class DetalleCursoCanvas:
    """Respuesta de `GET /courses/:id?include[]=permissions&permissions[]=...`
    (SPEC 04 S4.7.2 items 2, 4, 5, 6, 7, 13, 16, 17, 19: un solo viaje)."""

    existe: bool
    publicado: bool
    time_zone: str | None
    permisos: dict[str, bool]


@dataclass(frozen=True)
class SeccionCanvas:
    """`GET /courses/:id/sections` (item 8, deteccion de cross-listing, A-053)."""

    section_id: int
    nombre: str
    es_cross_listed: bool


@dataclass(frozen=True)
class PeriodoCalificacionCanvas:
    """`GET /courses/:id/grading_periods` (item 11)."""

    is_closed: bool


@dataclass(frozen=True)
class RosterCanvas:
    """Primera pagina de `GET /courses/:id/users?enrollment_type[]=student`
    (items 12 y 15: tamano real de pagina y recuento de estudiantes)."""

    cantidad_primera_pagina: int
    hay_siguiente_pagina: bool


def item_3_aprobado(matriculas: list[MatriculaCanvas]) -> bool:
    """S4.7.2 item 3: profesor del curso y no limitado a una seccion."""
    return tiene_matricula_profesor_activa(matriculas) and not (
        todas_las_matriculas_profesor_limitadas_a_seccion(matriculas)
    )


# Canvas partio `manage_assignments` en `_add`/`_edit`/`_delete`; en una
# instancia actual el nombre antiguo responde `false`, igual que un permiso
# inexistente (medido en uandes.test.instructure.com el 15-sep-2026).
PERMISO_TAREAS_ANTIGUO = "manage_assignments"
PERMISOS_TAREAS_GRANULARES = ("manage_assignments_add", "manage_assignments_edit")


def item_16_aprobado(permisos: dict[str, bool]) -> bool:
    """S4.7.2 item 16: crear y editar tareas. Vale el permiso antiguo o, en su
    lugar, los dos granulares (crear y editar) a la vez."""
    if permisos.get(PERMISO_TAREAS_ANTIGUO):
        return True
    return all(permisos.get(p) for p in PERMISOS_TAREAS_GRANULARES)


@dataclass(frozen=True)
class IdentidadExistente:
    canvas_user_id: int


def verificar_identidad(
    *, canvas_user_id_devuelto: int, identidad_previa: IdentidadExistente | None
) -> None:
    """Comprobaciones 2.d/2.e: si ya hay identidad registrada, debe coincidir."""
    if identidad_previa is not None and identidad_previa.canvas_user_id != canvas_user_id_devuelto:
        raise RechazoVinculacion(MotivoRechazoVinculacion.IDENTIDAD_NO_COINCIDE)
