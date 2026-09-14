"""Rutas de acceso con Google OIDC (SPEC 02 S2.2). Flujo completo paso a paso en S2.2.2.

Simplificacion deliberada de Etapa P1 frente a S2.2.7: el redirect de error al
frontend solo lleva `motivo` en la query, nunca el correo completo (ni para
mostrarlo) -- evita que un correo personal quede en el historial del
navegador o en logs de proxies intermedios. El texto de cada motivo en el
frontend puede decir "esa cuenta de Google" en vez de interpolar la direccion.
"""

from __future__ import annotations

import hashlib
import secrets

import httpx
import jwt as pyjwt
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.adaptadores import cursos_repo
from app.adaptadores.cliente_google import (
    FalloProveedorGoogle,
    construir_url_autorizacion,
    generar_pkce,
    intercambiar_codigo,
)
from app.adaptadores.tokens_oidc import (
    ReclamacionesConfirmacion,
    StateInvalido,
    emitir_confirmacion,
    emitir_state,
    verificar_confirmacion,
    verificar_state,
)
from app.adaptadores.usuarios_repo import (
    ConflictoCorreoCanonico,
    DatosGoogle,
    crear_sesion,
    obtener_o_crear_usuario,
)
from app.api.dependencias import NOMBRE_COOKIE_CSRF, NOMBRE_COOKIE_SESION, obtener_sesion_bd
from app.dominio.identidad import (
    CorreoAdmitido,
    MotivoRechazoAcceso,
    RechazoCorreo,
    normalizar_correo_google,
)
from app.infraestructura.config import Settings, obtener_configuracion
from app.infraestructura.logs import obtener_logger

router = APIRouter(tags=["auth"], prefix="/auth")
_logger = obtener_logger(__name__)

NOMBRE_COOKIE_TXN = "oidc_txn"
_DESTINO_POR_DEFECTO = "/cursos"
_MAX_AGE_TXN = 600


def _ip_truncada(request: Request) -> str | None:
    if request.client is None:
        return None
    ip = request.client.host
    if ":" in ip:  # IPv6: conserva los primeros 4 grupos
        return ":".join(ip.split(":")[:4]) + "::"
    partes = ip.split(".")
    if len(partes) == 4:  # IPv4: trunca el ultimo octeto
        return ".".join(partes[:3]) + ".0"
    return ip


def _redirect_uri_google(settings: Settings) -> str:
    """URL de retorno registrada en Google, desde la configuracion y nunca desde
    `request.base_url`: detras del proxy de la plataforma, la peticion llega
    con esquema `http` y el host interno, y Google rechazaria la URL.

    Dos formas de despliegue, sin codigo distinto:
    - API en su propio origen (`VITE_API_BASE_URL=https://api.<dominio>`): el
      navegador llega a la API por ese origen.
    - Frontend que hace de proxy de `/api` y `/auth` (`VITE_API_BASE_URL`
      vacio): el navegador llega a la API por el origen del frontend, y las
      cookies de sesion quedan en ese mismo origen.
    """
    origen = settings.vite_api_base_url.strip() or settings.frontend_origen
    return origen.rstrip("/") + "/auth/google/callback"


def _redirect_error(settings: Settings, motivo: str) -> RedirectResponse:
    return RedirectResponse(f"{settings.frontend_origen}/acceso?motivo={motivo}", status_code=302)


def _redirect_confirmar(settings: Settings, token: str) -> RedirectResponse:
    return RedirectResponse(f"{settings.frontend_origen}/confirmar?token={token}", status_code=302)


def _establecer_cookies_sesion(
    respuesta: RedirectResponse, *, token_sesion: str, dominio_cookie: str | None
) -> None:
    csrf_token = secrets.token_urlsafe(32)
    respuesta.set_cookie(
        NOMBRE_COOKIE_SESION,
        token_sesion,
        max_age=7 * 24 * 3600,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        domain=dominio_cookie,
    )
    respuesta.set_cookie(
        NOMBRE_COOKIE_CSRF,
        csrf_token,
        max_age=7 * 24 * 3600,
        httponly=False,
        secure=True,
        samesite="lax",
        path="/",
        domain=dominio_cookie,
    )


