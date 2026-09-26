"""Versiones de entrega: progreso de captura, ficha del sujeto, acciones
manuales y acceso directo auditado (SPEC 09 S9.6-S9.9, S9.12; Etapa F4).

Las lecturas no llaman a GitHub (Ley 1). Las tres acciones manuales son
escrituras sincronas que si hablan con GitHub, porque «fijar un SHA» tiene que
rechazarse antes de escribir nada si el commit no es del repositorio
(CA-9.8-05); la etiqueta se sigue creando en segundo plano.

«Recapturar con otra fecha» y «fijar en un commit» exigen el rol `PROFESOR`,
no solo el permiso: es la unica accion que decide que codigo se corrige sin
huella en Canvas (S9.8.8; `ACCIONES_SOLO_PROFESOR`).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adaptadores import actividad_repo, versiones_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.bitacora_repo import registrar as registrar_bitacora
from app.adaptadores.cliente_github import (
    FalloProveedorGithub,
    RechazoProveedorGithub,
    crear_cliente_github_desde_config,
)
from app.adaptadores.modelos_aprovisionamiento import FechaEfectiva, Repositorio, Sujeto
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_github import AccesoDocenteRepositorio
from app.adaptadores.modelos_identidad import Usuario
from app.adaptadores.modelos_padron import Estudiante, Grupo
from app.adaptadores.modelos_tarea import Entrega
from app.adaptadores.modelos_version import VersionEntrega
from app.api.dependencias import exigir_csrf, obtener_sesion_bd, requiere
from app.dominio.estados import (
    EstadoAccesoDocente,
    EstadoFechaEfectiva,
    OrigenCaptura,
    RolMembresia,
    ViaAccesoDocente,
)
from app.dominio.fechas import formatear_fecha
from app.dominio.permisos import Permiso
from app.dominio.versiones import (
    EntregaDelSujeto,
    entrega_anterior,
    url_arbol,
    url_comparacion,
    url_zip,
)
from app.infraestructura.config import obtener_configuracion

router = APIRouter(tags=["versiones"])

_CAPTURA_TARDIA = timedelta(minutes=15)  # S9.6.2


def _curso(bd: Session, curso_id: uuid.UUID) -> Curso:
    curso = bd.get(Curso, curso_id)
    if curso is None:
        raise HTTPException(status_code=404)
    return curso


def _entrega(bd: Session, curso_id: uuid.UUID, entrega_id: uuid.UUID) -> Entrega:
    entrega = (
        bd.query(Entrega)
        .filter(Entrega.id == entrega_id, Entrega.curso_id == curso_id)
        .one_or_none()
    )
    if entrega is None:
        raise HTTPException(status_code=404)
    return entrega


def _sujeto(bd: Session, entrega: Entrega, sujeto_id: uuid.UUID) -> Sujeto:
    sujeto = (
        bd.query(Sujeto)
        .filter(Sujeto.id == sujeto_id, Sujeto.tarea_id == entrega.tarea_id)
        .one_or_none()
    )
    if sujeto is None:
        raise HTTPException(status_code=404)
    return sujeto


def _nombre_sujeto(bd: Session, sujeto: Sujeto) -> str:
    if sujeto.grupo_id is not None:
        grupo = bd.get(Grupo, sujeto.grupo_id)
        return grupo.nombre if grupo is not None else "—"
    estudiante = bd.get(Estudiante, sujeto.estudiante_id)
    return estudiante.nombre if estudiante is not None else "—"


def _http(exc: versiones_repo.RechazoVersion) -> HTTPException:
    return HTTPException(status_code=422, detail={"motivo": exc.motivo, "detalle": exc.detalle})


# --- Salidas ---


class EnlacesSalida(BaseModel):
    arbol: str | None
    comparacion: str | None
    zip: str | None


class VersionSalida(BaseModel):
    id: uuid.UUID
    intento: int
    vigente: bool
    estado: str
    motivo: str | None
    commit_sha: str | None
    commit_mensaje: str | None
    rama: str | None
    fecha_corte: str
    capturada_en: str
    captura_tardia_minutos: int | None
    tag_nombre: str | None
    tag_estado: str
    tag_motivo: str | None
    tag_error: str | None
    advertencias: list[str]
    verificacion: dict[str, Any]
    origen_captura: str
    motivo_manual: str | None
    creada_por: str | None
    integrantes: list[dict[str, Any]]
    sujeto_etiqueta: str
    repositorio_full_name: str | None
    fecha_origen: str | None
    canvas_override_id: int | None
    comparacion_base: str | None
    commits_posteriores_al_cierre: int | None
    enlaces: EnlacesSalida


def _salida(bd: Session, version: VersionEntrega, zona: str) -> VersionSalida:
    base = f"/api/cursos/{_curso_de(bd, version)}/versiones/{version.id}/abrir?destino="
    tiene_sha = version.commit_sha is not None and version.repositorio_full_name is not None
    etiqueta_base, _ = _base_de_comparacion(bd, version)
    retraso = version.capturada_en - version.fecha_corte_utc
    autor = (
        bd.get(Usuario, version.creada_por_usuario_id) if version.creada_por_usuario_id else None
    )
    return VersionSalida(
        id=version.id,
        intento=version.intento,
        vigente=version.vigente,
        estado=version.estado,
        motivo=version.motivo,
        commit_sha=version.commit_sha,
        commit_mensaje=version.commit_mensaje,
        rama=version.rama,
        fecha_corte=formatear_fecha(version.fecha_corte_utc, zona),
        capturada_en=formatear_fecha(version.capturada_en, zona),
        captura_tardia_minutos=(
            int(retraso.total_seconds() // 60) if retraso > _CAPTURA_TARDIA else None
        ),
        tag_nombre=version.tag_nombre,
        tag_estado=version.tag_estado,
        tag_motivo=version.tag_motivo,
        tag_error=version.tag_error,
        advertencias=list(version.advertencias or []),
        verificacion=version.verificacion or {},
        origen_captura=version.origen_captura,
        motivo_manual=version.motivo_manual,
        creada_por=autor.nombre if autor is not None else None,
        integrantes=version.integrantes or [],
        sujeto_etiqueta=version.sujeto_etiqueta,
        repositorio_full_name=version.repositorio_full_name,
        fecha_origen=version.fecha_origen,
        canvas_override_id=version.canvas_override_id,
        comparacion_base=etiqueta_base,
        # S9.8.3: derivado del espejo, sin coste de API; nulo si el espejo de
        # ese repositorio aun no tuvo su lectura completa.
        commits_posteriores_al_cierre=_posteriores(bd, version),
        enlaces=EnlacesSalida(
            arbol=f"{base}arbol" if tiene_sha else None,
            comparacion=f"{base}comparacion" if tiene_sha and etiqueta_base else None,
            zip=f"{base}zip" if tiene_sha else None,
        ),
    )


def _posteriores(bd: Session, version: VersionEntrega) -> int | None:
    repositorio = bd.get(Repositorio, version.repositorio_id) if version.repositorio_id else None
    if repositorio is None or not actividad_repo.espejo_fiable(bd, repositorio):
        return None
    return actividad_repo.commits_posteriores_al_cierre(bd, repositorio.id, version.fecha_corte_utc)


def _curso_de(bd: Session, version: VersionEntrega) -> uuid.UUID:
    entrega = bd.get(Entrega, version.entrega_id)
    assert entrega is not None
    return entrega.curso_id


def _base_de_comparacion(bd: Session, version: VersionEntrega) -> tuple[str | None, str | None]:
    """S9.9.3: contra la version vigente de la entrega anterior **para este
    sujeto** (A-173); si no hay, contra el commit inicial del repositorio; si
    tampoco hay, no se ofrece comparacion ni se inventa una base."""
    entrega = bd.get(Entrega, version.entrega_id)
    assert entrega is not None
    filas = (
        bd.query(Entrega.id, Entrega.orden, FechaEfectiva.due_at_utc, Entrega.nombre)
        .join(FechaEfectiva, FechaEfectiva.entrega_id == Entrega.id)
        .filter(
            Entrega.tarea_id == entrega.tarea_id,
            FechaEfectiva.sujeto_id == version.sujeto_id,
            FechaEfectiva.estado == EstadoFechaEfectiva.VIGENTE.value,
        )
        .all()
    )
    anterior_id = entrega_anterior(
        [EntregaDelSujeto(entrega_id=i, orden=o, due_at=d) for i, o, d, _ in filas],
        actual=entrega.id,
    )
    if anterior_id is not None:
        previa = versiones_repo.version_vigente(bd, anterior_id, version.sujeto_id)  # type: ignore[arg-type]
        if previa is not None and previa.commit_sha is not None:
            nombre = next(n for i, _, _, n in filas if i == anterior_id)
            return f"entrega anterior «{nombre}»", previa.commit_sha
    repositorio = bd.get(Repositorio, version.repositorio_id) if version.repositorio_id else None
    if repositorio is not None and repositorio.commit_inicial_sha:
        return "desde el inicio del repositorio", repositorio.commit_inicial_sha
    return None, None


# --- Lecturas ---


class FilaCapturaSalida(BaseModel):
    sujeto_id: uuid.UUID
    sujeto: str
    fecha: str
    estado_captura: str
    version: VersionSalida | None


class ProgresoCapturaSalida(BaseModel):
    entrega_id: uuid.UUID
    estado_validacion: str
    vencidas: int
    registradas: int
    por_estado: dict[str, int]
    capturas_tardias: int
    filas: list[FilaCapturaSalida]


@router.get(
    "/api/cursos/{curso_id}/entregas/{entrega_id}/progreso-captura",
    response_model=ProgresoCapturaSalida,
)
def progreso_captura(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> ProgresoCapturaSalida:
    """S9.6.1: la barra «registrando versiones: N de M» se calcula sobre las
    fechas efectivas vencidas, no sobre filas de `version_entrega`."""
    curso = _curso(bd, curso_id)
    entrega = _entrega(bd, curso_id, entrega_id)
    ahora = ahora_utc()
    fechas = {
        f.sujeto_id: f
        for f in bd.query(FechaEfectiva).filter(
            FechaEfectiva.entrega_id == entrega.id,
            FechaEfectiva.estado == EstadoFechaEfectiva.VIGENTE.value,
        )
    }
    vigentes = {
        v.sujeto_id: v
        for v in bd.query(VersionEntrega).filter(
            VersionEntrega.entrega_id == entrega.id, VersionEntrega.vigente.is_(True)
        )
    }
    filas: list[FilaCapturaSalida] = []
    por_estado: dict[str, int] = {}
    vencidas = tardias = 0
    for sujeto in bd.query(Sujeto).filter(Sujeto.tarea_id == entrega.tarea_id):
        fecha = fechas.get(sujeto.id)
        version = vigentes.get(sujeto.id)
        if fecha is None and version is None:
            if not sujeto.activo:
                continue
            estado = "NO_APLICA"  # «esta entrega no aplica a este sujeto» (S9.3.2)
        elif version is not None:
            estado = version.estado
            por_estado[estado] = por_estado.get(estado, 0) + 1
            if version.capturada_en - version.fecha_corte_utc > _CAPTURA_TARDIA:
                tardias += 1
        elif fecha is not None and fecha.due_at_utc is None:
            estado = "SIN_FECHA"
        elif fecha is not None and fecha.due_at_utc is not None and fecha.due_at_utc > ahora:
            estado = "PENDIENTE_DE_CIERRE"
        else:
            estado = "REGISTRANDO"
        if fecha is not None and fecha.due_at_utc is not None and fecha.due_at_utc <= ahora:
            vencidas += 1
        filas.append(
            FilaCapturaSalida(
                sujeto_id=sujeto.id,
                sujeto=_nombre_sujeto(bd, sujeto),
                fecha=formatear_fecha(fecha.due_at_utc if fecha else None, curso.zona_horaria),
                estado_captura=estado,
                version=_salida(bd, version, curso.zona_horaria) if version is not None else None,
            )
        )
    return ProgresoCapturaSalida(
        entrega_id=entrega.id,
        estado_validacion=entrega.estado_validacion,
        vencidas=vencidas,
        registradas=sum(por_estado.values()),
        por_estado=por_estado,
        capturas_tardias=tardias,
        filas=sorted(filas, key=lambda f: f.sujeto),
    )


class FichaVersionSalida(BaseModel):
    sujeto: str
    vigente: VersionSalida | None
    anteriores: list[VersionSalida]
    acceso_docente: str | None


@router.get(
    "/api/cursos/{curso_id}/entregas/{entrega_id}/sujetos/{sujeto_id}/version",
    response_model=FichaVersionSalida,
)
def ficha_version(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    sujeto_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> FichaVersionSalida:
    """La version vigente y todas las supersedidas: nada se descarta nunca
    (R2.4.7). Los recuentos de commits posteriores al cierre necesitan el
    espejo de actividad (Bloque 2). TODO(etapa-F5)."""
    curso = _curso(bd, curso_id)
    entrega = _entrega(bd, curso_id, entrega_id)
    sujeto = _sujeto(bd, entrega, sujeto_id)
    todas = (
        bd.query(VersionEntrega)
        .filter(VersionEntrega.entrega_id == entrega.id, VersionEntrega.sujeto_id == sujeto.id)
        .order_by(VersionEntrega.intento)
        .all()
    )
    vigente = next((v for v in todas if v.vigente), None)
    return FichaVersionSalida(
        sujeto=_nombre_sujeto(bd, sujeto),
        vigente=_salida(bd, vigente, curso.zona_horaria) if vigente is not None else None,
        anteriores=[_salida(bd, v, curso.zona_horaria) for v in todas if not v.vigente],
        acceso_docente=_estado_acceso_docente(bd, vigente.repositorio_id if vigente else None),
    )


def _estado_acceso_docente(bd: Session, repositorio_id: uuid.UUID | None) -> str | None:
    if repositorio_id is None:
        return None
    fila = (
        bd.query(AccesoDocenteRepositorio)
        .filter(
            AccesoDocenteRepositorio.repositorio_id == repositorio_id,
            AccesoDocenteRepositorio.via == ViaAccesoDocente.TEAM.value,
        )
        .first()
    )
    return fila.estado if fila is not None else None


# --- Acciones manuales (S9.8.8) ---


class CapturarAhoraEntrada(BaseModel):
    motivo_manual: str


class RecapturarEntrada(BaseModel):
    fecha_corte: datetime
    motivo_manual: str


class FijarShaEntrada(BaseModel):
    sha: str
    motivo_manual: str


def _ejecutar_captura(
    bd: Session,
    *,
    curso: Curso,
    entrega: Entrega,
    sujeto: Sujeto,
    corte: datetime,
    origen: OrigenCaptura,
    actor: uuid.UUID,
    motivo_manual: str,
    sha: str | None = None,
) -> VersionSalida:
    cliente = crear_cliente_github_desde_config(obtener_configuracion())
    try:
        version = versiones_repo.capturar(
            bd,
            cliente,
            entrega_id=entrega.id,
            sujeto_id=sujeto.id,
            corte=corte,
            origen=origen,
            actor_usuario_id=actor,
            motivo_manual=motivo_manual,
            sha_fijado=sha,
        )
    except versiones_repo.RechazoVersion as exc:
        raise _http(exc) from None
    except versiones_repo.GithubSinAcceso:
        raise HTTPException(
            status_code=503,
            detail={
                "motivo": "GITHUB_SIN_ACCESO",
                "detalle": "La aplicación no tiene acceso a la organización de GitHub en este "
                "momento. Revisa la instalación en «Vinculación» y vuelve a intentarlo.",
            },
        ) from None
    except (RechazoProveedorGithub, FalloProveedorGithub) as exc:
        raise HTTPException(
            status_code=502, detail={"motivo": "GITHUB_NO_RESPONDIO", "detalle": str(exc)}
        ) from None
    if version is None:
        raise HTTPException(
            status_code=409,
            detail={
                "motivo": "ENTREGA_NO_CAPTURABLE",
                "detalle": "Esta entrega está excluida o ya no existe en Canvas.",
            },
        )
    return _salida(bd, version, curso.zona_horaria)


@router.post(
    "/api/cursos/{curso_id}/entregas/{entrega_id}/sujetos/{sujeto_id}/version/capturar-ahora",
    response_model=VersionSalida,
    dependencies=[Depends(exigir_csrf)],
)
def capturar_ahora(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    sujeto_id: uuid.UUID,
    datos: CapturarAhoraEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.TAREA_ADMINISTRAR)),
) -> VersionSalida:
    """Accion 1: adelanta el trabajo sin cambiar la fecha de corte, y solo sin
    version vigente; pulsarlo dos veces no captura dos veces."""
    curso = _curso(bd, curso_id)
    entrega = _entrega(bd, curso_id, entrega_id)
    sujeto = _sujeto(bd, entrega, sujeto_id)
    try:
        motivo = versiones_repo.validar_motivo_manual(datos.motivo_manual)
        corte = versiones_repo.corte_para_capturar_ahora(bd, entrega=entrega, sujeto=sujeto)
    except versiones_repo.RechazoVersion as exc:
        raise _http(exc) from None
    return _ejecutar_captura(
        bd,
        curso=curso,
        entrega=entrega,
        sujeto=sujeto,
        corte=corte,
        origen=OrigenCaptura.MANUAL_AHORA,
        actor=membresia.usuario_id,
        motivo_manual=motivo,
    )


@router.post(
    "/api/cursos/{curso_id}/entregas/{entrega_id}/sujetos/{sujeto_id}/version/recapturar",
    response_model=VersionSalida,
    dependencies=[Depends(exigir_csrf)],
)
def recapturar(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    sujeto_id: uuid.UUID,
    datos: RecapturarEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(
        requiere(Permiso.TAREA_ADMINISTRAR, rol_minimo=RolMembresia.PROFESOR)
    ),
) -> VersionSalida:
    """Accion 2 (solo `PROFESOR`): una fila nueva con la fecha indicada."""
    curso = _curso(bd, curso_id)
    entrega = _entrega(bd, curso_id, entrega_id)
    sujeto = _sujeto(bd, entrega, sujeto_id)
    corte = datos.fecha_corte
    if corte.tzinfo is None:
        raise _http(
            versiones_repo.RechazoVersion(
                "CORTE_SIN_ZONA", "La fecha de corte debe traer su zona horaria."
            )
        )
    try:
        motivo = versiones_repo.validar_motivo_manual(datos.motivo_manual)
        versiones_repo.validar_corte_manual(bd, sujeto=sujeto, corte=corte)
    except versiones_repo.RechazoVersion as exc:
        raise _http(exc) from None
    return _ejecutar_captura(
        bd,
        curso=curso,
        entrega=entrega,
        sujeto=sujeto,
        corte=corte,
        origen=OrigenCaptura.MANUAL_FECHA,
        actor=membresia.usuario_id,
        motivo_manual=motivo,
    )


@router.post(
    "/api/cursos/{curso_id}/entregas/{entrega_id}/sujetos/{sujeto_id}/version/fijar-sha",
    response_model=VersionSalida,
    dependencies=[Depends(exigir_csrf)],
)
def fijar_sha(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    sujeto_id: uuid.UUID,
    datos: FijarShaEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(
        requiere(Permiso.TAREA_ADMINISTRAR, rol_minimo=RolMembresia.PROFESOR)
    ),
) -> VersionSalida:
    """Accion 3 (solo `PROFESOR`): el SHA se verifica contra GitHub antes de
    escribir nada; uno de otro repositorio se rechaza (CA-9.8-05)."""
    curso = _curso(bd, curso_id)
    entrega = _entrega(bd, curso_id, entrega_id)
    sujeto = _sujeto(bd, entrega, sujeto_id)
    try:
        motivo = versiones_repo.validar_motivo_manual(datos.motivo_manual)
    except versiones_repo.RechazoVersion as exc:
        raise _http(exc) from None
    fecha = (
        bd.query(FechaEfectiva)
        .filter(
            FechaEfectiva.entrega_id == entrega.id,
            FechaEfectiva.sujeto_id == sujeto.id,
            FechaEfectiva.estado == EstadoFechaEfectiva.VIGENTE.value,
        )
        .one_or_none()
    )
    corte = fecha.due_at_utc if fecha is not None and fecha.due_at_utc else ahora_utc()
    return _ejecutar_captura(
        bd,
        curso=curso,
        entrega=entrega,
        sujeto=sujeto,
        corte=corte,
        origen=OrigenCaptura.MANUAL_SHA,
        actor=membresia.usuario_id,
        motivo_manual=motivo,
        sha=datos.sha.strip().lower(),
    )


@router.post(
    "/api/cursos/{curso_id}/entregas/{entrega_id}/registrar-versiones",
    status_code=202,
    dependencies=[Depends(exigir_csrf)],
)
def registrar_versiones(
    curso_id: uuid.UUID,
    entrega_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.TAREA_ADMINISTRAR)),
) -> dict[str, int]:
    """S9.6.7: «registrar ahora las versiones con la fecha de cierre de Canvas»
    para una entrega vinculada con la fecha ya vencida. Encola; no captura
    dentro de la peticion."""
    entrega = _entrega(bd, curso_id, entrega_id)
    try:
        encoladas = versiones_repo.registrar_versiones_tras_cierre(
            bd, entrega=entrega, actor_usuario_id=membresia.usuario_id
        )
    except versiones_repo.RechazoVersion as exc:
        raise HTTPException(
            status_code=409, detail={"motivo": exc.motivo, "detalle": exc.detalle}
        ) from None
    return {"encoladas": encoladas}


# --- Acceso directo auditado (S9.9) ---

_MOTIVO_ACCESO = {
    EstadoAccesoDocente.PENDIENTE.value: (
        "ACCESO_DOCENTE_PENDIENTE",
        "Preparando tu acceso al repositorio: el equipo docente todavía no tiene lectura en "
        "GitHub. Se reintenta solo en el próximo ciclo de accesos.",
    ),
    EstadoAccesoDocente.ERROR.value: (
        "ACCESO_DOCENTE_ERROR",
        "GitHub rechazó dar lectura al equipo docente sobre este repositorio. Reintenta desde "
        "la pestaña de repositorios.",
    ),
    EstadoAccesoDocente.REVOCADO.value: (
        "ACCESO_DOCENTE_REVOCADO",
        "El equipo docente ya no tiene lectura sobre este repositorio.",
    ),
}


@router.get("/api/cursos/{curso_id}/versiones/{version_id}/abrir")
def abrir_version(
    curso_id: uuid.UUID,
    version_id: uuid.UUID,
    destino: Literal["arbol", "comparacion", "zip"] = Query(...),
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> RedirectResponse:
    """S9.9.2-S9.9.4: la URL por SHA, nunca por etiqueta; antes de redirigir se
    comprueba el acceso docente --entregar un enlace roto es peor que decir por
    que no esta listo-- y se deja en la bitacora quien abrio que version.
    Cero llamadas externas: la aplicacion no descarga ni guarda codigo."""
    version = bd.get(VersionEntrega, version_id)
    if version is None or _curso_de(bd, version) != curso_id:
        raise HTTPException(status_code=404)
    if version.commit_sha is None or version.repositorio_full_name is None:
        raise HTTPException(
            status_code=409,
            detail={
                "motivo": "SIN_COMMIT",
                "detalle": "Esta versión no tiene un commit registrado que abrir.",
            },
        )
    estado = _estado_acceso_docente(bd, version.repositorio_id)
    if estado != EstadoAccesoDocente.CONCEDIDO.value:
        motivo, detalle = _MOTIVO_ACCESO.get(
            estado or "", ("ACCESO_DOCENTE_PENDIENTE", _MOTIVO_ACCESO["PENDIENTE"][1])
        )
        raise HTTPException(status_code=409, detail={"motivo": motivo, "detalle": detalle})
    if destino == "arbol":
        url = url_arbol(version.repositorio_full_name, version.commit_sha)
    elif destino == "zip":
        url = url_zip(version.repositorio_full_name, version.commit_sha)
    else:
        _, base = _base_de_comparacion(bd, version)
        if base is None:
            raise HTTPException(
                status_code=409,
                detail={
                    "motivo": "SIN_LINEA_BASE",
                    "detalle": "Sin línea base registrada para este repositorio.",
                },
            )
        url = url_comparacion(version.repositorio_full_name, base, version.commit_sha)
    registrar_bitacora(
        bd,
        accion="VERSION_ABIERTA",
        entidad="version_entrega",
        entidad_id=str(version.id),
        actor_usuario_id=membresia.usuario_id,
        curso_id=curso_id,
        despues={"destino": destino, "commit_sha": version.commit_sha},
    )
    return RedirectResponse(url, status_code=307)
