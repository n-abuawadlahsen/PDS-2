"""Trabajo `resolver_sha` (SPEC 09 S9.6.1-S9.6.2; SPEC 14 S14.7.4 fila 22;
A-101, A-213). Cada minuto, global; cerrojo 2; 8 intentos en ~2 h.

Dos formas, como `aprovisionar_repositorios`: sin payload es el tick global,
que encola una captura por cada `(entrega, sujeto)` vencido con la clave
`version:<entrega>:<sujeto>:<corte_epoch>`; con payload es esa captura, que
inserta la fila solo cuando el SHA queda resuelto.

GitHub sin acceso al capturar (S9.10.4): el trabajo se pospone 30 minutos sin
consumir ninguno de los 8 intentos, y la fila que se escriba al final lleva
`CAPTURA_DIFERIDA_POR_GITHUB`.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.adaptadores import trabajos_repo, versiones_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_github import crear_cliente_github_desde_config
from app.adaptadores.modelos_infraestructura import Trabajo
from app.dominio.estados import OrigenCaptura
from app.infraestructura.cerrojos import cerrojo_github
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar


@registrar("resolver_sha")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    payload = trabajo.payload or {}
    if not payload.get("entrega_id"):
        versiones_repo.barrido(sesion)
        return
    assert trabajo.curso_id is not None
    cliente = crear_cliente_github_desde_config(obtener_configuracion())
    actor = payload.get("actor_usuario_id")
    try:
        with cerrojo_github(sesion, trabajo.curso_id):
            versiones_repo.capturar(
                sesion,
                cliente,
                entrega_id=uuid.UUID(payload["entrega_id"]),
                sujeto_id=uuid.UUID(payload["sujeto_id"]),
                corte=datetime.fromisoformat(payload["corte"]),
                origen=OrigenCaptura(payload.get("origen", OrigenCaptura.AUTOMATICA.value)),
                actor_usuario_id=uuid.UUID(actor) if actor else None,
                motivo_manual=payload.get("motivo_manual"),
                sha_fijado=payload.get("sha_fijado"),
                diferida=bool(payload.get("pospuesto")) or trabajo.intentos > 0,
            )
    except versiones_repo.GithubSinAcceso as exc:
        trabajo.payload = {**payload, "pospuesto": True}
        raise trabajos_repo.PosponerTrabajo(
            ahora_utc() + versiones_repo.REEVALUACION_SIN_ACCESO, f"GITHUB_SIN_ACCESO: {exc}"
        ) from exc
