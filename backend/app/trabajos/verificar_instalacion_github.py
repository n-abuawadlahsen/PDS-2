"""Trabajo `verificar_instalacion_github`, cada hora (SPEC 04 S4.6.4, S4.6.5).

Global (no de un curso): recorre TODAS las instalaciones de la App via
`GET /app/installations`, la unica forma de detectar sin webhook que una
instalacion pendiente de aprobacion del owner ya se aprobo.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.adaptadores import github_repo
from app.adaptadores.cliente_github import crear_cliente_github_desde_config
from app.adaptadores.modelos_infraestructura import Trabajo
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar


@registrar("verificar_instalacion_github")
def ejecutar(sesion: Session, _trabajo: Trabajo) -> None:
    cliente = crear_cliente_github_desde_config(obtener_configuracion())
    github_repo.reconciliar_instalaciones(sesion, cliente)
