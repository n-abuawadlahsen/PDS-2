"""SPEC 08 S8.5-S8.8 (Etapa P8): reglas puras del aprovisionamiento."""

from __future__ import annotations

from datetime import timedelta

from app.dominio.aprovisionamiento import (
    ESPERAS_REINTENTO_SEGUNDOS,
    MAX_INTENTOS_TRANSITORIOS,
    SONDEOS_CONTENIDO_SEGUNDOS,
    clasificar_rechazo_github,
    destino_al_reintentar,
    espera_reintento,
    estado_acceso_tras_invitar,
    evaluar_predicado_operativo,
    minutos_restantes,
    motivo_espera_individual,
    motivo_no_es_sujeto_individual,
)
from app.dominio.estados import (
    EstadoAccesoRepositorio,
    EstadoRepositorio,
    FamiliaError,
    MotivoDegradado,
    MotivoDesactivacionSujeto,
    MotivoEsperandoInformacion,
    SubtipoErrorPermanente,
)


def test_sujeto_individual_exige_matricula_y_visibilidad():
    assert (
        motivo_no_es_sujeto_individual(estado_estudiante="ACTIVO", visible_en_alguna_entrega=True)
        is None
    )
    assert (
        motivo_no_es_sujeto_individual(estado_estudiante="INVITADO", visible_en_alguna_entrega=True)
        is None
    )
    assert (
        motivo_no_es_sujeto_individual(estado_estudiante="RETIRADO", visible_en_alguna_entrega=True)
        == MotivoDesactivacionSujeto.SIN_MATRICULA_ACTIVA
    )
    assert (
        motivo_no_es_sujeto_individual(estado_estudiante="ACTIVO", visible_en_alguna_entrega=False)
        == MotivoDesactivacionSujeto.SIN_VISIBILIDAD
    )


def test_ca_8_5_05_la_espera_siempre_tiene_motivo():
    assert motivo_espera_individual(estado_mapeo="VIGENTE", estado_tarea="ACTIVA") is None
    assert (
        motivo_espera_individual(estado_mapeo="SIN_DATO", estado_tarea="ACTIVA")
        == MotivoEsperandoInformacion.SIN_MAPEO_GITHUB
    )
    assert (
        motivo_espera_individual(estado_mapeo=None, estado_tarea="ACTIVA")
        == MotivoEsperandoInformacion.SIN_MAPEO_GITHUB
    )
    assert (
        motivo_espera_individual(estado_mapeo="EN_CONFLICTO", estado_tarea="ACTIVA")
        == MotivoEsperandoInformacion.MAPEO_EN_CONFLICTO
    )
    assert (
        motivo_espera_individual(estado_mapeo="VIGENTE", estado_tarea="INCONSISTENTE")
        == MotivoEsperandoInformacion.TAREA_INCONSISTENTE
    )


def _predicado(**cambios: object):
    argumentos: dict[str, object] = {
        "estados_acceso_estudiantes": [EstadoAccesoRepositorio.ACEPTADO.value],
        "hay_errores_al_invitar": False,
        "integrantes_pendientes_en_canvas": False,
        "estado_acceso_docente": "CONCEDIDO",
    }
    argumentos.update(cambios)
    return evaluar_predicado_operativo(**argumentos)  # type: ignore[arg-type]


def test_ca_8_6_01_todo_aceptado_y_docente_concedido_es_operativo():
    resultado = _predicado()
    assert resultado.estado == EstadoRepositorio.OPERATIVO
    assert resultado.motivo is None


def test_acceso_directo_cuenta_como_cubierto():
    assert (
        _predicado(estados_acceso_estudiantes=["ACCESO_DIRECTO"]).estado
        == EstadoRepositorio.OPERATIVO
    )


def test_invitacion_pendiente_es_degradado_nunca_error():
    resultado = _predicado(estados_acceso_estudiantes=["INVITADO"])
    assert resultado.estado == EstadoRepositorio.DEGRADADO
    assert resultado.motivo == MotivoDegradado.FALTA_ACEPTAR_INVITACION_GITHUB


