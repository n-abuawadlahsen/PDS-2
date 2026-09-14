"""Motor y fabrica de sesiones de SQLAlchemy.

Tope duro de 10 conexiones por proceso (ARQUITECTURA.md S14.3.2, medido contra
el conector con pooling de Supabase), configurado en el pool, no descubierto en
produccion.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.infraestructura.config import Settings

_MAX_CONEXIONES_POR_PROCESO = 10


def crear_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url,
        pool_size=_MAX_CONEXIONES_POR_PROCESO,
        max_overflow=0,
        pool_pre_ping=True,
    )


def crear_fabrica_sesiones(settings: Settings) -> sessionmaker[Session]:
    engine = crear_engine(settings)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def obtener_sesion(fabrica: sessionmaker[Session]) -> Iterator[Session]:
    sesion = fabrica()
    try:
        yield sesion
        sesion.commit()
    except Exception:
        sesion.rollback()
        raise
    finally:
        sesion.close()
