"""Escritura de `sincronizacion` y `cursor_sincronizacion` (SPEC 05 S5.4.2;
primer escritor real: Etapa P5)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_infraestructura import CursorSincronizacion, Sincronizacion


def registrar_ciclo(
    bd: Session, *, curso_id: uuid.UUID, recurso: str, resultado: str, contadores: dict[str, Any]
) -> Sincronizacion:
    fila = Sincronizacion(
        curso_id=curso_id,
        recurso=recurso,
        resultado=resultado,
        contadores=contadores,
        creado_en=ahora_utc(),
    )
    bd.add(fila)
    bd.flush()
    return fila


def actualizar_cursor(
    bd: Session,
    *,
    curso_id: uuid.UUID,
    recurso: str,
    referencia: str,
    per_page_medido: int | None = None,
    estado: str | None = None,
    ultimo_error: str | None = None,
) -> CursorSincronizacion:
    """`referencia` distingue cursores del mismo recurso dentro de un curso
    (p. ej. un `canvas_group_id` para el cursor de pertenencias de ESE grupo)."""
    fila = (
        bd.query(CursorSincronizacion)
        .filter(
            CursorSincronizacion.curso_id == curso_id,
            CursorSincronizacion.recurso == recurso,
            CursorSincronizacion.referencia == referencia,
        )
        .one_or_none()
    )
    ahora = ahora_utc()
    if fila is None:
        fila = CursorSincronizacion(curso_id=curso_id, recurso=recurso, referencia=referencia)
        bd.add(fila)
    if per_page_medido is not None:
        fila.per_page_medido = per_page_medido
    fila.estado = estado
    fila.ultimo_error = ultimo_error
    if ultimo_error is None:
        fila.ultimo_exito_en = ahora
    bd.flush()
    return fila