@router.post("/google/inicio")
def google_inicio(
    destino: str = Form(default=_DESTINO_POR_DEFECTO),
    invitacion_token: str | None = Form(default=None),
    settings: Settings = Depends(obtener_configuracion),
) -> RedirectResponse:
    """`invitacion_token` (SPEC 02 S2.5.5): presente cuando el acceso viene del
    boton "Aceptar la invitacion" de `/invitaciones/{token}`. Viaja dentro del
    `state` firmado, nunca en la URL de retorno a Google."""
    pkce = generar_pkce()
    nonce = secrets.token_urlsafe(24)
    txn_id = secrets.token_urlsafe(32)
    jti = secrets.token_urlsafe(16)
    txn_hash = hashlib.sha256(txn_id.encode()).hexdigest()

    state = emitir_state(
        signing_key=settings.signing_key,
        nonce=nonce,
        destino=destino,
        txn_hash=txn_hash,
        jti=jti,
        code_verifier=pkce.code_verifier,
        invitacion_token=invitacion_token,
    )
    redirect_uri = _redirect_uri_google(settings)
    url = construir_url_autorizacion(
        client_id=settings.google_client_id,
        redirect_uri=redirect_uri,
        state=state,
        nonce=nonce,
        code_challenge=pkce.code_challenge,
    )

    respuesta = RedirectResponse(url, status_code=302)
    respuesta.set_cookie(
        NOMBRE_COOKIE_TXN,
        txn_id,
        max_age=_MAX_AGE_TXN,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/auth",
    )
    return respuesta


@router.get("/google/callback")
def google_callback(
    request: Request,
    state: str,
    code: str | None = None,
    error: str | None = None,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
) -> RedirectResponse:
    if error == "access_denied":
        return _redirect_error(settings, MotivoRechazoAcceso.ACCESO_CANCELADO.value)

    try:
        reclamaciones_state = verificar_state(signing_key=settings.signing_key, state=state)
    except StateInvalido:
        _logger.warning("auth.callback.state_invalido")
        return _redirect_error(settings, MotivoRechazoAcceso.STATE_INVALIDO.value)

    if not code:
        _logger.warning("auth.callback.sin_code", error_google=error)
        return _redirect_error(settings, MotivoRechazoAcceso.STATE_INVALIDO.value)

    redirect_uri = _redirect_uri_google(settings)
    try:
        claims = intercambiar_codigo(
            code=code,
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            redirect_uri=redirect_uri,
            code_verifier=reclamaciones_state.code_verifier,
            nonce_esperado=reclamaciones_state.nonce,
        )
    except FalloProveedorGoogle:
        return _redirect_error(settings, MotivoRechazoAcceso.FALLO_PROVEEDOR.value)
    except (ValueError, httpx.HTTPStatusError, pyjwt.PyJWTError) as exc:
        # Solo el tipo y el codigo de error de Google: nunca el code, tokens ni secretos.
        error_google = None
        if isinstance(exc, httpx.HTTPStatusError):
            try:
                error_google = exc.response.json().get("error")
            except ValueError:
                error_google = None
        _logger.warning(
            "auth.callback.canje_fallido",
            error=type(exc).__name__,
            detalle=None if isinstance(exc, httpx.HTTPStatusError) else str(exc),
            status=exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None,
            error_google=error_google,
        )
        return _redirect_error(settings, MotivoRechazoAcceso.STATE_INVALIDO.value)

    try:
        correo = normalizar_correo_google(
            claims.email, email_verified=claims.email_verified, hd=claims.hd
        )
    except RechazoCorreo as exc:
        return _redirect_error(settings, exc.motivo.value)

    cookie_txn = request.cookies.get(NOMBRE_COOKIE_TXN)
    if cookie_txn is not None:
        if hashlib.sha256(cookie_txn.encode()).hexdigest() != reclamaciones_state.txn_hash:
            _logger.warning("auth.callback.txn_no_coincide")
            return _redirect_error(settings, MotivoRechazoAcceso.STATE_INVALIDO.value)
        return _completar_acceso(
            bd,
            settings,
            request,
            sub=claims.sub,
            correo=correo,
            nombre=claims.name,
            avatar_url=claims.picture,
            jti_oidc=reclamaciones_state.jti,
            destino=reclamaciones_state.destino,
            invitacion_token=reclamaciones_state.invitacion_token,
        )

    # Camino degradado (S2.2.2 parrafo 4): la cookie oidc_txn no volvio.
    token_confirmacion = emitir_confirmacion(
        signing_key=settings.signing_key,
        datos=ReclamacionesConfirmacion(
            sub=claims.sub,
            email=correo.email,
            email_verified=claims.email_verified,
            nombre=claims.name,
            avatar_url=claims.picture,
            hd=claims.hd,
            jti_oidc=reclamaciones_state.jti,
            destino=reclamaciones_state.destino,
            invitacion_token=reclamaciones_state.invitacion_token,
        ),
    )
    return _redirect_confirmar(settings, token_confirmacion)


