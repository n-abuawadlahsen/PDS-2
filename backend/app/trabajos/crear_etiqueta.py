"""Trabajo `crear_etiqueta` (SPEC 09 S9.6.2; SPEC 14 S14.7.4 fila 23; A-104,
A-213). Encolado por `resolver_sha`; cerrojo 2; clave
`tag:<entrega>:<sujeto>:<intento>`; 8 intentos en ~2 h.

Es comodidad de navegacion, no evidencia (Ley 4): si falla, la version ya
esta registrada y solo cambia `tag_estado`.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.adaptadores import trabajos_repo, versiones_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_github import crear_cliente_github_desde_config
from app.adaptadores.modelos_infraestructura import Trabajo
from app.adaptadores.modelos_version import VersionEntrega
from app.infraestructura.cerrojos import cerrojo_github
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar


@registrar("crear_etiqueta")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    assert trabajo.curso_id is not None
    version = sesion.get(VersionEntrega, uuid.UUID(trabajo.payload["version_id"]))
    if version is None:
        return
    cliente = crear_cliente_github_desde_config(obtener_configuracion())
    try:
        with cerrojo_github(sesion, trabajo.curso_id):
            versiones_repo.crear_etiqueta(sesion, cliente, version=version)
    except versiones_repo.GithubSinAcceso as exc:
        raise trabajos_repo.PosponerTrabajo(
            ahora_utc() + versiones_repo.REEVALUACION_SIN_ACCESO, f"GITHUB_SIN_ACCESO: {exc}"
        ) from exc
