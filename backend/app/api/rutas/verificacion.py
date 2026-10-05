"""Paso 4 del asistente: checklist de verificacion (SPEC 04 S4.7).

`POST .../verificacion` encola el trabajo y responde `202` con `ejecucion_id`
de inmediato; la interfaz sondea cada 2s, nunca SSE ni WebSocket (RG-061).

Orden de registro de rutas deliberado: FastAPI/Starlette resuelve por orden
de registro, no por especificidad -- `/items/5-bis` y `/items/17-bis` deben
registrarse ANTES de `/items/{item}`, o la ruta generica las capturaria
primero y las dejaria inalcanzables.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adaptadores import trabajos_repo, verificacion_repo
from app.adaptadores.bitacora_repo import registrar as registrar_bitacora
from app.adaptadores.cliente_canvas import ClienteCanvas, crear_cliente_canvas
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_github import VerificacionVinculacion
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.api.dependencias import exigir_csrf, obtener_sesion_bd, requiere, usuario_actual
from app.dominio.permisos import Permiso
from app.dominio.verificacion import CATALOGO_VERIFICACION
from app.infraestructura.cifrado import Llavero
from app.infraestructura.config import Settings, obtener_configuracion
from app.infraestructura.identificadores import uuid7

router = APIRouter(tags=["verificacion"])

_ITEMS_VALIDOS = {i.id for i in CATALOGO_VERIFICACION}


def _llavero(settings: Settings) -> Llavero:
    return Llavero(settings.llavero_cifrado(), settings.app_encryption_key_activa)


class ItemSalida(BaseModel):
    item: str | None
    resultado: str
    detalle: dict[str, object]
    ejecutada_en: str


def _a_salida(fila: VerificacionVinculacion) -> ItemSalida:
    return ItemSalida(
        item=fila.item,
        resultado=fila.resultado,
        detalle=fila.detalle,
        ejecutada_en=fila.ejecutada_en.isoformat(),
    )


def _obtener_curso_o_404(bd: Session, curso_id: uuid.UUID) -> Curso:
    curso = bd.query(Curso).filter(Curso.id == curso_id).one_or_none()
    if curso is None:
        raise HTTPException(status_code=404)
    return curso


def _cliente_canvas_del_curso(curso: Curso, settings: Settings) -> ClienteCanvas:
    return crear_cliente_canvas(
        modo=settings.canvas_modo, canvas_base_url=curso.canvas_base_url or settings.canvas_base_url
    )


def _ultima_fila(bd: Session, curso_id: uuid.UUID, item: str) -> VerificacionVinculacion:
    fila = (
        bd.query(VerificacionVinculacion)
        .filter(VerificacionVinculacion.curso_id == curso_id, VerificacionVinculacion.item == item)
        .order_by(VerificacionVinculacion.ejecutada_en.desc())
        .first()
    )
    assert fila is not None
    return fila


class EjecucionSalida(BaseModel):
    ejecucion_id: uuid.UUID


@router.post(
    "/api/cursos/{curso_id}/verificacion",
    status_code=202,
    response_model=EjecucionSalida,
    dependencies=[Depends(exigir_csrf)],
)
def encolar_checklist(
    curso_id: uuid.UUID,
    response: Response,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_ADMINISTRAR)),
) -> EjecucionSalida:
    _obtener_curso_o_404(bd, curso_id)
    ejecucion_id = uuid7()
    trabajos_repo.encolar(
        bd,
        tipo="ejecutar_checklist_vinculacion",
        clave_idempotencia=f"checklist:{curso_id}:{ejecucion_id}",
        max_intentos=1,
        curso_id=curso_id,
        payload={"ejecucion_id": str(ejecucion_id)},
    )
    response.headers["Location"] = f"/api/cursos/{curso_id}/verificacion/{ejecucion_id}"
    return EjecucionSalida(ejecucion_id=ejecucion_id)


class PruebaEscrituraEntrada(BaseModel):
    consiento: bool


@router.post(
    "/api/cursos/{curso_id}/verificacion/items/5-bis",
    response_model=ItemSalida,
    dependencies=[Depends(exigir_csrf)],
)
def ejecutar_5bis(
    curso_id: uuid.UUID,
    datos: PruebaEscrituraEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_ADMINISTRAR)),
) -> ItemSalida:
    """Prueba de escritura sincrona (S4.7.2), fuera del trabajo encolado."""
    curso = _obtener_curso_o_404(bd, curso_id)
    cliente = _cliente_canvas_del_curso(curso, settings)
    verificacion_repo.ejecutar_prueba_5bis(
        bd, cliente, _llavero(settings), curso=curso, consiento=datos.consiento
    )
    return _a_salida(_ultima_fila(bd, curso_id, "5-bis"))


@router.post(
    "/api/cursos/{curso_id}/verificacion/items/17-bis",
    response_model=ItemSalida,
    dependencies=[Depends(exigir_csrf)],
)
def ejecutar_17bis(
    curso_id: uuid.UUID,
    datos: PruebaEscrituraEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_ADMINISTRAR)),
) -> ItemSalida:
    curso = _obtener_curso_o_404(bd, curso_id)
    cliente = _cliente_canvas_del_curso(curso, settings)
    verificacion_repo.ejecutar_prueba_17bis(
        bd, cliente, _llavero(settings), curso=curso, consiento=datos.consiento
    )
    return _a_salida(_ultima_fila(bd, curso_id, "17-bis"))


@router.post(
    "/api/cursos/{curso_id}/verificacion/items/14/firmar",
    response_model=ItemSalida,
    dependencies=[Depends(exigir_csrf)],
)
def firmar_item_14(
    curso_id: uuid.UUID,
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_ADMINISTRAR)),
) -> ItemSalida:
    """S4.7.3: unica forma de escribir `VERIFICADO_A_MANO`, firmada por un
    profesor en pantalla, con fecha y actor persistidos."""
    usuario, _ = actual
    curso = _obtener_curso_o_404(bd, curso_id)
    verificacion_repo.firmar_item_14_a_mano(bd, curso=curso, actor_usuario_id=usuario.id)
    registrar_bitacora(
        bd,
        accion="VERIFICACION_FIRMADA_A_MANO",
        entidad="verificacion_vinculacion",
        entidad_id="14",
        actor_usuario_id=usuario.id,
        curso_id=curso_id,
    )
    return _a_salida(_ultima_fila(bd, curso_id, "14"))


@router.post(
    "/api/cursos/{curso_id}/verificacion/items/{item}",
    status_code=202,
    response_model=EjecucionSalida,
    dependencies=[Depends(exigir_csrf)],
)
def reejecutar_item(
    curso_id: uuid.UUID,
    item: str,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_ADMINISTRAR)),
) -> EjecucionSalida:
    if item not in _ITEMS_VALIDOS or item in ("5-bis", "17-bis"):
        raise HTTPException(
            status_code=404, detail="item desconocido o no reejecutable por esta via"
        )
    _obtener_curso_o_404(bd, curso_id)
    ejecucion_id = uuid7()
    trabajos_repo.encolar(
        bd,
        tipo="ejecutar_checklist_vinculacion",
        clave_idempotencia=f"checklist-item:{curso_id}:{item}:{ejecucion_id}",
        max_intentos=1,
        curso_id=curso_id,
        payload={"ejecucion_id": str(ejecucion_id), "solo_items": [item]},
    )
    return EjecucionSalida(ejecucion_id=ejecucion_id)


@router.get("/api/cursos/{curso_id}/verificacion/ultima", response_model=list[ItemSalida])
def ultima_verificacion(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> list[ItemSalida]:
    ultimos = verificacion_repo.ultimos_resultados(bd, curso_id)
    filas = (
        bd.query(VerificacionVinculacion)
        .filter(
            VerificacionVinculacion.curso_id == curso_id,
            VerificacionVinculacion.item.in_(ultimos.keys()),
        )
        .order_by(VerificacionVinculacion.ejecutada_en.asc())
        .all()
    )
    mas_reciente_por_item: dict[str, VerificacionVinculacion] = {}
    for fila in filas:
        if fila.item is not None:
            mas_reciente_por_item[fila.item] = fila
    return [_a_salida(f) for f in mas_reciente_por_item.values()]


@router.get("/api/cursos/{curso_id}/verificacion/{ejecucion_id}", response_model=list[ItemSalida])
def estado_ejecucion(
    curso_id: uuid.UUID,
    ejecucion_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> list[ItemSalida]:
    filas = (
        bd.query(VerificacionVinculacion)
        .filter(
            VerificacionVinculacion.curso_id == curso_id,
            VerificacionVinculacion.ejecucion_id == ejecucion_id,
        )
        .order_by(VerificacionVinculacion.ejecutada_en.asc())
        .all()
    )
    return [_a_salida(f) for f in filas]