@router.post("/confirmar")
def confirmar(
    request: Request,
    token: str = Form(...),
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
) -> RedirectResponse:
    """Camino degradado: recibe un POST de formulario real del navegador (no
    `fetch`), igual que `/auth/google/inicio` -- asi el navegador sigue el 302
    de vuelta al frontend de forma nativa, con sus cookies de sesion, sin las
    complicaciones de CORS de seguir redirecciones entre origenes con `fetch`.

    El propio JWT de confirmacion (firmado, de un solo uso via `jti_oidc`,
    entregado solo al navegador que completo el redirect de Google) es la
    prueba anti-CSRF -- nadie mas puede fabricarlo ni interceptarlo sin
    SIGNING_KEY. Exigir POST (no GET) impide que se dispare por un enlace o
    pixel.
    """
    try:
        claims = verificar_confirmacion(signing_key=settings.signing_key, token=token)
    except StateInvalido:
        return _redirect_error(settings, MotivoRechazoAcceso.STATE_INVALIDO.value)

    try:
        correo = normalizar_correo_google(
            claims.email, email_verified=claims.email_verified, hd=claims.hd
        )
    except RechazoCorreo as exc:
        return _redirect_error(settings, exc.motivo.value)

    return _completar_acceso(
        bd,
        settings,
        request,
        sub=claims.sub,
        correo=correo,
        nombre=claims.nombre,
        avatar_url=claims.avatar_url,
        jti_oidc=claims.jti_oidc,
        destino=claims.destino,
        invitacion_token=claims.invitacion_token,
    )


def _completar_acceso(
    bd: Session,
    settings: Settings,
    request: Request,
    *,
    sub: str,
    correo: CorreoAdmitido,
    nombre: str,
    avatar_url: str | None,
    jti_oidc: str,
    destino: str,
    invitacion_token: str | None = None,
) -> RedirectResponse:
    try:
        usuario = obtener_o_crear_usuario(
            bd, DatosGoogle(sub=sub, correo=correo, nombre=nombre, avatar_url=avatar_url)
        )
    except ConflictoCorreoCanonico:
        return _redirect_error(settings, "CONFLICTO_IDENTIDAD")

    if not usuario.activo:
        return _redirect_error(settings, MotivoRechazoAcceso.CUENTA_CERRADA.value)

    try:
        _fila_sesion, token_sesion = crear_sesion(
            bd,
            usuario,
            jti_oidc=jti_oidc,
            agente=request.headers.get("user-agent"),
            ip_truncada=_ip_truncada(request),
        )
    except ValueError:
        _logger.warning("auth.callback.jti_ya_consumido")
        return _redirect_error(settings, MotivoRechazoAcceso.STATE_INVALIDO.value)

    destino_final = destino
    if invitacion_token:
        # S2.5.5: coincidiendo el correo, acepta en la misma transaccion de
        # acceso. Si no coincide o la invitacion ya no es aceptable, el login
        # igual se completa (Google ya autentico a esta persona); solo la
        # aceptacion de ESA invitacion falla, con su propio motivo en pantalla.
        invitacion = cursos_repo.obtener_invitacion_por_token(bd, invitacion_token)
        if invitacion is None:
            destino_final = f"/invitaciones/{invitacion_token}?error=NO_ENCONTRADA"
        else:
            try:
                cursos_repo.aceptar_invitacion(bd, invitacion, usuario=usuario)
                destino_final = f"/cursos/{invitacion.curso_id}/equipo?bienvenida=1"
            except cursos_repo.InvitacionNoAceptable as exc:
                destino_final = f"/invitaciones/{invitacion_token}?error={exc.motivo}"

    respuesta = RedirectResponse(f"{settings.frontend_origen}{destino_final}", status_code=302)
    _establecer_cookies_sesion(
        respuesta, token_sesion=token_sesion, dominio_cookie=settings.cookie_dominio
    )
    return respuesta
