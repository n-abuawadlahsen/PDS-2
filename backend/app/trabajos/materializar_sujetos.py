"""Trabajo `materializar_sujetos` (SPEC 08 S8.5.1 paso 3; A-164). Cerrojo 1, 3 reintentos.

Tras cada sincronizacion y en barrido cada 5 minutos: recalcula quien es sujeto
de cada tarea activa, aplica la guarda de A-093 y encola el aprovisionamiento de
los que quedaron listos. No llama a ningun proveedor.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.adaptadores import aprovisionamiento_repo
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Trabajo
from app.infraestructura.cerrojos import cerrojo_canvas
from app.trabajos.registro import registrar


@registrar("materializar_sujetos")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    assert trabajo.curso_id is not None
    curso = sesion.query(Curso).filter(Curso.id == trabajo.curso_id).one()
    with cerrojo_canvas(sesion, curso.id):
        aprovisionamiento_repo.materializar_sujetos(sesion, curso=curso)
