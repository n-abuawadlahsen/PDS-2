"""Trabajo `sincronizar_acceso_docente` (PLAN-IMPLEMENTACION.md Etapa P4).

Dos modos: con `membresia_id` en el payload, incorpora a esa persona sola (al
cambiar el equipo del curso, S2.9.6); sin payload, barrido cada hora que
confirma `org_github_estado = PENDIENTE -> ACTIVA` cuando la invitacion de
organizacion ya fue aceptada.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.adaptadores import github_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_github import ClienteGitHub, crear_cliente_github_desde_config
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_identidad import Usuario
from app.adaptadores.modelos_infraestructura import Trabajo
from app.dominio.estados import EstadoMembresia, EstadoOrgGithubMembresia
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar


@registrar("sincronizar_acceso_docente")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    settings = obtener_configuracion()
    cliente = crear_cliente_github_desde_config(settings)

    membresia_id_raw = trabajo.payload.get("membresia_id")
    if membresia_id_raw:
        curso = sesion.query(Curso).filter(Curso.id == trabajo.curso_id).one()
        membresia = (
            sesion.query(MembresiaCurso)
            .filter(MembresiaCurso.id == uuid.UUID(membresia_id_raw))
            .one()
        )
        github_repo.sincronizar_acceso_de_un_docente(
            sesion, cliente, curso=curso, membresia=membresia
        )
        return

    _barrido_pendientes(sesion, cliente)


def _barrido_pendientes(sesion: Session, cliente: ClienteGitHub) -> None:
    pendientes = (
        sesion.query(MembresiaCurso)
        .join(Curso, Curso.id == MembresiaCurso.curso_id)
        .filter(
            MembresiaCurso.estado == EstadoMembresia.ACTIVA.value,
            MembresiaCurso.org_github_estado == EstadoOrgGithubMembresia.PENDIENTE.value,
            Curso.github_org_login.is_not(None),
            Curso.github_installation_id.is_not(None),
        )
        .all()
    )
    for membresia in pendientes:
        curso = sesion.query(Curso).filter(Curso.id == membresia.curso_id).one()
        usuario = sesion.query(Usuario).filter(Usuario.id == membresia.usuario_id).one()
        if not usuario.github_login_declarado or curso.github_installation_id is None:
            continue
        if curso.github_org_login is None:
            continue
        token = cliente.obtener_token_instalacion(curso.github_installation_id)
        estado = cliente.obtener_membresia_organizacion(
            curso.github_org_login, usuario.github_login_declarado, token
        )
        if estado == "active":
            membresia.org_github_estado = EstadoOrgGithubMembresia.ACTIVA.value
            membresia.org_github_activa_en = ahora_utc()
    sesion.flush()
