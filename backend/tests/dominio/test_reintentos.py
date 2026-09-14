from __future__ import annotations

from app.dominio.reintentos import calcular_espera


def test_respeta_retry_after_si_viene():
    assert calcular_espera(intento=5, retry_after_segundos=42.0) == 42.0


def test_crece_exponencialmente_sin_retry_after():
    espera_1 = calcular_espera(intento=1)
    espera_2 = calcular_espera(intento=2)
    espera_3 = calcular_espera(intento=3)
    assert espera_1 < espera_2 < espera_3


def test_tiene_tope():
    espera_alta = calcular_espera(intento=100)
    assert espera_alta <= 15 * 60 * 1.5  # tope + jitter maximo