def test_motivos_de_degradado():
    assert (
        _predicado(estados_acceso_estudiantes=["EXPIRADA"]).motivo
        == MotivoDegradado.INVITACION_EXPIRADA
    )
    assert _predicado(estados_acceso_estudiantes=[]).motivo == MotivoDegradado.INTEGRANTE_SIN_MAPEO
    assert (
        _predicado(estados_acceso_estudiantes=["POR_INVITAR"], hay_errores_al_invitar=True).motivo
        == MotivoDegradado.ERROR_AL_CONCEDER_ACCESO
    )
    assert (
        _predicado(integrantes_pendientes_en_canvas=True).motivo
        == MotivoDegradado.INTEGRANTE_PENDIENTE_EN_CANVAS
    )
    assert (
        _predicado(estado_acceso_docente="PENDIENTE").motivo == MotivoDegradado.SIN_ACCESO_DOCENTE
    )
    assert _predicado(estado_acceso_docente=None).motivo == MotivoDegradado.SIN_ACCESO_DOCENTE
    assert (
        _predicado(estado_acceso_docente="ERROR").motivo == MotivoDegradado.ERROR_AL_CONCEDER_ACCESO
    )


def test_ca_8_6_05_y_08_limite_de_tasa_espera_y_no_es_error():
    for status, mensaje in ((429, "Too many"), (403, "API rate limit exceeded")):
        clasificacion = clasificar_rechazo_github(status, mensaje, en_ventana_de_creacion=False)
        assert clasificacion.familia == FamiliaError.TRANSITORIO
        assert clasificacion.estado == EstadoRepositorio.ESPERANDO_LIMITE


def test_clasificacion_de_errores():
    assert (
        clasificar_rechazo_github(502, "", en_ventana_de_creacion=False).estado
        == EstadoRepositorio.ERROR_TRANSITORIO
    )
    assert (
        clasificar_rechazo_github(404, "", en_ventana_de_creacion=True).estado
        == EstadoRepositorio.ERROR_TRANSITORIO
    )
    bloqueado = clasificar_rechazo_github(
        403, "Resource not accessible by integration", en_ventana_de_creacion=False
    )
    assert bloqueado.familia == FamiliaError.BLOQUEANTE
    assert bloqueado.estado == EstadoRepositorio.BLOQUEADO
    dos_pasos = clasificar_rechazo_github(
        403, "requires two-factor authentication", en_ventana_de_creacion=False
    )
    assert dos_pasos.subtipo == SubtipoErrorPermanente.ORG_EXIGE_2FA
    validacion = clasificar_rechazo_github(422, "Validation Failed", en_ventana_de_creacion=False)
    assert validacion.estado == EstadoRepositorio.ERROR_PERMANENTE


def test_ocho_reintentos_en_unas_dos_horas():
    assert MAX_INTENTOS_TRANSITORIOS == 8
    total = sum(ESPERAS_REINTENTO_SEGUNDOS)
    assert (
        timedelta(hours=1, minutes=45) <= timedelta(seconds=total) <= timedelta(hours=2, minutes=15)
    )
    assert espera_reintento(1) == timedelta(seconds=60)
    assert espera_reintento(99) == timedelta(seconds=1800)


def test_sondeo_de_contenido_acotado_a_94_segundos():
    assert len(SONDEOS_CONTENIDO_SEGUNDOS) == 8
    assert sum(SONDEOS_CONTENIDO_SEGUNDOS) == 94


def test_ca_8_11_03_cuenta_eliminada_no_vuelve_a_listo_para_crear():
    assert destino_al_reintentar("CUENTA_ELIMINADA") == EstadoRepositorio.ESPERANDO_INFORMACION
    assert destino_al_reintentar("LOGIN_ES_ORGANIZACION") == EstadoRepositorio.ESPERANDO_INFORMACION
    assert destino_al_reintentar("NOMBRE_OCUPADO_POR_TERCERO") == EstadoRepositorio.LISTO_PARA_CREAR
    assert destino_al_reintentar(None) == EstadoRepositorio.LISTO_PARA_CREAR


def test_ca_8_8_01_acceso_previo_es_acceso_directo():
    assert estado_acceso_tras_invitar(204) == EstadoAccesoRepositorio.ACCESO_DIRECTO
    assert estado_acceso_tras_invitar(201) == EstadoAccesoRepositorio.INVITADO


def test_estimacion_de_tiempo_restante():
    assert minutos_restantes(pendientes=0) == 0
    assert minutos_restantes(pendientes=1) == 1
    assert minutos_restantes(pendientes=60) == 6
    assert minutos_restantes(pendientes=90, ritmo_segundos=12) == 18
