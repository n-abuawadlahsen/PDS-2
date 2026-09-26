"""Trabajo `purga_retencion` (SPEC 14 S14.7.4; SPEC 11 S11.2.4). Diario.

Lo retenido por la suspension del curso, el modo solo lectura o una ventana
tras restauracion durante mas de siete dias pasa a CADUCADO con
`SUSPENSION_PROLONGADA`. No borra ninguna fila de `mensaje_saliente`.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.adaptadores import comunicaciones_repo
from app.adaptadores.modelos_infraestructura import Trabajo
from app.trabajos.registro import registrar


@registrar("purga_retencion")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    comunicaciones_repo.purgar(sesion)
