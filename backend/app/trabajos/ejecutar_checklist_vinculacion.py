"""Trabajo `ejecutar_checklist_vinculacion` (SPEC 04 S4.7.1).

`POST /api/cursos/{id}/verificacion` (y su variante de un solo item) generan
el `ejecucion_id` y lo dejan en el `payload` antes de encolar, para poder
responder `202` con el mismo id que despues se sondea.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.adaptadores import verificacion_repo
from app.adaptadores.cliente_canvas import crear_cliente_canvas
from app.adaptadores.cliente_github import crear_cliente_github_desde_config
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Trabajo
from app.infraestructura.cifrado import Llavero
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar


@registrar("ejecutar_checklist_vinculacion")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    curso = sesion.query(Curso).filter(Curso.id == trabajo.curso_id).one()
    settings = obtener_configuracion()

    cliente_canvas = crear_cliente_canvas(
        modo=settings.canvas_modo, canvas_base_url=curso.canvas_base_url or settings.canvas_base_url
    )
    cliente_github = crear_cliente_github_desde_config(settings)
    llavero = Llavero(settings.llavero_cifrado(), settings.app_encryption_key_activa)

    solo_items_raw = trabajo.payload.get("solo_items")
    solo_items = tuple(solo_items_raw) if solo_items_raw else None

    verificacion_repo.ejecutar_checklist(
        sesion,
        cliente_canvas,
        cliente_github,
        llavero,
        curso=curso,
        ejecucion_id=uuid.UUID(trabajo.payload["ejecucion_id"]),
        solo_items=solo_items,
    )
