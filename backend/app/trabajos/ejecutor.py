"""Punto de entrada del trabajador: `python -m app.trabajos.ejecutor` (S14.5.1).

Orden de arranque (S14.8.3.1): aplica migraciones primero, con
`pg_advisory_lock` dedicado; el servicio web nunca migra. Despues entra al
bucle: cada 30 s intenta el tick del planificador, y en cada vuelta toma como
maximo un trabajo pendiente con `SELECT ... FOR UPDATE SKIP LOCKED`.

Apagado ordenado (S14.7.6, S14.5.3): al recibir SIGTERM, dispone de 25 s de
gracia; los trabajos que tenia tomados vuelven a PENDIENTE sin contar como
intento fallido.
"""

from __future__ import annotations

import os
import signal
import socket
import time
from datetime import datetime, timedelta

from sqlalchemy.orm import Session, sessionmaker

from app.adaptadores import programacion_repo, trabajos_repo
from app.dominio.estados import FamiliaError
from app.dominio.reintentos import proximo_intento_en
from app.infraestructura.config import obtener_configuracion
from app.infraestructura.db import crear_engine, crear_fabrica_sesiones
from app.infraestructura.logs import configurar_logs, obtener_logger
from app.infraestructura.migraciones import aplicar_migraciones
from app.trabajos import (  # noqa: F401 (registra manejadores)
    aprovisionar_repositorios,
    despachar_outbox,
    ejecutar_checklist_vinculacion,
    materializar_sujetos,
    planificador,
    recolector_mapeos,
    reconciliar_accesos,
    registro,
    revalidar_mapeos,
    revocar_acceso_docente,
    sincronizar_acceso_docente,
    sync_grupos,
    sync_roster,
    sync_tareas_y_fechas,
    verificar_instalacion_github,
    vigilancia,
)

_logger = obtener_logger(__name__)
_INTERVALO_TICK_SEGUNDOS = 30
_INTERVALO_INACTIVO_SEGUNDOS = 1


class ErrorClasificado(Exception):
    def __init__(self, familia: FamiliaError, mensaje: str) -> None:
        self.familia = familia
        super().__init__(mensaje)


def _id_trabajador() -> str:
    return f"{socket.gethostname()}:{os.getpid()}"


def _procesar_un_trabajo(sesion: Session, *, tomado_por: str) -> bool:
    trabajo = trabajos_repo.tomar_siguiente(sesion, tomado_por=tomado_por)
    if trabajo is None:
        return False
    sesion.commit()

    manejador = registro.obtener_manejador(trabajo.tipo)
    if manejador is None:
        trabajos_repo.marcar_reintentar(
            sesion,
            trabajo,
            proximo_intento_en=datetime.now(),
            error=f"sin manejador para {trabajo.tipo}",
        )
        sesion.commit()
        return True

    try:
        manejador(sesion, trabajo)
        trabajos_repo.marcar_ok(sesion, trabajo)
    except Exception as exc:  # noqa: BLE001 - clasificado explicitamente abajo
        familia = exc.familia if isinstance(exc, ErrorClasificado) else FamiliaError.TRANSITORIO
        intento = trabajo.intentos + 1
        cuando = proximo_intento_en(ahora=datetime.now(), intento=intento)
        if familia == FamiliaError.PERMANENTE:
            trabajo.max_intentos = 0  # cero reintentos: pasa a REQUIERE_ATENCION de inmediato
        trabajos_repo.marcar_reintentar(sesion, trabajo, proximo_intento_en=cuando, error=str(exc))
        _logger.warning("trabajo.fallo", tipo=trabajo.tipo, familia=familia.value, error=str(exc))
    sesion.commit()
    return True


def ejecutar_ciclo(
    fabrica: sessionmaker[Session], *, tomado_por: str, ultimo_tick: datetime
) -> datetime:
    ahora = datetime.now()
    if (ahora - ultimo_tick) >= timedelta(seconds=_INTERVALO_TICK_SEGUNDOS):
        with fabrica() as sesion:
            planificador.tick(sesion)
            sesion.commit()
        ultimo_tick = ahora

    with fabrica() as sesion:
        proceso = _procesar_un_trabajo(sesion, tomado_por=tomado_por)
    if not proceso:
        time.sleep(_INTERVALO_INACTIVO_SEGUNDOS)
    return ultimo_tick


def main() -> None:
    settings = obtener_configuracion()
    configurar_logs(entorno=settings.entorno, version=settings.app_version)

    engine_migraciones = crear_engine(settings)
    try:
        aplicar_migraciones(engine_migraciones, database_url=settings.database_url)
    finally:
        # El pooler de Supabase en modo sesion limita los clientes: el motor de
        # migraciones no debe retener conexiones ociosas el resto del proceso.
        engine_migraciones.dispose()

    fabrica = crear_fabrica_sesiones(settings)
    with fabrica() as sesion:
        # El despacho del outbox es global: existe aunque ningun curso haya
        # activado todavia una tarea (S14.7.4).
        programacion_repo.asegurar_periodicos_globales(sesion)
        sesion.commit()
    tomado_por = _id_trabajador()
    _logger.info("ejecutor.arrancando", tomado_por=tomado_por)

    detener = {"valor": False}

    def _manejar_sigterm(signum: int, frame: object) -> None:  # noqa: ARG001
        detener["valor"] = True

    signal.signal(signal.SIGTERM, _manejar_sigterm)

    ultimo_tick = datetime.min
    while not detener["valor"]:
        ultimo_tick = ejecutar_ciclo(fabrica, tomado_por=tomado_por, ultimo_tick=ultimo_tick)

    with fabrica() as sesion:
        liberados = trabajos_repo.liberar_huerfanos_por_apagado(sesion, tomado_por=tomado_por)
        sesion.commit()
    _logger.info("ejecutor.apagado_ordenado", liberados=liberados)


if __name__ == "__main__":
    main()
