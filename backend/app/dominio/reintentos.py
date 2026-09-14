"""Calculo puro de retroceso exponencial con jitter y tope (SPEC 14 S14.7.2 #4).

Respeta siempre `retry-after` cuando el proveedor lo entrega; si no, retroceso
exponencial con jitter. Sin I/O: el "cuando" (ahora) y el "cuanto azar" (random)
se inyectan para que la funcion sea determinista en pruebas.
"""

from __future__ import annotations

from datetime import datetime, timedelta

_BASE_SEGUNDOS = 2.0
_TOPE_SEGUNDOS = 15 * 60.0


def calcular_espera(
    *,
    intento: int,
    retry_after_segundos: float | None = None,
    jitter_0_a_1: float = 0.0,
) -> float:
    """Devuelve segundos de espera antes del proximo intento (intento >= 1)."""
    if retry_after_segundos is not None:
        return max(0.0, retry_after_segundos)
    base = min(_BASE_SEGUNDOS * (2.0 ** (intento - 1)), _TOPE_SEGUNDOS)
    jitter = base * jitter_0_a_1 * 0.5
    return float(base + jitter)


def proximo_intento_en(
    *,
    ahora: datetime,
    intento: int,
    retry_after_segundos: float | None = None,
    jitter_0_a_1: float = 0.0,
) -> datetime:
    espera = calcular_espera(
        intento=intento, retry_after_segundos=retry_after_segundos, jitter_0_a_1=jitter_0_a_1
    )
    return ahora + timedelta(seconds=espera)
