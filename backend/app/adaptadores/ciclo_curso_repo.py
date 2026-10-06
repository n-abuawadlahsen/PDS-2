"""Archivo reversible del curso y archivo remoto optativo, con cinco guardas."""

import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.adaptadores import archivado_repo, bitacora_repo, trabajos_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_aprovisionamiento import FechaEfectiva, Repositorio
from app.adaptadores.modelos_correccion import Correccion
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_infraestructura import Bitacora, Trabajo, TrabajoPeriodico
from app.adaptadores.modelos_tarea import Entrega, Tarea
from app.adaptadores.modelos_version import VersionEntrega


def previsualizar(bd: Session, curso_id: uuid.UUID) -> dict[str, Any]:
    curso = bd.get(Curso, curso_id)
    assert curso is not None
    versiones = (
        bd.query(VersionEntrega.id)
        .filter(
            VersionEntrega.entrega_id == FechaEfectiva.entrega_id,
            VersionEntrega.sujeto_id == FechaEfectiva.sujeto_id,
            VersionEntrega.vigente.is_(True),
        )
        .exists()
    )
    capturas = [
        {
            "entrega_id": str(e.id),
            "entrega": e.nombre,
            "sujeto_id": str(f.sujeto_id),
            "cierre": f.due_at_utc,
        }
        for f, e in bd.query(FechaEfectiva, Entrega)
        .join(Entrega, Entrega.id == FechaEfectiva.entrega_id)
        .filter(Entrega.curso_id == curso_id, FechaEfectiva.estado == "VIGENTE", ~versiones)
        .order_by(Entrega.orden, FechaEfectiva.sujeto_id)
    ]
    pendientes = (
        bd.query(Repositorio)
        .filter(
            Repositorio.curso_id == curso_id,
            Repositorio.github_repo_id.isnot(None),
            Repositorio.estado.notin_(archivado_repo.TERMINALES),
        )
        .all()
    )
    bloqueos = []
    for tarea in bd.query(Tarea).filter(Tarea.id.in_({r.tarea_id for r in pendientes})):
        resultado = archivado_repo.evaluar(bd, curso, tarea, ahora=ahora_utc())
        if tarea.estado == "BORRADOR" or not resultado.permitido:
            bloqueos.append(
                {
                    "tarea_id": str(tarea.id),
                    "tarea": tarea.nombre,
                    "motivo": resultado.fallida.motivo
                    if resultado.fallida
                    else "La tarea está en borrador.",
                }
            )
    archivo = _ultimo_archivo(bd, curso_id)
    ids = (archivo.despues or {}).get("trabajos_archivado", []) if archivo else []
    return {
        "repositorios": bd.query(Repositorio.id).filter_by(curso_id=curso_id).count(),
        "sin_capturar": len(capturas),
        "capturas_pendientes": capturas,
        "repositorios_por_archivar": len(pendientes),
        "bloqueos": bloqueos,
        "trabajos_archivado": ids if curso.estado == "ARCHIVADO" else [],
    }


def _ultimo_archivo(bd: Session, curso_id: uuid.UUID) -> Bitacora | None:
    return (
        bd.query(Bitacora)
        .filter_by(curso_id=curso_id, accion="CURSO_ARCHIVADO")
        .order_by(Bitacora.creado_en.desc(), Bitacora.id.desc())
        .first()
    )


def permite_trabajo_archivado(bd: Session, curso: Curso, trabajo: Trabajo) -> bool:
    """Sólo la tanda explícitamente consentida puede escribir el archivo remoto."""
    if trabajo.tipo != archivado_repo.TIPO_TRABAJO or trabajo.payload.get("accion") != "archivar":
        return False
    archivo = _ultimo_archivo(bd, curso.id)
    if not archivo or str(trabajo.id) not in (archivo.despues or {}).get("trabajos_archivado", []):
        return False
    return (
        bd.query(MembresiaCurso.id)
        .filter_by(
            curso_id=curso.id, usuario_id=archivo.actor_usuario_id, estado="ACTIVA", rol="PROFESOR"
        )
        .first()
        is not None
    )


