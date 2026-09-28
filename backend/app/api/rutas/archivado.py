"""Bloque «Cierre de la tarea»: archivar y desarchivar sus repositorios (A-168,
A-197, A-227; Etapa F8).

`GET .../archivado` pinta las cinco guardas desde la base, sin llamar a nadie,
para que la pantalla las muestre todas antes de habilitar el boton. Las tres
acciones exigen `tarea.administrar` y rol `PROFESOR` (caso 4 de
`ACCIONES_SOLO_PROFESOR`) y solo encolan: GitHub lo llama el trabajo
`archivar_repositorios` (A-226).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adaptadores import archivado_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_curso import MembresiaCurso
from app.api.dependencias import exigir_csrf, obtener_sesion_bd, requiere
from app.api.rutas.tablero import _tarea
from app.dominio.archivado import ResultadoArchivado
from app.dominio.estados import EstadoRepositorio, EstadoTarea, RolMembresia
from app.dominio.permisos import Permiso

router = APIRouter(tags=["archivado"])


class GuardaSalida(BaseModel):
    numero: int
    titulo: str
    cumple: bool
    motivo: str | None
    confirmacion: str | None
    detalle: list[str]


class AvisoSalida(BaseModel):
    destinatarios: int
    encolados: int
    enviados: int
    bloqueados: int
    ultimo_envio: datetime | None
    canal_bloqueado: bool


class ArchivadoSalida(BaseModel):
    tarea_estado: str
    archivables: int
    archivados: int
    fuera_de_alcance_o_inaccesibles: int
    guardas: list[GuardaSalida]
    permitido: bool
    aviso: AvisoSalida
    en_curso: int
    puede_desarchivar: bool


def _guardas(resultado: ResultadoArchivado) -> list[GuardaSalida]:
    return [
        GuardaSalida(
            numero=g.numero,
            titulo=g.titulo,
            cumple=g.cumple,
            motivo=g.motivo,
            confirmacion=g.confirmacion,
            detalle=list(g.detalle),
        )
        for g in resultado.guardas
    ]


@router.get("/api/cursos/{curso_id}/tareas/{tarea_id}/archivado", response_model=ArchivadoSalida)
def estado_archivado(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    response: Response,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> ArchivadoSalida:
    curso, tarea = _tarea(bd, curso_id, tarea_id)
    todos = archivado_repo.repositorios_de_tarea(bd, tarea.id)
    pendientes = [r for r in todos if r.estado not in archivado_repo.TERMINALES]
    archivados = [r for r in todos if r.estado == EstadoRepositorio.ARCHIVADO.value]
    resultado = archivado_repo.evaluar(bd, curso, tarea, ahora=ahora_utc(), repositorios=pendientes)
    aviso = archivado_repo.aviso_previo(bd, curso, tarea, pendientes)
    response.headers["X-Llamadas-Externas"] = "0"
    return ArchivadoSalida(
        tarea_estado=tarea.estado,
        archivables=len(pendientes),
        archivados=len(archivados),
        fuera_de_alcance_o_inaccesibles=len(todos) - len(pendientes) - len(archivados),
        guardas=_guardas(resultado),
        permitido=resultado.permitido and bool(pendientes),
        aviso=AvisoSalida(**aviso.__dict__),
        en_curso=archivado_repo.trabajos_en_curso(bd, tarea.id),
        puede_desarchivar=bool(archivados),
    )


@router.post(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/archivar/aviso",
    status_code=202,
    dependencies=[Depends(exigir_csrf)],
)
def enviar_aviso_previo(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(
        requiere(Permiso.TAREA_ADMINISTRAR, rol_minimo=RolMembresia.PROFESOR)
    ),
) -> dict[str, int]:
    """Guarda 4: encola el aviso de catorce dias por Canvas, uno por persona."""
    curso, tarea = _tarea(bd, curso_id, tarea_id)
    return {"encolados": archivado_repo.encolar_aviso_previo(bd, curso, tarea)}


class ArchivarEntrada(BaseModel):
    confirmacion_sin_captura: str | None = None
    confirmacion_sin_aviso: str | None = None


@router.post(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/archivar",
    status_code=202,
    dependencies=[Depends(exigir_csrf)],
)
def archivar(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    datos: ArchivarEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(
        requiere(Permiso.TAREA_ADMINISTRAR, rol_minimo=RolMembresia.PROFESOR)
    ),
) -> dict[str, Any]:
    curso, tarea = _tarea(bd, curso_id, tarea_id)
    if tarea.estado in (EstadoTarea.BORRADOR.value, EstadoTarea.ARCHIVADA.value):
        raise HTTPException(
            status_code=409,
            detail={"codigo": "TAREA_NO_ARCHIVABLE", "motivo": f"La tarea está {tarea.estado}."},
        )
    pendientes = archivado_repo.archivables(bd, tarea.id)
    resultado = archivado_repo.evaluar(
        bd,
        curso,
        tarea,
        ahora=ahora_utc(),
        repositorios=pendientes,
        confirmacion_sin_captura=datos.confirmacion_sin_captura,
        confirmacion_sin_aviso=datos.confirmacion_sin_aviso,
    )
    if not resultado.permitido or not pendientes:
        fallida = resultado.fallida
        raise HTTPException(
            status_code=409,
            detail={
                "codigo": "ARCHIVADO_BLOQUEADO",
                "motivo": fallida.motivo if fallida else "No hay repositorios que archivar.",
                "guardas": [g.model_dump() for g in _guardas(resultado)],
            },
        )
    encolados = archivado_repo.solicitar(
        bd,
        curso,
        tarea,
        accion=archivado_repo.ARCHIVAR,
        repositorios=pendientes,
        actor_usuario_id=membresia.usuario_id,
        confirmaciones={
            "confirmacion_sin_captura": datos.confirmacion_sin_captura,
            "confirmacion_sin_aviso": datos.confirmacion_sin_aviso,
        },
    )
    return {"repositorios": encolados}


@router.post(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/desarchivar",
    status_code=202,
    dependencies=[Depends(exigir_csrf)],
)
def desarchivar(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(
        requiere(Permiso.TAREA_ADMINISTRAR, rol_minimo=RolMembresia.PROFESOR)
    ),
) -> dict[str, Any]:
    """Desarchiva todos los repositorios archivados de la tarea."""
    curso, tarea = _tarea(bd, curso_id, tarea_id)
    archivados = [
        r
        for r in archivado_repo.repositorios_de_tarea(bd, tarea.id)
        if r.estado == EstadoRepositorio.ARCHIVADO.value
    ]
    if not archivados:
        raise HTTPException(
            status_code=409,
            detail={"codigo": "NADA_QUE_DESARCHIVAR", "motivo": "No hay repositorios archivados."},
        )
    encolados = archivado_repo.solicitar(
        bd,
        curso,
        tarea,
        accion=archivado_repo.DESARCHIVAR,
        repositorios=archivados,
        actor_usuario_id=membresia.usuario_id,
        confirmaciones={},
    )
    return {"repositorios": encolados}
