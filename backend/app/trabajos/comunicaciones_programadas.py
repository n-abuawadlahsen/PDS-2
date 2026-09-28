"""Trabajo `comunicaciones_programadas` (SPEC 14 S14.7.4 fila 28; SPEC 11
S11.6.2). Cada 5 minutos por curso.

Evalua los recordatorios (invitacion, cierre, cuenta de GitHub) y anuncia los
cambios de fecha cuya ventana de agrupacion ya cerro. Encola siempre, aunque
un interruptor este apagado: la guarda 4 del despacho lo filtra y el
historial queda completo. No llama a ningun proveedor.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.adaptadores import comunicaciones_repo
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Trabajo
from app.trabajos.registro import registrar


@registrar("comunicaciones_programadas")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    assert trabajo.curso_id is not None
    curso = sesion.query(Curso).filter(Curso.id == trabajo.curso_id).one()
    comunicaciones_repo.programar(sesion, curso)
