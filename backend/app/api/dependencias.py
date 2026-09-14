"""Dependencias transversales de FastAPI: sesion, CSRF, base de datos.

Sesion opaca respaldada en base de datos (SPEC 02 S2.2.6): la cookie sólo
guarda un identificador aleatorio de 256 bits, nunca un JWT autocontenido.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta

from fastapi import Cookie, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session, sessionmaker

from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_curso import MembresiaCurso
from app.adaptadores.modelos_identidad import Sesion, SesionMembresia, Usuario
from app.dominio.estados import EstadoMembresia, RolMembresia
from app.dominio.permisos import Permiso, permisos_efectivos
from app.infraestructura.config import Settings, obtener_configuracion

NOMBRE_COOKIE_SESION = "sesion"
NOMBRE_COOKIE_CSRF = "csrf_token"
CABECERA_CSRF = "X-CSRF-Token"

_EXPIRACION_DESLIZANTE = timedelta(hours=12)
_EXPIRACION_ABSOLUTA = timedelta(days=7)

_fabrica: sessionmaker[Session] | None = None


def configurar_fabrica_sesiones(fabrica: sessionmaker[Session]) -> None:
    global _fabrica
    _fabrica = fabrica


def obtener_sesion_bd() -> Iterator[Session]:
    if _fabrica is None:
        raise RuntimeError("fabrica de sesiones no configurada")
    sesion = _fabrica()
    try:
        yield sesion
        sesion.commit()
    except Exception:
        sesion.rollback()
        raise
    finally:
        sesion.close()


def obtener_ajustes() -> Settings:
    return obtener_configuracion()


def generar_token_opaco() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def usuario_actual(
    sesion_token: str | None = Cookie(default=None, alias=NOMBRE_COOKIE_SESION),
    bd: Session = Depends(obtener_sesion_bd),
) -> tuple[Usuario, Sesion]:
    if not sesion_token:
        raise HTTPException(status_code=401, detail="sin sesion")

    token_hash = hash_token(sesion_token)
    fila_sesion = bd.query(Sesion).filter(Sesion.token_hash == token_hash).one_or_none()
    ahora = datetime.now(UTC)

    if fila_sesion is None or fila_sesion.revocada_en is not None or fila_sesion.expira_en <= ahora:
        raise HTTPException(status_code=401, detail="sesion invalida o expirada")

    usuario = bd.query(Usuario).filter(Usuario.id == fila_sesion.usuario_id).one_or_none()
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=401, detail="cuenta cerrada")

    # Expiracion deslizante, con tope absoluto de 7 dias (S2.2.6).
    fila_sesion.expira_en = min(
        ahora + _EXPIRACION_DESLIZANTE, fila_sesion.creada_en + _EXPIRACION_ABSOLUTA
    )
    return usuario, fila_sesion


def exigir_csrf(
    request: Request,
    csrf_cookie: str | None = Cookie(default=None, alias=NOMBRE_COOKIE_CSRF),
    csrf_header: str | None = Header(default=None, alias=CABECERA_CSRF),
) -> None:
    """S2.2.6: toda mutacion exige X-CSRF-Token contrastado contra cookie de doble envio."""
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    if not csrf_cookie or not csrf_header or not secrets.compare_digest(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="CSRF invalido")


def requiere(
    permiso: Permiso, rol_minimo: RolMembresia | None = None
) -> Callable[..., MembresiaCurso]:
    """Dependencia de autorizacion de curso (SPEC 02 S2.3.9, S2.7.1).

    Unico lugar del codigo donde `rol_minimo='PROFESOR'` puede aparecer (A-179,
    RG-122) -- `rol_minimo` solo debe pasarse para las seis acciones de
    `dominio.permisos.ACCIONES_SOLO_PROFESOR`.

    Resuelve la membresia del `curso_id` de la ruta y, en el mismo lugar,
    contrasta `sesion_membresia.version` contra `membresia_curso.version`: si
    difieren, refresca la fila (S2.7.1) en vez de destruir la sesion entera.
    """

    def dependencia(
        curso_id: uuid.UUID,
        actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
        bd: Session = Depends(obtener_sesion_bd),
    ) -> MembresiaCurso:
        usuario, sesion = actual
        membresia = (
            bd.query(MembresiaCurso)
            .filter(MembresiaCurso.curso_id == curso_id, MembresiaCurso.usuario_id == usuario.id)
            .one_or_none()
        )
        if membresia is None:
            raise HTTPException(status_code=404)

        fila_sm = (
            bd.query(SesionMembresia)
            .filter(
                SesionMembresia.sesion_id == sesion.id, SesionMembresia.membresia_id == membresia.id
            )
            .one_or_none()
        )
        if fila_sm is None:
            bd.add(
                SesionMembresia(
                    sesion_id=sesion.id,
                    membresia_id=membresia.id,
                    version=membresia.version,
                    refrescada_en=ahora_utc(),
                )
            )
            bd.flush()
        elif fila_sm.version != membresia.version:
            fila_sm.version = membresia.version
            fila_sm.refrescada_en = ahora_utc()
            bd.flush()

        if membresia.estado != EstadoMembresia.ACTIVA.value:
            raise HTTPException(status_code=403, detail="ya no formas parte de este curso")

        if rol_minimo is not None and membresia.rol != rol_minimo.value:
            raise HTTPException(status_code=403, detail={"codigo": "PERMISO_INSUFICIENTE"})

        efectivos = permisos_efectivos(
            rol=membresia.rol,
            permisos_configurados=frozenset(Permiso(p) for p in membresia.permisos),
        )
        if permiso not in efectivos:
            raise HTTPException(status_code=403, detail={"codigo": "PERMISO_INSUFICIENTE"})

        return membresia

    return dependencia
