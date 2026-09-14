"""`/tareas`: tarea individual, entrega unica y repositorio base (SPEC 08
S8.2-S8.3, SPEC 13 S13.5.1-S13.5.2; Etapa P7).

Solo dos manejadores de este modulo hablan con un proveedor, y son las
escrituras sincronas 2 y 3 de A-169 contra GitHub (crear el repositorio base y
administrar sus archivos, mas su previsualizacion). Crear una tarea, vincular o
desvincular una entrega y activar leen el espejo: nunca llaman a Canvas (A-089).

Orden de registro: las rutas literales bajo `/tareas/` van antes que
`/tareas/{tarea_id}`, porque FastAPI resuelve por orden de registro y no por
especificidad (mismo bug que ya se corrigio en Etapa P4).
"""

from __future__ import annotations

import uuid
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adaptadores import repositorio_base_repo, tareas_repo
from app.adaptadores.cliente_github import (
    ClienteGitHub,
    FalloProveedorGithub,
    RechazoProveedorGithub,
    crear_cliente_github_desde_config,
)
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_infraestructura import CursorSincronizacion
from app.adaptadores.modelos_tarea import Entrega, Tarea
from app.api.dependencias import exigir_csrf, obtener_sesion_bd, requiere
from app.dominio.permisos import Permiso
from app.dominio.tareas import PLANTILLAS_GITIGNORE, MotivoRechazoTarea, RechazoTarea
from app.infraestructura.config import Settings, obtener_configuracion

router = APIRouter(tags=["tareas"])

_MOTIVOS_DE_VALIDACION = frozenset(
    {
        MotivoRechazoTarea.SLUG_INVALIDO,
        MotivoRechazoTarea.GITIGNORE_FUERA_DE_LISTA,
        MotivoRechazoTarea.RUTA_INVALIDA,
        MotivoRechazoTarea.ARCHIVO_DEMASIADO_GRANDE,
        MotivoRechazoTarea.FINAL_NO_ELEGIDA,
    }
)


def _http_rechazo(exc: RechazoTarea) -> HTTPException:
    status = 422 if exc.motivo in _MOTIVOS_DE_VALIDACION else 409
    return HTTPException(
        status_code=status, detail={"motivo": exc.motivo.value, "detalle": exc.detalle}
    )


def _http_rechazo_github(exc: RechazoProveedorGithub) -> HTTPException:
    return HTTPException(
        status_code=502,
        detail={
            "motivo": "GITHUB_RECHAZO",
            "detalle": f"GitHub respondió {exc.status_code}: {exc.mensaje_literal}",
        },
    )


def _http_fallo_github(exc: FalloProveedorGithub) -> HTTPException:
    return HTTPException(
        status_code=504,
        detail={
            "motivo": "GITHUB_NO_RESPONDIO",
            "detalle": f"GitHub no respondió a tiempo ({exc}). La operación quedó registrada: "
            "vuelve a intentarlo en unos minutos, no se duplicará nada.",
        },
    )


def _curso(bd: Session, curso_id: uuid.UUID) -> Curso:
    curso = bd.query(Curso).filter(Curso.id == curso_id).one_or_none()
    if curso is None:
        raise HTTPException(status_code=404)
    return curso


def _tarea(bd: Session, curso_id: uuid.UUID, tarea_id: uuid.UUID) -> Tarea:
    tarea = bd.query(Tarea).filter(Tarea.id == tarea_id, Tarea.curso_id == curso_id).one_or_none()
    if tarea is None:
        raise HTTPException(status_code=404)
    return tarea


def _github(settings: Settings, curso: Curso) -> tuple[ClienteGitHub, str]:
    if curso.github_installation_id is None or curso.github_org_login is None:
        raise _http_rechazo(
            RechazoTarea(
                MotivoRechazoTarea.GITHUB_NO_VINCULADO,
                "El curso todavía no tiene GitHub vinculado.",
            )
        )
    cliente = crear_cliente_github_desde_config(settings)
    try:
        return cliente, cliente.obtener_token_instalacion(curso.github_installation_id)
    except FalloProveedorGithub as exc:
        raise _http_fallo_github(exc) from None
    except httpx.HTTPStatusError as exc:
        raise _http_rechazo_github(
            RechazoProveedorGithub(exc.response.status_code, exc.response.text[:500])
        ) from None


