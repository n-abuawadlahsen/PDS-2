"""Trabajo `barrido_completo_actividad` (SPEC 14 S14.7.4 fila 26; SPEC 09
S9.8.5, S9.10.2). Diario; cerrojo 2.

«No existe `verificar_etiquetas_entrega`: la verificacion de etiquetas vive en
el barrido nocturno» (notas de lectura de S14.7.4). La Etapa F4 lo pone en
servicio solo con esa parte -- etiqueta borrada que se recrea, etiqueta movida
que nunca se sobrescribe, SHA que dejo de ser alcanzable --; la puesta al dia
completa del espejo de actividad llega con la ingesta. TODO(etapa-F5).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.adaptadores import versiones_repo
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
        versiones_repo.verificar_versiones(sesion, cliente, curso=curso)
