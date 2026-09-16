"""Revocacion con identidad capturada y comprobacion del estado vigente."""

from sqlalchemy.orm import Session

from app.adaptadores.modelos_infraestructura import Trabajo
from app.trabajos.registro import registrar
from app.trabajos.sincronizar_acceso_docente import ejecutar as reconciliar


@registrar("revocar_acceso_docente")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    reconciliar(sesion, trabajo)
