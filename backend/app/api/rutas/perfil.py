"""Perfil docente: identidad, sesiones, cierre y cuenta GitHub con consentimiento."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.adaptadores import acceso_docente_repo, cuenta_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_github import FalloProveedorGithub, crear_cliente_github_desde_config
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.api.dependencias import exigir_csrf, obtener_sesion_bd, usuario_actual
from app.dominio.vinculacion_github import es_cuenta_de_organizacion
from app.infraestructura.cerrojos import bloquear_equipo
from app.infraestructura.config import Settings, obtener_configuracion

router = APIRouter(tags=["perfil"], prefix="/api/perfil")


class PerfilSalida(BaseModel):
    id: uuid.UUID
    email: str
    nombre: str
    avatar_url: str | None
    activo: bool
    github_login_declarado: str | None = None


class PerfilEntrada(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)


@router.get("", response_model=PerfilSalida)
def obtener_perfil(actual: tuple[Usuario, Sesion] = Depends(usuario_actual)) -> Usuario:
    usuario, _ = actual
    return usuario


@router.patch("", response_model=PerfilSalida, dependencies=[Depends(exigir_csrf)])
def actualizar_perfil(
    datos: PerfilEntrada,
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
) -> Usuario:
    usuario, _ = actual
    usuario.nombre = datos.nombre
    usuario.actualizado_en = ahora_utc()
    bd.flush()
    return usuario


@router.delete("", dependencies=[Depends(exigir_csrf)])
def cerrar_cuenta(
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
) -> dict[str, Any]:
    usuario, _ = actual

    bloqueantes = cuenta_repo.cerrar(bd, usuario)
    if bloqueantes:
        raise HTTPException(
            status_code=409,
            detail={
                "motivo": "UNICA_PROFESORA_ACTIVA",
                "cursos": [{"curso_id": str(c.curso_id), "nombre": c.nombre} for c in bloqueantes],
            },
        )

    return {"ok": True}


@router.get("/cierre")
def consultar_cierre(
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
) -> dict[str, Any]:
    cursos = cuenta_repo.cursos_bloqueantes(bd, actual[0])
    return {
        "puede_cerrar": not cursos,
        "cursos": [{"curso_id": str(c.curso_id), "nombre": c.nombre} for c in cursos],
    }


class CuentaGithubEntrada(BaseModel):
    login: str = Field(
        min_length=1, max_length=39, pattern=r"^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$"
    )
    consiento: bool


@router.put("/cuenta-github", response_model=PerfilSalida, dependencies=[Depends(exigir_csrf)])
def declarar_cuenta_github(
    datos: CuentaGithubEntrada,
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
) -> Usuario:
    """Valida identidad y elegibilidad global, y encola el cambio de accesos."""
    if not datos.consiento:
        raise HTTPException(status_code=422, detail="falta el consentimiento")

    cliente = crear_cliente_github_desde_config(settings)
    try:
        info = cliente.obtener_cuenta_usuario(datos.login)
        existe_org = cliente.existe_como_organizacion(datos.login)
    except FalloProveedorGithub as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None
    if info is None or es_cuenta_de_organizacion(existe_como_organizacion=existe_org):
        raise HTTPException(
            status_code=422, detail="esa cuenta de GitHub no existe o es una organizacion"
        )

    usuario, _ = actual
    bloquear_equipo(bd)
    bd.refresh(usuario)
    if not usuario.activo:
        raise HTTPException(status_code=401, detail="cuenta cerrada")
    assert info is not None
    motivo = acceso_docente_repo.motivo_no_elegible(
        bd, usuario=usuario, github_id=info.github_user_id, login=info.login
    )
    if motivo:
        raise HTTPException(status_code=422, detail=motivo)
    anterior = usuario.github_login_declarado
    usuario.cuenta_github_id = info.github_user_id
    usuario.github_login_declarado = info.login
    usuario.consentimiento_github_en = ahora_utc()
    usuario.actualizado_en = ahora_utc()
    acceso_docente_repo.programar_cambio_cuenta(bd, usuario, anterior)
    bd.flush()
    return usuario


@router.delete("/cuenta-github", response_model=PerfilSalida, dependencies=[Depends(exigir_csrf)])
def desvincular_cuenta_github(
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
) -> Usuario:
    usuario, _ = actual
    bloquear_equipo(bd)
    bd.refresh(usuario)
    anterior = usuario.github_login_declarado
    usuario.cuenta_github_id = None
    usuario.github_login_declarado = None
    usuario.consentimiento_github_en = None
    usuario.actualizado_en = ahora_utc()
    acceso_docente_repo.programar_cambio_cuenta(bd, usuario, anterior)
    bd.flush()
    return usuario


@router.get("/sesiones")
def listar_sesiones(
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
) -> list[dict[str, Any]]:
    usuario, sesion_actual = actual
    filas = (
        bd.query(Sesion)
        .filter(
            Sesion.usuario_id == usuario.id,
            Sesion.revocada_en.is_(None),
            Sesion.expira_en > datetime.now(UTC),
        )
        .order_by(Sesion.creada_en.desc())
        .all()
    )
    return [
        {
            "id": fila.id,
            "agente": fila.agente,
            "creada_en": fila.creada_en.isoformat(),
            "es_la_actual": fila.id == sesion_actual.id,
        }
        for fila in filas
    ]


@router.delete("/sesiones", dependencies=[Depends(exigir_csrf)])
def cerrar_otras_sesiones(
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
) -> dict[str, Any]:
    """CA-2.10-02: cerrar sesion en 'Mis sesiones' invalida las demas de inmediato."""
    usuario, sesion_actual = actual
    ahora = ahora_utc()
    afectadas = (
        bd.query(Sesion)
        .filter(
            Sesion.usuario_id == usuario.id,
            Sesion.id != sesion_actual.id,
            Sesion.revocada_en.is_(None),
        )
        .update({"revocada_en": ahora})
    )
    bd.flush()
    return {"sesiones_cerradas": afectadas}
