"""GET /api/capacidades (SPEC 14 S14.6.3, ARQUITECTURA.md linea 3901).

"Es la unica fuente de la navegacion del frontend." Devuelve {perfil, banderas}.

El catalogo de las 12 banderas vive en `app/dominio/alcance.py` (Etapa P7 lo
movio ahi: las reglas de tarea consultan la misma lista para decidir la capa 3).
Bajo `PERFIL_ALCANCE=parcial` ninguna esta activa todavia; bajo `completo`
estan todas. El calendario exacto de retiro (23-sep/30-sep/3-oct) se añade
cuando cada bandera tenga codigo real detras.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.dominio.alcance import NOMBRES_BANDERAS, bandera_activa
from app.infraestructura.config import Settings, obtener_configuracion

router = APIRouter(tags=["capacidades"], prefix="/api")

BANDERAS_ALCANCE = NOMBRES_BANDERAS


@router.get("/capacidades")
def capacidades(settings: Settings = Depends(obtener_configuracion)) -> dict[str, Any]:
    banderas_activas = [b for b in BANDERAS_ALCANCE if bandera_activa(settings.perfil_alcance, b)]
    return {"perfil": settings.perfil_alcance, "banderas": banderas_activas}
