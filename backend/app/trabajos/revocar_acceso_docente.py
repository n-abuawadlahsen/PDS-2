"""Trabajo `revocar_acceso_docente` (SPEC 02 S2.9.3). Cerrojo 2, 4 reintentos.

La revocacion real son tres llamadas a GitHub, en orden (equipo, colaborador,
membresia de organizacion), cada una con lectura previa para que un reintento
sea un no-op -- ver app.adaptadores.github_repo.revocar_acceso_tres_planos.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.adaptadores.cliente_github import crear_cliente_github_desde_config
from app.adaptadores.github_repo import revocar_acceso_tres_planos
from app.adaptadores.modelos_infraestructura import Trabajo
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar


@registrar("revocar_acceso_docente")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    membresia_id = uuid.UUID(trabajo.payload["membresia_id"])
    cliente = crear_cliente_github_desde_config(obtener_configuracion())
    revocar_acceso_tres_planos(sesion, cliente, membresia_id=membresia_id)
