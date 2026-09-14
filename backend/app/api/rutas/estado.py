"""GET /estado (SPEC 14 S14.13.1). Listo y diagnostico.

Etapa 0 implementa solo la forma anonima (booleanos y contadores agregados,
sin nombre ni identificador de curso). La forma completa por curso (S14.13.1)
depende de `curso`/permisos (Etapa P2) y se añade entonces.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.adaptadores.modelos_infraestructura import Respaldo, TrabajoPeriodico
from app.api.dependencias import obtener_sesion_bd
from app.infraestructura.config import Settings, obtener_configuracion
from app.infraestructura.migraciones import revision_actual, revision_esperada

router = APIRouter(tags=["estado"])


@router.get("/estado")
def estado(
    bd: Session = Depends(obtener_sesion_bd), settings: Settings = Depends(obtener_configuracion)
) -> dict[str, Any]:
    try:
        bd.execute(select(1))
        bd_alcanzable = True
    except OperationalError:
        bd_alcanzable = False

    if not bd_alcanzable:
        return {"degradado": True, "base_de_datos": {"alcanzable": False}}

    ultimo_respaldo = bd.execute(
        select(Respaldo).order_by(Respaldo.fecha.desc()).limit(1)
    ).scalar_one_or_none()
    planificador_retrasado = (
        bd.execute(select(TrabajoPeriodico).where(TrabajoPeriodico.activo.is_(True)))
        .scalars()
        .all()
    )

    revision_bd = revision_actual(bd.get_bind())
    revision_codigo = revision_esperada()
    esquema_al_dia = revision_bd == revision_codigo

    degradado = (not esquema_al_dia) or (
        ultimo_respaldo is not None and not ultimo_respaldo.exitoso
    )

    return {
        "degradado": degradado,
        "base_de_datos": {"alcanzable": True},
        "esquema": {"revision_actual": revision_bd, "revision_esperada": revision_codigo},
        "respaldo": {
            "ultimo_exito_en": ultimo_respaldo.creado_en.isoformat()
            if ultimo_respaldo and ultimo_respaldo.exitoso
            else None,
            "tamano_bytes": ultimo_respaldo.tamano_bytes if ultimo_respaldo else None,
        },
        "planificador": {"trabajos_activos": len(planificador_retrasado)},
        "entorno": settings.entorno,
    }
