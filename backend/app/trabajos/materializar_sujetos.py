"""Trabajo `materializar_sujetos` (SPEC 08 S8.5.1 paso 3; A-164). Cerrojo 1, 3 reintentos.

Tras cada sincronizacion y en barrido cada 5 minutos: recalcula quien es sujeto
de cada tarea activa, aplica la guarda de A-093 y encola el aprovisionamiento de
los que quedaron listos. No llama a ningun proveedor.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.adaptadores import aprovisionamiento_repo, correccion_repo
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Trabajo
from app.adaptadores.modelos_tarea import Entrega, Tarea
from app.infraestructura.cerrojos import cerrojo_canvas
from app.trabajos.registro import registrar


@registrar("materializar_sujetos")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    assert trabajo.curso_id is not None
    curso = sesion.query(Curso).filter(Curso.id == trabajo.curso_id).one()
    with cerrojo_canvas(sesion, curso.id):
        aprovisionamiento_repo.materializar_sujetos(sesion, curso=curso)
        # S12.5.2 (F11): un sujeto tardio queda SIN_CORRECTOR con incidencia si
        # la entrega ya tenia reparto; nunca se asigna solo.
        for entrega in (
            sesion.query(Entrega)
            .join(Tarea, Tarea.id == Entrega.tarea_id)
            .filter(
                Tarea.curso_id == curso.id, Tarea.estado.in_(("ACTIVA", "INCONSISTENTE", "CERRADA"))
            )
        ):
            if correccion_repo.hay_filas(sesion, entrega.id):
                correccion_repo.asegurar_filas(sesion, entrega)
