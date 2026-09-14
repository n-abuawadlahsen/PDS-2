"""DTOs y huella de configuracion de la tarea de registro de GitHub
(SPEC 07 S7.2.3, S7.4.1). Sin I/O.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime

NOMBRE_TAREA_REGISTRO = "Registro de tu cuenta de GitHub"


@dataclass(frozen=True)
class ConfiguracionTareaRegistro:
    """Los ocho campos de configuracion cuya huella detecta si alguien alteró
    la tarea en Canvas (S7.2.3 `registro_huella_config`; S7.1 correccion:
    un solo tipo de incidencia, `TAREA_REGISTRO_ALTERADA`). El conjunto
    exacto de ocho campos no esta enumerado literalmente en el capitulo leido
    hasta ahora: se fija aqui como los que la aplicacion misma escribe al
    crear la tarea (S7.4.1), documentado como decision, no citado letra por
    letra de una tabla del SPEC."""

    nombre: str
    descripcion_html: str
    submission_types: str
    points_possible: float
    omit_from_final_grade: bool
    published: bool
    due_at_iso: str | None
    grading_type: str

    def huella(self) -> bytes:
        contenido = "|".join(
            [
                self.nombre,
                self.descripcion_html,
                self.submission_types,
                str(self.points_possible),
                str(self.omit_from_final_grade),
                str(self.published),
                self.due_at_iso or "",
                self.grading_type,
            ]
        )
        return hashlib.sha256(contenido.encode()).digest()


@dataclass(frozen=True)
class TareaRegistroCreada:
    canvas_assignment_id: int
    configuracion: ConfiguracionTareaRegistro


@dataclass(frozen=True)
class EntregaRegistro:
    """Una fila de `GET /courses/:id/students/submissions?assignment_ids[]=`."""

    canvas_user_id: int
    body_html: str | None
    submitted_at: datetime | None
