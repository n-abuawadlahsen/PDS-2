"""Consulta del espejo y enlace a Canvas; RG-082 prohíbe editar el assignment."""

from typing import Any

from sqlalchemy.orm import Session

from app.adaptadores.modelos_correccion import Correccion, PublicacionNota
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_tarea import AssignmentCanvas, Entrega


def previsualizar(bd: Session, entrega: Entrega) -> dict[str, Any]:
    espejo = (
        bd.query(AssignmentCanvas)
        .filter_by(curso_id=entrega.curso_id, canvas_assignment_id=entrega.canvas_assignment_id)
        .one_or_none()
    )
    intentada = (
        bd.query(PublicacionNota.id)
        .join(Correccion, Correccion.id == PublicacionNota.correccion_id)
        .filter(Correccion.entrega_id == entrega.id)
        .first()
    )
    iniciada = (
        bd.query(Correccion.id)
        .filter(
            Correccion.entrega_id == entrega.id,
            (Correccion.estado == "PUBLICANDO") | (Correccion.intentos > 0),
        )
        .first()
    )
    grupal = bool(espejo and espejo.es_grupal)
    individual = bool(espejo and espejo.payload.get("grade_group_students_individually"))
    curso = bd.get(Curso, entrega.curso_id)
    enlace = (
        f"{curso.canvas_base_url.rstrip('/')}/courses/{curso.canvas_course_id}/assignments/{entrega.canvas_assignment_id}/edit"
        if curso and curso.canvas_base_url and curso.canvas_course_id
        else None
    )
    return {
        "es_grupal": grupal,
        "individual": individual,
        "puede_cambiar": grupal and not individual and not intentada and not iniciada,
        "motivo": "Ya existe un intento de publicación para esta entrega."
        if intentada or iniciada
        else None,
        "enlace_canvas": enlace,
    }
