"""Casos de prueba obligatorios de SPEC 02 S2.2.4, S2.2.5, S2.2.7."""

from __future__ import annotations

import pytest

from app.dominio.identidad import MotivoRechazoCorreo, RechazoCorreo, normalizar_correo_google


def test_gmail_simple_se_admite():
    resultado = normalizar_correo_google("ana@gmail.com", email_verified=True, hd=None)
    assert resultado.email == "ana@gmail.com"
    assert resultado.email_canonico == "ana@gmail.com"


def test_mayusculas_se_normalizan():
    resultado = normalizar_correo_google("Ana@GMail.com", email_verified=True, hd=None)
    assert resultado.email == "ana@gmail.com"


def test_googlemail_se_normaliza_a_gmail():
    resultado = normalizar_correo_google("ana@googlemail.com", email_verified=True, hd=None)
    assert resultado.email == "ana@gmail.com"


def test_institucional_con_hd_se_rechaza():
    with pytest.raises(RechazoCorreo) as exc_info:
        normalizar_correo_google("ana@uandes.cl", email_verified=True, hd="uandes.cl")
    assert exc_info.value.motivo == MotivoRechazoCorreo.HD_PRESENTE


def test_gmail_con_hd_se_rechaza_igual():
    """hd manda y se rechaza aunque la direccion termine en @gmail.com (S2.2.4)."""
    with pytest.raises(RechazoCorreo) as exc_info:
        normalizar_correo_google("ana@gmail.com", email_verified=True, hd="workspace.example.com")
    assert exc_info.value.motivo == MotivoRechazoCorreo.HD_PRESENTE


def test_correo_no_verificado_se_rechaza():
    with pytest.raises(RechazoCorreo) as exc_info:
        normalizar_correo_google("ana@gmail.com", email_verified=False, hd=None)
    assert exc_info.value.motivo == MotivoRechazoCorreo.CORREO_NO_VERIFICADO


def test_dominio_ajeno_se_rechaza():
    with pytest.raises(RechazoCorreo) as exc_info:
        normalizar_correo_google("ana@hotmail.com", email_verified=True, hd=None)
    assert exc_info.value.motivo == MotivoRechazoCorreo.DOMINIO_NO_GMAIL


def test_puntos_y_sufijo_producen_mismo_canonico():
    """CA-2.2-10: ana.perez+ramo@gmail.com y anaperez@gmail.com -> mismo email_canonico."""
    a = normalizar_correo_google("ana.perez+ramo@gmail.com", email_verified=True, hd=None)
    b = normalizar_correo_google("anaperez@gmail.com", email_verified=True, hd=None)
    assert a.email_canonico == b.email_canonico == "anaperez@gmail.com"
