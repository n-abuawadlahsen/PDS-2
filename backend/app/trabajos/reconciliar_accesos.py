"""Trabajo `reconciliar_accesos` (SPEC 08 S8.8; A-212). Cerrojo 2, 15 min, 4 reintentos."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.adaptadores import aprovisionamiento_repo
from app.adaptadores.cliente_github import crear_cliente_github_desde_config
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Trabajo
from app.infraestructura.cerrojos import cerrojo_github
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar


@registrar("reconciliar_accesos")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    assert trabajo.curso_id is not None
    curso = sesion.query(Curso).filter(Curso.id == trabajo.curso_id).one()
    cliente = crear_cliente_github_desde_config(obtener_configuracion())
    with cerrojo_github(sesion, curso.id):
        aprovisionamiento_repo.reconciliar_accesos(sesion, cliente, curso=curso)
