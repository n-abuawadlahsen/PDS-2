"""Trabajo `vigilancia` (SPEC 14 S14.7.6, S14.7.4 fila 21). Cadencia: 5 min.

Devuelve a PENDIENTE toda fila `trabajo` en EN_CURSO cuyo `tomado_en` tenga mas
de 10 minutos: muerte sin señal del proceso que la tenia tomada.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.adaptadores import trabajos_repo
from app.adaptadores.modelos_infraestructura import Trabajo
from app.infraestructura.logs import obtener_logger
from app.trabajos.registro import registrar

_logger = obtener_logger(__name__)


@registrar("vigilancia")
def ejecutar(sesion: Session, _trabajo: Trabajo) -> None:
    recuperados = trabajos_repo.liberar_huerfanos_por_vigilancia(sesion, umbral_minutos=10)
    if recuperados:
        _logger.info("vigilancia.huerfanos_recuperados", cantidad=recuperados)
