"""Acceso a la cola `trabajo` (SPEC 14 S14.7.1).

`tomar_siguiente` usa `SELECT ... FOR UPDATE SKIP LOCKED`: dos trabajadores
compitiendo por la misma fila nunca bloquean al otro, simplemente cada uno
toma una fila distinta (S14.7.7 CA-3).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_infraestructura import Trabajo
from app.dominio.estados import EstadoTrabajo


def encolar(
    sesion: Session,
    *,
    tipo: str,
    clave_idempotencia: str,
    max_intentos: int,
    curso_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> Trabajo | None:
    """Inserta un trabajo. Si la clave de idempotencia ya esta activa, no hace nada.

    S14.7.2 garantia 1: el indice unico parcial hace este `None` estructural,
    no una comprobacion previa en memoria que pueda tener una carrera.
    """
    trabajo = Trabajo(
        tipo=tipo,
        clave_idempotencia=clave_idempotencia,
        curso_id=curso_id,
        payload=payload or {},
        estado=EstadoTrabajo.PENDIENTE.value,
        max_intentos=max_intentos,
        creado_en=ahora_utc(),
    )
    sesion.add(trabajo)
    try:
        sesion.flush()
    except IntegrityError:
        sesion.rollback()
        return None
    return trabajo


def tomar_siguiente(
    sesion: Session, *, tomado_por: str, tipos: list[str] | None = None
) -> Trabajo | None:
    consulta = (
        select(Trabajo)
        .where(Trabajo.estado.in_([EstadoTrabajo.PENDIENTE.value, EstadoTrabajo.REINTENTAR.value]))
        .where((Trabajo.proximo_intento_en.is_(None)) | (Trabajo.proximo_intento_en <= ahora_utc()))
        .order_by(Trabajo.creado_en)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    if tipos:
        consulta = consulta.where(Trabajo.tipo.in_(tipos))
    trabajo = sesion.execute(consulta).scalar_one_or_none()
    if trabajo is None:
        return None
    trabajo.estado = EstadoTrabajo.EN_CURSO.value
    trabajo.tomado_por = tomado_por
    trabajo.tomado_en = ahora_utc()
    sesion.flush()
    return trabajo


def marcar_ok(sesion: Session, trabajo: Trabajo) -> None:
    trabajo.estado = EstadoTrabajo.OK.value
    trabajo.terminado_en = ahora_utc()
    sesion.flush()


def marcar_reintentar(
    sesion: Session, trabajo: Trabajo, *, proximo_intento_en: datetime, error: str
) -> None:
    trabajo.intentos += 1
    trabajo.ultimo_error = error
    trabajo.tomado_por = None
    trabajo.tomado_en = None
    if trabajo.intentos >= trabajo.max_intentos:
        trabajo.estado = EstadoTrabajo.REQUIERE_ATENCION.value
    else:
        trabajo.estado = EstadoTrabajo.REINTENTAR.value
        trabajo.proximo_intento_en = proximo_intento_en
    sesion.flush()


def liberar_huerfanos_por_apagado(sesion: Session, *, tomado_por: str) -> int:
    """Apagado ordenado (S14.7.6): vuelve a PENDIENTE sin contarlo como intento."""
    trabajos = (
        sesion.execute(
            select(Trabajo).where(
                Trabajo.estado == EstadoTrabajo.EN_CURSO.value, Trabajo.tomado_por == tomado_por
            )
        )
        .scalars()
        .all()
    )
    for trabajo in trabajos:
        trabajo.estado = EstadoTrabajo.PENDIENTE.value
        trabajo.tomado_por = None
        trabajo.tomado_en = None
        trabajo.proximo_intento_en = ahora_utc()
    sesion.flush()
    return len(trabajos)


def liberar_huerfanos_por_vigilancia(sesion: Session, *, umbral_minutos: int = 10) -> int:
    """Muerte sin señal (S14.7.6): el trabajo `vigilancia`, cada 5 min."""
    from datetime import timedelta

    limite = ahora_utc() - timedelta(minutes=umbral_minutos)
    trabajos = (
        sesion.execute(
            select(Trabajo).where(
                Trabajo.estado == EstadoTrabajo.EN_CURSO.value, Trabajo.tomado_en < limite
            )
        )
        .scalars()
        .all()
    )
    for trabajo in trabajos:
        trabajo.estado = EstadoTrabajo.PENDIENTE.value
        trabajo.tomado_por = None
        trabajo.tomado_en = None
        trabajo.proximo_intento_en = ahora_utc()
    sesion.flush()
    return len(trabajos)
