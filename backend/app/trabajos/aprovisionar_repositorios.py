"""Trabajo `aprovisionar_repositorios` (SPEC 08 S8.7; A-114, A-217). Cerrojo 2, 8 en ~2 h.

Dos disparadores (S8.7.1): por evento, con `repositorio_id` en el payload y clave
`repo:<tarea>:<sujeto>`; y por barrido cada 2 minutos, sin payload, que re-evalua
todo lo pendiente del curso. Toma siempre el espacio de cerrojo de GitHub y nunca
el de Canvas, para no quedar detras de una sincronizacion lenta (A-217).
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.adaptadores import aprovisionamiento_repo
from app.adaptadores.cliente_github import crear_cliente_github_desde_config
from app.adaptadores.modelos_aprovisionamiento import Repositorio
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Trabajo
from app.infraestructura.cerrojos import cerrojo_github
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar


@registrar("aprovisionar_repositorios")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    assert trabajo.curso_id is not None
    curso = sesion.query(Curso).filter(Curso.id == trabajo.curso_id).one()
    cliente = crear_cliente_github_desde_config(obtener_configuracion())
    repositorio_id = trabajo.payload.get("repositorio_id")
    with cerrojo_github(sesion, curso.id):
        if repositorio_id:
            repositorio = sesion.get(Repositorio, uuid.UUID(repositorio_id))
            if repositorio is not None:
                aprovisionamiento_repo.aprovisionar_repositorio(
                    sesion, cliente, repositorio=repositorio, trabajo_id=trabajo.id
                )
            return
        aprovisionamiento_repo.barrido_aprovisionamiento(sesion, cliente, curso=curso)
