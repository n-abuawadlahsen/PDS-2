"""Correccion: bandeja, estado de la entrega, pantalla, reparto y reclamos
(SPEC 12 S12.4-S12.8, S12.11, S12.15; Etapa F11).

Todo miembro activo lee la matriz completa (`curso.ver`); editar exige
`correccion.corregir` y ser el asignado (el profesor, todas); repartir exige
`correccion.asignar`. Ninguna vista llama a Canvas ni a GitHub: la rubrica se
lee del espejo y los enlaces al codigo pasan por el endpoint auditado de F4.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.adaptadores import bitacora_repo, correccion_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_aprovisionamiento import FechaEfectiva, Sujeto
from app.adaptadores.modelos_correccion import (
    Correccion,
    EstadoCanvasSubmission,
    NotaInternaCorreccion,
)
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_identidad import Usuario
from app.adaptadores.modelos_tarea import Entrega, Tarea
from app.adaptadores.modelos_version import VersionEntrega
from app.api.dependencias import exigir_csrf, obtener_sesion_bd, requiere
from app.dominio.correccion import (
    ETIQUETA_ESTADO,
    ETIQUETA_MOTIVO_NO_PUBLICABLE,
    TERMINALES,
    huella_rubrica,
    suma_rubrica,
)
from app.dominio.estados import CriterioAsignacion, EstadoCorreccion
from app.dominio.fechas import formatear_fecha
from app.dominio.permisos import Permiso, permisos_efectivos
from app.infraestructura.cerrojos import bloquear_equipo

router = APIRouter(tags=["correccion"])

_MOTIVO_SIN_ENLACE = {
    None: "El repositorio todavía no tiene acceso docente registrado.",
    "PENDIENTE": "Preparando tu acceso al repositorio; vuelve a intentarlo en unos minutos.",
    "ERROR": "No se pudo dar acceso docente al repositorio; revisa la pestaña de repositorios.",
    "REVOCADO": "El equipo docente ya no tiene lectura sobre este repositorio.",
}


def _permisos(membresia: MembresiaCurso) -> frozenset[Permiso]:
    return permisos_efectivos(
        rol=membresia.rol, permisos_configurados=frozenset(Permiso(p) for p in membresia.permisos)
    )


def _rechazo(exc: correccion_repo.RechazoCorreccion) -> HTTPException:
    return HTTPException(
        status_code=exc.codigo, detail={"codigo": "CORRECCION", "motivo": exc.motivo}
    )


def _curso(bd: Session, curso_id: uuid.UUID) -> Curso:
    curso = bd.get(Curso, curso_id)
    if curso is None:
        raise HTTPException(status_code=404)
    return curso


def _entrega(bd: Session, curso_id: uuid.UUID, entrega_id: uuid.UUID) -> Entrega:
    entrega = bd.get(Entrega, entrega_id)
    if entrega is None or entrega.curso_id != curso_id:
        raise HTTPException(status_code=404)
    return entrega


# --- Bandeja (S12.6) ---


@router.get("/api/cursos/{curso_id}/correccion")
def bandeja(
    curso_id: uuid.UUID,
    response: Response,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> dict[str, Any]:
    curso = _curso(bd, curso_id)
    permisos = _permisos(membresia)
    tareas = (
        bd.query(Tarea)
        .filter(Tarea.curso_id == curso.id, Tarea.estado != "BORRADOR")
        .order_by(Tarea.nombre)
        .all()
    )
    mias = correccion_repo.mis_asignaciones(bd, curso, membresia)
    nuevas = sum(1 for m in mias if m["nueva"])
    sin_corrector = (
        bd.query(Correccion)
        .join(Entrega, Entrega.id == Correccion.entrega_id)
        .filter(
            Entrega.curso_id == curso.id, Correccion.estado == EstadoCorreccion.SIN_CORRECTOR.value
        )
        .count()
    )
    membresia.correccion_vista_en = ahora_utc()
    response.headers["X-Llamadas-Externas"] = "0"
    return {
        "mis_asignaciones": mias,
        "contador": {
            "asignadas": len(mias),
            "corregidas": sum(
                1
                for m in mias
                if m["estado"]
                not in (EstadoCorreccion.ASIGNADA.value, EstadoCorreccion.EN_CURSO.value)
            ),
            "publicadas": sum(1 for m in mias if m["estado"] in TERMINALES),
        },
        "nuevas": nuevas,
        "sin_corrector": sin_corrector,
        "puede_repartir": curso.estado != "ARCHIVADO" and Permiso.CORRECCION_ASIGNAR in permisos,
        "puede_publicar": curso.estado != "ARCHIVADO" and Permiso.NOTA_PUBLICAR in permisos,
        "es_profesor": membresia.rol == "PROFESOR",
        "tareas": [
            {
                "id": str(t.id),
                "nombre": t.nombre,
                "entregas": [
                    {"id": str(e.id), "nombre": e.nombre, "orden": e.orden}
                    for e in bd.query(Entrega)
                    .filter(Entrega.tarea_id == t.id)
                    .order_by(Entrega.orden)
                ],
            }
            for t in tareas
        ],
    }


@router.get("/api/cursos/{curso_id}/tareas/{tarea_id}/correccion/estado")
def estado_de_la_entrega(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    response: Response,
    bd: Session = Depends(obtener_sesion_bd),
    _m: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> dict[str, Any]:
    """Matriz nominal, tres agregados y doble contador en una respuesta
    (A-180); cualquier miembro activo la ve completa (CA-12.4-01)."""
    curso = _curso(bd, curso_id)
    tarea = bd.get(Tarea, tarea_id)
    if tarea is None or tarea.curso_id != curso_id:
        raise HTTPException(status_code=404)
    response.headers["X-Llamadas-Externas"] = "0"
    return correccion_repo.matriz(bd, curso, tarea)


# --- Pantalla de correccion (S12.8) ---


def _version(bd: Session, c: Correccion) -> VersionEntrega | None:
    return bd.get(VersionEntrega, c.version_entrega_id) if c.version_entrega_id else None


@router.get("/api/cursos/{curso_id}/correccion/{entrega_id}/{sujeto_id}")
def pantalla(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    sujeto_id: uuid.UUID,
    response: Response,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> dict[str, Any]:
    curso = _curso(bd, curso_id)
    entrega = _entrega(bd, curso_id, entrega_id)
    correccion_repo.asegurar_filas(bd, entrega)
    try:
        c, a = correccion_repo.fila(bd, entrega.id, sujeto_id)
    except correccion_repo.RechazoCorreccion as exc:
        raise _rechazo(exc) from exc
    propietario = correccion_repo.es_propietario(membresia, a)
    if propietario:
        correccion_repo.abrir(bd, c, a, membresia=membresia, curso_id=curso.id)
    sujeto = bd.get(Sujeto, sujeto_id)
    assert sujeto is not None
    nombre, _ = correccion_repo.nombre_de_sujeto(bd, sujeto)
    miembros = correccion_repo.integrantes(bd, sujeto)
    tarea = bd.get(Tarea, entrega.tarea_id)
    fecha = (
        bd.query(FechaEfectiva)
        .filter(
            FechaEfectiva.entrega_id == entrega.id,
            FechaEfectiva.sujeto_id == sujeto_id,
            FechaEfectiva.estado == "VIGENTE",
        )
        .one_or_none()
    )
    version = _version(bd, c)
    repo = correccion_repo.repositorio_de(bd, sujeto_id)
    acceso = correccion_repo.acceso_docente(bd, repo.id if repo else None)
    criterios, ajustes, usar_rubrica = correccion_repo.rubrica_de(bd, entrega)
    huella = huella_rubrica(criterios, ajustes) if criterios else None
    corrector = None
    if a.membresia_id:
        m = bd.get(MembresiaCurso, a.membresia_id)
        u = bd.get(Usuario, m.usuario_id) if m else None
        corrector = u.nombre if u else None
    permisos = _permisos(membresia)
    orden = correccion_repo.orden_de_recorrido(bd, entrega)
    posicion = orden.index(sujeto_id) if sujeto_id in orden else 0
    pendientes = {
        s
        for (s,) in bd.query(Correccion.sujeto_id).filter(
            Correccion.entrega_id == entrega.id,
            Correccion.estado.in_(
                (EstadoCorreccion.ASIGNADA.value, EstadoCorreccion.EN_CURSO.value)
            ),
        )
    }
    siguiente_sin_corregir = (
        next(
            (
                orden[(posicion + i) % len(orden)]
                for i in range(1, len(orden) + 1)
                if orden[(posicion + i) % len(orden)] in pendientes
                and orden[(posicion + i) % len(orden)] != sujeto_id
            ),
            None,
        )
        if orden
        else None
    )
    historial = []
    for previa in (
        bd.query(Entrega)
        .filter(Entrega.tarea_id == entrega.tarea_id, Entrega.orden < entrega.orden)
        .order_by(Entrega.orden)
    ):
        cp = (
            bd.query(Correccion)
            .filter(Correccion.entrega_id == previa.id, Correccion.sujeto_id == sujeto_id)
            .one_or_none()
        )
        historial.append(
            {
                "entrega": previa.nombre,
                "estado": ETIQUETA_ESTADO[cp.estado] if cp else "Sin corrección",
                "nota_publicada": cp.nota_local if cp and cp.estado in TERMINALES else None,
            }
        )
    canvas = {m.id: bd.get(EstadoCanvasSubmission, (entrega.id, m.id)) for m in miembros}
    notas = (
        bd.query(NotaInternaCorreccion)
        .filter(NotaInternaCorreccion.correccion_id == c.id)
        .order_by(NotaInternaCorreccion.creada_en)
        .all()
    )
    response.headers["X-Llamadas-Externas"] = "0"
    return {
        "entrega": {
            "id": str(entrega.id),
            "nombre": entrega.nombre,
            "tarea_id": str(entrega.tarea_id),
            "tarea": tarea.nombre if tarea else "",
            "grading_type": entrega.grading_type or "points",
            "puntos_posibles": entrega.puntos_posibles,
            "fecha_efectiva": formatear_fecha(fecha.due_at_utc, curso.zona_horaria)
            if fecha and fecha.due_at_utc
            else None,
            "origen_fecha": fecha.origen if fecha else None,
        },
        "sujeto": {
            "id": str(sujeto.id),
            "nombre": nombre,
            "integrantes": [m.nombre for m in miembros],
            "activo": sujeto.activo,
        },
        "estado": c.estado,
        "etiqueta": ETIQUETA_ESTADO[c.estado],
        "corrector": corrector,
        "es_propietario": propietario,
        "puede_publicar": Permiso.NOTA_PUBLICAR in permisos,
        "titular": _titular(bd, curso),
        "publicable": c.publicable,
        "motivo_no_publicable": ETIQUETA_MOTIVO_NO_PUBLICABLE.get(c.motivo_no_publicable or ""),
        "banderas": {
            "version_desactualizada": c.version_desactualizada,
            "reclamo_abierto": c.reclamo_abierto,
            "sin_commits": c.sin_commits,
            "reconocimiento_sin_codigo": c.reconocimiento_sin_codigo,
        },
        "version": None
        if version is None
        else {
            "id": str(version.id),
            "estado": version.estado,
            "sha": version.commit_sha,
            "sha_corto": version.commit_sha[:7] if version.commit_sha else None,
            "tag": version.tag_nombre,
            "repositorio": version.repositorio_full_name,
            "fecha_corte": formatear_fecha(version.fecha_corte_utc, curso.zona_horaria),
            "capturada_en": version.capturada_en.isoformat(),
        },
        "repositorio_estado": repo.estado if repo else None,
        "acceso_docente": acceso,
        "motivo_sin_enlace": None
        if acceso == "CONCEDIDO"
        else _MOTIVO_SIN_ENLACE.get(acceso, _MOTIVO_SIN_ENLACE[None]),
        "borrador": {
            "nota": c.nota_local,
            "rubrica": c.rubrica_local,
            "comentario": c.comentario,
            "version": c.version,
            **correccion_repo.metadatos_borrador(bd, c),
            "comentario_renderizado": correccion_repo.comentario_para_canvas(bd, c, entrega, curso),
        }
        if propietario
        else None,
        "rubrica": {
            "criterios": criterios,
            "ajustes": ajustes,
            "usar_para_calificar": usar_rubrica,
            "suma_sugerida": suma_rubrica(criterios, c.rubrica_local) if propietario else None,
            "cambio_sin_revisar": bool(
                criterios
                and c.huella_rubrica is not None
                and c.huella_rubrica != huella
                and c.rubrica_revisada_en is None
            ),
        },
        "notas_internas": [
            {
                "clase": n.clase,
                "texto": n.texto if propietario or n.clase != "NOTA" else None,
                "desenlace": n.desenlace_reclamo,
                "creada_en": n.creada_en.isoformat(),
            }
            for n in notas
        ],
        "historial": historial,
        "canvas": [
            {
                "estudiante": m.nombre,
                "score": float(fila.score) if fila and fila.score is not None else None,
                "calificada_en": fila.graded_at.isoformat() if fila and fila.graded_at else None,
            }
            for m, fila in ((m, canvas[m.id]) for m in miembros)
        ],
        "navegacion": {
            "posicion": posicion + 1,
            "total": len(orden),
            "anterior": str(orden[posicion - 1]) if posicion > 0 else None,
            "siguiente": str(orden[posicion + 1]) if posicion + 1 < len(orden) else None,
            "siguiente_sin_corregir": str(siguiente_sin_corregir)
            if siguiente_sin_corregir
            else None,
        },
    }


def _titular(bd: Session, curso: Curso) -> str:
    from app.adaptadores import canvas_repo

    credencial = canvas_repo.obtener_credencial_operativa(bd, curso.id)
    usuario = bd.get(Usuario, credencial.usuario_id) if credencial else None
    return usuario.nombre if usuario else "el profesor titular"


class BorradorEntrada(BaseModel):
    nota: str | None = Field(default=None, max_length=20)
    rubrica: dict[str, Any] | None = None
    comentario: str | None = Field(default=None, max_length=8000)
    version: int | None = None


@router.put(
    "/api/cursos/{curso_id}/correccion/{entrega_id}/{sujeto_id}/borrador",
    dependencies=[Depends(exigir_csrf)],
)
def guardar_borrador(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    sujeto_id: uuid.UUID,
    datos: BorradorEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CORRECCION_CORREGIR)),
) -> dict[str, Any]:
    entrega = _entrega(bd, curso_id, entrega_id)
    try:
        c, a = correccion_repo.fila(bd, entrega.id, sujeto_id)
        correccion_repo.guardar_borrador(
            bd,
            c,
            a,
            entrega=entrega,
            membresia=membresia,
            nota=datos.nota,
            rubrica=datos.rubrica,
            comentario=datos.comentario,
            version_esperada=datos.version,
        )
    except correccion_repo.RechazoCorreccion as exc:
        raise _rechazo(exc) from exc
    return {
        "estado": c.estado,
        "version": c.version,
        **correccion_repo.metadatos_borrador(bd, c),
        "comentario_renderizado": correccion_repo.comentario_para_canvas(
            bd, c, entrega, _curso(bd, curso_id)
        ),
    }


@router.post(
    "/api/cursos/{curso_id}/correccion/{entrega_id}/{sujeto_id}/lista",
    dependencies=[Depends(exigir_csrf)],
)
def marcar_lista(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    sujeto_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CORRECCION_CORREGIR)),
) -> dict[str, Any]:
    entrega = _entrega(bd, curso_id, entrega_id)
    try:
        c, a = correccion_repo.fila(bd, entrega.id, sujeto_id)
        correccion_repo.marcar_lista(bd, c, a, entrega=entrega, membresia=membresia)
    except correccion_repo.RechazoCorreccion as exc:
        raise _rechazo(exc) from exc
    return {"estado": c.estado, "nota": c.nota_local}


# --- Notas internas y reclamos (S12.15.1) ---


class NotaEntrada(BaseModel):
    texto: str = Field(min_length=1, max_length=4000)


class CierreReclamoEntrada(BaseModel):
    texto: str = Field(min_length=1, max_length=4000)
    desenlace: str | None = None


@router.post(
    "/api/cursos/{curso_id}/correccion/{entrega_id}/{sujeto_id}/notas",
    dependencies=[Depends(exigir_csrf)],
)
def agregar_nota(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    sujeto_id: uuid.UUID,
    datos: NotaEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CORRECCION_CORREGIR)),
) -> dict[str, str]:
    entrega = _entrega(bd, curso_id, entrega_id)
    try:
        c, a = correccion_repo.fila(bd, entrega.id, sujeto_id)
    except correccion_repo.RechazoCorreccion as exc:
        raise _rechazo(exc) from exc
    if not correccion_repo.es_propietario(membresia, a):
        raise HTTPException(status_code=403, detail="Esta corrección está asignada a otra persona.")
    correccion_repo.agregar_nota_interna(bd, c, membresia=membresia, texto=datos.texto)
    return {"clase": "NOTA"}


@router.post(
    "/api/cursos/{curso_id}/correccion/{entrega_id}/{sujeto_id}/reclamos",
    dependencies=[Depends(exigir_csrf)],
)
def registrar_reclamo(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    sujeto_id: uuid.UUID,
    datos: NotaEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> dict[str, bool]:
    """Cualquier miembro registra el reclamo; no congela la nota ni abre
    incidencia (CA-12.15-01)."""
    entrega = _entrega(bd, curso_id, entrega_id)
    try:
        c, _ = correccion_repo.fila(bd, entrega.id, sujeto_id)
    except correccion_repo.RechazoCorreccion as exc:
        raise _rechazo(exc) from exc
    correccion_repo.agregar_nota_interna(
        bd, c, membresia=membresia, texto=datos.texto, clase="RECLAMO_ABIERTO"
    )
    return {"reclamo_abierto": True}


@router.post(
    "/api/cursos/{curso_id}/correccion/{entrega_id}/{sujeto_id}/reclamos/cerrar",
    dependencies=[Depends(exigir_csrf)],
)
def cerrar_reclamo(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    sujeto_id: uuid.UUID,
    datos: CierreReclamoEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> dict[str, bool]:
    if datos.desenlace not in ("SIN_CAMBIO", "NOTA_CORREGIDA", "ERROR_DE_LA_APLICACION"):
        raise HTTPException(status_code=422, detail="Elige cómo terminó el reclamo.")  # CA-12.15-02
    if datos.desenlace == "NOTA_CORREGIDA" and Permiso.NOTA_PUBLICAR not in _permisos(membresia):
        raise HTTPException(status_code=403, detail={"codigo": "PERMISO_INSUFICIENTE"})
    entrega = _entrega(bd, curso_id, entrega_id)
    try:
        c, _ = correccion_repo.fila(bd, entrega.id, sujeto_id)
    except correccion_repo.RechazoCorreccion as exc:
        raise _rechazo(exc) from exc
    if not c.reclamo_abierto:
        raise HTTPException(status_code=409, detail="No hay un reclamo abierto.")
    correccion_repo.agregar_nota_interna(
        bd,
        c,
        membresia=membresia,
        texto=datos.texto,
        clase="RECLAMO_CERRADO",
        desenlace=datos.desenlace,
    )
    return {"reclamo_abierto": False}


# --- Reparto (S12.5) ---


@router.post(
    "/api/cursos/{curso_id}/correccion/avisar-profesores",
    dependencies=[Depends(exigir_csrf)],
    status_code=202,
)
def avisar_profesores(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    actor: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> dict[str, Any]:
    from app.adaptadores import aviso_correctores_repo

    try:
        cantidad = aviso_correctores_repo.encolar(
            bd, _curso(bd, curso_id), actor, ahora=ahora_utc()
        )
    except correccion_repo.RechazoCorreccion as exc:
        raise _rechazo(exc) from exc
    return {"encolados": cantidad}


@router.get("/api/cursos/{curso_id}/entregas/{entrega_id}/calificacion-individual")
def previsualizar_calificacion_individual(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    response: Response,
    bd: Session = Depends(obtener_sesion_bd),
    _m: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> dict[str, Any]:
    from app.adaptadores import calificacion_grupal_repo

    response.headers["X-Llamadas-Externas"] = "0"
    return calificacion_grupal_repo.previsualizar(bd, _entrega(bd, curso_id, entrega_id))


class RepartoEntrada(BaseModel):
    criterio: CriterioAsignacion
    reasignar: bool = False
    incluir_no_calificables: bool = False
    manual: dict[uuid.UUID, uuid.UUID | None] = {}
    por_seccion: dict[uuid.UUID, uuid.UUID] = {}
    realinear: bool = False


def _propuesta_salida(
    bd: Session, propuesta: correccion_repo.Propuesta, curso_id: uuid.UUID
) -> dict[str, Any]:
    nombres = {m.id: u.nombre for m, u in correccion_repo.correctores(bd, curso_id)}
    return {
        "filas": [
            {
                "sujeto_id": str(f.sujeto_id),
                "sujeto": f.sujeto,
                "actual": nombres.get(f.actual) if f.actual else None,
                "propuesto": nombres.get(f.propuesto) if f.propuesto else None,
                "estado": ETIQUETA_ESTADO[f.estado],
                "sobrescribe": f.sobrescribe,
            }
            for f in propuesta.filas
        ],
        "totales": {
            (nombres.get(uuid.UUID(k), k) if k != "sin corrector" else "Sin corrector"): v
            for k, v in propuesta.totales.items()
        },
        "requiere_decision": [str(x) for x in propuesta.requiere_decision],
    }


@router.get("/api/cursos/{curso_id}/correccion/correctores")
def listar_correctores(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _m: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> list[dict[str, Any]]:
    return [
        {
            "membresia_id": str(m.id),
            "nombre": u.nombre,
            "rol": m.rol,
            "peso": correccion_repo.peso_de(m),
            "sin_github": not u.github_login_declarado,
        }
        for m, u in correccion_repo.correctores(bd, curso_id)
    ]


class PesoEntrada(BaseModel):
    peso: int | None = Field(ge=0, le=10)


@router.patch(
    "/api/cursos/{curso_id}/correccion/correctores/{membresia_id}/peso",
    dependencies=[Depends(exigir_csrf)],
)
def actualizar_peso(
    curso_id: uuid.UUID,
    membresia_id: uuid.UUID,
    datos: PesoEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    actor: MembresiaCurso = Depends(requiere(Permiso.CORRECCION_ASIGNAR)),
) -> dict[str, Any]:
    bloquear_equipo(bd)
    objetivo = (
        bd.query(MembresiaCurso)
        .filter_by(id=membresia_id, curso_id=curso_id)
        .with_for_update()
        .one_or_none()
    )
    if objetivo is None:
        raise HTTPException(status_code=404)
    if objetivo.estado != "ACTIVA":
        raise HTTPException(status_code=409, detail="Ese corrector ya no es miembro activo.")
    antes = objetivo.peso_correccion
    objetivo.peso_correccion = datos.peso
    bitacora_repo.registrar(
        bd,
        accion="PESO_CORRECCION_ACTUALIZADO",
        entidad="membresia_curso",
        entidad_id=str(objetivo.id),
        actor_usuario_id=actor.usuario_id,
        curso_id=curso_id,
        antes={"peso": antes},
        despues={"peso": datos.peso},
    )
    return {"membresia_id": str(objetivo.id), "peso": correccion_repo.peso_de(objetivo)}


@router.post(
    "/api/cursos/{curso_id}/correccion/{entrega_id}/reparto/previsualizar",
    dependencies=[Depends(exigir_csrf)],
)
def previsualizar_reparto(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    datos: RepartoEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    _m: MembresiaCurso = Depends(requiere(Permiso.CORRECCION_ASIGNAR)),
) -> dict[str, Any]:
    """Nada se escribe al previsualizar (S12.5.3)."""
    entrega = _entrega(bd, curso_id, entrega_id)
    propuesta = correccion_repo.previsualizar(
        bd,
        entrega,
        criterio=datos.criterio,
        reasignar=datos.reasignar,
        incluir_no_calificables=datos.incluir_no_calificables,
        manual=datos.manual,
        por_seccion=datos.por_seccion,
    )
    if datos.realinear:
        from app.adaptadores import realineacion_repo

        propuesta = realineacion_repo.previsualizar(bd, entrega)
    return _propuesta_salida(bd, propuesta, curso_id)


@router.post(
    "/api/cursos/{curso_id}/correccion/{entrega_id}/reparto/aplicar",
    dependencies=[Depends(exigir_csrf)],
)
def aplicar_reparto(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    datos: RepartoEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CORRECCION_ASIGNAR)),
) -> dict[str, int]:
    entrega = _entrega(bd, curso_id, entrega_id)
    cambios = correccion_repo.aplicar(
        bd,
        entrega,
        criterio=datos.criterio,
        actor=membresia,
        reasignar=datos.reasignar,
        incluir_no_calificables=datos.incluir_no_calificables,
        manual=datos.manual,
        por_seccion=datos.por_seccion,
        realinear=datos.realinear,
    )
    return {"cambios": cambios}


# --- Etapa F12: publicacion de notas (S12.10, S12.13-S12.15) ---


def _rechazo_publicacion(exc: Any) -> HTTPException:
    return HTTPException(
        status_code=exc.codigo,
        detail={"codigo": "PUBLICACION", "motivo": exc.motivo, **exc.detalle},
    )


class PublicarEntrada(BaseModel):
    resolucion: str | None = Field(default=None, pattern="^PUBLICAR_MIA$")
    version_revisada: bool = False
    confirmacion_reclamo: str | None = None
    reconocimiento_sin_codigo: bool = False


@router.post(
    "/api/cursos/{curso_id}/correccion/{entrega_id}/{sujeto_id}/publicar",
    dependencies=[Depends(exigir_csrf)],
)
def publicar(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    sujeto_id: uuid.UUID,
    datos: PublicarEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.NOTA_PUBLICAR)),
) -> dict[str, Any]:
    """Escritura sincrona #5 (A-169). Con `publicable = false` responde 409
    sin llamar a Canvas (CA-12.3-03)."""
    from app.adaptadores import publicacion_repo

    curso = _curso(bd, curso_id)
    entrega = _entrega(bd, curso_id, entrega_id)
    try:
        c, _ = correccion_repo.fila(bd, entrega.id, sujeto_id)
        return publicacion_repo.publicar(
            bd,
            c,
            entrega=entrega,
            curso=curso,
            actor=membresia,
            resolucion=datos.resolucion,
            version_revisada=datos.version_revisada,
            confirmacion_reclamo=datos.confirmacion_reclamo,
            reconocimiento_sin_codigo=datos.reconocimiento_sin_codigo,
        )
    except correccion_repo.RechazoCorreccion as exc:
        raise _rechazo(exc) from exc
    except publicacion_repo.RechazoPublicacion as exc:
        bd.commit()  # el motivo de no publicable o la incidencia quedan escritos
        raise _rechazo_publicacion(exc) from exc


class MotivoEntrada(BaseModel):
    motivo: str = Field(default="", max_length=2000)


@router.post(
    "/api/cursos/{curso_id}/correccion/{entrega_id}/{sujeto_id}/{accion}",
    dependencies=[Depends(exigir_csrf)],
)
def accion_de_publicacion(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    sujeto_id: uuid.UUID,
    accion: str,
    datos: MotivoEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> dict[str, Any]:
    """reintentar, reabrir y adoptar-canvas exigen `nota.publicar`;
    rubrica-revisada exige ser quien corrige."""
    from app.adaptadores import publicacion_repo

    entrega = _entrega(bd, curso_id, entrega_id)
    try:
        c, a = correccion_repo.fila(bd, entrega.id, sujeto_id)
    except correccion_repo.RechazoCorreccion as exc:
        raise _rechazo(exc) from exc
    if accion == "rubrica-revisada":
        if not correccion_repo.es_propietario(membresia, a):
            raise HTTPException(
                status_code=403, detail="Esta corrección está asignada a otra persona."
            )
        criterios, ajustes, _ = correccion_repo.rubrica_de(bd, entrega)
        c.huella_rubrica = huella_rubrica(criterios, ajustes) if criterios else None
        c.rubrica_revisada_en = ahora_utc()
        return {"revisada": True}
    if accion not in ("reintentar", "reabrir", "adoptar-canvas"):
        raise HTTPException(status_code=404)
    if Permiso.NOTA_PUBLICAR not in _permisos(membresia):
        raise HTTPException(status_code=403, detail={"codigo": "PERMISO_INSUFICIENTE"})
    try:
        if accion == "reintentar":
            publicacion_repo.reintentar(bd, c, actor=membresia, curso_id=curso_id)
        elif accion == "reabrir":
            publicacion_repo.reabrir(bd, c, actor=membresia, curso_id=curso_id, motivo=datos.motivo)
        else:
            publicacion_repo.adoptar_nota_de_canvas(bd, c, entrega=entrega, actor=membresia)
    except publicacion_repo.RechazoPublicacion as exc:
        raise _rechazo_publicacion(exc) from exc
    except correccion_repo.RechazoCorreccion as exc:
        raise _rechazo(exc) from exc
    return {"estado": c.estado, "nota": c.nota_local}


@router.post(
    "/api/cursos/{curso_id}/correccion/{entrega_id}/comprobar",
    status_code=202,
    dependencies=[Depends(exigir_csrf)],
)
def comprobar_contra_canvas(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _m: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> dict[str, object]:
    """Encola la lectura de Canvas y expone su estado consultable (CA-12.11-05)."""
    from app.adaptadores import publicacion_repo

    entrega = _entrega(bd, curso_id, entrega_id)
    motivo = f"manual:{ahora_utc():%Y%m%d%H%M}"
    publicacion_repo.encolar_reconciliacion(bd, curso_id, entrega.id, motivo=motivo)
    from app.adaptadores.modelos_infraestructura import Trabajo

    trabajo = (
        bd.query(Trabajo)
        .filter_by(
            curso_id=curso_id,
            clave_idempotencia=f"{publicacion_repo.TIPO_RECONCILIAR}:{entrega_id}:{motivo}",
        )
        .order_by(Trabajo.creado_en.desc())
        .first()
    )
    return {"encolada": True, "trabajo_id": str(trabajo.id) if trabajo else None}


class SinEntregaEntrada(BaseModel):
    sujeto_ids: list[uuid.UUID]
    nota: str = Field(min_length=1, max_length=20)
    comentario: str = Field(min_length=1, max_length=4000)
    confirmacion: str = Field(min_length=10, max_length=500)


@router.post(
    "/api/cursos/{curso_id}/correccion/{entrega_id}/sin-entrega",
    dependencies=[Depends(exigir_csrf)],
)
def preparar_sin_entrega(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    datos: SinEntregaEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.NOTA_PUBLICAR)),
) -> dict[str, int]:
    """S12.10.7: deja lista la misma nota y comentario para los sujetos sin
    commits elegidos; la publicacion sigue por «publicar seleccionadas», una
    por una y con el pre-chequeo completo."""
    entrega = _entrega(bd, curso_id, entrega_id)
    preparadas = 0
    for sujeto_id in datos.sujeto_ids:
        try:
            c, a = correccion_repo.fila(bd, entrega.id, sujeto_id)
        except correccion_repo.RechazoCorreccion:
            continue
        if (
            not c.sin_commits
            or c.estado in TERMINALES
            or c.estado == EstadoCorreccion.PUBLICANDO.value
        ):
            continue
        if c.estado == EstadoCorreccion.SIN_CORRECTOR.value:
            a.membresia_id = membresia.id
            a.asignada_por = membresia.id
            a.asignada_en = ahora_utc()
            correccion_repo.transicionar(
                bd,
                c,
                EstadoCorreccion.ASIGNADA,
                actor_usuario_id=membresia.usuario_id,
                curso_id=curso_id,
            )
        try:
            correccion_repo.guardar_borrador(
                bd,
                c,
                a,
                entrega=entrega,
                membresia=membresia,
                nota=datos.nota,
                rubrica=None,
                comentario=datos.comentario,
                version_esperada=None,
            )
            correccion_repo.marcar_lista(bd, c, a, entrega=entrega, membresia=membresia)
        except correccion_repo.RechazoCorreccion as exc:
            raise _rechazo(exc) from exc
        preparadas += 1
    from app.adaptadores.bitacora_repo import registrar as registrar_bitacora

    registrar_bitacora(
        bd,
        accion="SIN_ENTREGA_PREPARADA",
        entidad="entrega",
        entidad_id=str(entrega.id),
        actor_usuario_id=membresia.usuario_id,
        curso_id=curso_id,
        despues={"sujetos": preparadas, "confirmacion": datos.confirmacion},
    )
    return {"preparadas": preparadas}
