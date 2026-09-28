"""Trabajo `reconciliar_notas_canvas` (SPEC 14 S14.7.4 fila 30; SPEC 12
S12.13; A-206, A-218). Cerrojo 1, clave `(entrega, ventana)`, 4 reintentos.

Con `entrega_id` en el payload reconcilia esa entrega (inmediata tras
publicar o por «comprobar contra Canvas»); sin el, recorre las entregas del
curso segun su ventana: cada 30 min dentro, una vez al dia fuera, nunca en una
tarea archivada.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.adaptadores import publicacion_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Trabajo
from app.adaptadores.modelos_tarea import Entrega, Tarea
from app.trabajos.registro import registrar


@registrar(publicacion_repo.TIPO_RECONCILIAR)
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    assert trabajo.curso_id is not None
    curso = sesion.query(Curso).filter(Curso.id == trabajo.curso_id).one()
    if trabajo.payload.get("entrega_id"):
        entrega = sesion.get(Entrega, uuid.UUID(trabajo.payload["entrega_id"]))
        tarea = sesion.get(Tarea, entrega.tarea_id) if entrega else None
        entregas = [entrega] if entrega and tarea and tarea.estado != "ARCHIVADA" else []
    else:
        entregas = publicacion_repo.entregas_a_reconciliar(sesion, curso, ahora=ahora_utc())
    for entrega in entregas:
        if entrega is None or entrega.canvas_assignment_id is None:
            continue
        try:
            publicacion_repo.reconciliar(sesion, curso, entrega)
        except publicacion_repo.RechazoPublicacion:
            return  # sin credencial operativa: nada que leer hasta que vuelva