# --- Esquemas de salida ---


class EntregaSalida(BaseModel):
    id: uuid.UUID
    canvas_assignment_id: int
    tipo: str
    orden: int
    nombre: str
    slug: str
    publicada: bool
    due_at_base: datetime | None
    estado_validacion: str
    sincronizado_en: datetime


class ArchivoBaseSalida(BaseModel):
    ruta: str
    sha: str
    tamano_bytes: int
    actualizado_en: datetime


class RepositorioBaseSalida(BaseModel):
    id: uuid.UUID
    nombre: str
    full_name: str | None
    url_html: str | None
    estado: str
    rama_por_defecto: str | None
    clase_error: str | None
    error_mensaje_literal: str | None
    archivos: list[ArchivoBaseSalida]


class TareaResumenSalida(BaseModel):
    id: uuid.UUID
    nombre: str
    slug: str
    modalidad: str
    estado: str
    cantidad_entregas: int
    estado_repositorio_base: str | None
    creada_en: datetime


class AccionSalida(BaseModel):
    habilitada: bool
    motivo: str | None


class TareaDetalleSalida(BaseModel):
    id: uuid.UUID
    nombre: str
    slug: str
    modalidad: str
    estado: str
    gitignore_template: str | None
    activada_en: datetime | None
    entregas: list[EntregaSalida]
    repositorio_base: RepositorioBaseSalida | None
    nombre_repositorio_base: str
    activar: AccionSalida
    vincular_otra_entrega: AccionSalida
    crear_repositorio_base: AccionSalida


class AssignmentCanvasSalida(BaseModel):
    canvas_assignment_id: int
    nombre: str
    es_grupal: bool
    publicada: bool
    due_at: datetime | None
    seleccionable: bool
    motivo: str | None


class AssignmentsCanvasSalida(BaseModel):
    assignments: list[AssignmentCanvasSalida]
    sincronizado_en: datetime | None
    plantillas_gitignore: list[str]


class VistaPreviaNombreSalida(BaseModel):
    slug: str
    slug_valido: bool
    slug_ocupado: bool
    ejemplo_repositorio: str | None
    ejemplo_sujeto: str
    repositorio_base: str | None


def _salida_entrega(e: Entrega) -> EntregaSalida:
    return EntregaSalida(
        id=e.id,
        canvas_assignment_id=e.canvas_assignment_id,
        tipo=e.tipo,
        orden=e.orden,
        nombre=e.nombre,
        slug=e.slug,
        publicada=e.publicada,
        due_at_base=e.due_at_base,
        estado_validacion=e.estado_validacion,
        sincronizado_en=e.sincronizado_en,
    )


def _detalle(bd: Session, *, curso: Curso, tarea: Tarea, settings: Settings) -> TareaDetalleSalida:
    base = tareas_repo.repositorio_base_de_tarea(bd, tarea.id)
    base_salida = None
    if base is not None:
        base_salida = RepositorioBaseSalida(
            id=base.id,
            nombre=base.nombre,
            full_name=base.full_name,
            url_html=base.url_html,
            estado=base.estado,
            rama_por_defecto=base.rama_por_defecto,
            clase_error=base.clase_error,
            error_mensaje_literal=base.error_mensaje_literal,
            archivos=[
                ArchivoBaseSalida(
                    ruta=a.ruta,
                    sha=a.sha,
                    tamano_bytes=a.tamano_bytes,
                    actualizado_en=a.actualizado_en,
                )
                for a in repositorio_base_repo.listar_archivos(bd, base)
            ],
        )
    motivo_activar = tareas_repo.motivo_activacion(
        bd, tarea=tarea, curso=curso, perfil_alcance=settings.perfil_alcance
    )
    motivo_otra = tareas_repo.motivo_vincular_otra_entrega(
        bd, tarea=tarea, perfil_alcance=settings.perfil_alcance
    )
    motivo_base: str | None = None
    if curso.github_installation_id is None:
        motivo_base = "El curso todavía no tiene GitHub vinculado."
    elif tarea.estado != "BORRADOR":
        motivo_base = "El repositorio base solo se declara mientras la tarea está en borrador."
    elif base is not None and base.estado not in ("ERROR", "CREANDO"):
        motivo_base = "Esta tarea ya tiene repositorio base."
    return TareaDetalleSalida(
        id=tarea.id,
        nombre=tarea.nombre,
        slug=tarea.slug,
        modalidad=tarea.modalidad,
        estado=tarea.estado,
        gitignore_template=tarea.gitignore_template,
        activada_en=tarea.activada_en,
        entregas=[_salida_entrega(e) for e in tareas_repo.entregas_de_tarea(bd, tarea.id)],
        repositorio_base=base_salida,
        nombre_repositorio_base=tareas_repo.vista_previa_nombres(
            bd, curso=curso, nombre=tarea.nombre, slug=tarea.slug
        ).repositorio_base
        or "",
        activar=AccionSalida(habilitada=motivo_activar is None, motivo=motivo_activar),
        vincular_otra_entrega=AccionSalida(habilitada=motivo_otra is None, motivo=motivo_otra),
        crear_repositorio_base=AccionSalida(habilitada=motivo_base is None, motivo=motivo_base),
    )


