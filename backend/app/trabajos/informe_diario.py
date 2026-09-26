"""Trabajo `informe_diario` (SPEC 14 S14.7.4 fila 29; SPEC 11 S11.3.3; A-229).

07:00 en la zona del curso y barrido cada 30 min hasta las 23:00: si la fila
`(curso, hoy)` ya existe no hace nada. La genera desde el espejo (ninguna
llamada externa) y encola un correo por suscriptor solo si la creo ahora y
hay tareas activas.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.adaptadores import informe_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Trabajo
from app.dominio.estados import OrigenMensaje
from app.infraestructura.cerrojos import cerrojo_canvas
from app.trabajos.registro import registrar

HORA_INICIO = 7
HORA_FIN = 23


def en_horario(curso: Curso, ahora: datetime) -> bool:
    hora = ahora.astimezone(ZoneInfo(curso.zona_horaria)).hour
    return HORA_INICIO <= hora < HORA_FIN


def generar_y_encolar(sesion: Session, curso: Curso, *, ahora: datetime) -> bool:
    informe, creado = informe_repo.generar(sesion, curso, ahora=ahora, origen="PROGRAMADO")
    if creado:
        informe_repo.encolar_correos(
            sesion,
            informe,
            informe_repo.suscriptores(sesion, curso.id),
            reserva="INFORME",
            origen=OrigenMensaje.AUTOMATICO,
        )
    return creado


@registrar("informe_diario")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    assert trabajo.curso_id is not None
    curso = sesion.query(Curso).filter(Curso.id == trabajo.curso_id).one()
    ahora = ahora_utc()
    if not en_horario(curso, ahora):
        return
    with cerrojo_canvas(sesion, curso.id):
        generar_y_encolar(sesion, curso, ahora=ahora)
