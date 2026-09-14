"""Crear/restaurar la tarea de registro de GitHub en Canvas (SPEC 07 S7.4.1;
SPEC 05 S5.5.1 escritura sincrona #4).

Las seis escrituras sincronas comparten contrato (S5.5.1): lectura antes del
efecto (aqui, `curso.registro_estado`), resultado mostrado en pantalla, y
registro en bitacora -- la escritura misma nunca envia una comunicacion al
estudiante. El tope duro de 20s y su caida a un trabajo de cola lo aplica el
propio `ClienteCanvasReal` (timeout) mas el llamador (`api/rutas`), que
encola `crear_registro_github` si la llamada sincrona se agota.
"""

from __future__ import annotations

import uuid
from datetime import timedelta

from sqlalchemy.orm import Session

from app.adaptadores.base import ahora_utc
from app.adaptadores.bitacora_repo import registrar as registrar_bitacora
from app.adaptadores.cliente_canvas import ClienteCanvas
from app.adaptadores.modelos_curso import Curso
from app.dominio.estados import EstadoTareaRegistro
from app.dominio.registro_canvas import NOMBRE_TAREA_REGISTRO, ConfiguracionTareaRegistro

_DESCRIPCION_POR_DEFECTO = (
    "<p>Entrega el enlace a tu perfil de GitHub (por ejemplo "
    "<code>https://github.com/tu-usuario</code>) o tu usuario. "
    "Vas a recibir un comentario en esta misma entrega confirmando que "
    "quedo registrado, o pidiendote que corrijas algo.</p>"
)
_DIAS_HASTA_CIERRE = 90


def _configuracion_canonica(descripcion_html: str | None) -> ConfiguracionTareaRegistro:
    return ConfiguracionTareaRegistro(
        nombre=NOMBRE_TAREA_REGISTRO,
        descripcion_html=descripcion_html or _DESCRIPCION_POR_DEFECTO,
        submission_types="online_text_entry",
        points_possible=0.0,
        omit_from_final_grade=True,
        published=True,
        due_at_iso=(ahora_utc() + timedelta(days=_DIAS_HASTA_CIERRE)).isoformat(),
        grading_type="points",
    )


def crear_tarea_registro(
    bd: Session,
    cliente: ClienteCanvas,
    token: str,
    *,
    curso: Curso,
    actor_usuario_id: uuid.UUID,
    descripcion_html: str | None = None,
) -> Curso:
    """S7.1 correccion: exige `curso.administrar` (lo comprueba el llamador).
    Lectura antes del efecto: si ya esta `ACTIVA`, no hace nada (idempotente,
    S4.5.5 mismo patron)."""
    assert curso.canvas_course_id is not None
    if curso.registro_estado == EstadoTareaRegistro.ACTIVA.value:
        return curso

    config = _configuracion_canonica(descripcion_html)
    creada = cliente.crear_tarea_registro(token, curso.canvas_course_id, config)

    curso.canvas_assignment_id_registro = creada.canvas_assignment_id
    curso.registro_creado_en = ahora_utc()
    curso.registro_creado_por = actor_usuario_id
    curso.registro_estado = EstadoTareaRegistro.ACTIVA.value
    curso.registro_huella_config = config.huella()
    curso.actualizado_en = ahora_utc()
    bd.flush()

    registrar_bitacora(
        bd,
        accion="TAREA_REGISTRO_CREADA",
        entidad="curso",
        entidad_id=str(curso.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=curso.id,
        despues={"canvas_assignment_id": creada.canvas_assignment_id},
    )
    return curso


def restaurar_tarea_registro(
    bd: Session, cliente: ClienteCanvas, token: str, *, curso: Curso, actor_usuario_id: uuid.UUID
) -> Curso:
    """`DESAPARECIDA` -> se crea una tarea nueva (la vieja ya no existe en
    Canvas). `ALTERADA` -> se reescribe la configuracion canonica sobre la
    misma tarea. Cualquier otro estado no hace nada."""
    assert curso.canvas_course_id is not None
    if curso.registro_estado == EstadoTareaRegistro.DESAPARECIDA.value:
        curso.registro_estado = EstadoTareaRegistro.NO_CREADA.value
        return crear_tarea_registro(
            bd, cliente, token, curso=curso, actor_usuario_id=actor_usuario_id
        )

    if curso.registro_estado == EstadoTareaRegistro.ALTERADA.value:
        assert curso.canvas_assignment_id_registro is not None
        config = _configuracion_canonica(None)
        cliente.actualizar_tarea_registro(
            token, curso.canvas_course_id, curso.canvas_assignment_id_registro, config
        )
        curso.registro_estado = EstadoTareaRegistro.ACTIVA.value
        curso.registro_huella_config = config.huella()
        curso.actualizado_en = ahora_utc()
        bd.flush()
        registrar_bitacora(
            bd,
            accion="TAREA_REGISTRO_RESTAURADA",
            entidad="curso",
            entidad_id=str(curso.id),
            actor_usuario_id=actor_usuario_id,
            curso_id=curso.id,
        )
    return curso


def verificar_configuracion(
    bd: Session, cliente: ClienteCanvas, token: str, *, curso: Curso
) -> None:
    """S7.2.3 `registro_huella_config`: se llama en cada ciclo de
    `recolector_mapeos` para detectar `ALTERADA`/`DESAPARECIDA`. Un solo tipo
    de incidencia, `TAREA_REGISTRO_ALTERADA`, con severidad derivada del
    detalle (S7.1 correccion de precedencia) -- se abre desde el llamador
    (job), no aqui, para mantener este modulo sin dependencia de
    `incidencia_repo` en el camino feliz."""
    assert curso.canvas_course_id is not None
    if (
        curso.registro_estado != EstadoTareaRegistro.ACTIVA.value
        or curso.canvas_assignment_id_registro is None
    ):
        return
    config_actual = cliente.obtener_configuracion_tarea(
        token, curso.canvas_course_id, curso.canvas_assignment_id_registro
    )
    if config_actual is None:
        curso.registro_estado = EstadoTareaRegistro.DESAPARECIDA.value
        bd.flush()
        return
    if config_actual.huella() != curso.registro_huella_config:
        curso.registro_estado = EstadoTareaRegistro.ALTERADA.value
        bd.flush()
