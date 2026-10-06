"""Identidades Canvas: coincidencia informativa y confirmación transaccional.

La persona con historia conserva su UUID. La fila nueva sin evidencia queda
como alias retirado. Los snapshots de versiones y los mapeos no se reescriben.
"""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.adaptadores import bitacora_repo, incidencia_repo, trabajos_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.correccion_repo import RechazoCorreccion
from app.adaptadores.modelos_aprovisionamiento import Repositorio, Sujeto
from app.adaptadores.modelos_correccion import Correccion
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_infraestructura import Bitacora, Incidencia
from app.adaptadores.modelos_mapeo import MapeoGithub
from app.adaptadores.modelos_padron import Estudiante, Grupo, Matricula, PertenenciaGrupo
from app.adaptadores.modelos_tarea import VisibilidadEntrega
from app.adaptadores.modelos_version import VersionEntrega


def coincidencias(anterior: Estudiante, nuevo: Estudiante) -> list[str]:
    return [
        campo
        for campo in ("login_id", "sis_user_id")
        if getattr(anterior, campo) and getattr(anterior, campo) == getattr(nuevo, campo)
    ]


def detectar(bd: Session, curso: Curso) -> int:
    estudiantes = bd.query(Estudiante).filter_by(curso_id=curso.id, fusionada_en_id=None).all()
    retirados = [e for e in estudiantes if e.estado == "RETIRADO" and e.retirado_en is not None]
    abiertos = 0
    for nuevo in estudiantes:
        if nuevo.estado not in ("ACTIVO", "INVITADO"):
            continue
        candidatos = [
            {
                "estudiante_id": str(e.id),
                "nombre": e.nombre,
                "canvas_user_id": e.canvas_user_id,
                "coincidencias": coincidencias(e, nuevo),
            }
            for e in retirados
            if e.id != nuevo.id
            and e.ultima_vista_en <= nuevo.primera_vista_en
            and coincidencias(e, nuevo)
        ]
        if candidatos:
            incidencia_repo.abrir_o_actualizar(
                bd,
                tipo="POSIBLE_FUSION_CANVAS",
                severidad="ADVERTENCIA",
                sujeto_tipo="ESTUDIANTE",
                sujeto_id=nuevo.id,
                curso_id=curso.id,
                detalle={"nuevo_id": str(nuevo.id), "candidatos": candidatos},
            )
            abiertos += 1
    return abiertos


def _motivo_conflicto(bd: Session, nuevo: Estudiante, anterior: Estudiante) -> str | None:
    ids = [s for (s,) in bd.query(Sujeto.id).filter_by(estudiante_id=nuevo.id)]
    if (
        bd.query(Repositorio.id)
        .filter(
            Repositorio.sujeto_id.in_(ids),
            (Repositorio.github_repo_id.isnot(None)) | (Repositorio.estado == "CREANDO"),
        )
        .first()
    ):
        return (
            "La identidad nueva tiene un repositorio creado o en creación. Revisa sus evidencias."
        )
    if bd.query(VersionEntrega.id).filter(VersionEntrega.sujeto_id.in_(ids)).first():
        return "La identidad nueva tiene versiones capturadas. Revisa ambos historiales."
    if (
        bd.query(Correccion.id)
        .filter(
            Correccion.sujeto_id.in_(ids),
            (Correccion.nota_local.isnot(None))
            | (Correccion.comentario.isnot(None))
            | (Correccion.rubrica_local.isnot(None))
            | (Correccion.intentos > 0)
            | (Correccion.estado.notin_(("SIN_CORRECTOR", "ASIGNADA"))),
        )
        .first()
    ):
        return "La identidad nueva tiene correcciones iniciadas. Revisa ambos historiales."
    if (
        bd.query(MapeoGithub.id)
        .filter(
            MapeoGithub.estudiante_id == nuevo.id,
            MapeoGithub.estado.notin_(("SIN_DATO", "SUPERSEDIDO")),
        )
        .first()
    ):
        return "La identidad nueva declaró una cuenta GitHub. Revisa ambas cuentas."
    if (
        bd.query(Correccion.id)
        .join(Sujeto, Sujeto.id == Correccion.sujeto_id)
        .filter(Sujeto.estudiante_id == anterior.id, Correccion.estado == "PUBLICANDO")
        .first()
    ):
        return "Hay una publicación en curso para la identidad anterior. Espera a que termine."
    return None


