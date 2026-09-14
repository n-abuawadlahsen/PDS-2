"""Trabajo `despachar_outbox` (SPEC 11 S11.2; A-125). Global, cada 30 s.

Toma el cerrojo de Canvas del curso de cada mensaje en el momento del envio
("1 en su parte de Canvas", catalogo S14.7.4).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.adaptadores import outbox_repo
from app.adaptadores.modelos_infraestructura import Trabajo
from app.trabajos.registro import registrar


@registrar("despachar_outbox")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    outbox_repo.despachar_pendientes(sesion, tomado_por=trabajo.tomado_por or "despachar_outbox")
