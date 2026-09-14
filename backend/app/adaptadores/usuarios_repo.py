"""Alta/actualizacion de `usuario` y creacion de `sesion` (SPEC 02 S2.2.5-S2.2.6)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.api.dependencias import generar_token_opaco, hash_token
from app.dominio.identidad import CorreoAdmitido

_EXPIRACION_INICIAL = timedelta(hours=12)


class ConflictoCorreoCanonico(Exception):
    """S2.2.5: el email_canonico nuevo choca con el de otro usuario. No se toca nada."""


@dataclass(frozen=True)
class DatosGoogle:
    sub: str
    correo: CorreoAdmitido
    nombre: str
    avatar_url: str | None


def obtener_o_crear_usuario(sesion_bd: Session, datos: DatosGoogle) -> Usuario:
    existente = sesion_bd.query(Usuario).filter(Usuario.google_sub == datos.sub).one_or_none()
    ahora = ahora_utc()

    if existente is None:
        usuario = Usuario(
            google_sub=datos.sub,
            email=datos.correo.email,
            email_canonico=datos.correo.email_canonico,
            nombre=datos.nombre,
            avatar_url=datos.avatar_url,
            activo=True,
            creado_en=ahora,
            actualizado_en=ahora,
        )
        sesion_bd.add(usuario)
        sesion_bd.flush()
        return usuario

    # Cambio de direccion en Google: manda el sub (S2.2.5).
    if existente.email != datos.correo.email:
        conflicto = (
            sesion_bd.query(Usuario)
            .filter(
                Usuario.email_canonico == datos.correo.email_canonico, Usuario.id != existente.id
            )
            .one_or_none()
        )
        if conflicto is not None:
            raise ConflictoCorreoCanonico(
                f"email_canonico {datos.correo.email_canonico} ya pertenece a otro usuario"
            )
        existente.email = datos.correo.email
        existente.email_canonico = datos.correo.email_canonico
        existente.actualizado_en = ahora
        sesion_bd.flush()

    return existente


def crear_sesion(
    sesion_bd: Session,
    usuario: Usuario,
    *,
    jti_oidc: str,
    agente: str | None,
    ip_truncada: str | None,
) -> tuple[Sesion, str]:
    """Crea la fila `sesion` y devuelve (fila, token_en_claro). El token no se persiste."""
    token = generar_token_opaco()
    ahora = ahora_utc()
    fila = Sesion(
        usuario_id=usuario.id,
        token_hash=hash_token(token),
        jti_oidc=jti_oidc,
        creada_en=ahora,
        expira_en=ahora + _EXPIRACION_INICIAL,
        agente=agente,
        ip_truncada=ip_truncada,
    )
    sesion_bd.add(fila)
    try:
        sesion_bd.flush()
    except IntegrityError as exc:
        # jti_oidc repetido: replay de un state ya canjeado con exito (S2.2.7 motivo 5).
        sesion_bd.rollback()
        raise ValueError("jti_oidc ya consumido") from exc
    return fila, token
