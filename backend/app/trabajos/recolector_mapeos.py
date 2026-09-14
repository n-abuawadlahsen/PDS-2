"""Trabajo `recolector_mapeos` (SPEC 07 S7.4.1). Cerrojo 1, 4 reintentos.

Lee las entregas de la tarea de registro, procesa cada una por la via 1
(S7.4), y responde siempre con un comentario en la misma entrega (S7.4.6).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.adaptadores import (
    canvas_repo,
    incidencia_repo,
    mapeo_github_repo,
    registro_github_repo,
    tareas_repo,
)
from app.adaptadores.bitacora_repo import registrar as registrar_bitacora
from app.adaptadores.cliente_canvas import crear_cliente_canvas
from app.adaptadores.cliente_github import crear_cliente_github_desde_config
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Trabajo
from app.adaptadores.modelos_mapeo import CuentaGithub
from app.adaptadores.modelos_padron import Estudiante
from app.dominio.estados import EstadoMapeoGithub, EstadoTareaRegistro
from app.dominio.mapeo_github import texto_comentario_resultado
from app.infraestructura.cerrojos import cerrojo_canvas
from app.infraestructura.cifrado import Llavero
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar

# S7.1 correccion (RG-189): "un solo tipo, TAREA_REGISTRO_ALTERADA, con
# severidad derivada del detalle". El SPEC no fija literalmente el mapeo
# estado->severidad; se interpreta que `DESAPARECIDA` (nadie puede entregar)
# es BLOQUEANTE y `ALTERADA` (la tarea sigue viva, solo cambio su config) es
# solo ADVERTENCIA.
_SEVERIDAD_POR_ESTADO_REGISTRO = {
    EstadoTareaRegistro.DESAPARECIDA.value: "BLOQUEANTE",
    EstadoTareaRegistro.ALTERADA.value: "ADVERTENCIA",
}


def _sincronizar_incidencia_tarea_registro(sesion: Session, curso: Curso) -> None:
    if curso.registro_estado in _SEVERIDAD_POR_ESTADO_REGISTRO:
        incidencia_repo.abrir_o_actualizar(
            sesion,
            tipo="TAREA_REGISTRO_ALTERADA",
            severidad=_SEVERIDAD_POR_ESTADO_REGISTRO[curso.registro_estado],
            sujeto_tipo="CURSO",
            curso_id=curso.id,
            detalle={"registro_estado": curso.registro_estado},
        )
    else:
        incidencia_repo.cerrar(sesion, tipo="TAREA_REGISTRO_ALTERADA", curso_id=curso.id)


@registrar("recolector_mapeos")
def ejecutar(sesion: Session, trabajo: Trabajo) -> None:
    assert trabajo.curso_id is not None
    curso = sesion.query(Curso).filter(Curso.id == trabajo.curso_id).one()
    if curso.canvas_course_id is None:
        return
    credencial = canvas_repo.obtener_credencial_operativa(sesion, curso.id)
    if credencial is None:
        return

    settings = obtener_configuracion()
    llavero = Llavero(settings.llavero_cifrado(), settings.app_encryption_key_activa)
    token = canvas_repo.descifrar_token(llavero, credencial)
    cliente_canvas = crear_cliente_canvas(
        modo=settings.canvas_modo, canvas_base_url=curso.canvas_base_url or settings.canvas_base_url
    )
    cliente_github = crear_cliente_github_desde_config(settings)

    with cerrojo_canvas(sesion, curso.id):
        registro_github_repo.verificar_configuracion(sesion, cliente_canvas, token, curso=curso)
        _sincronizar_incidencia_tarea_registro(sesion, curso)
        if (
            curso.registro_estado != EstadoTareaRegistro.ACTIVA.value
            or curso.canvas_assignment_id_registro is None
        ):
            return

        resultado = cliente_canvas.obtener_entregas_tarea_paginado(
            token, curso.canvas_course_id, curso.canvas_assignment_id_registro
        )
        estudiante_por_canvas_id = {
            e.canvas_user_id: e
            for e in sesion.query(Estudiante).filter(Estudiante.curso_id == curso.id).all()
        }

        for entrega in resultado.items:
            estudiante = estudiante_por_canvas_id.get(entrega.canvas_user_id)
            if estudiante is None:
                # S7.9.9: quien no es estudiante del curso no genera mapeo ni comentario.
                registrar_bitacora(
                    sesion,
                    accion="ENTREGA_REGISTRO_SIN_ESTUDIANTE",
                    entidad="curso",
                    entidad_id=str(curso.id),
                    curso_id=curso.id,
                    despues={"canvas_user_id": entrega.canvas_user_id},
                )
                continue
            if not entrega.body_html:
                continue

            resultado_proc = mapeo_github_repo.procesar_entrega_autoservicio(
                sesion,
                cliente_github,
                curso_id=curso.id,
                estudiante=estudiante,
                texto_html=entrega.body_html,
            )
            if resultado_proc is None:
                continue  # sin cambios desde la ultima vez; no se vuelve a comentar

            login_canonico = None
            if (
                resultado_proc.mapeo.estado == EstadoMapeoGithub.VIGENTE.value
                and resultado_proc.mapeo.cuenta_github_id
            ):
                cuenta = (
                    sesion.query(CuentaGithub)
                    .filter(CuentaGithub.id == resultado_proc.mapeo.cuenta_github_id)
                    .one_or_none()
                )
                login_canonico = cuenta.login if cuenta else None

            comentario = texto_comentario_resultado(
                EstadoMapeoGithub(resultado_proc.mapeo.estado), login_canonico=login_canonico
            )
            cliente_canvas.comentar_entrega(
                token,
                curso.canvas_course_id,
                curso.canvas_assignment_id_registro,
                entrega.canvas_user_id,
                comentario,
            )

    # S8.7.1: un mapeo que pasa a VIGENTE dispara su repositorio por evento,
    # sin esperar al barrido de 5 minutos (CA-8.7-02).
    tareas_repo.encolar_materializacion(sesion, curso_id=curso.id)
