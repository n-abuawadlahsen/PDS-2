"""SPEC 05 S5.2.3 (canonica) / SPEC 04 S4.5.2: las cinco comprobaciones."""

from __future__ import annotations

import pytest

from app.dominio.vinculacion_canvas import (
    IdentidadExistente,
    MatriculaCanvas,
    MotivoRechazoVinculacion,
    RechazoVinculacion,
    tiene_matricula_profesor_activa,
    todas_las_matriculas_profesor_limitadas_a_seccion,
    verificar_identidad,
)


def test_2b_matricula_profesor_activa_se_acepta():
    matriculas = [MatriculaCanvas("TeacherEnrollment", "active", limitada_a_seccion=False)]
    assert tiene_matricula_profesor_activa(matriculas)


def test_2b_sin_matricula_de_profesor_se_rechaza():
    matriculas = [MatriculaCanvas("StudentEnrollment", "active", limitada_a_seccion=False)]
    assert not tiene_matricula_profesor_activa(matriculas)


def test_2b_matricula_de_profesor_inactiva_no_cuenta():
    matriculas = [MatriculaCanvas("TeacherEnrollment", "completed", limitada_a_seccion=False)]
    assert not tiene_matricula_profesor_activa(matriculas)


def test_a052_todas_limitadas_a_seccion_bloquea():
    matriculas = [MatriculaCanvas("TeacherEnrollment", "active", limitada_a_seccion=True)]
    assert todas_las_matriculas_profesor_limitadas_a_seccion(matriculas)


def test_a052_una_sin_limitar_no_bloquea():
    matriculas = [
        MatriculaCanvas("TeacherEnrollment", "active", limitada_a_seccion=True),
        MatriculaCanvas("TeacherEnrollment", "active", limitada_a_seccion=False),
    ]
    assert not todas_las_matriculas_profesor_limitadas_a_seccion(matriculas)


def test_a052_sin_matriculas_profesor_no_bloquea_por_esta_regla():
    assert not todas_las_matriculas_profesor_limitadas_a_seccion([])


def test_2d_identidad_coincidente_no_se_rechaza():
    verificar_identidad(canvas_user_id_devuelto=42, identidad_previa=IdentidadExistente(42))


def test_2d_identidad_distinta_se_rechaza():
    with pytest.raises(RechazoVinculacion) as exc_info:
        verificar_identidad(canvas_user_id_devuelto=42, identidad_previa=IdentidadExistente(99))
    assert exc_info.value.motivo == MotivoRechazoVinculacion.IDENTIDAD_NO_COINCIDE


def test_2e_sin_identidad_previa_no_se_rechaza():
    verificar_identidad(canvas_user_id_devuelto=42, identidad_previa=None)
