"""Trabajos `reconciliar_actividad` y `precierre_actividad` (SPEC 14 S14.7.4
filas 24-25; SPEC 10 S10.2.1, S10.2.3; SPEC 06 S6.8.4; A-072). Cerrojo 2.

`reconciliar_actividad`: cada 15 minutos por curso, la red de seguridad
condicional por ETag, hasta 200 repositorios por ciclo.
`precierre_actividad`: por repositorio, en los 15 minutos previos a cada
fecha efectiva, pone al dia el espejo antes del corte; la captura sigue
disparandose a la hora exacta.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.adaptadores import actividad_repo
from app.adaptadores.cliente_github import crear_cliente_github_desde_config
from app.adaptadores.modelos_aprovisionamiento import Repositorio
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Trabajo
from app.infraestructura.cerrojos import cerrojo_github, cerrojo_repositorio
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar


@registrar("reconciliar_actividad")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    assert trabajo.curso_id is not None
    curso = sesion.query(Curso).filter(Curso.id == trabajo.curso_id).one()
    cliente = crear_cliente_github_desde_config(obtener_configuracion())
    with cerrojo_github(sesion, curso.id):
        actividad_repo.reconciliar_curso(sesion, cliente, curso=curso)


@registrar("precierre_actividad")
def ejecutar_precierre(sesion: Session, trabajo: Trabajo) -> None:
    repositorio = sesion.get(Repositorio, uuid.UUID(trabajo.payload["repositorio_id"]))
    if repositorio is None or repositorio.github_repo_id is None:
        return
    curso = sesion.get(Curso, repositorio.curso_id)
    if curso is None or curso.github_org_login is None or curso.github_installation_id is None:
        return
    cliente = crear_cliente_github_desde_config(obtener_configuracion())
    with cerrojo_github(sesion, curso.id):
        cerrojo_repositorio(sesion, str(repositorio.github_repo_id))
        actividad_repo.reconciliar_repositorio(
            sesion,
            cliente,
            repositorio=repositorio,
            org=curso.github_org_login,
            token=cliente.obtener_token_instalacion(curso.github_installation_id),
        )
