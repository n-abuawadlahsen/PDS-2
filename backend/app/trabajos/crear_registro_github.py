"""Completa el registro Canvas cuando su creación/restauración síncrona agota la espera."""

import uuid

from sqlalchemy.orm import Session

from app.adaptadores import canvas_repo, registro_github_repo
from app.adaptadores.cliente_canvas import crear_cliente_canvas
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_identidad import Usuario
from app.adaptadores.modelos_infraestructura import Trabajo
from app.dominio.permisos import Permiso, permisos_efectivos
from app.infraestructura.cerrojos import cerrojo_canvas
from app.infraestructura.cifrado import Llavero
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar


@registrar("crear_registro_github")
def ejecutar(bd: Session, trabajo: Trabajo) -> None:
    curso = bd.get(Curso, trabajo.curso_id)
    actor_id = uuid.UUID(trabajo.payload["actor_usuario_id"])
    actor = bd.get(Usuario, actor_id)
    miembro = (
        bd.query(MembresiaCurso)
        .filter_by(curso_id=trabajo.curso_id, usuario_id=actor_id)
        .one_or_none()
    )
    if curso is None or curso.estado == "ARCHIVADO" or actor is None or not actor.activo:
        raise ValueError("El curso o la cuenta ya no permiten completar el registro.")
    if (
        miembro is None
        or miembro.estado != "ACTIVA"
        or Permiso.COMUNICACION_ENVIAR
        not in permisos_efectivos(
            rol=miembro.rol,
            permisos_configurados=frozenset(Permiso(p) for p in miembro.permisos),
        )
    ):
        raise ValueError(
            "La persona que solicitó el registro ya no tiene permiso de comunicaciones."
        )
    credencial = canvas_repo.obtener_credencial_operativa(bd, curso.id)
    if credencial is None or curso.canvas_course_id is None:
        raise ValueError("Renueva la vinculación Canvas antes de completar el registro.")
    settings = obtener_configuracion()
    token = canvas_repo.descifrar_token(
        Llavero(settings.llavero_cifrado(), settings.app_encryption_key_activa), credencial
    )
    cliente = crear_cliente_canvas(
        modo=settings.canvas_modo, canvas_base_url=curso.canvas_base_url or settings.canvas_base_url
    )
    with cerrojo_canvas(bd, curso.id):
        operacion = (
            registro_github_repo.restaurar_tarea_registro
            if trabajo.payload.get("restaurar")
            else registro_github_repo.crear_tarea_registro
        )
        operacion(bd, cliente, token, curso=curso, actor_usuario_id=actor_id)
