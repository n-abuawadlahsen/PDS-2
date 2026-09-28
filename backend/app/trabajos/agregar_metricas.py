"""Trabajo `agregar_metricas` (SPEC 14 S14.7.4 fila 27; SPEC 10 S10.4.1;
A-114, A-221). Cada 10 minutos por curso; recomputa, nunca incrementa.

No llama a ningun proveedor: transforma el espejo (`commit`,
`autoria_commit`) en agregados y alertas.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.adaptadores import metricas_repo
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Trabajo
from app.trabajos.registro import registrar


@registrar("agregar_metricas")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    assert trabajo.curso_id is not None
    curso = sesion.query(Curso).filter(Curso.id == trabajo.curso_id).one()
    metricas_repo.agregar_metricas(sesion, curso=curso)
