"""Trabajo `barrido_completo_actividad` (SPEC 14 S14.7.4 fila 26; SPEC 09
S9.8.5, S9.10.2). Diario; cerrojo 2.

Tres partes, en este orden: el relleno hacia atras pendiente y la
reconciliacion completa sin ETag de cada repositorio en ingesta (S10.2.6,
F5), y la verificacion de versiones --etiqueta borrada que se recrea, movida
que nunca se sobrescribe, SHA inalcanzable-- que «vive en el barrido
nocturno» (notas de lectura de S14.7.4, F4).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.adaptadores import actividad_repo, versiones_repo
from app.adaptadores.cliente_github import crear_cliente_github_desde_config
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Trabajo
from app.infraestructura.cerrojos import cerrojo_github
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar


@registrar("barrido_completo_actividad")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    assert trabajo.curso_id is not None
    curso = sesion.query(Curso).filter(Curso.id == trabajo.curso_id).one()
    cliente = crear_cliente_github_desde_config(obtener_configuracion())
    with cerrojo_github(sesion, curso.id):
        actividad_repo.barrido_curso(sesion, cliente, curso=curso)
        versiones_repo.verificar_versiones(sesion, cliente, curso=curso)