def archivar(
    bd: Session, *, curso_id: uuid.UUID, actor: MembresiaCurso, archivar_repositorios: bool = False
) -> Curso:
    curso = bd.query(Curso).filter_by(id=curso_id).with_for_update().one()
    if curso.estado == "ARCHIVADO":
        return curso
    if (
        bd.query(Trabajo.id).filter_by(curso_id=curso_id, estado="EN_CURSO").first()
        or bd.query(Correccion.id)
        .join(Entrega, Entrega.id == Correccion.entrega_id)
        .filter(Entrega.curso_id == curso_id, Correccion.estado == "PUBLICANDO")
        .first()
    ):
        raise HTTPException(
            status_code=409,
            detail="Hay procesos o publicaciones en curso. Espera a que terminen para archivar.",
        )
    if archivar_repositorios:
        vista = previsualizar(bd, curso_id)
        if vista["bloqueos"]:
            raise HTTPException(
                status_code=409,
                detail={
                    "codigo": "ARCHIVADO_BLOQUEADO",
                    "motivo": "Revisa el cierre de las tareas o desmarca los repositorios.",
                    "bloqueos": vista["bloqueos"],
                },
            )
    periodicos = bd.query(TrabajoPeriodico).filter_by(curso_id=curso_id, activo=True).all()
    antes = {
        "estado": curso.estado,
        "modo_escritura": curso.modo_escritura,
        "comunicaciones_salientes": curso.comunicaciones_salientes,
        "periodicos_activos": [str(p.id) for p in periodicos],
    }
    for periodico in periodicos:
        periodico.activo = False
    for trabajo in bd.query(Trabajo).filter(
        Trabajo.curso_id == curso_id, Trabajo.estado.in_(("PENDIENTE", "REINTENTAR"))
    ):
        trabajos_repo.cancelar(bd, trabajo, motivo="CURSO_ARCHIVADO")
    curso.estado = "ARCHIVADO"
    curso.comunicaciones_salientes = "SUSPENDIDAS"
    curso.modo_escritura = "SOLO_LECTURA"
    curso.actualizado_en = ahora_utc()
    trabajos_archivado = []
    if archivar_repositorios:
        tanda = str(uuid.uuid4())
        for tarea in bd.query(Tarea).filter_by(curso_id=curso_id):
            repos = archivado_repo.archivables(bd, tarea.id)
            if not repos:
                continue
            archivado_repo.solicitar(
                bd,
                curso,
                tarea,
                accion=archivado_repo.ARCHIVAR,
                repositorios=repos,
                actor_usuario_id=actor.usuario_id,
                confirmaciones={"archivo_curso": tanda},
            )
        trabajos_archivado = [
            str(t.id)
            for t in bd.query(Trabajo).filter(
                Trabajo.curso_id == curso_id,
                Trabajo.payload["archivo_curso"].astext == tanda,
            )
        ]
    bitacora_repo.registrar(
        bd,
        accion="CURSO_ARCHIVADO",
        entidad="curso",
        entidad_id=str(curso_id),
        curso_id=curso_id,
        actor_usuario_id=actor.usuario_id,
        antes=antes,
        despues={
            "estado": "ARCHIVADO",
            "trabajos_archivado": trabajos_archivado,
            "archivar_repositorios": archivar_repositorios,
        },
    )
    return curso


def desarchivar(bd: Session, *, curso_id: uuid.UUID, actor: MembresiaCurso) -> Curso:
    curso = bd.query(Curso).filter_by(id=curso_id).with_for_update().one()
    if curso.estado != "ARCHIVADO":
        return curso
    if bd.query(Trabajo.id).filter_by(curso_id=curso_id, estado="EN_CURSO").first():
        raise HTTPException(
            status_code=409, detail="Espera a que termine el archivado de repositorios."
        )
    archivo = _ultimo_archivo(bd, curso_id)
    if archivo is None or not archivo.antes:
        raise HTTPException(
            status_code=409,
            detail="No hay configuración anterior registrada para restaurar este curso.",
        )
    antes = archivo.antes
    for trabajo in bd.query(Trabajo).filter(
        Trabajo.curso_id == curso_id,
        Trabajo.estado.in_(("PENDIENTE", "REINTENTAR")),
    ):
        trabajos_repo.cancelar(bd, trabajo, motivo="CURSO_DESARCHIVADO")
    curso.estado = antes["estado"]
    if curso.estado == "ACTIVO":
        from app.adaptadores import canvas_repo

        if canvas_repo.obtener_credencial_operativa(bd, curso_id) is None:
            curso.estado = "CANVAS_DESVINCULADO"
        elif curso.github_installation_id is None:
            curso.estado = "GITHUB_DESVINCULADO"
    curso.modo_escritura = antes["modo_escritura"]
    curso.comunicaciones_salientes = antes["comunicaciones_salientes"]
    curso.actualizado_en = ahora_utc()
    for periodico in bd.query(TrabajoPeriodico).filter(
        TrabajoPeriodico.curso_id == curso_id,
        TrabajoPeriodico.id.in_([uuid.UUID(p) for p in antes["periodicos_activos"]]),
    ):
        periodico.activo = True
        periodico.proxima_ejecucion = ahora_utc()
    bitacora_repo.registrar(
        bd,
        accion="CURSO_DESARCHIVADO",
        entidad="curso",
        entidad_id=str(curso_id),
        curso_id=curso_id,
        actor_usuario_id=actor.usuario_id,
        antes={"estado": "ARCHIVADO"},
        despues={"estado": curso.estado},
    )
    return curso