def listar(bd: Session, curso_id: uuid.UUID) -> list[dict[str, Any]]:
    resultado = []
    for incidencia in (
        bd.query(Incidencia)
        .filter_by(curso_id=curso_id, tipo="POSIBLE_FUSION_CANVAS", abierta=True)
        .order_by(Incidencia.creado_en)
    ):
        nuevo = bd.get(Estudiante, incidencia.sujeto_id)
        if not nuevo or nuevo.fusionada_en_id or nuevo.estado not in ("ACTIVO", "INVITADO"):
            continue
        candidatos = []
        for candidato in incidencia.detalle.get("candidatos", []):
            anterior = bd.get(Estudiante, uuid.UUID(candidato["estudiante_id"]))
            if not anterior or anterior.estado != "RETIRADO" or anterior.fusionada_en_id:
                continue
            candidatos.append(
                {
                    **candidato,
                    "motivo_bloqueo": _motivo_conflicto(bd, nuevo, anterior),
                    "repositorios_conservados": bd.query(Repositorio.id)
                    .join(Sujeto, Sujeto.id == Repositorio.sujeto_id)
                    .filter(Sujeto.estudiante_id == anterior.id)
                    .count(),
                    "versiones_conservadas": bd.query(VersionEntrega.id)
                    .join(Sujeto, Sujeto.id == VersionEntrega.sujeto_id)
                    .filter(Sujeto.estudiante_id == anterior.id)
                    .count(),
                }
            )
        if candidatos:
            resultado.append(
                {
                    "incidencia_id": str(incidencia.id),
                    "nuevo_id": str(nuevo.id),
                    "nombre": nuevo.nombre,
                    "canvas_user_id": nuevo.canvas_user_id,
                    "candidatos": candidatos,
                }
            )
    return resultado