# --- Rutas literales (antes que /tareas/{tarea_id}) ---


@router.get("/api/cursos/{curso_id}/tareas", response_model=list[TareaResumenSalida])
def listar_tareas(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> list[TareaResumenSalida]:
    salida = []
    for tarea in bd.query(Tarea).filter(Tarea.curso_id == curso_id).order_by(Tarea.creada_en):
        base = tareas_repo.repositorio_base_de_tarea(bd, tarea.id)
        salida.append(
            TareaResumenSalida(
                id=tarea.id,
                nombre=tarea.nombre,
                slug=tarea.slug,
                modalidad=tarea.modalidad,
                estado=tarea.estado,
                cantidad_entregas=len(tareas_repo.entregas_de_tarea(bd, tarea.id)),
                estado_repositorio_base=base.estado if base is not None else None,
                creada_en=tarea.creada_en,
            )
        )
    return salida


@router.get(
    "/api/cursos/{curso_id}/tareas/assignments-canvas", response_model=AssignmentsCanvasSalida
)
def listar_assignments_canvas(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> AssignmentsCanvasSalida:
    """Lee el espejo con su sello de antigüedad (A-231); nunca llama a Canvas."""
    curso = _curso(bd, curso_id)
    cursor = (
        bd.query(CursorSincronizacion)
        .filter(CursorSincronizacion.curso_id == curso_id, CursorSincronizacion.recurso == "tareas")
        .one_or_none()
    )
    return AssignmentsCanvasSalida(
        assignments=[
            AssignmentCanvasSalida(
                canvas_assignment_id=item.fila.canvas_assignment_id,
                nombre=item.fila.nombre,
                es_grupal=item.fila.es_grupal,
                publicada=item.fila.publicada,
                due_at=item.fila.due_at,
                seleccionable=item.seleccionable,
                motivo=item.motivo,
            )
            for item in tareas_repo.listar_assignments_seleccionables(
                bd, curso=curso, perfil_alcance=settings.perfil_alcance
            )
        ],
        sincronizado_en=cursor.ultimo_exito_en if cursor is not None else None,
        plantillas_gitignore=list(PLANTILLAS_GITIGNORE),
    )


@router.get(
    "/api/cursos/{curso_id}/tareas/vista-previa-nombre", response_model=VistaPreviaNombreSalida
)
def vista_previa_nombre(
    curso_id: uuid.UUID,
    nombre: str = "",
    slug: str | None = None,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> VistaPreviaNombreSalida:
    vista = tareas_repo.vista_previa_nombres(
        bd, curso=_curso(bd, curso_id), nombre=nombre, slug=slug
    )
    return VistaPreviaNombreSalida(
        slug=vista.slug,
        slug_valido=vista.slug_valido,
        slug_ocupado=vista.slug_ocupado,
        ejemplo_repositorio=vista.ejemplo_repositorio,
        ejemplo_sujeto=vista.ejemplo_sujeto,
        repositorio_base=vista.repositorio_base,
    )


class CrearTareaEntrada(BaseModel):
    nombre: str
    slug: str | None = None
    canvas_assignment_id: int
    gitignore_template: str | None = None


@router.post(
    "/api/cursos/{curso_id}/tareas",
    response_model=TareaDetalleSalida,
    dependencies=[Depends(exigir_csrf)],
)
def crear_tarea(
    curso_id: uuid.UUID,
    datos: CrearTareaEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    membresia: MembresiaCurso = Depends(requiere(Permiso.TAREA_ADMINISTRAR)),
) -> TareaDetalleSalida:
    curso = _curso(bd, curso_id)
    try:
        tarea = tareas_repo.crear_tarea(
            bd,
            curso=curso,
            nombre=datos.nombre,
            slug=datos.slug,
            canvas_assignment_id=datos.canvas_assignment_id,
            gitignore_template=datos.gitignore_template,
            actor_usuario_id=membresia.usuario_id,
            perfil_alcance=settings.perfil_alcance,
        )
    except RechazoTarea as exc:
        raise _http_rechazo(exc) from None
    return _detalle(bd, curso=curso, tarea=tarea, settings=settings)


# --- Rutas de una tarea ---


@router.get("/api/cursos/{curso_id}/tareas/{tarea_id}", response_model=TareaDetalleSalida)
def obtener_tarea(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> TareaDetalleSalida:
    return _detalle(
        bd, curso=_curso(bd, curso_id), tarea=_tarea(bd, curso_id, tarea_id), settings=settings
    )


class VincularEntregaEntrada(BaseModel):
    canvas_assignment_id: int
    final_canvas_assignment_id: int | None = None


@router.post(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/entregas",
    response_model=TareaDetalleSalida,
    dependencies=[Depends(exigir_csrf)],
)
def vincular_entrega(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    datos: VincularEntregaEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    membresia: MembresiaCurso = Depends(requiere(Permiso.TAREA_ADMINISTRAR)),
) -> TareaDetalleSalida:
    curso = _curso(bd, curso_id)
    tarea = _tarea(bd, curso_id, tarea_id)
    try:
        tareas_repo.vincular_entrega(
            bd,
            curso=curso,
            tarea=tarea,
            canvas_assignment_id=datos.canvas_assignment_id,
            final_canvas_assignment_id=datos.final_canvas_assignment_id,
            actor_usuario_id=membresia.usuario_id,
            perfil_alcance=settings.perfil_alcance,
        )
    except RechazoTarea as exc:
        raise _http_rechazo(exc) from None
    return _detalle(bd, curso=curso, tarea=tarea, settings=settings)


@router.delete(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/entregas/{entrega_id}",
    response_model=TareaDetalleSalida,
    dependencies=[Depends(exigir_csrf)],
)
def desvincular_entrega(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    entrega_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    membresia: MembresiaCurso = Depends(requiere(Permiso.TAREA_ADMINISTRAR)),
) -> TareaDetalleSalida:
    curso = _curso(bd, curso_id)
    tarea = _tarea(bd, curso_id, tarea_id)
    entrega = (
        bd.query(Entrega)
        .filter(Entrega.id == entrega_id, Entrega.tarea_id == tarea.id)
        .one_or_none()
    )
    if entrega is None:
        raise HTTPException(status_code=404)
    try:
        tareas_repo.desvincular_entrega(
            bd, curso=curso, tarea=tarea, entrega=entrega, actor_usuario_id=membresia.usuario_id
        )
    except RechazoTarea as exc:
        raise _http_rechazo(exc) from None
    return _detalle(bd, curso=curso, tarea=tarea, settings=settings)


@router.post(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/activar",
    response_model=TareaDetalleSalida,
    dependencies=[Depends(exigir_csrf)],
)
def activar_tarea(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    membresia: MembresiaCurso = Depends(requiere(Permiso.TAREA_ADMINISTRAR)),
) -> TareaDetalleSalida:
    curso = _curso(bd, curso_id)
    tarea = _tarea(bd, curso_id, tarea_id)
    try:
        tareas_repo.activar_tarea(
            bd,
            curso=curso,
            tarea=tarea,
            actor_usuario_id=membresia.usuario_id,
            perfil_alcance=settings.perfil_alcance,
        )
    except RechazoTarea as exc:
        raise _http_rechazo(exc) from None
    return _detalle(bd, curso=curso, tarea=tarea, settings=settings)


# --- Repositorio base: escrituras sincronas 2 y 3 de A-169 ---


@router.post(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/repositorio-base",
    response_model=TareaDetalleSalida,
    dependencies=[Depends(exigir_csrf)],
)
def crear_repositorio_base(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    membresia: MembresiaCurso = Depends(requiere(Permiso.TAREA_ADMINISTRAR)),
) -> TareaDetalleSalida:
    """R2.3.5: "crear desde la aplicacion un repositorio base". El resultado se
    muestra en pantalla: estado nuevo o el error literal de GitHub."""
    curso = _curso(bd, curso_id)
    tarea = _tarea(bd, curso_id, tarea_id)
    try:
        base = repositorio_base_repo.registrar_intencion_repositorio_base(
            bd, curso=curso, tarea=tarea, actor_usuario_id=membresia.usuario_id
        )
    except RechazoTarea as exc:
        raise _http_rechazo(exc) from None
    # A-169 punto 2: la intencion queda persistida antes de llamar a GitHub.
    bd.commit()

    cliente, token = _github(settings, curso)
    try:
        repositorio_base_repo.completar_creacion_repositorio_base(
            bd,
            cliente,
            token,
            curso=curso,
            tarea=tarea,
            base=base,
            actor_usuario_id=membresia.usuario_id,
        )
    except FalloProveedorGithub as exc:
        bd.commit()
        raise _http_fallo_github(exc) from None
    return _detalle(bd, curso=curso, tarea=tarea, settings=settings)


class EscribirArchivoEntrada(BaseModel):
    contenido_base64: str


class RenombrarArchivoEntrada(BaseModel):
    desde: str
    hacia: str


class PrevisualizacionSalida(BaseModel):
    ruta: str
    tamano_bytes: int
    texto: str | None
    motivo_sin_texto: str | None


def _ejecutar_escritura_archivo(
    bd: Session,
    settings: Settings,
    *,
    curso: Curso,
    tarea: Tarea,
    membresia: MembresiaCurso,
    accion_intencion: str,
    rutas: dict[str, str],
    operacion: str,
    contenido_base64: str | None = None,
) -> None:
    try:
        base = repositorio_base_repo.exigir_base_operable(bd, tarea)
        rutas_validas = {k: repositorio_base_repo.exigir_ruta(v) for k, v in rutas.items()}
        if contenido_base64 is not None:
            repositorio_base_repo.validar_contenido_base64(contenido_base64)
    except RechazoTarea as exc:
        raise _http_rechazo(exc) from None
    repositorio_base_repo.registrar_intencion_archivo(
        bd,
        curso=curso,
        base=base,
        accion=accion_intencion,
        rutas=rutas_validas,
        actor_usuario_id=membresia.usuario_id,
    )
    bd.commit()

    cliente, token = _github(settings, curso)
    try:
        if operacion == "escribir":
            assert contenido_base64 is not None
            repositorio_base_repo.escribir_archivo(
                bd,
                cliente,
                token,
                curso=curso,
                base=base,
                ruta=rutas_validas["ruta"],
                contenido_base64=contenido_base64,
                actor_usuario_id=membresia.usuario_id,
            )
        elif operacion == "borrar":
            repositorio_base_repo.borrar_archivo(
                bd,
                cliente,
                token,
                curso=curso,
                base=base,
                ruta=rutas_validas["ruta"],
                actor_usuario_id=membresia.usuario_id,
            )
        else:
            repositorio_base_repo.renombrar_archivo(
                bd,
                cliente,
                token,
                curso=curso,
                base=base,
                desde=rutas_validas["desde"],
                hacia=rutas_validas["hacia"],
                actor_usuario_id=membresia.usuario_id,
            )
    except RechazoTarea as exc:
        raise _http_rechazo(exc) from None
    except RechazoProveedorGithub as exc:
        raise _http_rechazo_github(exc) from None
    except FalloProveedorGithub as exc:
        raise _http_fallo_github(exc) from None


@router.post(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/repositorio-base/renombrar",
    response_model=TareaDetalleSalida,
    dependencies=[Depends(exigir_csrf)],
)
def renombrar_archivo_base(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    datos: RenombrarArchivoEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    membresia: MembresiaCurso = Depends(requiere(Permiso.TAREA_ADMINISTRAR)),
) -> TareaDetalleSalida:
    curso = _curso(bd, curso_id)
    tarea = _tarea(bd, curso_id, tarea_id)
    _ejecutar_escritura_archivo(
        bd,
        settings,
        curso=curso,
        tarea=tarea,
        membresia=membresia,
        accion_intencion="ARCHIVO_BASE_RENOMBRADO_SOLICITADO",
        rutas={"desde": datos.desde, "hacia": datos.hacia},
        operacion="renombrar",
    )
    return _detalle(bd, curso=curso, tarea=tarea, settings=settings)


@router.put(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/repositorio-base/archivos/{ruta:path}",
    response_model=TareaDetalleSalida,
    dependencies=[Depends(exigir_csrf)],
)
def escribir_archivo_base(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    ruta: str,
    datos: EscribirArchivoEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    membresia: MembresiaCurso = Depends(requiere(Permiso.TAREA_ADMINISTRAR)),
) -> TareaDetalleSalida:
    curso = _curso(bd, curso_id)
    tarea = _tarea(bd, curso_id, tarea_id)
    _ejecutar_escritura_archivo(
        bd,
        settings,
        curso=curso,
        tarea=tarea,
        membresia=membresia,
        accion_intencion="ARCHIVO_BASE_ESCRITURA_SOLICITADA",
        rutas={"ruta": ruta},
        operacion="escribir",
        contenido_base64=datos.contenido_base64,
    )
    return _detalle(bd, curso=curso, tarea=tarea, settings=settings)


@router.delete(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/repositorio-base/archivos/{ruta:path}",
    response_model=TareaDetalleSalida,
    dependencies=[Depends(exigir_csrf)],
)
def borrar_archivo_base(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    ruta: str,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    membresia: MembresiaCurso = Depends(requiere(Permiso.TAREA_ADMINISTRAR)),
) -> TareaDetalleSalida:
    curso = _curso(bd, curso_id)
    tarea = _tarea(bd, curso_id, tarea_id)
    _ejecutar_escritura_archivo(
        bd,
        settings,
        curso=curso,
        tarea=tarea,
        membresia=membresia,
        accion_intencion="ARCHIVO_BASE_BORRADO_SOLICITADO",
        rutas={"ruta": ruta},
        operacion="borrar",
    )
    return _detalle(bd, curso=curso, tarea=tarea, settings=settings)


@router.get(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/repositorio-base/archivos/{ruta:path}",
    response_model=PrevisualizacionSalida,
)
def previsualizar_archivo_base(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    ruta: str,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> PrevisualizacionSalida:
    curso = _curso(bd, curso_id)
    tarea = _tarea(bd, curso_id, tarea_id)
    try:
        base = repositorio_base_repo.exigir_base_operable(bd, tarea)
        ruta_valida = repositorio_base_repo.exigir_ruta(ruta)
    except RechazoTarea as exc:
        raise _http_rechazo(exc) from None
    cliente, token = _github(settings, curso)
    try:
        vista = repositorio_base_repo.previsualizar_archivo(
            cliente, token, curso=curso, base=base, ruta=ruta_valida
        )
    except RechazoTarea as exc:
        raise _http_rechazo(exc) from None
    except RechazoProveedorGithub as exc:
        raise _http_rechazo_github(exc) from None
    except FalloProveedorGithub as exc:
        raise _http_fallo_github(exc) from None
    return PrevisualizacionSalida(
        ruta=vista.ruta,
        tamano_bytes=vista.tamano_bytes,
        texto=vista.texto,
        motivo_sin_texto=vista.motivo_sin_texto,
    )
