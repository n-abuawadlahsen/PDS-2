"""SPEC 07 S7.2-S7.3, S7.9: reglas puras del espejo de Canvas."""

from __future__ import annotations

from app.dominio.estados import EstadoEstudiante
from app.dominio.padron import (
    cambio_masivo_de_estado,
    confirma_ausencia,
    detectar_traslado_o_doble_pertenencia,
    estado_estudiante_desde_matriculas,
    roster_sospechoso,
    slug_desde_nombre,
)


def test_estado_activo_gana_sobre_los_demas():
    assert (
        estado_estudiante_desde_matriculas(["completed", "active", "inactive"])
        == EstadoEstudiante.ACTIVO
    )


def test_estado_invitado_si_no_hay_activo():
    assert estado_estudiante_desde_matriculas(["invited", "completed"]) == EstadoEstudiante.INVITADO


def test_estado_concluido_si_solo_hay_completed():
    assert estado_estudiante_desde_matriculas(["completed"]) == EstadoEstudiante.CONCLUIDO


def test_estado_sin_workflow_reconocible_es_inactivo_por_defecto():
    assert estado_estudiante_desde_matriculas(["deleted", "rejected"]) == EstadoEstudiante.INACTIVO


def test_confirma_ausencia_requiere_dos_ciclos():
    assert not confirma_ausencia(1)
    assert confirma_ausencia(2)
    assert confirma_ausencia(3)


def test_roster_sospechoso_primer_sync_nunca_es_sospechoso():
    assert not roster_sospechoso(cantidad_anterior=0, cantidad_actual=0)
    assert not roster_sospechoso(cantidad_anterior=0, cantidad_actual=50)


def test_roster_sospechoso_caida_a_cero():
    assert roster_sospechoso(cantidad_anterior=42, cantidad_actual=0)


def test_roster_sospechoso_bajo_el_60_por_ciento():
    assert roster_sospechoso(cantidad_anterior=200, cantidad_actual=40)


def test_roster_no_sospechoso_sobre_el_60_por_ciento():
    assert not roster_sospechoso(cantidad_anterior=200, cantidad_actual=130)


def test_cambio_masivo_mas_del_30_por_ciento():
    assert cambio_masivo_de_estado(activos_anterior=100, cantidad_cambiados=31)
    assert not cambio_masivo_de_estado(activos_anterior=100, cantidad_cambiados=30)


def test_traslado_de_grupo_limpio():
    resultado = detectar_traslado_o_doble_pertenencia(
        grupos_aceptados_anteriores=frozenset({"grupo-a"}),
        grupos_aceptados_actuales=frozenset({"grupo-b"}),
    )
    assert resultado.es_traslado
    assert not resultado.conjunto_ambiguo


def test_doble_pertenencia_simultanea_no_es_traslado():
    resultado = detectar_traslado_o_doble_pertenencia(
        grupos_aceptados_anteriores=frozenset({"grupo-a"}),
        grupos_aceptados_actuales=frozenset({"grupo-a", "grupo-b"}),
    )
    assert not resultado.es_traslado
    assert resultado.conjunto_ambiguo


def test_salida_simple_sin_grupo_nuevo_no_es_traslado():
    resultado = detectar_traslado_o_doble_pertenencia(
        grupos_aceptados_anteriores=frozenset({"grupo-a"}),
        grupos_aceptados_actuales=frozenset(),
    )
    assert not resultado.es_traslado
    assert not resultado.conjunto_ambiguo


def test_slug_desde_nombre_normaliza_y_desambigua():
    assert slug_desde_nombre("Grupo Número 1", canvas_group_id=42) == "grupo-numero-1-42"
    assert slug_desde_nombre("", canvas_group_id=7) == "grupo-7"
