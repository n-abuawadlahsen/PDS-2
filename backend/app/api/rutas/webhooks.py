"""Receptor de webhooks de la GitHub App (SPEC 06 S6.8.2; SPEC 10 S10.2.2;
A-070; Etapa F5).

Valida la firma sobre el cuerpo crudo antes de parsear, persiste la entrega y
responde `202` sin procesar nada: todo ocurre despues, en `procesar_webhooks`.
Una firma invalida se registra y responde `401`, y nunca se procesa.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.adaptadores import actividad_repo, trabajos_repo
from app.api.dependencias import obtener_sesion_bd
from app.dominio.actividad import firma_valida
from app.infraestructura.config import Settings, obtener_configuracion

router = APIRouter(tags=["webhooks"])

TIPO_PROCESAR = "procesar_webhooks"


@router.post("/webhooks/github", status_code=202)
async def recibir_webhook(
    request: Request,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
) -> JSONResponse:
    cuerpo = await request.body()
    delivery_id = request.headers.get("X-GitHub-Delivery")
    evento = request.headers.get("X-GitHub-Event")
    if not delivery_id or not evento:
        return JSONResponse({"detail": "faltan cabeceras de GitHub"}, status_code=400)
    valida = firma_valida(
        cuerpo,
        request.headers.get("X-Hub-Signature-256"),
        secretos=[settings.github_webhook_secret, settings.github_webhook_secret_anterior],
    )
    payload: dict[str, Any] | None = None
    if valida:
        try:
            payload = json.loads(cuerpo)
        except ValueError:
            payload = None
    fila = actividad_repo.registrar_entrega(
        bd,
        delivery_id=delivery_id,
        evento=evento,
        cuerpo=cuerpo,
        payload=payload,
        firma_valida=valida,
    )
    if not valida:
        bd.commit()  # se registra aunque se rechace (S6.8.2)
        return JSONResponse({"detail": "firma inválida"}, status_code=401)
    if fila is not None:
        trabajos_repo.encolar(
            bd,
            tipo=TIPO_PROCESAR,
            clave_idempotencia=f"webhook:{delivery_id}",
            max_intentos=5,
            payload={"evento_webhook_id": str(fila.id)},
        )
    return JSONResponse({"ok": True}, status_code=202)
