"""Suscripcion al informe docente diario (SPEC 11 S11.4; A-228; Etapa F9).

Modelo de baja voluntaria: quien entra al equipo docente queda suscrito en la
misma transaccion. Cada persona gobierna la suya; ninguna funcion de aqui
recibe un usuario distinto del que actua, salvo los efectos del ciclo de vida
de la membresia (retiro y reincorporacion).
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_informe import SuscripcionInforme
from app.dominio.informe import TOPE_SUSCRIPTORES


def activas_del_curso(bd: Session, curso_id: uuid.UUID) -> int:
    return (
        bd.query(SuscripcionInforme)
        .filter(SuscripcionInforme.curso_id == curso_id, SuscripcionInforme.activa.is_(True))
        .count()
    )


def _activar_con_tope(bd: Session, fila: SuscripcionInforme) -> None:
    ahora = ahora_utc()
    if activas_del_curso(bd, fila.curso_id) >= TOPE_SUSCRIPTORES:
        fila.activa = False
        fila.origen_baja = "TOPE_SUSCRIPTORES"
        fila.dada_de_baja_en = ahora
    else:
        fila.activa = True
        fila.origen_baja = None
        fila.dada_de_baja_en = None
    fila.actualizada_en = ahora


def al_entrar(bd: Session, *, curso_id: uuid.UUID, usuario_id: uuid.UUID) -> SuscripcionInforme:
    """Alta al crear el curso o aceptar la invitacion; al reincorporarse se
    restaura salvo que la ultima baja fuera de la propia persona (S11.4.6)."""
    fila = bd.get(SuscripcionInforme, (curso_id, usuario_id))
    if fila is None:
        fila = SuscripcionInforme(
            curso_id=curso_id, usuario_id=usuario_id, activa=False, actualizada_en=ahora_utc()
        )
        bd.add(fila)
        bd.flush()
        _activar_con_tope(bd, fila)
    elif not fila.activa and fila.origen_baja != "USUARIO":
        _activar_con_tope(bd, fila)
    bd.flush()
    return fila


def al_retirarse(bd: Session, *, curso_id: uuid.UUID, usuario_id: uuid.UUID) -> None:
    fila = bd.get(SuscripcionInforme, (curso_id, usuario_id))
    if fila is None or not fila.activa:
        return
    fila.activa = False
    fila.origen_baja = "RETIRO_MEMBRESIA"
    fila.dada_de_baja_en = fila.actualizada_en = ahora_utc()
    bd.flush()


def cambiar_propia(
    bd: Session, *, curso_id: uuid.UUID, usuario_id: uuid.UUID, activa: bool
) -> SuscripcionInforme:
    """La unica via con la que una persona cambia su suscripcion."""
    fila = bd.get(SuscripcionInforme, (curso_id, usuario_id))
    if fila is None:
        fila = SuscripcionInforme(
            curso_id=curso_id, usuario_id=usuario_id, activa=False, actualizada_en=ahora_utc()
        )
        bd.add(fila)
        bd.flush()
    if activa:
        if not fila.activa:
            _activar_con_tope(bd, fila)
    else:
        fila.activa = False
        fila.origen_baja = "USUARIO"
        fila.dada_de_baja_en = fila.actualizada_en = ahora_utc()
    bd.flush()
    return fila
