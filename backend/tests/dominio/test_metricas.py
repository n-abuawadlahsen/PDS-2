"""Etapa F6 (SPEC 10 S10.4-S10.8; A-118 a A-124, A-171, A-205, A-220 a A-223):
metricas, predicados y estado agregado, reglas puras."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from app.dominio.metricas import (
    EstadoEntregaAgregado,
    SujetoEntrega,
    causa_sin_participacion,
    cuartiles,
    dia_del_curso,
    en_ventana,
    es_commit_contable,
    estado_entrega,
    evaluar_actividad,
    indice_desequilibrio,
    progreso_frente_al_cierre,
    racha_sin_actividad,
    senal_reparto_concentrado,
    umbral_aplicable,
    ventana_entrega,
)

_T = datetime(2026, 10, 1, 23, 59, tzinfo=UTC)


@dataclass
class _C:
    motivo_exclusion: str


def test_commit_contable_tiene_tres_exclusiones_y_nada_mas():
    assert es_commit_contable(_C("NINGUNO"))
    for motivo in ("MERGE", "COMMIT_INICIAL", "HUERFANO"):
        assert not es_commit_contable(_C(motivo))


def test_dia_del_curso_en_la_zona_del_curso():
    # 02:30 UTC del 2 de octubre es la noche del 1 de octubre en Santiago.
    instante = datetime(2026, 10, 2, 2, 30, tzinfo=UTC)
    assert dia_del_curso(instante, "America/Santiago") == date(2026, 10, 1)
    assert dia_del_curso(instante, "UTC") == date(2026, 10, 2)


def test_ventana_abierta_por_izquierda_cerrada_por_derecha():
    """CA-10.6-03: un commit exactamente en el cierre pertenece a esa entrega."""
    creado = _T - timedelta(days=20)
    v1 = ventana_entrega(
        due_anterior=None, repositorio_creado_en=creado, due_actual=_T, ahora=_T + timedelta(days=5)
    )
    assert v1 is not None
    assert en_ventana(_T, v1)
    assert not en_ventana(creado, v1)
    v2 = ventana_entrega(
        due_anterior=_T,
        repositorio_creado_en=creado,
        due_actual=_T + timedelta(days=7),
        ahora=_T,
    )
    assert v2 is not None and not en_ventana(_T, v2)


def test_ventana_recortada_a_la_pertenencia_del_integrante():
    """CA-10.6-04: quien entro a mitad del tramo empieza el dia de su entrada."""
    entrada = _T - timedelta(days=3)
    v = ventana_entrega(
        due_anterior=None,
        repositorio_creado_en=_T - timedelta(days=20),
        due_actual=_T,
        ahora=_T,
        activa_desde=entrada,
    )
    assert v is not None and v.inicio == entrada
    # Sin fecha de cierre: la ventana queda abierta hasta ahora.
    abierta = ventana_entrega(
        due_anterior=None, repositorio_creado_en=_T - timedelta(days=2), due_actual=None, ahora=_T
    )
    assert abierta is not None and abierta.fin == _T


def test_umbral_baja_a_dos_dias_cerca_de_un_cierre():
    ahora = _T - timedelta(hours=48)
    assert umbral_aplicable(7, proximo_cierre=_T, ahora=ahora) == 2
    assert umbral_aplicable(7, proximo_cierre=_T, ahora=_T - timedelta(days=5)) == 7
    assert umbral_aplicable(7, proximo_cierre=None, ahora=ahora) == 7


def test_ca_10_5_03_repositorio_joven_no_esta_sin_actividad():
    ahora = _T
    joven = evaluar_actividad(
        observado_desde=ahora - timedelta(days=3),
        ultimo_commit_estudiantil=None,
        umbral_dias=7,
        ahora=ahora,
    )
    assert joven.estado == "SIN_DATO_SUFICIENTE"
    assert (joven.dias_observados, joven.umbral_dias) == (3, 7)
    parado = evaluar_actividad(
        observado_desde=ahora - timedelta(days=30),
        ultimo_commit_estudiantil=ahora - timedelta(days=8),
        umbral_dias=7,
        ahora=ahora,
    )
    assert parado.estado == "SIN_ACTIVIDAD"
    activo = evaluar_actividad(
        observado_desde=ahora - timedelta(days=30),
        ultimo_commit_estudiantil=ahora - timedelta(days=2),
        umbral_dias=7,
        ahora=ahora,
    )
    assert activo.estado == "CON_ACTIVIDAD"


def test_causas_de_sin_participacion_en_cascada():
    """CA-10.5-05: con commits sin atribuir nadie queda en SIN_COMMITS."""
    assert causa_sin_participacion(acceso="INVITADO", commits=0, hay_sin_atribuir=True) == (
        "SIN_ACCESO"
    )
    assert causa_sin_participacion(acceso="ACEPTADO", commits=0, hay_sin_atribuir=True) == (
        "SIN_ATRIBUIR"
    )
    assert causa_sin_participacion(acceso="ACCESO_DIRECTO", commits=0, hay_sin_atribuir=False) == (
        "SIN_COMMITS"
    )
    assert causa_sin_participacion(acceso="ACEPTADO", commits=3, hay_sin_atribuir=False) is None


def _sujeto(due, *, version=None):
    return SujetoEntrega(due_at=due, estado_version=version)


def test_estado_agregado_de_la_entrega_nueve_valores():
    ahora = _T
    antes, despues = _T - timedelta(days=1), _T + timedelta(days=1)
    caso = {
        "VIGENTE": [_sujeto(despues)],
    }
    assert caso  # legibilidad
    assert (
        estado_entrega(estado_validacion="EXCLUIDA", publicada=True, sujetos=[], ahora=ahora)
        == EstadoEntregaAgregado.EXCLUIDA
    )
    assert (
        estado_entrega(
            estado_validacion="ELIMINADA_EN_CANVAS", publicada=False, sujetos=[], ahora=ahora
        )
        == EstadoEntregaAgregado.ELIMINADA_EN_CANVAS
    )
    assert (
        estado_entrega(estado_validacion="VIGENTE", publicada=False, sujetos=[], ahora=ahora)
        == EstadoEntregaAgregado.NO_PUBLICADA
    )
    assert (
        estado_entrega(
            estado_validacion="VINCULADA_TRAS_EL_CIERRE", publicada=True, sujetos=[], ahora=ahora
        )
        == EstadoEntregaAgregado.VINCULADA_TRAS_EL_CIERRE
    )
    assert (
        estado_entrega(
            estado_validacion="VIGENTE", publicada=True, sujetos=[_sujeto(None)], ahora=ahora
        )
        == EstadoEntregaAgregado.SIN_FECHA
    )
    assert (
        estado_entrega(
            estado_validacion="VIGENTE", publicada=True, sujetos=[_sujeto(despues)], ahora=ahora
        )
        == EstadoEntregaAgregado.ABIERTA
    )
    # CA-10.6-01: dos secciones, una ya cerro y otra no.
    assert (
        estado_entrega(
            estado_validacion="VIGENTE",
            publicada=True,
            sujetos=[_sujeto(antes, version="CAPTURADA"), _sujeto(despues)],
            ahora=ahora,
        )
        == EstadoEntregaAgregado.EN_CIERRE
    )
    assert (
        estado_entrega(
            estado_validacion="VIGENTE",
            publicada=True,
            sujetos=[_sujeto(antes, version="CAPTURADA"), _sujeto(antes)],
            ahora=ahora,
        )
        == EstadoEntregaAgregado.CERRADA_CAPTURANDO
    )
    assert (
        estado_entrega(
            estado_validacion="VIGENTE",
            publicada=True,
            sujetos=[_sujeto(antes, version="CAPTURADA"), _sujeto(antes, version="SIN_COMMITS")],
            ahora=ahora,
        )
        == EstadoEntregaAgregado.CERRADA_REGISTRADA
    )


def test_indice_de_desequilibrio_y_senal():
    """CA-10.8-02/03."""
    assert indice_desequilibrio([8, 2]) == 80
    assert indice_desequilibrio([0, 0]) is None  # «no calculable», nunca 0 ni 100
    assert indice_desequilibrio([5]) == 100
    assert senal_reparto_concentrado([8, 2], con_acceso=2, umbral_pct=70) is True
    # Menos de 10 commits atribuidos: sin senal aunque el indice supere el umbral...
    assert senal_reparto_concentrado([4, 1], con_acceso=2, umbral_pct=70) is False
    # ...salvo que uno tenga cero y otro tres o mas.
    assert senal_reparto_concentrado([3, 0], con_acceso=2, umbral_pct=70) is True
    assert senal_reparto_concentrado([8, 2], con_acceso=1, umbral_pct=70) is False


def test_cuartiles_racha_y_progreso():
    assert cuartiles([1, 2, 3, 4, 5]) == (2.0, 3.0, 4.0)
    assert cuartiles([]) is None
    hoy = date(2026, 10, 10)
    assert racha_sin_actividad(date(2026, 10, 7), hoy) == 3
    assert racha_sin_actividad(None, hoy) is None  # «sin actividad desde su creacion»
    ahora = _T
    assert (
        progreso_frente_al_cierre(
            [(_T - timedelta(hours=1), _T - timedelta(hours=10)), (_T - timedelta(hours=1), None)],
            ahora=ahora,
        )
        == 50
    )
