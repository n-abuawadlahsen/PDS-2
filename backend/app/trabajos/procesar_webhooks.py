"""Trabajo `procesar_webhooks` (SPEC 14 S14.7.4 fila 15; SPEC 10 S10.2.2,
S10.2.5; A-070). Continuo; cerrojo por repositorio; clave `delivery_id`; 5 reintentos.

Un evento sin destino todavia se pospone con retroceso 1, 5, 15 y 60 minutos
durante 24 horas, sin consumir intentos; agotado el plazo queda
`DESCARTADO_SIN_DESTINO` conservando su cabecera y sin abrir incidencia.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.adaptadores import actividad_repo, trabajos_repo
from app.adaptadores.cliente_github import crear_cliente_github_desde_config
from app.adaptadores.modelos_actividad import EventoWebhook
from app.adaptadores.modelos_infraestructura import Trabajo
from app.infraestructura.cerrojos import cerrojo_repositorio
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar


@registrar("procesar_webhooks")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    evento = sesion.get(EventoWebhook, uuid.UUID(trabajo.payload["evento_webhook_id"]))
    if evento is None:
        return
    repositorio_gh = (evento.payload or {}).get("repository") or {}
    cerrojo_repositorio(sesion, str(repositorio_gh.get("id") or evento.delivery_id))
    cliente = crear_cliente_github_desde_config(obtener_configuracion())
    try:
        actividad_repo.procesar_evento(sesion, cliente, evento=evento)
    except actividad_repo.SinDestinoTodavia as exc:
        raise trabajos_repo.PosponerTrabajo(exc.cuando, "SIN_DESTINO_PENDIENTE") from exc
