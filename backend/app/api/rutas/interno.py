"""POST /interno/latido (SPEC 14 S14.7.7). Vigilante externo del planificador.

Fuera del middleware de sesion y del de CSRF. Autenticacion: cabecera
`X-Latido-Firma: v1={hex}` con HMAC-SHA256 sobre `{timestamp}.{nonce}`,
comparado en tiempo constante. El `nonce` se registra como
`trabajo.clave_idempotencia` del tipo `latido`: su indice unico parcial hace
la deteccion de repeticion estructural, no una lista en memoria.

`timestamp` y `nonce` viajan como parametros de consulta: el SPEC fija la
cabecera de firma y el material firmado, pero no el transporte de esos dos
valores -- esta es la decision de implementacion, documentada aqui en vez de
en ARQUITECTURA.md porque no es una decision de dominio.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.adaptadores.trabajos_repo import encolar, marcar_ok
from app.api.dependencias import obtener_sesion_bd
from app.infraestructura.config import Settings, obtener_configuracion

router = APIRouter(tags=["interno"], prefix="/interno")

_VENTANA_SEGUNDOS = 5 * 60


def _firma_valida(*, signing_key: str, timestamp: str, nonce: str, firma_recibida: str) -> bool:
    material = f"{timestamp}.{nonce}".encode()
    calculada = hmac.new(signing_key.encode(), material, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"v1={calculada}", firma_recibida)


@router.post("/latido")
def latido(
    timestamp: str = Query(...),
    nonce: str = Query(...),
    x_latido_firma: str | None = Header(default=None, alias="X-Latido-Firma"),
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
) -> dict[str, Any]:
    if not x_latido_firma:
        raise HTTPException(status_code=401, detail="falta X-Latido-Firma")
    if not _firma_valida(
        signing_key=settings.signing_key,
        timestamp=timestamp,
        nonce=nonce,
        firma_recibida=x_latido_firma,
    ):
        raise HTTPException(status_code=401, detail="firma invalida")

    try:
        marca = int(timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="timestamp invalido") from exc
    if abs(time.time() - marca) > _VENTANA_SEGUNDOS:
        raise HTTPException(status_code=401, detail="timestamp fuera de ventana")

    registro_nonce = encolar(bd, tipo="latido", clave_idempotencia=nonce, max_intentos=1)
    if registro_nonce is None:
        raise HTTPException(status_code=401, detail="nonce ya consumido")
    marcar_ok(bd, registro_nonce)

    # TODO(etapa-operacion): comprobar trabajo_periodico.ultima_ejecucion vs
    # proxima_ejecucion y abrir PLANIFICADOR_DETENIDO si hay retraso > 3
    # cadencias (S14.7.7 paso 3). Requiere el catalogo de incidencias.
    return {"ok": True}
