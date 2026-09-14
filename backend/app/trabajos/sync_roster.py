"""Trabajo `sync_roster` (SPEC 05 S5.4.3, SPEC 07 S7.3.1). Cerrojo 1, 4 reintentos.

Unica fuente de que personas existen en el curso (S7.2.5): lee secciones y
matriculas, en ese orden, en la misma ejecucion.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.adaptadores import canvas_repo, padron_repo
from app.adaptadores.cliente_canvas import crear_cliente_canvas
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Trabajo
from app.infraestructura.cerrojos import cerrojo_canvas
from app.infraestructura.cifrado import Llavero
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar


@registrar("sync_roster")
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
        padron_repo.sincronizar_roster(sesion, cliente, curso=curso, token=token)
