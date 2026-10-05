"""Recuperación transaccional al renovar una credencial operativa (SPEC 04 §4.10)."""

from sqlalchemy.orm import Session

from app.adaptadores import bitacora_repo, trabajos_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_aprovisionamiento import MensajeSaliente
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_github import VerificacionVinculacion
from app.adaptadores.modelos_identidad import Usuario
from app.adaptadores.modelos_infraestructura import Incidencia, Trabajo
from app.dominio.verificacion import CATALOGO_VERIFICACION
from app.infraestructura.identificadores import uuid7

# SPEC 05 §5.7. No se invalidan las capacidades de GitHub ni el historial.
_CAPACIDADES_CANVAS = {
    "PUBLICAR_NOTA", "PUBLICAR_ANUNCIO", "BORRAR_ANUNCIO", "ENVIAR_MENSAJE",
    "COMENTAR_ENTREGA", "CREAR_TAREA", "EDITAR_TAREA_REGISTRO", "LEER_ROSTER",
    "LEER_GRUPOS", "LEER_FECHAS", "LEER_SUBMISSIONS", "LEER_GRADEABLE",
}


def al_renovar_operativa(bd: Session, *, curso: Curso, usuario: Usuario) -> None:
    ahora = ahora_utc()
    invalidacion = uuid7()
    items = [item.id for item in CATALOGO_VERIFICACION if item.id not in {"14", "18"}]
    for item in items:
        bd.add(VerificacionVinculacion(
            curso_id=curso.id, ejecucion_id=invalidacion, item=item, origen="CHECKLIST",
            resultado="NO_VERIFICADO", detalle={"motivo": "CREDENCIAL_CAMBIADA"},
            ejecutada_en=ahora, ejecutada_por=usuario.id,
        ))
    capacidades = bd.query(VerificacionVinculacion.capacidad).filter(
        VerificacionVinculacion.curso_id == curso.id,
        VerificacionVinculacion.origen == "RUNTIME",
        VerificacionVinculacion.capacidad.in_(_CAPACIDADES_CANVAS),
    ).distinct().all()
    for (capacidad,) in capacidades:
        bd.add(VerificacionVinculacion(
            curso_id=curso.id, ejecucion_id=invalidacion, origen="RUNTIME", capacidad=capacidad,
            resultado="NO_VERIFICADO", detalle={"motivo": "CREDENCIAL_CAMBIADA"},
            ejecutada_en=ahora, ejecutada_por=usuario.id,
        ))
    curso.via_anuncio_seccion = "NO_VERIFICADO"
    if curso.estado == "CANVAS_DESVINCULADO":
        curso.estado = "VINCULANDO"
    # Sólo lo que esperaba una credencial: no se saltan bloqueos de permisos ni límites.
    trabajos = bd.query(Trabajo).filter_by(curso_id=curso.id, estado="ESPERANDO_CREDENCIAL").all()
    for trabajo in trabajos:
        trabajo.estado = "PENDIENTE"
        trabajo.proximo_intento_en = None
        trabajo.tomado_en = None
        trabajo.tomado_por = None
    mensajes = bd.query(MensajeSaliente).filter(
        MensajeSaliente.curso_id == curso.id,
        MensajeSaliente.estado == "ESPERANDO_CREDENCIAL",
        MensajeSaliente.canal.like("CANVAS_%"),
    ).all()
    for mensaje in mensajes:
        mensaje.estado = "PENDIENTE"
        mensaje.motivo_estado = None
        mensaje.tomado_en = None
        mensaje.tomado_por = None
    for incidencia in bd.query(Incidencia).filter_by(
        curso_id=curso.id, tipo="CANVAS_CREDENCIAL_INVALIDA", abierta=True
    ):
        incidencia.abierta = False
        incidencia.resuelta_en = ahora
    ejecucion = uuid7()
    trabajos_repo.encolar(
        bd, tipo="ejecutar_checklist_vinculacion", curso_id=curso.id, max_intentos=1,
        clave_idempotencia=f"checklist:{curso.id}:{ejecucion}",
        payload={"ejecucion_id": str(ejecucion),
                 "solo_items": [item for item in items if item not in {"5-bis", "17-bis"}]},
    )
    bitacora_repo.registrar(
        bd, accion="CREDENCIAL_CANVAS_RENOVADA", entidad="curso", entidad_id=str(curso.id),
        curso_id=curso.id, actor_usuario_id=usuario.id,
        despues={"titular_usuario_id": str(usuario.id), "verificacion_id": str(ejecucion),
                 "trabajos_reanudados": len(trabajos), "mensajes_reanudados": len(mensajes)},
    )
