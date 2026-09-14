"""Trabajo `sync_tareas_y_fechas` (SPEC 05 S5.4.3, SPEC 09 S9.4). Cerrojo 1, 4 reintentos.

Etapa P7 implementa su mitad de tareas: espejo `assignment_canvas`, refresco
de las entregas vinculadas y `visibilidad_entrega` (A-164 paso 1). La mitad de
fechas (`regla_fecha`, `fecha_efectiva`, huella) llega con la Etapa P8.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.adaptadores import canvas_repo, tareas_repo
from app.adaptadores.cliente_canvas import crear_cliente_canvas
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Trabajo
from app.infraestructura.cerrojos import cerrojo_canvas
from app.infraestructura.cifrado import Llavero
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar


@registrar("sync_tareas_y_fechas")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    assert trabajo.curso_id is not None
    curso = sesion.query(Curso).filter(Curso.id == trabajo.curso_id).one()
    if curso.canvas_course_id is None:
        return  # Canvas no vinculado todavia; nada que sincronizar
    credencial = canvas_repo.obtener_credencial_operativa(sesion, curso.id)
    if credencial is None:
        return

    settings = obtener_configuracion()
    llavero = Llavero(settings.llavero_cifrado(), settings.app_encryption_key_activa)
    token = canvas_repo.descifrar_token(llavero, credencial)
    cliente = crear_cliente_canvas(
        modo=settings.canvas_modo, canvas_base_url=curso.canvas_base_url or settings.canvas_base_url
    )

    with cerrojo_canvas(sesion, curso.id):
        tareas_repo.sincronizar_tareas(sesion, cliente, curso=curso, token=token)
