"""SPEC 04 S4.7: catalogo, orden de carriles, y reglas de calificacion."""

from __future__ import annotations

from app.dominio.estados import ResultadoVerificacion
from app.dominio.verificacion import (
    CATALOGO_VERIFICACION,
    ITEMS_CARRIL_GITHUB,
    ORDEN_CARRIL_CANVAS,
    Severidad,
    curso_puede_pasar_a_activo,
    resultado_binario,
    resultado_item_17,
)


def test_ca_4_7_06_catalogo_tiene_21_entradas():
    assert len(CATALOGO_VERIFICACION) == 21


def test_ordenes_de_carril_cubren_los_19_numerados_sin_solape():
    assert set(ORDEN_CARRIL_CANVAS) & set(ITEMS_CARRIL_GITHUB) == set()
    assert len(ORDEN_CARRIL_CANVAS) == 17
    assert len(ITEMS_CARRIL_GITHUB) == 2


def test_bloqueantes_primero_en_el_orden_canvas():
    ids_bloqueantes = {i.id for i in CATALOGO_VERIFICACION if i.severidad == Severidad.BLOQUEANTE}
    primeros = ORDEN_CARRIL_CANVAS[:4]
    assert set(primeros) >= (ids_bloqueantes & set(ORDEN_CARRIL_CANVAS))


def test_resultado_binario_aprobado_es_siempre_correcto():
    for severidad in Severidad:
        assert (
            resultado_binario(aprobado=True, severidad=severidad) == ResultadoVerificacion.CORRECTO
        )


def test_resultado_binario_bloqueante_reprobado_es_bloqueante():
    assert (
        resultado_binario(aprobado=False, severidad=Severidad.BLOQUEANTE)
        == ResultadoVerificacion.BLOQUEANTE
    )


def test_resultado_binario_advertencia_fuerte_reprobado_es_advertencia():
    assert (
        resultado_binario(aprobado=False, severidad=Severidad.ADVERTENCIA_FUERTE)
        == ResultadoVerificacion.ADVERTENCIA
    )


def test_resultado_binario_informativo_reprobado_sigue_siendo_correcto():
    assert (
        resultado_binario(aprobado=False, severidad=Severidad.INFORMATIVO)
        == ResultadoVerificacion.CORRECTO
    )


def test_item_17_bloqueante_si_item_6_fallo():
    assert resultado_item_17(aprobado=False, item_6_fallo=True) == ResultadoVerificacion.BLOQUEANTE


def test_item_17_advertencia_si_item_6_ok():
    assert (
        resultado_item_17(aprobado=False, item_6_fallo=False) == ResultadoVerificacion.ADVERTENCIA
    )


def test_item_17_aprobado_es_correcto_sin_importar_item_6():
    assert resultado_item_17(aprobado=True, item_6_fallo=True) == ResultadoVerificacion.CORRECTO


def test_curso_puede_pasar_a_activo_sin_bloqueantes():
    resultados = {
        "1": ResultadoVerificacion.CORRECTO,
        "4": ResultadoVerificacion.ADVERTENCIA,
        "7": ResultadoVerificacion.NO_VERIFICADO,
    }
    assert curso_puede_pasar_a_activo(resultados)


def test_curso_no_puede_pasar_a_activo_con_un_bloqueante():
    resultados = {"1": ResultadoVerificacion.CORRECTO, "2": ResultadoVerificacion.BLOQUEANTE}
    assert not curso_puede_pasar_a_activo(resultados)
