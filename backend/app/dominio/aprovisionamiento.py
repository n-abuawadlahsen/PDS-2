"""Reglas puras del aprovisionamiento de repositorios (SPEC 08 S8.5-S8.8; A-092,
A-093, A-094, A-116, A-164, A-211, A-212; Etapa P8).

Recibe estados ya leidos y decide. Las llamadas a GitHub y las escrituras viven
en `app/adaptadores/aprovisionamiento_repo.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.dominio.estados import (
    EstadoAccesoDocente,
    EstadoAccesoRepositorio,
    EstadoEstudiante,
    EstadoMapeoGithub,
    EstadoRepositorio,
    EstadoTarea,
    FamiliaError,
    MotivoDegradado,
    MotivoDesactivacionSujeto,
    MotivoEsperandoInformacion,
    SubtipoErrorPermanente,
)

# S8.6.3 (A-096): ocho sondeos de contenido con retroceso, 94 s acumulados.
SONDEOS_CONTENIDO_SEGUNDOS: tuple[int, ...] = (2, 2, 5, 5, 10, 10, 30, 30)

# S8.7.1: "hasta 8 intentos en aproximadamente 2 horas". La tabla generica de
# `reintentos.py` (base 2 s) agotaria los 8 en menos de 10 minutos; esta es la
# que corresponde al significado de negocio de este trabajo (suma ~2 h).
ESPERAS_REINTENTO_SEGUNDOS: tuple[int, ...] = (60, 120, 240, 480, 900, 1800, 1800, 1800)
MAX_INTENTOS_TRANSITORIOS = len(ESPERAS_REINTENTO_SEGUNDOS)

# S8.6.1: `BLOQUEADO` se reevalua cada 30 minutos, nunca en bucle.
REEVALUACION_BLOQUEADO = timedelta(minutes=30)
# Espera por limite de GitHub sin `retry-after` explicito.
ESPERA_LIMITE_POR_DEFECTO = timedelta(seconds=60)

# S8.7.2: ritmo nominal de un repositorio cada 6 segundos.
RITMO_NOMINAL_SEGUNDOS = 6

ESTADOS_ACCESO_CUBIERTO = frozenset(
    {EstadoAccesoRepositorio.ACEPTADO.value, EstadoAccesoRepositorio.ACCESO_DIRECTO.value}
)

# Estados de la maquina 2 en los que el repositorio ya existe en GitHub.
ESTADOS_CON_REPOSITORIO = frozenset(
    {
        EstadoRepositorio.CREADO_SIN_CONTENIDO.value,
        EstadoRepositorio.CONTENIDO_LISTO.value,
        EstadoRepositorio.CONFIGURANDO_ACCESOS.value,
        EstadoRepositorio.OPERATIVO.value,
        EstadoRepositorio.DEGRADADO.value,
        EstadoRepositorio.FUERA_DE_ALCANCE.value,
        EstadoRepositorio.ARCHIVADO.value,
    }
)

# S8.9.2: mientras haya alguno en estos estados, la tarea muestra progreso.
ESTADOS_EN_CURSO = frozenset(
    {
        EstadoRepositorio.ESPERANDO_INFORMACION.value,
        EstadoRepositorio.LISTO_PARA_CREAR.value,
        EstadoRepositorio.CREANDO.value,
        EstadoRepositorio.CREADO_SIN_CONTENIDO.value,
        EstadoRepositorio.CONTENIDO_LISTO.value,
        EstadoRepositorio.CONFIGURANDO_ACCESOS.value,
    }
)

_ESTADOS_ESTUDIANTE_SUJETO = frozenset(
    {EstadoEstudiante.ACTIVO.value, EstadoEstudiante.INVITADO.value}
)


# --- A-164 paso 2 y 3: quien es sujeto, y por que deja de serlo ---


def motivo_no_es_sujeto_individual(
    *, estado_estudiante: str, visible_en_alguna_entrega: bool
) -> MotivoDesactivacionSujeto | None:
    """`None` = el estudiante es sujeto de la tarea individual (A-164 paso 2)."""
    if estado_estudiante not in _ESTADOS_ESTUDIANTE_SUJETO:
        return MotivoDesactivacionSujeto.SIN_MATRICULA_ACTIVA
    if not visible_en_alguna_entrega:
        return MotivoDesactivacionSujeto.SIN_VISIBILIDAD
    return None


def es_integrante_elegible(*, estado_estudiante: str, visible_en_alguna_entrega: bool) -> bool:
    """A-164 paso 2, tarea grupal: el integrante `accepted` cuenta si ademas
    cumple las dos condiciones del sujeto individual."""
    return (
        motivo_no_es_sujeto_individual(
            estado_estudiante=estado_estudiante,
            visible_en_alguna_entrega=visible_en_alguna_entrega,
        )
        is None
    )


def motivo_no_es_sujeto_grupal(
    *, grupo_activo: bool, integrantes_elegibles: int
) -> MotivoDesactivacionSujeto | None:
    """`None` = el grupo es sujeto de la tarea grupal: tiene al menos un
    integrante `accepted` elegible (A-164 paso 2, A-048)."""
    if not grupo_activo:
        return MotivoDesactivacionSujeto.GRUPO_DISUELTO
    if integrantes_elegibles == 0:
        return MotivoDesactivacionSujeto.GRUPO_SIN_ACEPTADOS
    return None


# --- A-093 / A-094: la guarda y su motivo cerrado ---


def motivo_espera_individual(
    *, estado_mapeo: str | None, estado_tarea: str, solo_lectura: bool = False
) -> MotivoEsperandoInformacion | None:
    """`None` = se cumple la guarda (mapeo `VIGENTE`) y el sujeto pasa a
    `LISTO_PARA_CREAR`. Un sujeto que espera siempre dice por que (CA-8.5-05)."""
    if estado_tarea == EstadoTarea.INCONSISTENTE.value:
        return MotivoEsperandoInformacion.TAREA_INCONSISTENTE
    if solo_lectura:
        return MotivoEsperandoInformacion.CURSO_EN_SOLO_LECTURA
    if estado_mapeo == EstadoMapeoGithub.VIGENTE.value:
        return None
    if estado_mapeo == EstadoMapeoGithub.EN_CONFLICTO.value:
        return MotivoEsperandoInformacion.MAPEO_EN_CONFLICTO
    return MotivoEsperandoInformacion.SIN_MAPEO_GITHUB


def motivo_espera_grupal(
    *,
    estados_mapeo_integrantes: list[str | None],
    hay_integrante_en_dos_grupos: bool,
    estado_tarea: str,
    solo_lectura: bool = False,
) -> MotivoEsperandoInformacion | None:
    """A-093, tarea grupal: basta **un** integrante `accepted` con mapeo
    `VIGENTE` (R2.3.10, CA-8.5-01); los demas se incorporan despues. Un
    integrante en dos grupos del mismo conjunto es dato sucio de Canvas: el
    grupo espera hasta que se resuelva alli (A-049), sin frenar a los demas."""
    if estado_tarea == EstadoTarea.INCONSISTENTE.value:
        return MotivoEsperandoInformacion.TAREA_INCONSISTENTE
    if solo_lectura:
        return MotivoEsperandoInformacion.CURSO_EN_SOLO_LECTURA
    if not estados_mapeo_integrantes:
        return MotivoEsperandoInformacion.GRUPO_SIN_INTEGRANTES_ACEPTADOS
    if hay_integrante_en_dos_grupos:
        return MotivoEsperandoInformacion.ESTUDIANTE_EN_DOS_GRUPOS
    if EstadoMapeoGithub.VIGENTE.value in estados_mapeo_integrantes:
        return None
    if EstadoMapeoGithub.EN_CONFLICTO.value in estados_mapeo_integrantes:
        return MotivoEsperandoInformacion.MAPEO_EN_CONFLICTO
    return MotivoEsperandoInformacion.SIN_MAPEO_GITHUB


# --- S8.6.2: el predicado de OPERATIVO, escrito una sola vez ---


@dataclass(frozen=True)
class ResultadoPredicado:
    estado: EstadoRepositorio
    motivo: MotivoDegradado | None


def evaluar_predicado_operativo(
    *,
    estados_acceso_estudiantes: list[str],
    hay_errores_al_invitar: bool,
    integrantes_pendientes_en_canvas: bool,
    estado_acceso_docente: str | None,
) -> ResultadoPredicado:
    """A-092: `OPERATIVO` si y solo si (1) el contenido esta resuelto -- el
    llamador solo invoca esto desde `CONTENIDO_LISTO` en adelante --, (2) cada
    integrante tiene acceso `ACEPTADO`/`ACCESO_DIRECTO` y nadie esta pendiente
    en Canvas, y (3) el equipo docente tiene lectura `CONCEDIDA`.

    Cualquier otra situacion es `DEGRADADO` con uno de los seis motivos. El
    orden de los motivos es el de lo que el docente puede resolver primero."""
    cubiertos = bool(estados_acceso_estudiantes) and all(
        e in ESTADOS_ACCESO_CUBIERTO for e in estados_acceso_estudiantes
    )
    if not cubiertos:
        if hay_errores_al_invitar:
            return ResultadoPredicado(
                EstadoRepositorio.DEGRADADO, MotivoDegradado.ERROR_AL_CONCEDER_ACCESO
            )
        if not estados_acceso_estudiantes or any(
            e == EstadoAccesoRepositorio.SIN_MAPEO.value for e in estados_acceso_estudiantes
        ):
            return ResultadoPredicado(
                EstadoRepositorio.DEGRADADO, MotivoDegradado.INTEGRANTE_SIN_MAPEO
            )
        if any(e == EstadoAccesoRepositorio.EXPIRADA.value for e in estados_acceso_estudiantes):
            return ResultadoPredicado(
                EstadoRepositorio.DEGRADADO, MotivoDegradado.INVITACION_EXPIRADA
            )
        return ResultadoPredicado(
            EstadoRepositorio.DEGRADADO, MotivoDegradado.FALTA_ACEPTAR_INVITACION_GITHUB
        )
    if integrantes_pendientes_en_canvas:
        return ResultadoPredicado(
            EstadoRepositorio.DEGRADADO, MotivoDegradado.INTEGRANTE_PENDIENTE_EN_CANVAS
        )
    if estado_acceso_docente == EstadoAccesoDocente.ERROR.value:
        return ResultadoPredicado(
            EstadoRepositorio.DEGRADADO, MotivoDegradado.ERROR_AL_CONCEDER_ACCESO
        )
    if estado_acceso_docente != EstadoAccesoDocente.CONCEDIDO.value:
        return ResultadoPredicado(EstadoRepositorio.DEGRADADO, MotivoDegradado.SIN_ACCESO_DOCENTE)
    return ResultadoPredicado(EstadoRepositorio.OPERATIVO, None)


# --- S8.6.4 (A-116): tres familias de error ---


@dataclass(frozen=True)
class ClasificacionError:
    familia: FamiliaError
    estado: EstadoRepositorio
    subtipo: SubtipoErrorPermanente | None


def clasificar_rechazo_github(
    status_code: int, mensaje: str, *, en_ventana_de_creacion: bool
) -> ClasificacionError:
    """Un limite de GitHub nunca se pinta como error del equipo (Ley 5): va a
    `ESPERANDO_LIMITE`, no a `ERROR_*`."""
    texto = mensaje.lower()
    if status_code == 429 or (
        status_code == 403 and ("rate limit" in texto or "secondary" in texto)
    ):
        return ClasificacionError(
            FamiliaError.TRANSITORIO, EstadoRepositorio.ESPERANDO_LIMITE, None
        )
    if status_code >= 500 or (status_code == 404 and en_ventana_de_creacion):
        return ClasificacionError(
            FamiliaError.TRANSITORIO, EstadoRepositorio.ERROR_TRANSITORIO, None
        )
    if status_code == 403 and "two-factor" in texto:
        return ClasificacionError(
            FamiliaError.PERMANENTE,
            EstadoRepositorio.ERROR_PERMANENTE,
            SubtipoErrorPermanente.ORG_EXIGE_2FA,
        )
    if status_code == 403:
        # Politica de la organizacion o permisos de la App por aprobar: se
        # reevalua cada 30 min en vez de reintentarse en bucle (S8.6.4).
        return ClasificacionError(FamiliaError.BLOQUEANTE, EstadoRepositorio.BLOQUEADO, None)
    if status_code in (401, 404):
        return ClasificacionError(
            FamiliaError.PERMANENTE,
            EstadoRepositorio.ERROR_PERMANENTE,
            SubtipoErrorPermanente.PERMISO_INSUFICIENTE,
        )
    return ClasificacionError(FamiliaError.PERMANENTE, EstadoRepositorio.ERROR_PERMANENTE, None)


def espera_reintento(intento: int) -> timedelta:
    """`intento` desde 1. Fuera de la tabla, se mantiene el ultimo escalon."""
    indice = min(max(intento, 1), MAX_INTENTOS_TRANSITORIOS) - 1
    return timedelta(seconds=ESPERAS_REINTENTO_SEGUNDOS[indice])


# --- S8.11.3: salida de ERROR_PERMANENTE segun subtipo ---

_SUBTIPOS_QUE_EXIGEN_CORREGIR_CUENTA = frozenset(
    {
        SubtipoErrorPermanente.CUENTA_ELIMINADA.value,
        SubtipoErrorPermanente.LOGIN_ES_ORGANIZACION.value,
    }
)


def destino_al_reintentar(subtipo: str | None) -> EstadoRepositorio:
    """«Reintentar» nunca devuelve a `LISTO_PARA_CREAR` un repositorio cuyo
    bloqueo real esta en el mapeo del estudiante (CA-8.11-03)."""
    if subtipo in _SUBTIPOS_QUE_EXIGEN_CORREGIR_CUENTA:
        return EstadoRepositorio.ESPERANDO_INFORMACION
    return EstadoRepositorio.LISTO_PARA_CREAR


# --- S8.8.2: acceso del estudiante ---


def estado_acceso_tras_invitar(status_code: int) -> EstadoAccesoRepositorio:
    """`PUT collaborators`: `201` crea invitacion; `204` es acceso inmediato
    (ya tenia acceso previo, p. ej. es miembro de la organizacion)."""
    if status_code == 204:
        return EstadoAccesoRepositorio.ACCESO_DIRECTO
    return EstadoAccesoRepositorio.INVITADO


_ESTADOS_CON_ACCESO_CONCEDIDO = frozenset(
    {
        EstadoAccesoRepositorio.INVITADO.value,
        EstadoAccesoRepositorio.ACEPTADO.value,
        EstadoAccesoRepositorio.ACCESO_DIRECTO.value,
    }
)


def estado_acceso_tras_salir_del_grupo(estado: str) -> EstadoAccesoRepositorio | None:
    """S8.8.3 (A-212): la salida de un integrante -- ya confirmada en dos
    ciclos por `sync_grupos` -- solo **propone** la revocacion; ninguna persona
    ha decidido todavia y GitHub no se toca. `None` = la fila no cambia."""
    if estado in _ESTADOS_CON_ACCESO_CONCEDIDO:
        return EstadoAccesoRepositorio.REVOCACION_PROPUESTA
    return None


# --- S8.9.2 / S8.7.2: progreso y estimacion ---


def minutos_restantes(*, pendientes: int, ritmo_segundos: int = RITMO_NOMINAL_SEGUNDOS) -> int:
    """Estimacion de «quedan ~N min»: pendientes por el ritmo efectivo, redondeada
    hacia arriba. El ritmo lo fija el freno de presupuesto del momento."""
    if pendientes <= 0:
        return 0
    return max(1, -(-pendientes * ritmo_segundos // 60))


def listo_para_reintentar(proximo_intento_en: datetime | None, ahora: datetime) -> bool:
    return proximo_intento_en is None or proximo_intento_en <= ahora
