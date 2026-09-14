"""SPEC 14 S14.6.4: AES-256-GCM, AAD por curso, llavero versionado."""

from __future__ import annotations

import os

import pytest

from app.infraestructura.cifrado import DescifradoFallido, Llavero


def _llavero(*, activa: int = 1) -> Llavero:
    return Llavero({1: os.urandom(32), 2: os.urandom(32)}, version_activa=activa)


def test_cifrar_y_descifrar_es_identidad():
    llavero = _llavero()
    texto = b"token-de-canvas-secreto"
    valor = llavero.cifrar(texto, curso_id=42)
    assert llavero.descifrar(valor, curso_id=42) == texto


def test_aad_liga_el_valor_a_un_solo_curso():
    llavero = _llavero()
    valor = llavero.cifrar(b"secreto", curso_id=1)
    with pytest.raises(DescifradoFallido):
        llavero.descifrar(valor, curso_id=2)


def test_version_de_clave_ausente_falla_como_credencial_invalida():
    llavero_para_cifrar = Llavero({5: os.urandom(32)}, version_activa=5)
    valor = llavero_para_cifrar.cifrar(b"secreto", curso_id=1)

    llavero_sin_esa_version = Llavero({1: os.urandom(32)}, version_activa=1)
    with pytest.raises(DescifradoFallido):
        llavero_sin_esa_version.descifrar(valor, curso_id=1)


def test_llave_activa_ausente_del_llavero_falla_al_construir():
    with pytest.raises(ValueError):
        Llavero({1: os.urandom(32)}, version_activa=2)


def test_recifrado_perezoso_identifica_filas_con_version_vieja():
    llavero = _llavero(activa=2)
    assert llavero.filas_por_recifrar({1, 2}) == {1}
