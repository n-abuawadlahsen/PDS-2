"""Tick del planificador (SPEC 14 S14.7.1, S14.7.7). Cadencia: 30 s.

Toma `pg_advisory_lock('global', 'tick_planificador')` antes de encolar nada:
un solo ejecutor por instante, aunque un despliegue progresivo solape dos
procesos durante unos segundos (S14.7.7). La clave de idempotencia unica en
`trabajo` es la segunda defensa, independiente de esta.
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_infraestructura import Trabajo, TrabajoPeriodico
from app.adaptadores.trabajos_repo import encolar
from app.infraestructura.cerrojos import cerrojo_global
from app.infraestructura.logs import obtener_logger
from app.trabajos.registro import tipos_implementados

_logger = obtener_logger(__name__)
_MAX_INTENTOS_POR_DEFECTO = 3


def tick(sesion: Session) -> int:
    """Encola lo vencido de `trabajo_periodico`. Devuelve cuantos encolo."""
    with cerrojo_global(sesion, "tick_planificador"):
        ahora = ahora_utc()
        vencidos = (
            sesion.execute(
                select(TrabajoPeriodico).where(
                    TrabajoPeriodico.activo.is_(True),
                    TrabajoPeriodico.proxima_ejecucion <= ahora,
                )
            )
            .scalars()
            .all()
        )

        encolados = 0
        for periodico in vencidos:
            # Nota de lectura S14.7.4 #3: un trabajo cuya bandera de alcance no
            # esta retirada no se encola. Aqui la version simplificada de
            # Etapa 0 es: solo se encola si hay un manejador implementado.
            if periodico.tipo not in tipos_implementados():
                continue
            # No acumular barridos si GitHub tarda o un docente ya solicito uno.
            if (
                periodico.tipo == "reconciliar_accesos"
                and sesion.query(Trabajo.id)
                .filter(
                    Trabajo.tipo == periodico.tipo,
                    Trabajo.curso_id == periodico.curso_id,
                    Trabajo.estado.in_(["PENDIENTE", "EN_CURSO", "REINTENTAR"]),
                )
                .first()
            ):
                continue
            clave = f"tick:{periodico.tipo}:{periodico.curso_id}:{ahora.isoformat()}"
            trabajo = encolar(
                sesion,
                tipo=periodico.tipo,
                clave_idempotencia=clave,
                max_intentos=4
                if periodico.tipo == "reconciliar_accesos"
                else _MAX_INTENTOS_POR_DEFECTO,
                curso_id=periodico.curso_id,
                payload={"periodico": True} if periodico.tipo == "reconciliar_accesos" else None,
            )
            if trabajo is not None:
                encolados += 1
            periodico.ultima_ejecucion = ahora
            periodico.proxima_ejecucion = ahora + timedelta(seconds=periodico.cadencia_segundos)
        sesion.flush()
        if encolados:
            _logger.info("planificador.tick", encolados=encolados)
        return encolados
