"""Pendientes: la pantalla unica de informacion faltante (SPEC 07 S7.8).

R2.2.6: "una sola pantalla, no un listado accesorio". Los cuatro bloques
literales de S7.8.1. El bloque 4 (invitaciones de GitHub sin aceptar) lee
`acceso_repositorio`, que existe desde la Etapa P8.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adaptadores.base import ahora_utc
from app.adaptadores.bitacora_repo import registrar as registrar_bitacora
from app.adaptadores.canvas_repo import descifrar_token, obtener_credencial_operativa
from app.adaptadores.cliente_canvas import FalloProveedorCanvas, crear_cliente_canvas
from app.adaptadores.modelos_aprovisionamiento import AccesoRepositorio, Repositorio
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_infraestructura import Incidencia
from app.adaptadores.modelos_mapeo import CuentaGithub, MapeoGithub
from app.adaptadores.modelos_padron import Estudiante, Grupo, PertenenciaGrupo
from app.api.dependencias import exigir_csrf, obtener_sesion_bd, requiere
from app.dominio.estados import EstadoAccesoRepositorio, EstadoMapeoGithub, MotivoInvalidacionMapeo
from app.dominio.permisos import Permiso
from app.infraestructura.cifrado import Llavero
from app.infraestructura.config import Settings, obtener_configuracion

router = APIRouter(tags=["pendientes"])

_TOPE_RECORDATORIOS_HORAS = 24
_MOTIVOS_BLOQUE_2 = {
    MotivoInvalidacionMapeo.LOGIN_REASIGNADO.value,
    MotivoInvalidacionMapeo.CUENTA_NO_ELEGIBLE.value,
}


def _llavero(settings: Settings) -> Llavero:
    return Llavero(settings.llavero_cifrado(), settings.app_encryption_key_activa)


class FilaBloque1(BaseModel):
    estudiante_id: uuid.UUID
    nombre: str
    estado_estudiante: str
    estado_mapeo: str


class FilaBloque2(BaseModel):
    estudiante_id: uuid.UUID
    nombre: str
    estado_mapeo: str
    motivo_invalidacion: str | None
    cuenta_login: str | None


class FilaBloque3(BaseModel):
    tipo: str
    severidad: str
    estudiante_id: uuid.UUID | None
    nombre: str | None
    detalle: dict[str, object]


class FilaBloque4(BaseModel):
    estudiante_id: uuid.UUID
    nombre: str
    estado_acceso: str


class PendientesSalida(BaseModel):
    bloque_1_sin_cuenta: list[FilaBloque1]
    bloque_2_en_conflicto: list[FilaBloque2]
    bloque_3_grupos_incompletos: list[FilaBloque3]
    bloque_4_invitaciones_sin_aceptar: list[FilaBloque4]


@router.get("/api/cursos/{curso_id}/pendientes", response_model=PendientesSalida)
def obtener_pendientes(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> PendientesSalida:
    curso = bd.query(Curso).filter(Curso.id == curso_id).one_or_none()
    if curso is None:
        raise HTTPException(status_code=404)

    estudiantes = bd.query(Estudiante).filter(Estudiante.curso_id == curso_id).all()
    nombre_por_id = {e.id: e for e in estudiantes}

    mapeos_vivos = (
        bd.query(MapeoGithub)
        .filter(
            MapeoGithub.curso_id == curso_id,
            MapeoGithub.estado != EstadoMapeoGithub.SUPERSEDIDO.value,
        )
        .all()
    )
    cuentas_por_id = {
        c.id: c
        for c in bd.query(CuentaGithub)
        .filter(
            CuentaGithub.id.in_([m.cuenta_github_id for m in mapeos_vivos if m.cuenta_github_id])
        )
        .all()
    }

    # Bloque 1 (S7.8.1, CA-7.8-01): "sin excepcion" -- se incluye a todo
    # estudiante con mapeo != VIGENTE, sin filtrar por estado.estudiante.
    bloque_1 = [
        FilaBloque1(
            estudiante_id=m.estudiante_id,
            nombre=nombre_por_id[m.estudiante_id].nombre,
            estado_estudiante=nombre_por_id[m.estudiante_id].estado,
            estado_mapeo=m.estado,
        )
        for m in mapeos_vivos
        if m.estado != EstadoMapeoGithub.VIGENTE.value and m.estudiante_id in nombre_por_id
    ]

    # Bloque 2 (S7.8.1): EN_CONFLICTO, o INVALIDADO por LOGIN_REASIGNADO/CUENTA_NO_ELEGIBLE.
    bloque_2 = [
        FilaBloque2(
            estudiante_id=m.estudiante_id,
            nombre=nombre_por_id[m.estudiante_id].nombre,
            estado_mapeo=m.estado,
            motivo_invalidacion=m.motivo_invalidacion,
            cuenta_login=cuentas_por_id[m.cuenta_github_id].login
            if m.cuenta_github_id in cuentas_por_id
            else None,
        )
        for m in mapeos_vivos
        if m.estudiante_id in nombre_por_id
        and (
            m.estado == EstadoMapeoGithub.EN_CONFLICTO.value
            or (
                m.estado == EstadoMapeoGithub.INVALIDADO.value
                and m.motivo_invalidacion in _MOTIVOS_BLOQUE_2
            )
        )
    ]

    # Bloque 3 (S7.8.1): incidencias abiertas de GRUPO_INCOMPLETO/ESTUDIANTE_EN_DOS_GRUPOS,
    # mas integrantes invited/requested, mas estudiantes activos sin ningun grupo
    # (interpretacion: solo se marcan "sin grupo" si el curso ya tiene al menos
    # un conjunto de grupos colaborativo, para no listar cursos que aun no usan grupos).
    incidencias = (
        bd.query(Incidencia)
        .filter(
            Incidencia.curso_id == curso_id,
            Incidencia.abierta.is_(True),
            Incidencia.tipo.in_(["GRUPO_INCOMPLETO", "ESTUDIANTE_EN_DOS_GRUPOS"]),
        )
        .all()
    )
    bloque_3 = [
        FilaBloque3(
            tipo=i.tipo,
            severidad=i.severidad,
            estudiante_id=i.sujeto_id if i.sujeto_tipo == "ESTUDIANTE" else None,
            nombre=(
                nombre_por_id[i.sujeto_id].nombre
                if i.sujeto_tipo == "ESTUDIANTE" and i.sujeto_id in nombre_por_id
                else None
            ),
            detalle=i.detalle,
        )
        for i in incidencias
    ]

    pertenencias_pendientes = (
        bd.query(PertenenciaGrupo)
        .join(Grupo, Grupo.id == PertenenciaGrupo.grupo_id)
        .filter(Grupo.curso_id == curso_id, PertenenciaGrupo.activa.is_(True))
        .filter(PertenenciaGrupo.workflow_state.in_(["invited", "requested"]))
        .all()
    )
    for p in pertenencias_pendientes:
        if p.estudiante_id not in nombre_por_id:
            continue
        bloque_3.append(
            FilaBloque3(
                tipo="PENDIENTE_DE_ACEPTAR_EN_CANVAS",
                severidad="INFORMATIVA",
                estudiante_id=p.estudiante_id,
                nombre=nombre_por_id[p.estudiante_id].nombre,
                detalle={"workflow_state": p.workflow_state, "grupo_id": str(p.grupo_id)},
            )
        )

    hay_grupos_colaborativos = (
        bd.query(Grupo).filter(Grupo.curso_id == curso_id).first() is not None
    )
    if hay_grupos_colaborativos:
        estudiantes_con_grupo = {
            p.estudiante_id
            for p in bd.query(PertenenciaGrupo)
            .join(Grupo, Grupo.id == PertenenciaGrupo.grupo_id)
            .filter(Grupo.curso_id == curso_id, PertenenciaGrupo.activa.is_(True))
            .all()
        }
        for e in estudiantes:
            if e.estado in ("ACTIVO", "INVITADO") and e.id not in estudiantes_con_grupo:
                bloque_3.append(
                    FilaBloque3(
                        tipo="ESTUDIANTE_SIN_GRUPO",
                        severidad="INFORMATIVA",
                        estudiante_id=e.id,
                        nombre=e.nombre,
                        detalle={},
                    )
                )

    # S7.8.1 bloque 4 (Etapa P8): accesos de estudiante invitados que aun no
    # entraron, o cuya invitacion expiro o desaparecio («rechazada o caducada»,
    # A-100: no se nombra una causa que no se puede probar).
    accesos_pendientes = (
        bd.query(AccesoRepositorio)
        .join(Repositorio, Repositorio.id == AccesoRepositorio.repositorio_id)
        .filter(
            Repositorio.curso_id == curso_id,
            AccesoRepositorio.estado.in_(
                [
                    EstadoAccesoRepositorio.INVITADO.value,
                    EstadoAccesoRepositorio.EXPIRADA.value,
                    EstadoAccesoRepositorio.DESAPARECIDA.value,
                ]
            ),
        )
        .all()
    )
    bloque_4 = [
        FilaBloque4(
            estudiante_id=a.estudiante_id,
            nombre=nombre_por_id[a.estudiante_id].nombre,
            estado_acceso=a.estado,
        )
        for a in accesos_pendientes
        if a.estudiante_id in nombre_por_id
    ]

    return PendientesSalida(
        bloque_1_sin_cuenta=bloque_1,
        bloque_2_en_conflicto=bloque_2,
        bloque_3_grupos_incompletos=bloque_3,
        bloque_4_invitaciones_sin_aceptar=bloque_4,
    )


@router.post(
    "/api/cursos/{curso_id}/pendientes/{estudiante_id}/recordatorio",
    dependencies=[Depends(exigir_csrf)],
)
def enviar_recordatorio(
    curso_id: uuid.UUID,
    estudiante_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    membresia: MembresiaCurso = Depends(requiere(Permiso.COMUNICACION_ENVIAR)),
) -> dict[str, bool]:
    """Via 4, caso por estudiante (S7.4.5): mensaje sincrono de Canvas,
    tope de 1 por estudiante por dia via `estudiante.ultimo_recordatorio_en`."""
    curso = bd.query(Curso).filter(Curso.id == curso_id).one_or_none()
    if curso is None:
        raise HTTPException(status_code=404)
    estudiante = (
        bd.query(Estudiante)
        .filter(Estudiante.id == estudiante_id, Estudiante.curso_id == curso_id)
        .one_or_none()
    )
    if estudiante is None:
        raise HTTPException(status_code=404)

    ahora = ahora_utc()
    if estudiante.ultimo_recordatorio_en is not None:
        transcurridas = (ahora - estudiante.ultimo_recordatorio_en).total_seconds() / 3600
        if transcurridas < _TOPE_RECORDATORIOS_HORAS:
            raise HTTPException(
                status_code=429, detail="ya se envio un recordatorio a este estudiante hoy"
            )

    credencial = obtener_credencial_operativa(bd, curso_id)
    if credencial is None or curso.canvas_course_id is None:
        raise HTTPException(status_code=409, detail="el curso no tiene Canvas vinculado")

    token = descifrar_token(_llavero(settings), credencial)
    cliente = crear_cliente_canvas(
        modo=settings.canvas_modo, canvas_base_url=curso.canvas_base_url or settings.canvas_base_url
    )
    try:
        cliente.enviar_conversacion(
            token,
            destinatarios_canvas_user_ids=[estudiante.canvas_user_id],
            asunto="Falta registrar tu cuenta de GitHub",
            cuerpo=(
                "Todavia no pudimos confirmar tu cuenta de GitHub para este curso. "
                "Por favor entrega tu usuario o el enlace a tu perfil en la tarea de "
                "registro de GitHub en Canvas."
            ),
        )
    except FalloProveedorCanvas as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None

    estudiante.ultimo_recordatorio_en = ahora
    registrar_bitacora(
        bd,
        accion="RECORDATORIO_GITHUB_ENVIADO",
        entidad="estudiante",
        entidad_id=str(estudiante_id),
        actor_usuario_id=membresia.usuario_id,
        curso_id=curso_id,
    )
    return {"ok": True}
