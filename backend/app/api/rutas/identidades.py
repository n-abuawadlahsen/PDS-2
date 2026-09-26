"""Identidades de Git no resueltas y su correccion docente (SPEC 10 S10.3.4,
S10.3.6, S10.3.7; Etapa F5).

El correo sale siempre ofuscado del servidor; solo `revelar`, con
`mapeo.editar`, lo entrega completo y deja constancia en la bitacora.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adaptadores import actividad_repo
from app.adaptadores.bitacora_repo import registrar as registrar_bitacora
from app.adaptadores.modelos_actividad import IdentidadGit
from app.adaptadores.modelos_aprovisionamiento import Repositorio
from app.adaptadores.modelos_curso import MembresiaCurso
from app.adaptadores.modelos_padron import Estudiante
from app.api.dependencias import exigir_csrf, obtener_sesion_bd, requiere
from app.dominio.actividad import ofuscar_email
from app.dominio.estados import EstadoIdentidadGit, MotivoExclusionCommit
from app.dominio.permisos import Permiso

router = APIRouter(tags=["identidades"])

AVISO_TERCEROS = (
    "Estos correos vienen de los commits y pueden pertenecer a personas ajenas al curso. "
    "Úsalos sólo para asociar una cuenta y no los compartas fuera de la aplicación."
)


def _repositorio(
    bd: Session, curso_id: uuid.UUID, tarea_id: uuid.UUID, repo_id: uuid.UUID
) -> Repositorio:
    repo = (
        bd.query(Repositorio)
        .filter(
            Repositorio.id == repo_id,
            Repositorio.curso_id == curso_id,
            Repositorio.tarea_id == tarea_id,
        )
        .one_or_none()
    )
    if repo is None:
        raise HTTPException(status_code=404)
    return repo


def _identidad(bd: Session, repo: Repositorio, identidad_id: uuid.UUID) -> IdentidadGit:
    identidad = bd.get(IdentidadGit, identidad_id)
    if identidad is None or identidad.repositorio_id != repo.id:
        raise HTTPException(status_code=404)
    return identidad


class IdentidadSalida(BaseModel):
    id: uuid.UUID
    email: str | None
    nombre_visto: str | None
    estado: str
    estudiante: str | None
    commits_contables: int
    primer_commit_en: datetime | None
    ultimo_commit_en: datetime | None


def _salida(bd: Session, identidad: IdentidadGit) -> IdentidadSalida:
    commits = actividad_repo.commits_de_identidad(bd, identidad)
    contables = [c for c in commits if c.motivo_exclusion == MotivoExclusionCommit.NINGUNO.value]
    estudiante = bd.get(Estudiante, identidad.estudiante_id) if identidad.estudiante_id else None
    fechas = [c.fecha_committer for c in commits]
    return IdentidadSalida(
        id=identidad.id,
        email=ofuscar_email(identidad.email_visto),
        nombre_visto=identidad.nombre_visto_ultimo or identidad.nombre_visto,
        estado=identidad.estado,
        estudiante=estudiante.nombre if estudiante is not None else None,
        commits_contables=len(contables),
        primer_commit_en=min(fechas) if fechas else None,
        ultimo_commit_en=max(fechas) if fechas else None,
    )


@router.get(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/repos/{repo_id}/identidades",
    response_model=list[IdentidadSalida],
)
def listar_identidades(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    repo_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> list[IdentidadSalida]:
    repo = _repositorio(bd, curso_id, tarea_id, repo_id)
    return [
        _salida(bd, i)
        for i in bd.query(IdentidadGit)
        .filter(
            IdentidadGit.repositorio_id == repo.id,
            IdentidadGit.estado != EstadoIdentidadGit.SUPERSEDIDA.value,
        )
        .order_by(IdentidadGit.email_normalizado)
    ]


class ResolverEntrada(BaseModel):
    estudiante_id: uuid.UUID | None = None
    no_es_estudiante: bool = False
    propagar_a: list[uuid.UUID] = []
    confirmacion: str | None = None


@router.post(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/repos/{repo_id}/identidades/{identidad_id}/resolver",
    response_model=IdentidadSalida,
    dependencies=[Depends(exigir_csrf)],
)
def resolver(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    repo_id: uuid.UUID,
    identidad_id: uuid.UUID,
    datos: ResolverEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.MAPEO_EDITAR)),
) -> IdentidadSalida:
    repo = _repositorio(bd, curso_id, tarea_id, repo_id)
    identidad = _identidad(bd, repo, identidad_id)
    if identidad.estado == EstadoIdentidadGit.SUPERSEDIDA.value:
        raise HTTPException(
            status_code=409,
            detail={"motivo": "IDENTIDAD_SUPERSEDIDA", "detalle": "Esa fila ya fue reemplazada."},
        )
    try:
        nueva = actividad_repo.resolver_identidad(
            bd,
            identidad=identidad,
            estudiante_id=datos.estudiante_id,
            no_es_estudiante=datos.no_es_estudiante,
            propagar_a=datos.propagar_a,
            actor_usuario_id=membresia.usuario_id,
            confirmacion=datos.confirmacion,
        )
    except actividad_repo.RechazoIdentidad as exc:
        raise HTTPException(
            status_code=409 if exc.motivo == "CONFIRMACION_REQUERIDA" else 422,
            detail={"motivo": exc.motivo, "detalle": exc.detalle},
        ) from None
    return _salida(bd, nueva)


class CandidatoSalida(BaseModel):
    repositorio_id: uuid.UUID
    repositorio: str
    identidad_id: uuid.UUID
    nombre_visto: str | None
    commits: int
    marcada: bool


@router.get(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/repos/{repo_id}/identidades/{identidad_id}/propagacion",
    response_model=list[CandidatoSalida],
)
def propagacion(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    repo_id: uuid.UUID,
    identidad_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.MAPEO_EDITAR)),
) -> list[CandidatoSalida]:
    """Las casillas nacen desmarcadas: la propagacion es una propuesta."""
    repo = _repositorio(bd, curso_id, tarea_id, repo_id)
    identidad = _identidad(bd, repo, identidad_id)
    salida = []
    for otra, commits in actividad_repo.candidatos_propagacion(bd, identidad):
        destino = bd.get(Repositorio, otra.repositorio_id)
        salida.append(
            CandidatoSalida(
                repositorio_id=otra.repositorio_id,
                repositorio=destino.nombre if destino is not None else "—",
                identidad_id=otra.id,
                nombre_visto=otra.nombre_visto_ultimo or otra.nombre_visto,
                commits=commits,
                marcada=False,
            )
        )
    return salida


@router.post(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/repos/{repo_id}/identidades/{identidad_id}/revelar",
    dependencies=[Depends(exigir_csrf)],
)
def revelar(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    repo_id: uuid.UUID,
    identidad_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.MAPEO_EDITAR)),
) -> dict[str, str]:
    """S10.3.6: un autor cada vez, siempre auditado."""
    repo = _repositorio(bd, curso_id, tarea_id, repo_id)
    identidad = _identidad(bd, repo, identidad_id)
    registrar_bitacora(
        bd,
        accion="EMAIL_AUTOR_REVELADO",
        entidad="identidad_git",
        entidad_id=str(identidad.id),
        actor_usuario_id=membresia.usuario_id,
        curso_id=curso_id,
        despues={"repositorio_id": str(repo.id)},
    )
    return {"email": identidad.email_visto, "aviso": AVISO_TERCEROS}
