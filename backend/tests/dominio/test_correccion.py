"""Etapa F11 (SPEC 12 S12.3, S12.5, S12.9, S12.10.1): funciones puras."""

from __future__ import annotations

import uuid

import pytest

from app.dominio.correccion import (
    ETIQUETA_ESTADO,
    TRANSICIONES,
    Corrector,
    NotaInvalida,
    SujetoReparto,
    huella_rubrica,
    motivo_no_publicable,
    normalizar_nota,
    puede_transicionar,
    reparto_equitativo,
    reparto_por_seccion,
    suma_rubrica,
    validar_rubrica_local,
)
from app.dominio.estados import EstadoCorreccion, MotivoNoPublicable


def test_ocho_estados_con_etiqueta_y_ninguno_no_publicable():
    # CA-12.3-01, CA-12.3-02, CA-12.3-05
    assert len(EstadoCorreccion) == 8
    assert "NO_PUBLICABLE" not in {e.value for e in EstadoCorreccion}
    assert set(ETIQUETA_ESTADO) == {e.value for e in EstadoCorreccion}
    assert len(MotivoNoPublicable) == 10


def test_tabla_de_transiciones():
    assert sum(len(v) for v in TRANSICIONES.values()) >= 11
    assert puede_transicionar("ASIGNADA", "EN_CURSO")
    assert puede_transicionar("PUBLICADA", "EN_CURSO")  # reabrir
    assert puede_transicionar("PUBLICANDO", "LISTA_PARA_PUBLICAR")  # cancelada
    assert not puede_transicionar("SIN_CORRECTOR", "PUBLICADA")
    assert not puede_transicionar("PUBLICADA", "SIN_CORRECTOR")  # lo publicado no se retira


def test_formatos_de_nota():
    # CA-12.10-02
    assert normalizar_nota("points", "18,5", 20) == "18.5"
    assert normalizar_nota("percent", "85.5", None) == "85.5%"
    assert normalizar_nota("pass_fail", "Pass", None) == "pass"
    assert normalizar_nota("pass_fail", "incomplete", None) == "fail"
    assert normalizar_nota("letter_grade", "A-", None) == "A-"
    for tipo, valor in (
        ("points", "18.555"),
        ("points", "abc"),
        ("pass_fail", "7"),
        ("gpa_scale", "3"),
    ):
        with pytest.raises(NotaInvalida):
            normalizar_nota(tipo, valor, 20)


def test_motivos_de_no_publicable():
    base = dict(
        grading_type="points",
        moderada=False,
        anonima=False,
        publicada=True,
        estado_validacion=None,
        sujeto_activo=True,
    )
    assert motivo_no_publicable(**base) is None
    assert motivo_no_publicable(**{**base, "grading_type": "not_graded"}) == "NO_GRADED"
    assert motivo_no_publicable(**{**base, "anonima": True}) == "MODERADA_O_ANONIMA"
    assert motivo_no_publicable(**{**base, "publicada": False}) == "ENTREGA_DESPUBLICADA"
    assert (
        motivo_no_publicable(**{**base, "estado_validacion": "ELIMINADA_EN_CANVAS"})
        == "ENTREGA_ELIMINADA"
    )
    assert motivo_no_publicable(**{**base, "sujeto_activo": False}) == "SUJETO_EXCLUIDO"


def _u(n: int) -> uuid.UUID:
    return uuid.UUID(int=n)


def test_reparto_equitativo_es_determinista_y_respeta_pesos():
    # CA-12.5-02
    sujetos = [SujetoReparto(_u(i), f"Estudiante {i:02d}", (), None, False) for i in range(1, 10)]
    correctores = [
        Corrector(_u(100), "Beatriz", 2),
        Corrector(_u(101), "Andrés", 1),
        Corrector(_u(102), "Profesora", 0),
    ]
    uno = reparto_equitativo(sujetos, correctores)
    dos = reparto_equitativo(list(reversed(sujetos)), list(reversed(correctores)))
    assert uno == dos
    cuenta = {m: list(uno.values()).count(m) for m in set(uno.values())}
    assert cuenta == {_u(100): 6, _u(101): 3}  # peso 2 recibe el doble; peso 0 no entra


def test_reparto_solo_llena_filas_vacias_salvo_reasignar():
    sujetos = [
        SujetoReparto(_u(1), "A", (), _u(100), True),
        SujetoReparto(_u(2), "B", (), None, False),
        SujetoReparto(_u(3), "C", (), None, False, calificable=False),
    ]
    correctores = [Corrector(_u(100), "Beatriz", 1), Corrector(_u(101), "Andrés", 1)]
    assert reparto_equitativo(sujetos, correctores) == {
        _u(2): _u(101)
    }  # la carga de Beatriz cuenta
    assert set(
        reparto_equitativo(sujetos, correctores, reasignar=True, incluir_no_calificables=True)
    ) == {_u(1), _u(2), _u(3)}


def test_reparto_por_seccion_con_doble_seccion_requiere_decision():
    s1, s2 = _u(501), _u(502)
    sujetos = [
        SujetoReparto(_u(1), "A", (s1,), None, False),
        SujetoReparto(_u(2), "B", (s1, s2), None, False),
        SujetoReparto(_u(3), "C", (s2,), None, False),
    ]
    asignados, decision = reparto_por_seccion(sujetos, {s1: _u(100)})
    assert asignados == {_u(1): _u(100)} and decision == [_u(2)]


def test_rubrica_huella_validacion_y_suma():
    rubrica = [
        {
            "id": "c1",
            "description": "Correctitud",
            "points": 60,
            "ratings": [{"id": "r1", "points": 60}, {"id": "r2", "points": 30}],
        },
        {
            "id": "c2",
            "description": "Estilo",
            "points": 40,
            "ratings": [{"id": "r3", "points": 40}],
        },
    ]
    h = huella_rubrica(rubrica, {})
    assert h == huella_rubrica(rubrica, {"otro": 1}) and len(h) == 32
    assert h != huella_rubrica([{**rubrica[0], "points": 70}, rubrica[1]], {})
    local = {"c1": {"points": 30, "rating_id": "r2"}, "c2": {"points": 35}}
    assert validar_rubrica_local(rubrica, local) == []
    assert suma_rubrica(rubrica, local) == 65
    errores = validar_rubrica_local(
        rubrica, {"c1": {"points": 90}, "c9": {"points": 1}, "c2": {"rating_id": "r1"}}
    )
    assert len(errores) == 3
    assert suma_rubrica([{**rubrica[0], "criterion_use_range": True}], local) is None
