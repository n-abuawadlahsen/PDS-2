"""GET /salud (SPEC 14 S14.13.1). Vivo: el proceso responde. No toca la base."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends

from app.infraestructura.config import Settings, obtener_configuracion

router = APIRouter(tags=["salud"])


@router.get("/salud")
def salud(settings: Settings = Depends(obtener_configuracion)) -> dict[str, Any]:
    return {
        "estado": "ok",
        "version": settings.app_version,
        "servicio": "api",
        "hora": datetime.now(UTC).isoformat(),
    }
