"""Filas de `trabajo_periodico` que el tick del planificador recorre (SPEC 14
S14.7.1, S14.7.4; SPEC 08 S8.7.1; Etapa P8).

Hasta Etapa P7 ninguna etapa sembraba `trabajo_periodico`, asi que ningun
barrido corria solo y todo dependia de «sincronizar ahora». R2.3.10 exige que
los repositorios se creen «sin interaccion directa de un usuario», de modo que
al activar la primera tarea de un curso se programan sus barridos. Idempotente:
volver a llamarlo no duplica filas (`UNIQUE (tipo, curso_id)`).
"""

from __future__ import annotations

import uuid
from datetime import timedelta

from sqlalchemy.orm import Session

from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import TrabajoPeriodico
from app.dominio.estados import EstadoTarea

# Ajuste tras la prueba del 15-sep: adelantar aceptaciones sin esperar 15 min.
CADENCIA_ACCESOS_SEGUNDOS = 60

# Cadencias en segundos; reconciliar_accesos prioriza pendientes en lotes acotados.
PERIODICOS_DE_CURSO: tuple[tuple[str, int], ...] = (
    ("sync_roster", 600),
    ("sync_grupos", 600),
    ("sync_tareas_y_fechas", 300),
    ("recolector_mapeos", 900),
    ("materializar_sujetos", 300),
    ("aprovisionar_repositorios", 120),
    ("reconciliar_accesos", CADENCIA_ACCESOS_SEGUNDOS),
    ("reconciliar_actividad", 900),  # F5: la red de seguridad por ETag
    ("agregar_metricas", 600),  # F6: recomputa agregados y alertas
    # F4-F5: relleno hacia atras, reconciliacion completa y verificacion.
    ("barrido_completo_actividad", 86_400),
    ("informe_diario", 1800),  # F9: 07:00 y barrido cada 30 min hasta las 23:00
    ("comunicaciones_programadas", 300),  # F10: recordatorios y cambios de fecha
    ("reconciliar_notas_canvas", 1800),  # F12: 30 min en ventana; 1/dia fuera
)

PERIODICOS_GLOBALES: tuple[tuple[str, int], ...] = (
    ("despachar_outbox", 30),
    ("sincronizar_acceso_docente", 3600),
    ("resolver_sha", 60),  # F4: el tick de captura (S9.6.1)
    ("purga_retencion", 86_400),  # F10: retenido mas de 7 dias caduca
)


def _asegurar(bd: Session, *, tipo: str, curso_id: uuid.UUID | None, cadencia: int) -> None:
    fila = (
        bd.query(TrabajoPeriodico)
        .filter(TrabajoPeriodico.tipo == tipo, TrabajoPeriodico.curso_id == curso_id)
        .one_or_none()
    )
    if fila is None:
        bd.add(
            TrabajoPeriodico(
                tipo=tipo,
                curso_id=curso_id,
                cadencia_segundos=cadencia,
                proxima_ejecucion=ahora_utc(),
                activo=True,
            )
        )
    else:
        fila.activo = True
        fila.cadencia_segundos = cadencia


def asegurar_periodicos_de_curso(bd: Session, curso_id: uuid.UUID) -> None:
    curso = bd.get(Curso, curso_id)
    if curso and curso.estado == "ARCHIVADO":
        return
    for tipo, cadencia in PERIODICOS_DE_CURSO:
        _asegurar(bd, tipo=tipo, curso_id=curso_id, cadencia=cadencia)
    bd.flush()


def asegurar_periodicos_de_cursos_activos(bd: Session) -> None:
    """Al arrancar el trabajador: un curso que ya tenia tareas activas antes
    de un despliegue recibe los periodicos que ese despliegue agrego."""
    from app.adaptadores.modelos_tarea import Tarea

    for (curso_id,) in (
        bd.query(Tarea.curso_id)
        .join(Curso, Curso.id == Tarea.curso_id)
        .filter(Tarea.estado == EstadoTarea.ACTIVA.value, Curso.estado != "ARCHIVADO")
        .distinct()
    ):
        asegurar_periodicos_de_curso(bd, curso_id)


def asegurar_periodicos_globales(bd: Session) -> None:
    for tipo, cadencia in PERIODICOS_GLOBALES:
        # `UNIQUE (tipo, curso_id)` no impide dos filas con `curso_id` nulo en
        # Postgres: la comprobacion previa de `_asegurar` es la que lo evita.
        _asegurar(bd, tipo=tipo, curso_id=None, cadencia=cadencia)
    bd.flush()


def actualizar_cadencia_accesos(bd: Session) -> None:
    """Aplica tambien a cursos ya activados, sin reactivar programaciones pausadas."""
    ahora = ahora_utc()
    for fila in bd.query(TrabajoPeriodico).filter(
        TrabajoPeriodico.tipo == "reconciliar_accesos", TrabajoPeriodico.activo.is_(True)
    ):
        fila.cadencia_segundos = CADENCIA_ACCESOS_SEGUNDOS
        fila.proxima_ejecucion = min(
            fila.proxima_ejecucion, ahora + timedelta(seconds=CADENCIA_ACCESOS_SEGUNDOS)
        )


def ajustar_cadencia(bd: Session, *, tipo: str, curso_id: uuid.UUID, cadencia: int) -> None:
    """Cambia la cadencia de un periodico ya sembrado (S9.4.4: 5 min / 1 min).
    Si se acorta, la proxima ejecucion se adelanta para no esperar el ciclo
    largo que ya estaba programado."""
    fila = (
        bd.query(TrabajoPeriodico)
        .filter(TrabajoPeriodico.tipo == tipo, TrabajoPeriodico.curso_id == curso_id)
        .one_or_none()
    )
    if fila is None or fila.cadencia_segundos == cadencia:
        return
    fila.cadencia_segundos = cadencia
    limite = ahora_utc() + timedelta(seconds=cadencia)
    if fila.proxima_ejecucion > limite:
        fila.proxima_ejecucion = limite
    bd.flush()
