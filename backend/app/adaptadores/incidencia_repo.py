"""Escritura de `incidencia` (SPEC 14 S14.8.1; primer escritor real: Etapa P5).

`abrir_o_actualizar` es un upsert por `(tipo, curso_id, sujeto_id)` mientras
la incidencia siga abierta: varios tipos son "una sola abierta a la vez"
(p. ej. `ROSTER_TRUNCADO` por curso, S7.2.5), y reabrir cada ciclo crearia
ruido en vez de una unica fila viva con el detalle mas reciente.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_infraestructura import Incidencia


def abrir_o_actualizar(
    bd: Session,
    *,
    tipo: str,
    severidad: str,
    sujeto_tipo: str,
    curso_id: uuid.UUID | None,
    sujeto_id: uuid.UUID | None = None,
    detalle: dict[str, Any] | None = None,
) -> Incidencia:
    existente = (
        bd.query(Incidencia)
        .filter(
            Incidencia.tipo == tipo,
            Incidencia.curso_id == curso_id,
            Incidencia.sujeto_id == sujeto_id,
            Incidencia.abierta.is_(True),
        )
        .one_or_none()
    )
    if existente is not None:
        existente.detalle = detalle or {}
        bd.flush()
        return existente
    fila = Incidencia(
        tipo=tipo,
        severidad=severidad,
        sujeto_tipo=sujeto_tipo,
        sujeto_id=sujeto_id,
        curso_id=curso_id,
        detalle=detalle or {},
        creado_en=ahora_utc(),
    )
    bd.add(fila)
    bd.flush()
    return fila


def cerrar(
    bd: Session, *, tipo: str, curso_id: uuid.UUID | None, sujeto_id: uuid.UUID | None = None
) -> None:
    bd.query(Incidencia).filter(
        Incidencia.tipo == tipo,
        Incidencia.curso_id == curso_id,
        Incidencia.sujeto_id == sujeto_id,
        Incidencia.abierta.is_(True),
    ).update({"abierta": False, "resuelta_en": ahora_utc()})
    bd.flush()