def confirmar(
    bd: Session,
    *,
    curso_id: uuid.UUID,
    incidencia_id: uuid.UUID,
    anterior_id: uuid.UUID,
    actor: MembresiaCurso,
) -> Estudiante:
    incidencia = (
        bd.query(Incidencia)
        .filter_by(id=incidencia_id, curso_id=curso_id, tipo="POSIBLE_FUSION_CANVAS")
        .with_for_update()
        .one_or_none()
    )
    if not incidencia or not incidencia.sujeto_id:
        raise RechazoCorreccion("No existe esa propuesta de fusión.", codigo=404)
    nuevo = bd.get(Estudiante, incidencia.sujeto_id)
    anterior = bd.get(Estudiante, anterior_id)
    if not nuevo or not anterior or anterior.curso_id != curso_id or anterior.id == nuevo.id:
        raise RechazoCorreccion("Las dos identidades deben pertenecer a este curso.", codigo=404)
    if nuevo.fusionada_en_id == anterior.id:
        return anterior
    if (
        not incidencia.abierta
        or anterior.estado != "RETIRADO"
        or anterior.fusionada_en_id
        or nuevo.fusionada_en_id
        or nuevo.estado not in ("ACTIVO", "INVITADO")
        or not coincidencias(anterior, nuevo)
    ):
        raise RechazoCorreccion("La propuesta ya no coincide con el padrón actual.")
    if str(anterior.id) not in {
        c["estudiante_id"] for c in incidencia.detalle.get("candidatos", [])
    }:
        raise RechazoCorreccion("Esta identidad anterior no era candidata de la propuesta.")
    conflicto = _motivo_conflicto(bd, nuevo, anterior)
    if conflicto:
        raise RechazoCorreccion(conflicto)
    ahora = ahora_utc()
    canvas_anterior, canvas_nuevo = anterior.canvas_user_id, nuevo.canvas_user_id
    # El índice Canvas es inmediato. La clave transitoria sólo existe dentro
    # de esta transacción, antes de intercambiar las dos claves positivas.
    anterior.canvas_user_id = -canvas_nuevo
    bd.flush()
    nuevo.canvas_user_id = canvas_anterior
    bd.flush()
    anterior.canvas_user_id = canvas_nuevo
    anterior.estado = nuevo.estado
    for campo in (
        "nombre",
        "nombre_ordenable",
        "login_id",
        "sis_user_id",
        "email",
        "uuid",
        "past_uuid",
        "group_ids_canvas",
        "ultima_vista_en",
    ):
        setattr(anterior, campo, getattr(nuevo, campo))
    anterior.ciclos_ausente = 0
    anterior.retirado_en = None
    nuevo.fusionada_en_id = anterior.id
    nuevo.estado, nuevo.retirado_en = "RETIRADO", ahora
    for m in bd.query(Matricula).filter_by(estudiante_id=anterior.id):
        m.activa = False
    for m in bd.query(Matricula).filter_by(estudiante_id=nuevo.id):
        m.estudiante_id = anterior.id
    for p in bd.query(PertenenciaGrupo).filter_by(estudiante_id=anterior.id, activa_hasta=None):
        p.activa, p.activa_hasta = False, ahora
    for p in bd.query(PertenenciaGrupo).filter_by(estudiante_id=nuevo.id, activa_hasta=None):
        previa = (
            bd.query(PertenenciaGrupo)
            .filter_by(estudiante_id=anterior.id, grupo_id=p.grupo_id)
            .one_or_none()
        )
        if previa is None:
            p.estudiante_id = anterior.id
        else:
            previa.workflow_state, previa.activa = p.workflow_state, p.activa
            previa.activa_hasta, previa.ciclos_ausente = None, 0
            previa.activa_desde = p.activa_desde
            previa.sincronizado_en = ahora
            p.activa, p.activa_hasta = False, ahora
    for grupo in bd.query(Grupo).filter_by(lider_estudiante_id=nuevo.id):
        grupo.lider_estudiante_id = anterior.id
    for visibilidad in bd.query(VisibilidadEntrega).filter_by(estudiante_id=nuevo.id):
        vis_previa = bd.get(VisibilidadEntrega, (visibilidad.entrega_id, anterior.id))
        if vis_previa is None:
            bd.add(
                VisibilidadEntrega(
                    entrega_id=visibilidad.entrega_id,
                    estudiante_id=anterior.id,
                    visible=visibilidad.visible,
                    origen=visibilidad.origen,
                    sincronizado_en=ahora,
                )
            )
        else:
            vis_previa.visible = visibilidad.visible
            vis_previa.sincronizado_en = ahora
        visibilidad.visible = False
    for sujeto in bd.query(Sujeto).filter_by(estudiante_id=nuevo.id):
        sujeto.activo, sujeto.desactivado_en = False, ahora
        sujeto.motivo_desactivacion = "SIN_MATRICULA_ACTIVA"
    incidencia.abierta, incidencia.resuelta_en = False, ahora
    bitacora_repo.registrar(
        bd,
        accion="FUSION_CANVAS_CONFIRMADA",
        entidad="estudiante",
        entidad_id=str(anterior.id),
        actor_usuario_id=actor.usuario_id,
        curso_id=curso_id,
        antes={
            "anterior_id": str(anterior.id),
            "nuevo_id": str(nuevo.id),
            "canvas_user_id_anterior": canvas_anterior,
            "canvas_user_id_nuevo": canvas_nuevo,
        },
        despues={
            "estudiante_id": str(anterior.id),
            "canvas_user_id": canvas_nuevo,
            "alias_id": str(nuevo.id),
        },
    )
    for tipo in ("revalidar_mapeos", "materializar_sujetos", "sync_grupos", "sync_tareas_y_fechas"):
        trabajos_repo.encolar(
            bd,
            tipo=tipo,
            curso_id=curso_id,
            max_intentos=3,
            clave_idempotencia=f"fusion:{incidencia.id}:{tipo}",
        )
    bd.flush()
    return anterior


def historial(bd: Session, curso_id: uuid.UUID) -> list[dict[str, Any]]:
    return [
        {
            "fecha": b.creado_en,
            "actor_usuario_id": str(b.actor_usuario_id),
            "antes": b.antes,
            "despues": b.despues,
        }
        for b in bd.query(Bitacora)
        .filter_by(curso_id=curso_id, accion="FUSION_CANVAS_CONFIRMADA")
        .order_by(Bitacora.creado_en.desc())
    ]
