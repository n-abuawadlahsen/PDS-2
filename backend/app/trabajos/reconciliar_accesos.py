"""Comprueba invitaciones cada minuto y bajo demanda, con cerrojo 2 y lotes acotados."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.adaptadores import aprovisionamiento_repo
from app.adaptadores.cliente_github import crear_cliente_github_desde_config
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_infraestructura import Trabajo
from app.dominio.permisos import Permiso, permisos_efectivos
from app.infraestructura.cerrojos import cerrojo_github
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar


@registrar("reconciliar_accesos")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    assert trabajo.curso_id is not None
    curso = sesion.query(Curso).filter(Curso.id == trabajo.curso_id).one()
    actor_id = trabajo.payload.get("actor_membresia_id")
    if actor_id:
        actor = sesion.get(MembresiaCurso, uuid.UUID(actor_id))
        if (
            actor is None
            or actor.curso_id != curso.id
            or actor.estado != "ACTIVA"
            or Permiso.MAPEO_EDITAR
            not in permisos_efectivos(
                rol=actor.rol, permisos_configurados=frozenset(Permiso(p) for p in actor.permisos)
            )
        ):
            return
    cliente = crear_cliente_github_desde_config(obtener_configuracion())
    with cerrojo_github(sesion, curso.id):
        tarea_id = trabajo.payload.get("tarea_id")
        aprovisionamiento_repo.reconciliar_accesos(
            sesion,
            cliente,
            curso=curso,
            tarea_id=uuid.UUID(tarea_id) if tarea_id else None,
            periodico=bool(trabajo.payload.get("periodico")),
            repositorio_id=uuid.UUID(trabajo.payload["repositorio_id"])
            if trabajo.payload.get("repositorio_id")
            else None,
            estudiante_id=uuid.UUID(trabajo.payload["estudiante_id"])
            if trabajo.payload.get("estudiante_id")
            else None,
        )
