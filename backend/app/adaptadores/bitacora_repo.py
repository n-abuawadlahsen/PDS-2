"""Escritura de `bitacora` (SPEC 14 S14.8.1). Auditoria append-only."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_infraestructura import Bitacora


def registrar(
    bd: Session,
    *,
    accion: str,
    entidad: str,
    entidad_id: str | None = None,
    actor_usuario_id: uuid.UUID | None = None,
    curso_id: uuid.UUID | None = None,
    antes: dict[str, Any] | None = None,
    despues: dict[str, Any] | None = None,
) -> None:
    bd.add(
        Bitacora(
            curso_id=curso_id,
            accion=accion,
            entidad=entidad,
            entidad_id=entidad_id,
            actor_usuario_id=actor_usuario_id,
            antes=antes,
            despues=despues,
            creado_en=ahora_utc(),
        )
    )
    bd.flush()
