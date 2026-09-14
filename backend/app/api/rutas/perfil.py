"""`/perfil`, recorte de Etapa P1 (SPEC 02 S2.10). Exige sesion y ningun permiso.

Solo lo que Etapa P1 necesita: identidad (GET/PATCH), sesiones (GET/DELETE) y
cerrar cuenta (DELETE). El resto de `/perfil` (cuenta de GitHub, identidades de
Canvas, regenerar enlaces) llega con las etapas que crean esas tablas.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_github import crear_cliente_github_desde_config
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.api.dependencias import exigir_csrf, obtener_sesion_bd, usuario_actual
from app.dominio.cuenta import puede_cerrar_cuenta
from app.dominio.vinculacion_github import es_cuenta_de_organizacion
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

    # Etapa P1: no existe aun `curso`/`membresia_curso` (Etapa P2), asi que la
    # lista de cursos bloqueantes es siempre vacia -- ver app/dominio/cuenta.py.
    bloqueantes = puede_cerrar_cuenta([])
    if bloqueantes:
        raise HTTPException(
            status_code=409,
            detail={
                "motivo": "UNICA_PROFESORA_ACTIVA",
                "cursos": [c.__dict__ for c in bloqueantes],
            },
        )

    ahora = ahora_utc()
    bd.query(Sesion).filter(Sesion.usuario_id == usuario.id, Sesion.revocada_en.is_(None)).update(
        {"revocada_en": ahora}
    )
    usuario.activo = False
    usuario.actualizado_en = ahora
    bd.flush()
    return {"ok": True}


class CuentaGithubEntrada(BaseModel):
    login: str = Field(min_length=1)
    consiento: bool


@router.put("/cuenta-github", response_model=PerfilSalida, dependencies=[Depends(exigir_csrf)])
def declarar_cuenta_github(
    datos: CuentaGithubEntrada,
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
) -> Usuario:
    """Simplificacion de Etapa P4 citada en app/adaptadores/modelos_identidad.py:
    valida en vivo contra GitHub y guarda el login, sin esperar al catalogo
    `cuenta_github` completo de Etapa P6 (elegibilidad global, fusion con
    estudiantes, etc.)."""
    if not datos.consiento:
        raise HTTPException(status_code=422, detail="falta el consentimiento")

    cliente = crear_cliente_github_desde_config(settings)
    existe_usuario = cliente.existe_como_usuario(datos.login)
    existe_org = cliente.existe_como_organizacion(datos.login)
    if not existe_usuario or es_cuenta_de_organizacion(
        existe_como_usuario=existe_usuario, existe_como_organizacion=existe_org
    ):
        raise HTTPException(
            status_code=422, detail="esa cuenta de GitHub no existe o es una organizacion"
        )

    usuario, _ = actual
    usuario.github_login_declarado = datos.login
    usuario.consentimiento_github_en = ahora_utc()
    usuario.actualizado_en = ahora_utc()
    bd.flush()
    return usuario


@router.delete("/cuenta-github", response_model=PerfilSalida, dependencies=[Depends(exigir_csrf)])
def desvincular_cuenta_github(
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
) -> Usuario:
    usuario, _ = actual
    usuario.github_login_declarado = None
    usuario.consentimiento_github_en = None
    usuario.actualizado_en = ahora_utc()
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
