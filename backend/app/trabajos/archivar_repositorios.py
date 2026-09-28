"""Trabajo `archivar_repositorios` (SPEC 14 S14.7.4 fila 31; A-168, A-197).
Accion del profesor, por tarea; cerrojo 2; clave `(accion, repositorio)`;
3 intentos.

La aplicacion nunca archiva ni desarchiva por su cuenta: este trabajo solo
nace de `POST .../archivar` o `POST .../desarchivar`, y reevalua las cinco
guardas antes de tocar cada repositorio.
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.adaptadores import archivado_repo, trabajos_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_github import crear_cliente_github_desde_config
from app.adaptadores.modelos_infraestructura import Trabajo
from app.infraestructura.cerrojos import cerrojo_github
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar

_REEVALUACION_SIN_ACCESO = timedelta(minutes=30)


@registrar(archivado_repo.TIPO_TRABAJO)
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    assert trabajo.curso_id is not None
    cliente = crear_cliente_github_desde_config(obtener_configuracion())
    try:
        with cerrojo_github(sesion, trabajo.curso_id):
            archivado_repo.ejecutar(sesion, cliente, payload=trabajo.payload, trabajo_id=trabajo.id)
    except archivado_repo.GithubSinAcceso as exc:
        raise trabajos_repo.PosponerTrabajo(
            ahora_utc() + _REEVALUACION_SIN_ACCESO, f"GITHUB_SIN_ACCESO: {exc}"
        ) from exc
