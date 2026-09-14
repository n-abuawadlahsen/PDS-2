"""Paso 2 del asistente de vinculacion: Canvas (SPEC 04 S4.4-S4.5; Etapa P3).

Un unico permiso gobierna todo el capitulo: `curso.administrar`, NO
CONCEDIBLE a un ayudante (S4.3.1). No hay rutas REST fuera de las que
persiste el asistente (docs/PLAN-IMPLEMENTACION.md Etapa P3).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adaptadores import canvas_repo, github_repo
from app.adaptadores.cliente_canvas import FalloProveedorCanvas, crear_cliente_canvas
from app.adaptadores.cliente_github import FalloProveedorGithub, crear_cliente_github_desde_config
from app.adaptadores.modelos_canvas import CredencialCanvas
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_github import EquipoGithubCurso
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.api.dependencias import exigir_csrf, obtener_sesion_bd, requiere, usuario_actual
from app.dominio.permisos import Permiso
from app.dominio.vinculacion_canvas import RechazoVinculacion
from app.dominio.vinculacion_github import RechazoInstalacion
from app.infraestructura.cifrado import Llavero
from app.infraestructura.config import Settings, obtener_configuracion

router = APIRouter(tags=["vinculacion"])


def _llavero(settings: Settings) -> Llavero:
    return Llavero(settings.llavero_cifrado(), settings.app_encryption_key_activa)


class InstanciaSalida(BaseModel):
    base_url: str
    nombre_visible: str


@router.get("/api/canvas/instancias", response_model=list[InstanciaSalida])
def listar_instancias(
    _actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    settings: Settings = Depends(obtener_configuracion),
) -> list[InstanciaSalida]:
    return [
        InstanciaSalida(base_url=i.base_url, nombre_visible=i.nombre_visible)
        for i in settings.instancias_canvas()
    ]


class CursosDisponiblesEntrada(BaseModel):
    token: str
    canvas_base_url: str


@router.post("/api/cursos/{curso_id}/vinculacion/canvas/cursos-disponibles")
def cursos_disponibles(
    datos: CursosDisponiblesEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_ADMINISTRAR)),
) -> list[dict[str, object]]:
    base_url = canvas_repo.normalizar_canvas_base_url(datos.canvas_base_url)
    try:
        canvas_repo.validar_instancia_permitida(
            canvas_base_url=base_url,
            instancias_permitidas=[i.base_url for i in settings.instancias_canvas()],
        )
        cliente = crear_cliente_canvas(modo=settings.canvas_modo, canvas_base_url=base_url)
        return canvas_repo.listar_cursos_disponibles(
            cliente, bd, token=datos.token, canvas_base_url=base_url
        )
    except RechazoVinculacion as exc:
        raise HTTPException(status_code=422, detail=exc.motivo.value) from None
    except FalloProveedorCanvas as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None


class VincularEntrada(BaseModel):
    token: str
    canvas_base_url: str
    canvas_course_id: int


@router.post("/api/cursos/{curso_id}/vinculacion/canvas", dependencies=[Depends(exigir_csrf)])
def vincular_canvas(
    curso_id: uuid.UUID,
    datos: VincularEntrada,
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_ADMINISTRAR)),
) -> dict[str, object]:
    usuario, _ = actual
    curso = bd.query(Curso).filter(Curso.id == curso_id).one_or_none()
    if curso is None:
        raise HTTPException(status_code=404)

    base_url = canvas_repo.normalizar_canvas_base_url(datos.canvas_base_url)
    try:
        canvas_repo.validar_instancia_permitida(
            canvas_base_url=base_url,
            instancias_permitidas=[i.base_url for i in settings.instancias_canvas()],
        )
        cliente = crear_cliente_canvas(modo=settings.canvas_modo, canvas_base_url=base_url)
        resultado = canvas_repo.vincular_canvas(
            bd,
            cliente,
            _llavero(settings),
            curso=curso,
            usuario=usuario,
            token=datos.token,
            canvas_base_url=base_url,
            canvas_course_id=datos.canvas_course_id,
        )
    except RechazoVinculacion as exc:
        detalle: str | object = exc.motivo.value
        if exc.detalle:
            detalle = {"motivo": exc.motivo.value, "curso_ocupante": exc.detalle}
        raise HTTPException(status_code=422, detail=detalle) from None
    except FalloProveedorCanvas as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None

    return {"ok": True, "orden_respaldo": resultado.orden_respaldo, "curso_estado": curso.estado}


class CredencialSalida(BaseModel):
    titular_usuario_id: uuid.UUID
    estado: str
    huella: str
    orden_respaldo: int
    ultimo_chequeo_en: str | None


@router.get("/api/cursos/{curso_id}/vinculacion/canvas", response_model=list[CredencialSalida])
def estado_vinculacion_canvas(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> list[CredencialSalida]:
    """Nunca devuelve el token: ni cifrado ni descifrado (A-034)."""
    filas = (
        bd.query(CredencialCanvas)
        .filter(CredencialCanvas.curso_id == curso_id)
        .order_by(CredencialCanvas.orden_respaldo)
        .all()
    )
    return [
        CredencialSalida(
            titular_usuario_id=f.usuario_id,
            estado=f.estado,
            huella=f.huella,
            orden_respaldo=f.orden_respaldo,
            ultimo_chequeo_en=f.ultimo_chequeo_en.isoformat() if f.ultimo_chequeo_en else None,
        )
        for f in filas
    ]


# --- Paso 3: vinculacion con GitHub (S4.6) ---


class IniciarInstalacionEntrada(BaseModel):
    org_login_sugerido: str | None = None


class IniciarInstalacionSalida(BaseModel):
    instalar_url: str


@router.post(
    "/api/cursos/{curso_id}/vinculacion/github/iniciar",
    response_model=IniciarInstalacionSalida,
    dependencies=[Depends(exigir_csrf)],
)
def iniciar_instalacion_github(
    curso_id: uuid.UUID,
    datos: IniciarInstalacionEntrada,
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_ADMINISTRAR)),
) -> IniciarInstalacionSalida:
    usuario, _ = actual
    curso = bd.query(Curso).filter(Curso.id == curso_id).one_or_none()
    if curso is None:
        raise HTTPException(status_code=404)

    cliente = crear_cliente_github_desde_config(settings)
    try:
        slug = cliente.obtener_slug_app()
    except FalloProveedorGithub as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None

    state = github_repo.iniciar_instalacion(
        bd,
        curso=curso,
        usuario=usuario,
        signing_key=settings.signing_key,
        org_login_sugerido=datos.org_login_sugerido,
    )
    return IniciarInstalacionSalida(
        instalar_url=f"https://github.com/apps/{slug}/installations/new?state={state}"
    )


class CallbackInstalacionEntrada(BaseModel):
    state: str
    installation_id: int | None = None
    setup_action: str | None = None


@router.post("/api/vinculacion/github/callback", dependencies=[Depends(exigir_csrf)])
def callback_instalacion_github(
    datos: CallbackInstalacionEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
) -> dict[str, object]:
    """S4.6.3: los diez retornos posibles al volver de GitHub. `state`
    invalido/caducado nunca vincula por deduccion (S4.6.5): el llamador debe
    ofrecer la pantalla de adopcion explicita en su lugar."""
    try:
        curso = github_repo.resolver_curso_por_state(
            bd, signing_key=settings.signing_key, state=datos.state
        )
    except RechazoInstalacion:
        return {"resultado": "STATE_INVALIDO"}

    if datos.setup_action == "request":
        return {"resultado": "SOLICITUD_PENDIENTE", "curso_id": str(curso.id)}
    if datos.installation_id is None:
        return {"resultado": "SIN_INSTALLATION_ID", "curso_id": str(curso.id)}

    cliente = crear_cliente_github_desde_config(settings)
    try:
        instalacion = github_repo.vincular_instalacion(
            bd, cliente, curso=curso, installation_id=datos.installation_id
        )
        equipo = github_repo.crear_y_poblar_equipo_docente(
            bd, cliente, curso=curso, instalacion=instalacion
        )
    except RechazoInstalacion as exc:
        detalle: str | dict[str, str] = exc.motivo.value
        if exc.detalle:
            detalle = {"motivo": exc.motivo.value, "curso_ocupante": exc.detalle}
        raise HTTPException(status_code=422, detail=detalle) from None
    except FalloProveedorGithub as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None

    return {
        "resultado": "VINCULADO",
        "curso_id": str(curso.id),
        "org_login": instalacion.org_login,
        "equipo_docentes_slug": equipo.team_slug,
        "curso_estado": curso.estado,
    }


class InstalacionHuerfanaSalida(BaseModel):
    installation_id: int
    org_login: str
    actualizada_en: str


@router.get(
    "/api/cursos/{curso_id}/vinculacion/github/huerfanas",
    response_model=list[InstalacionHuerfanaSalida],
)
def listar_instalaciones_huerfanas(
    curso_id: uuid.UUID,
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_ADMINISTRAR)),
) -> list[InstalacionHuerfanaSalida]:
    usuario, _ = actual
    disponibles = github_repo.instalaciones_huerfanas_adoptables(
        bd, usuario=usuario, curso_id=curso_id
    )
    return [
        InstalacionHuerfanaSalida(
            installation_id=i.installation_id,
            org_login=i.org_login,
            actualizada_en=i.actualizada_en.isoformat(),
        )
        for i in disponibles
    ]


class AdoptarInstalacionEntrada(BaseModel):
    installation_id: int
    org_login_confirmado: str


@router.post(
    "/api/cursos/{curso_id}/vinculacion/github/huerfanas/adoptar",
    dependencies=[Depends(exigir_csrf)],
)
def adoptar_instalacion_huerfana(
    curso_id: uuid.UUID,
    datos: AdoptarInstalacionEntrada,
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_ADMINISTRAR)),
) -> dict[str, object]:
    usuario, _ = actual
    curso = bd.query(Curso).filter(Curso.id == curso_id).one_or_none()
    if curso is None:
        raise HTTPException(status_code=404)

    cliente = crear_cliente_github_desde_config(settings)
    try:
        instalacion = github_repo.adoptar_instalacion_huerfana(
            bd,
            curso=curso,
            usuario=usuario,
            installation_id=datos.installation_id,
            org_login_confirmado=datos.org_login_confirmado,
        )
        equipo = github_repo.crear_y_poblar_equipo_docente(
            bd, cliente, curso=curso, instalacion=instalacion
        )
    except RechazoInstalacion as exc:
        detalle: str | dict[str, str] = exc.motivo.value
        if exc.detalle:
            detalle = {"motivo": exc.motivo.value, "curso_ocupante": exc.detalle}
        raise HTTPException(status_code=422, detail=detalle) from None
    except FalloProveedorGithub as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None

    return {
        "ok": True,
        "org_login": instalacion.org_login,
        "equipo_docentes_slug": equipo.team_slug,
    }


class EstadoVinculacionGithubSalida(BaseModel):
    org_login: str | None
    installation_id: int | None
    equipo_docentes_slug: str | None
    curso_estado: str


@router.get(
    "/api/cursos/{curso_id}/vinculacion/github", response_model=EstadoVinculacionGithubSalida
)
def estado_vinculacion_github(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> EstadoVinculacionGithubSalida:
    curso = bd.query(Curso).filter(Curso.id == curso_id).one_or_none()
    if curso is None:
        raise HTTPException(status_code=404)
    equipo = (
        bd.query(EquipoGithubCurso).filter(EquipoGithubCurso.curso_id == curso_id).one_or_none()
    )
    return EstadoVinculacionGithubSalida(
        org_login=curso.github_org_login,
        installation_id=curso.github_installation_id,
        equipo_docentes_slug=equipo.team_slug if equipo else None,
        curso_estado=curso.estado,
    )
