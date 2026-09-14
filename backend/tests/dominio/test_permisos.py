"""SPEC 02 S2.3: catalogo cerrado de nueve permisos."""

from __future__ import annotations

import pytest

from app.dominio.permisos import (
    ACCIONES_SOLO_PROFESOR,
    PERMISOS_CONCEDIBLES,
    PERMISOS_CONFIGURABLES,
    PERMISOS_IMPLICITOS,
    PERMISOS_NO_CONCEDIBLES,
    Permiso,
    PermisoInvalido,
    permisos_efectivos,
    validar_permisos_ayudante,
    validar_permisos_profesor,
)


def test_son_exactamente_nueve_permisos():
    assert len(list(Permiso)) == 9


def test_dos_implicitos_siete_configurables():
    assert len(PERMISOS_IMPLICITOS) == 2
    assert len(PERMISOS_CONFIGURABLES) == 7
    assert PERMISOS_IMPLICITOS.isdisjoint(PERMISOS_CONFIGURABLES)


def test_cinco_concedibles_dos_no_concedibles():
    assert len(PERMISOS_CONCEDIBLES) == 5
    assert len(PERMISOS_NO_CONCEDIBLES) == 2
    assert PERMISOS_CONCEDIBLES | PERMISOS_NO_CONCEDIBLES == PERMISOS_CONFIGURABLES


def test_ayudante_con_permiso_no_concedible_se_rechaza():
    with pytest.raises(PermisoInvalido):
        validar_permisos_ayudante(frozenset({Permiso.CURSO_ADMINISTRAR}))


def test_ayudante_con_permiso_concedible_se_acepta():
    validar_permisos_ayudante(frozenset({Permiso.MAPEO_EDITAR, Permiso.NOTA_PUBLICAR}))


def test_profesor_con_permisos_no_vacio_se_rechaza():
    with pytest.raises(PermisoInvalido):
        validar_permisos_profesor(frozenset({Permiso.NOTA_PUBLICAR}))


def test_profesor_tiene_los_nueve_efectivos_aunque_columna_este_vacia():
    efectivos = permisos_efectivos(rol="PROFESOR", permisos_configurados=frozenset())
    assert efectivos == frozenset(Permiso)


def test_ayudante_efectivos_es_implicitos_mas_configurados():
    efectivos = permisos_efectivos(
        rol="AYUDANTE", permisos_configurados=frozenset({Permiso.MAPEO_EDITAR})
    )
    assert efectivos == PERMISOS_IMPLICITOS | {Permiso.MAPEO_EDITAR}


def test_acciones_solo_profesor_son_exactamente_seis():
    assert len(ACCIONES_SOLO_PROFESOR) == 6
