from __future__ import annotations

import pytest

from app.dominio.membresia import UltimoProfesorActivo, puede_retirar_o_degradar


def test_retirar_al_unico_profesor_activo_se_rechaza():
    with pytest.raises(UltimoProfesorActivo):
        puede_retirar_o_degradar(
            es_profesor_activo=True, cantidad_profesores_activos=1, curso_activo=True
        )


def test_retirar_a_un_profesor_con_respaldo_se_permite():
    puede_retirar_o_degradar(
        es_profesor_activo=True, cantidad_profesores_activos=2, curso_activo=True
    )


def test_retirar_a_un_ayudante_siempre_se_permite():
    puede_retirar_o_degradar(
        es_profesor_activo=False, cantidad_profesores_activos=1, curso_activo=True
    )


def test_curso_no_activo_no_aplica_el_invariante():
    puede_retirar_o_degradar(
        es_profesor_activo=True, cantidad_profesores_activos=1, curso_activo=False
    )
