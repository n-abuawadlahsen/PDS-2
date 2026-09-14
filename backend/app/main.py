"""Punto de entrada del servicio web: `uvicorn app.main:app` (SPEC 14 S14.5.1).

El servicio web nunca migra (S14.8.3.1): solo lee el estado del esquema para
`GET /estado`. CORS con lista blanca explicita -- `allow_origins=["*"]` esta
prohibido (S2.2.6) y una prueba de arquitectura falla si aparece.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dependencias import configurar_fabrica_sesiones
from app.api.rutas import (
    auth,
    capacidades,
    cursos,
    estado,
    interno,
    pendientes,
    perfil,
    personas,
    repositorios,
    salud,
    tareas,
    verificacion,
    vinculacion,
)
from app.infraestructura.config import obtener_configuracion
from app.infraestructura.db import crear_fabrica_sesiones
from app.infraestructura.logs import configurar_logs


def crear_app() -> FastAPI:
    settings = obtener_configuracion()
    configurar_logs(entorno=settings.entorno, version=settings.app_version)
    configurar_fabrica_sesiones(crear_fabrica_sesiones(settings))

    app = FastAPI(title="Proyecto 2 API", version=settings.app_version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origen],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
    )

    app.include_router(salud.router)
    app.include_router(estado.router)
    app.include_router(interno.router)
    app.include_router(capacidades.router)
    app.include_router(auth.router)
    app.include_router(perfil.router)
    app.include_router(cursos.router)
    app.include_router(vinculacion.router)
    app.include_router(verificacion.router)
    app.include_router(personas.router)
    app.include_router(pendientes.router)
    app.include_router(tareas.router)
    app.include_router(repositorios.router)

    return app


app = crear_app()
