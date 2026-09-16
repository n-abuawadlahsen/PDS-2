"""`/api/cursos`, equipo docente e invitaciones (SPEC 02 S2.4, S2.5, S2.7, S2.9; Etapa P2)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.adaptadores import (
    acceso_docente_repo,
    bitacora_repo,
    cuenta_repo,
    cursos_repo,
    invitaciones_correo,
)
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_curso import Curso, InvitacionEquipo, MembresiaCurso
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.adaptadores.modelos_infraestructura import Bitacora
from app.adaptadores.proveedor_correo import motivo_bloqueo
from app.api.dependencias import exigir_csrf, obtener_sesion_bd, requiere, usuario_actual
from app.dominio.estados import RolMembresia
from app.dominio.identidad import RechazoCorreo, normalizar_correo_google
from app.dominio.membresia import UltimoProfesorActivo, puede_retirar_o_degradar
from app.dominio.permisos import (
    Permiso,
    PermisoInvalido,
    permisos_efectivos,
    validar_permisos_ayudante,
    validar_permisos_profesor,
)
from app.infraestructura.config import Settings, obtener_configuracion

router = APIRouter(tags=["cursos"])


def _permisos_desde_lista(valores: list[str]) -> frozenset[Permiso]:
    try:
        return frozenset(Permiso(v) for v in valores)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"permiso desconocido: {exc}") from None


def _validar_permisos_de_rol(rol: RolMembresia, permisos: frozenset[Permiso]) -> None:
    try:
        if rol == RolMembresia.PROFESOR:
            validar_permisos_profesor(permisos)
        else:
            validar_permisos_ayudante(permisos)
    except PermisoInvalido as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None


# --------------------------------------------------------------------------
# Esquemas
# --------------------------------------------------------------------------


class CursoSalida(BaseModel):
    id: uuid.UUID
    estado: str
    nombre: str
    codigo: str
    periodo: str
    slug: str
    zona_horaria: str


class CursoEntrada(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)
    codigo: str = Field(min_length=1, max_length=12)
    periodo: str = Field(min_length=6, max_length=6)
    slug: str = Field(min_length=1, max_length=24)
    zona_horaria: str = Field(min_length=1)


class MiembroSalida(BaseModel):
    membresia_id: uuid.UUID
    usuario_id: uuid.UUID
    nombre: str
    email: str
    rol: str
    permisos: list[str]
    estado: str
    retirada_en: datetime | None
    github_login: str | None = None
    github_estado: str | None = None
    github_error: str | None = None


class InvitacionEntrada(BaseModel):
    email: str
    rol: RolMembresia
    permisos: list[str] = Field(default_factory=list)
    github_login_declarado: str | None = None


class InvitacionSalida(BaseModel):
    id: uuid.UUID
    email: str
    rol: str
    permisos: list[str]
    estado: str
    expira_en: datetime
    enlace: str | None = None
    correo_estado: str | None = None
    correo_motivo: str | None = None
    reenvios_restantes: int = 0


class PermisosEntrada(BaseModel):
    permisos: list[str]


class RolEntrada(BaseModel):
    rol: RolMembresia
    permisos: list[str] = Field(default_factory=list)


class ContextoSalida(BaseModel):
    rol: str
    permisos_efectivos: list[str]


class InvitacionPublicaSalida(BaseModel):
    curso_nombre: str
    rol: str
    permisos: list[str]
    email_enmascarado: str
    estado: str


def _enmascarar_email(email: str) -> str:
    local, _, dominio = email.partition("@")
    if len(local) <= 2:
        visible = local[:1]
    else:
        visible = local[:2]
    return f"{visible}{'*' * max(len(local) - len(visible), 3)}@{dominio}"


# --------------------------------------------------------------------------
# Cursos
# --------------------------------------------------------------------------


@router.post("/api/cursos", response_model=CursoSalida, dependencies=[Depends(exigir_csrf)])
def crear_curso(
    datos: CursoEntrada,
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
) -> Curso:
    usuario, _ = actual
    curso = cursos_repo.crear_curso(
        bd,
        creador=usuario,
        nombre=datos.nombre,
        codigo=datos.codigo,
        periodo=datos.periodo,
        slug=datos.slug,
        zona_horaria=datos.zona_horaria,
    )
    bitacora_repo.registrar(
        bd,
        accion="CURSO_CREADO",
        entidad="curso",
        entidad_id=str(curso.id),
        actor_usuario_id=usuario.id,
        curso_id=curso.id,
    )
    return curso


@router.get("/api/cursos", response_model=list[CursoSalida])
def listar_cursos(
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
) -> list[Curso]:
    usuario, _ = actual
    return cursos_repo.listar_cursos_de_usuario(bd, usuario.id)


@router.get("/api/cursos/{curso_id}/contexto", response_model=ContextoSalida)
def obtener_contexto(
    membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> ContextoSalida:
    efectivos = permisos_efectivos(
        rol=membresia.rol, permisos_configurados=frozenset(Permiso(p) for p in membresia.permisos)
    )
    return ContextoSalida(rol=membresia.rol, permisos_efectivos=sorted(p.value for p in efectivos))


# --------------------------------------------------------------------------
# Equipo
# --------------------------------------------------------------------------


@router.get("/api/cursos/{curso_id}/equipo", response_model=list[MiembroSalida])
def listar_equipo(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> list[MiembroSalida]:
    filas = cursos_repo.listar_equipo(bd, curso_id)
    usuarios = {
        u.id: u for u in bd.query(Usuario).filter(Usuario.id.in_([f.usuario_id for f in filas]))
    }
    return [
        MiembroSalida(
            membresia_id=f.id,
            usuario_id=f.usuario_id,
            nombre=usuarios[f.usuario_id].nombre,
            email=usuarios[f.usuario_id].email,
            rol=f.rol,
            permisos=f.permisos,
            estado=f.estado,
            retirada_en=f.retirada_en,
            github_login=usuarios[f.usuario_id].github_login_declarado,
            github_estado=f.org_github_estado,
            github_error=f.org_github_ultimo_error,
        )
        for f in filas
    ]


def _salida_invitacion(bd: Session, i: InvitacionEquipo, settings: Settings) -> InvitacionSalida:
    mensaje = invitaciones_correo.mensaje_de_invitacion(bd, i)
    motivo = mensaje.motivo_estado if mensaje else "ENLACE_ANTIGUO"
    if mensaje and mensaje.estado not in {"ENVIADO", "CANCELADO", "CADUCADO", "SUPRIMIDO"}:
        motivo = motivo_bloqueo(settings, i.email) or mensaje.ultimo_error_literal or motivo
    return InvitacionSalida(
        id=i.id,
        email=i.email,
        rol=i.rol,
        permisos=i.permisos,
        estado="EXPIRADA" if cursos_repo.invitacion_esta_vencida(i) else i.estado,
        expira_en=i.expira_en,
        enlace=invitaciones_correo.enlace(bd, i, settings),
        correo_estado=mensaje.estado if mensaje else None,
        correo_motivo=motivo,
        reenvios_restantes=max(
            0,
            4
            - cursos_repo.contar_reenvios(bd, curso_id=i.curso_id, email_canonico=i.email_canonico),
        ),
    )


def _validar_cuotas_invitacion(bd: Session, curso_id: uuid.UUID, actor_id: uuid.UUID) -> None:
    ahora = ahora_utc()
    if (
        bd.query(InvitacionEquipo)
        .filter(
            InvitacionEquipo.curso_id == curso_id,
            InvitacionEquipo.estado == "PENDIENTE",
            InvitacionEquipo.expira_en > ahora,
        )
        .count()
        >= 20
    ):
        raise HTTPException(
            status_code=409,
            detail="Este curso ya tiene 20 invitaciones pendientes. Revoca una antes de continuar.",
        )
    if (
        bd.query(InvitacionEquipo)
        .filter(
            InvitacionEquipo.invitada_por == actor_id,
            InvitacionEquipo.creada_en > ahora - timedelta(days=1),
        )
        .count()
        >= 50
    ):
        raise HTTPException(
            status_code=429,
            detail="Alcanzaste el límite de 50 invitaciones en 24 horas. Intenta mañana.",
        )


@router.get("/api/cursos/{curso_id}/equipo/invitaciones", response_model=list[InvitacionSalida])
def listar_invitaciones(
    curso_id: uuid.UUID,
    response: Response,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.EQUIPO_ADMINISTRAR)),
) -> list[InvitacionSalida]:
    response.headers["Cache-Control"] = "no-store"
    return [
        _salida_invitacion(bd, i, settings)
        for i in bd.query(InvitacionEquipo)
        .filter_by(curso_id=curso_id)
        .order_by(InvitacionEquipo.creada_en.desc())
        .all()
    ]


@router.post(
    "/api/cursos/{curso_id}/equipo/invitaciones/{invitacion_id}/reenviar",
    response_model=InvitacionSalida,
    dependencies=[Depends(exigir_csrf)],
)
def reenviar_invitacion(
    curso_id: uuid.UUID,
    invitacion_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    settings: Settings = Depends(obtener_configuracion),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.EQUIPO_ADMINISTRAR)),
) -> InvitacionSalida:
    i = bd.query(InvitacionEquipo).filter_by(id=invitacion_id, curso_id=curso_id).one_or_none()
    if i is None:
        raise HTTPException(status_code=404)
    if i.estado != "PENDIENTE":
        raise HTTPException(status_code=409, detail="Esta invitación ya fue aceptada o revocada.")
    i.estado = "REVOCADA"
    bd.flush()
    _validar_cuotas_invitacion(bd, curso_id, actual[0].id)
    try:
        creada = cursos_repo.reenviar_invitacion(bd, i, actor=actual[0])
    except cursos_repo.LimiteDeReenviosSuperado:
        raise HTTPException(
            status_code=409,
            detail="Alcanzaste los tres reenvíos permitidos para esta dirección y curso.",
        ) from None
    invitaciones_correo.cancelar(bd, i)
    invitaciones_correo.encolar(bd, creada, settings)
    bitacora_repo.registrar(
        bd,
        accion="INVITACION_REENVIADA",
        entidad="invitacion_equipo",
        entidad_id=str(creada.invitacion.id),
        actor_usuario_id=actual[0].id,
        curso_id=curso_id,
    )
    return _salida_invitacion(bd, creada.invitacion, settings)


@router.post(
    "/api/cursos/{curso_id}/equipo/invitaciones",
    response_model=InvitacionSalida,
    dependencies=[Depends(exigir_csrf)],
)
def crear_invitacion(
    curso_id: uuid.UUID,
    datos: InvitacionEntrada,
    response: Response,
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.EQUIPO_ADMINISTRAR)),
    settings: Settings = Depends(obtener_configuracion),
) -> InvitacionSalida:
    response.headers["Cache-Control"] = "no-store"
    usuario, _ = actual
    permisos = _permisos_desde_lista(datos.permisos)
    _validar_permisos_de_rol(datos.rol, permisos)

    try:
        correo = normalizar_correo_google(datos.email, email_verified=True, hd=None)
    except RechazoCorreo as exc:
        raise HTTPException(status_code=422, detail=exc.motivo.value) from None

    pendiente = (
        bd.query(InvitacionEquipo)
        .filter(
            InvitacionEquipo.curso_id == curso_id,
            InvitacionEquipo.email_canonico == correo.email_canonico,
            InvitacionEquipo.estado == "PENDIENTE",
        )
        .one_or_none()
    )
    if pendiente is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Ya existe una invitación para esta dirección. "
                "Usa Reenviar en la lista de invitaciones."
            ),
        )

    _validar_cuotas_invitacion(bd, curso_id, usuario.id)
    creada = cursos_repo.crear_invitacion(
        bd,
        curso_id=curso_id,
        invitador=usuario,
        email=correo.email,
        email_canonico=correo.email_canonico,
        rol=datos.rol,
        permisos=permisos,
        github_login_declarado=datos.github_login_declarado,
    )
    bitacora_repo.registrar(
        bd,
        accion="INVITACION_ENVIADA",
        entidad="invitacion_equipo",
        entidad_id=str(creada.invitacion.id),
        actor_usuario_id=usuario.id,
        curso_id=curso_id,
    )
    invitaciones_correo.encolar(bd, creada, settings)
    return _salida_invitacion(bd, creada.invitacion, settings)


@router.delete(
    "/api/cursos/{curso_id}/equipo/invitaciones/{invitacion_id}",
    dependencies=[Depends(exigir_csrf)],
)
def revocar_invitacion(
    curso_id: uuid.UUID,
    invitacion_id: uuid.UUID,
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.EQUIPO_ADMINISTRAR)),
) -> dict[str, bool]:
    usuario, _ = actual
    invitacion = (
        bd.query(InvitacionEquipo)
        .filter(InvitacionEquipo.id == invitacion_id, InvitacionEquipo.curso_id == curso_id)
        .one_or_none()
    )
    if invitacion is None:
        raise HTTPException(status_code=404)
    if invitacion.estado != "PENDIENTE":
        raise HTTPException(status_code=409, detail="Solo puedes revocar una invitación pendiente.")
    invitaciones_correo.cancelar(bd, invitacion)
    invitacion.estado = "REVOCADA"
    invitacion.revocada_en = ahora_utc()
    invitacion.revocada_por = usuario.id
    bd.flush()
    bitacora_repo.registrar(
        bd,
        accion="INVITACION_REVOCADA",
        entidad="invitacion_equipo",
        entidad_id=str(invitacion_id),
        actor_usuario_id=usuario.id,
        curso_id=curso_id,
    )
    return {"ok": True}


# --------------------------------------------------------------------------
# Miembros: permisos, rol, retiro, reincorporacion
# --------------------------------------------------------------------------


def _obtener_membresia_o_404(
    bd: Session, *, curso_id: uuid.UUID, membresia_id: uuid.UUID
) -> MembresiaCurso:
    fila = (
        bd.query(MembresiaCurso)
        .filter(MembresiaCurso.id == membresia_id, MembresiaCurso.curso_id == curso_id)
        .one_or_none()
    )
    if fila is None:
        raise HTTPException(status_code=404)
    return fila


@router.patch(
    "/api/cursos/{curso_id}/miembros/{membresia_id}/permisos", dependencies=[Depends(exigir_csrf)]
)
def cambiar_permisos_miembro(
    curso_id: uuid.UUID,
    membresia_id: uuid.UUID,
    datos: PermisosEntrada,
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.EQUIPO_ADMINISTRAR)),
) -> dict[str, bool]:
    usuario, _ = actual
    objetivo = _obtener_membresia_o_404(bd, curso_id=curso_id, membresia_id=membresia_id)
    if objetivo.rol == RolMembresia.PROFESOR.value:
        raise HTTPException(status_code=422, detail="un profesor no tiene permisos configurables")

    nuevos = _permisos_desde_lista(datos.permisos)
    _validar_permisos_de_rol(RolMembresia.AYUDANTE, nuevos)

    antes = list(objetivo.permisos)
    cursos_repo.cambiar_permisos(bd, objetivo, nuevos)
    bitacora_repo.registrar(
        bd,
        accion="PERMISOS_CAMBIADOS",
        entidad="membresia_curso",
        entidad_id=str(membresia_id),
        actor_usuario_id=usuario.id,
        curso_id=curso_id,
        antes={"permisos": antes},
        despues={"permisos": objetivo.permisos},
    )
    return {"ok": True}


@router.patch(
    "/api/cursos/{curso_id}/miembros/{membresia_id}/rol", dependencies=[Depends(exigir_csrf)]
)
def cambiar_rol_miembro(
    curso_id: uuid.UUID,
    membresia_id: uuid.UUID,
    datos: RolEntrada,
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.EQUIPO_ADMINISTRAR)),
) -> dict[str, bool]:
    usuario, _ = actual
    objetivo = _obtener_membresia_o_404(bd, curso_id=curso_id, membresia_id=membresia_id)

    permisos = _permisos_desde_lista(datos.permisos)
    _validar_permisos_de_rol(datos.rol, permisos)

    if datos.rol == RolMembresia.AYUDANTE and objetivo.rol == RolMembresia.PROFESOR.value:
        try:
            puede_retirar_o_degradar(
                es_profesor_activo=True,
                cantidad_profesores_activos=cursos_repo.contar_profesores_activos(bd, curso_id),
                curso_activo=True,
            )
        except UltimoProfesorActivo as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from None

    antes = {"rol": objetivo.rol, "permisos": list(objetivo.permisos)}
    cursos_repo.cambiar_rol(bd, objetivo, nuevo_rol=datos.rol, permisos_si_ayudante=permisos)
    bitacora_repo.registrar(
        bd,
        accion="ROL_CAMBIADO",
        entidad="membresia_curso",
        entidad_id=str(membresia_id),
        actor_usuario_id=usuario.id,
        curso_id=curso_id,
        antes=antes,
        despues={"rol": objetivo.rol, "permisos": objetivo.permisos},
    )
    return {"ok": True}


@router.get("/api/cursos/{curso_id}/miembros/{membresia_id}/impacto-retiro")
def impacto_retiro(
    curso_id: uuid.UUID,
    membresia_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.EQUIPO_ADMINISTRAR)),
) -> dict[str, object]:
    """S2.9.5. Repositorios/entregas sin corrector se computan desde P4/F11 en
    adelante; hoy siempre son cero porque esas tablas todavia no existen."""
    objetivo = _obtener_membresia_o_404(bd, curso_id=curso_id, membresia_id=membresia_id)
    sesiones_activas = (
        bd.query(Sesion)
        .filter(Sesion.usuario_id == objetivo.usuario_id, Sesion.revocada_en.is_(None))
        .count()
    )
    return {
        "sesiones_a_cerrar": sesiones_activas,
        "repositorios_perdidos": 0,
        "entregas_sin_corrector": 0,
        "es_profesor": objetivo.rol == RolMembresia.PROFESOR.value,
    }


@router.post(
    "/api/cursos/{curso_id}/equipo/{membresia_id}/retiro", dependencies=[Depends(exigir_csrf)]
)
def retirar_miembro(
    curso_id: uuid.UUID,
    membresia_id: uuid.UUID,
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.EQUIPO_ADMINISTRAR)),
) -> dict[str, bool]:
    usuario, _ = actual
    objetivo = _obtener_membresia_o_404(bd, curso_id=curso_id, membresia_id=membresia_id)
    try:
        cursos_repo.retirar_membresia(bd, objetivo, actor=usuario, curso_activo=True)
    except UltimoProfesorActivo as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None

    bitacora_repo.registrar(
        bd,
        accion="MEMBRESIA_RETIRADA",
        entidad="membresia_curso",
        entidad_id=str(membresia_id),
        actor_usuario_id=usuario.id,
        curso_id=curso_id,
    )
    cuenta_repo.retirar_credenciales(bd, objetivo)
    acceso_docente_repo.encolar_sincronizacion(bd, objetivo, revocar=True)
    return {"ok": True}


@router.post(
    "/api/cursos/{curso_id}/equipo/{membresia_id}/reincorporacion",
    dependencies=[Depends(exigir_csrf)],
)
def reincorporar_miembro(
    curso_id: uuid.UUID,
    membresia_id: uuid.UUID,
    datos: PermisosEntrada,
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.EQUIPO_ADMINISTRAR)),
) -> dict[str, bool]:
    usuario, _ = actual
    objetivo = _obtener_membresia_o_404(bd, curso_id=curso_id, membresia_id=membresia_id)
    permisos = _permisos_desde_lista(datos.permisos)
    if objetivo.rol == RolMembresia.AYUDANTE.value:
        _validar_permisos_de_rol(RolMembresia.AYUDANTE, permisos)

    try:
        cursos_repo.reincorporar_membresia(bd, objetivo, permisos=permisos)
    except cursos_repo.InvitacionNoAceptable as exc:
        raise HTTPException(status_code=409, detail=exc.motivo) from None
    acceso_docente_repo.encolar_sincronizacion(bd, objetivo)
    bitacora_repo.registrar(
        bd,
        accion="MEMBRESIA_REINCORPORADA",
        entidad="membresia_curso",
        entidad_id=str(membresia_id),
        actor_usuario_id=usuario.id,
        curso_id=curso_id,
    )
    return {"ok": True}


@router.post(
    "/api/cursos/{curso_id}/equipo/{membresia_id}/github/reintentar",
    dependencies=[Depends(exigir_csrf)],
)
def reintentar_acceso_github(
    curso_id: uuid.UUID,
    membresia_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.EQUIPO_ADMINISTRAR)),
) -> dict[str, bool]:
    objetivo = _obtener_membresia_o_404(bd, curso_id=curso_id, membresia_id=membresia_id)
    if objetivo.estado != "ACTIVA":
        raise HTTPException(
            status_code=409, detail="La persona ya no forma parte del equipo activo."
        )
    acceso_docente_repo.encolar_sincronizacion(bd, objetivo)
    return {"ok": True}


@router.get("/api/cursos/{curso_id}/equipo/historial")
def historial_equipo(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> list[dict[str, object]]:
    acciones = {
        "MEMBRESIA_RETIRADA",
        "MEMBRESIA_REINCORPORADA",
        "PERMISOS_CAMBIADOS",
        "ROL_CAMBIADO",
        "INVITACION_ENVIADA",
        "INVITACION_REVOCADA",
        "INVITACION_REENVIADA",
        "INVITACION_ACEPTADA",
    }
    filas = (
        bd.query(Bitacora)
        .filter(Bitacora.curso_id == curso_id, Bitacora.accion.in_(acciones))
        .order_by(Bitacora.creado_en.desc())
        .all()
    )
    return [
        {
            "accion": f.accion,
            "entidad_id": f.entidad_id,
            "actor_usuario_id": str(f.actor_usuario_id) if f.actor_usuario_id else None,
            "creado_en": f.creado_en.isoformat(),
            "antes": f.antes,
            "despues": f.despues,
        }
        for f in filas
    ]


# --------------------------------------------------------------------------
# Invitaciones publicas (sin sesion)
# --------------------------------------------------------------------------


@router.get("/api/invitaciones/{token}", response_model=InvitacionPublicaSalida)
def obtener_invitacion_publica(
    token: str, bd: Session = Depends(obtener_sesion_bd)
) -> InvitacionPublicaSalida:
    invitacion = cursos_repo.obtener_invitacion_por_token(bd, token)
    if invitacion is None:
        raise HTTPException(status_code=404)
    estado = invitacion.estado
    if cursos_repo.invitacion_esta_vencida(invitacion):
        estado = "EXPIRADA"
    curso = bd.query(Curso).filter(Curso.id == invitacion.curso_id).one()
    return InvitacionPublicaSalida(
        curso_nombre=curso.nombre,
        rol=invitacion.rol,
        permisos=invitacion.permisos,
        email_enmascarado=_enmascarar_email(invitacion.email),
        estado=estado,
    )


@router.post("/api/invitaciones/{token}/aceptar", dependencies=[Depends(exigir_csrf)])
def aceptar_invitacion_con_sesion(
    token: str,
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
) -> dict[str, bool]:
    """Camino para quien ya tiene sesion abierta con la cuenta correcta.

    Autoriza por hash del token mas coincidencia con `usuario.email_canonico`
    (S2.5.5 parrafo final) -- no exige `equipo.administrar`: el destinatario
    de la invitacion normalmente no es todavia miembro del curso.
    """
    usuario, _ = actual
    invitacion = cursos_repo.obtener_invitacion_por_token(bd, token)
    if invitacion is None:
        raise HTTPException(status_code=404)
    try:
        cursos_repo.aceptar_invitacion(bd, invitacion, usuario=usuario)
    except cursos_repo.InvitacionNoAceptable as exc:
        raise HTTPException(status_code=409, detail=exc.motivo) from None
    bitacora_repo.registrar(
        bd,
        accion="INVITACION_ACEPTADA",
        entidad="invitacion_equipo",
        entidad_id=str(invitacion.id),
        actor_usuario_id=usuario.id,
        curso_id=invitacion.curso_id,
    )
    bitacora_repo.registrar(
        bd,
        accion="MEMBRESIA_CREADA",
        entidad="membresia_curso",
        actor_usuario_id=usuario.id,
        curso_id=invitacion.curso_id,
    )
    return {"ok": True}
