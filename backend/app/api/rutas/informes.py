"""Informe docente diario y suscripcion (SPEC 11 S11.3-S11.5; Etapa F9).

Ninguna ruta de aqui recibe un `usuario_id` destino (CA-11.4-05): cada
persona ve y cambia solo lo suyo. Ninguna llama a Canvas ni a GitHub; el
correo lo envia `despachar_outbox`.

`/api/baja/{token}` es publica y firmada: el GET nunca cambia nada (lo abren
los escaneres de correo) y el POST aplica la baja o, con `accion=alta`, la
re-alta. No usa cookie, asi que no lleva token anti-CSRF (S11.4.4, RFC 8058).
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adaptadores import informe_repo, suscripciones_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.bitacora_repo import registrar as registrar_bitacora
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_identidad import Sesion, Usuario
from app.adaptadores.modelos_informe import InformeDiario, SuscripcionInforme
from app.api.dependencias import exigir_csrf, obtener_sesion_bd, requiere, usuario_actual
from app.dominio.estados import EstadoMembresia, OrigenMensaje
from app.dominio.informe import TOPE_ENVIARME
from app.dominio.permisos import Permiso

router = APIRouter(tags=["informes"])


def _curso(bd: Session, curso_id: uuid.UUID) -> Curso:
    curso = bd.get(Curso, curso_id)
    if curso is None:
        raise HTTPException(status_code=404)
    return curso


def _primer_generado(bd: Session, curso_id: uuid.UUID) -> date | None:
    fila = (
        bd.query(InformeDiario.fecha)
        .filter(InformeDiario.curso_id == curso_id, InformeDiario.estado == "GENERADO")
        .order_by(InformeDiario.fecha)
        .first()
    )
    return fila[0] if fila else None


class InformeResumen(BaseModel):
    fecha: date
    estado: str
    motivo: str | None
    origen: str


class InformesSalida(BaseModel):
    se_genera_desde: date | None
    informes: list[InformeResumen]


@router.get("/api/cursos/{curso_id}/informes", response_model=InformesSalida)
def listar_informes(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _m: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> InformesSalida:
    filas = (
        bd.query(InformeDiario)
        .filter(InformeDiario.curso_id == curso_id)
        .order_by(InformeDiario.fecha.desc())
        .limit(120)
        .all()
    )
    return InformesSalida(
        se_genera_desde=_primer_generado(bd, curso_id),
        informes=[
            InformeResumen(fecha=f.fecha, estado=f.estado, motivo=f.motivo, origen=f.origen)
            for f in filas
        ],
    )


class InformeSalida(BaseModel):
    fecha: date
    estado: str
    motivo: str | None
    html: str | None
    texto: str | None
    asunto: str | None
    frescura: dict[str, Any]


@router.get("/api/cursos/{curso_id}/informes/{fecha}", response_model=InformeSalida)
def ver_informe(
    curso_id: uuid.UUID,
    fecha: date,
    bd: Session = Depends(obtener_sesion_bd),
    _m: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> InformeSalida:
    informe = informe_repo.informe_del_dia(bd, curso_id, fecha)
    if informe is None:
        raise HTTPException(status_code=404, detail="No hay informe de ese día.")
    return InformeSalida(
        fecha=informe.fecha,
        estado=informe.estado,
        motivo=informe.motivo,
        html=informe.contenido_html,
        texto=informe.contenido_texto,
        asunto=(informe.contenido or {}).get("asunto"),
        frescura=informe.frescura,
    )


class VistaPreviaSalida(BaseModel):
    hay_tareas_activas: bool
    mensaje: str | None
    html: str | None
    texto: str | None


@router.get("/api/cursos/{curso_id}/informe-de-hoy/vista-previa", response_model=VistaPreviaSalida)
def vista_previa(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _m: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> VistaPreviaSalida:
    """Con los datos de ahora; no se guarda ni se envia (S11.5.4 accion 1)."""
    curso = _curso(bd, curso_id)
    ahora = ahora_utc()
    ultimo = (
        bd.query(InformeDiario)
        .filter(InformeDiario.curso_id == curso.id, InformeDiario.estado == "GENERADO")
        .order_by(InformeDiario.fecha.desc())
        .first()
    )
    from app.dominio.informe import ventana_del_informe

    desde, _ = ventana_del_informe(
        ultimo_generado_hasta=ultimo.ventana_hasta_utc if ultimo else None,
        ahora=ahora,
        curso_creado_en=curso.creado_en,
    )
    hoy = informe_repo.dia_del_curso(curso, ahora)
    doc, _, hay = informe_repo.construir(bd, curso, ahora=ahora, desde=desde, fecha=hoy)
    if not hay:
        return VistaPreviaSalida(
            hay_tareas_activas=False, mensaje=informe_repo.TEXTO_SIN_TAREAS, html=None, texto=None
        )
    html, texto = informe_repo.presentar(curso, doc, hoy)
    return VistaPreviaSalida(hay_tareas_activas=True, mensaje=None, html=html, texto=texto)


def _generar_hoy(bd: Session, curso: Curso, usuario_id: uuid.UUID) -> InformeDiario:
    informe, _ = informe_repo.generar(bd, curso, origen="MANUAL", usuario_id=usuario_id)
    if informe.estado != "GENERADO":
        raise HTTPException(
            status_code=409,
            detail={"codigo": "SIN_TAREAS_ACTIVAS", "motivo": informe_repo.TEXTO_SIN_TAREAS},
        )
    return informe


@router.post(
    "/api/cursos/{curso_id}/informe-de-hoy/enviarme",
    status_code=202,
    dependencies=[Depends(exigir_csrf)],
)
def enviarme(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> dict[str, int]:
    """S11.5.4 accion 2: solo a quien lo pide, dos veces al dia, con cargo al
    margen de la cuota."""
    curso = _curso(bd, curso_id)
    ahora = ahora_utc()
    if informe_repo.envios_manuales_de_hoy(bd, curso, membresia.usuario_id, ahora) >= TOPE_ENVIARME:
        raise HTTPException(
            status_code=429,
            detail={
                "codigo": "TOPE_ENVIARME",
                "motivo": "Ya te enviaste el informe de hoy dos veces; puedes verlo aquí.",
            },
        )
    informe = _generar_hoy(bd, curso, membresia.usuario_id)
    usuario = bd.get(Usuario, membresia.usuario_id)
    assert usuario is not None
    encolados = informe_repo.encolar_correos(
        bd,
        informe,
        [(membresia, usuario)],
        reserva="MARGEN",
        origen=OrigenMensaje.MANUAL,
        disparado_por=usuario.id,
        reenvio=True,
    )
    return {"encolados": encolados}


@router.post(
    "/api/cursos/{curso_id}/informe-de-hoy/enviar",
    status_code=202,
    dependencies=[Depends(exigir_csrf)],
)
def enviar_a_suscritos(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_ADMINISTRAR)),
) -> dict[str, int]:
    """S11.5.4 accion 3: si el informe ya existe no se regenera; se reenvia el
    mismo documento con la generacion siguiente."""
    curso = _curso(bd, curso_id)
    informe = _generar_hoy(bd, curso, membresia.usuario_id)
    encolados = informe_repo.encolar_correos(
        bd,
        informe,
        informe_repo.suscriptores(bd, curso.id),
        reserva="INFORME",
        origen=OrigenMensaje.SISTEMA,
        disparado_por=membresia.usuario_id,
        reenvio=True,
    )
    return {"encolados": encolados}


# --- Mis notificaciones (S11.4.5): autogestion, solo `curso.ver` ---


class SuscripcionSalida(BaseModel):
    curso_id: uuid.UUID
    curso_nombre: str
    curso_codigo: str
    activa: bool
    origen_baja: str | None
    se_genera_desde: date | None


def _salida(bd: Session, curso: Curso, fila: SuscripcionInforme | None) -> SuscripcionSalida:
    return SuscripcionSalida(
        curso_id=curso.id,
        curso_nombre=curso.nombre,
        curso_codigo=curso.codigo,
        activa=bool(fila and fila.activa),
        origen_baja=fila.origen_baja if fila else None,
        se_genera_desde=_primer_generado(bd, curso.id),
    )


@router.get("/api/cursos/{curso_id}/mis-notificaciones", response_model=SuscripcionSalida)
def mis_notificaciones(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> SuscripcionSalida:
    curso = _curso(bd, curso_id)
    return _salida(bd, curso, bd.get(SuscripcionInforme, (curso.id, membresia.usuario_id)))


class CambioSuscripcion(BaseModel):
    activa: bool


@router.put(
    "/api/cursos/{curso_id}/mis-notificaciones",
    response_model=SuscripcionSalida,
    dependencies=[Depends(exigir_csrf)],
)
def cambiar_mis_notificaciones(
    curso_id: uuid.UUID,
    datos: CambioSuscripcion,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> SuscripcionSalida:
    curso = _curso(bd, curso_id)
    fila = suscripciones_repo.cambiar_propia(
        bd, curso_id=curso.id, usuario_id=membresia.usuario_id, activa=datos.activa
    )
    registrar_bitacora(
        bd,
        accion="SUSCRIPCION_INFORME",
        entidad="suscripcion_informe",
        entidad_id=f"{curso.id}:{membresia.usuario_id}",
        actor_usuario_id=membresia.usuario_id,
        curso_id=curso.id,
        despues={"activa": fila.activa, "origen_baja": fila.origen_baja},
    )
    return _salida(bd, curso, fila)


# --- Vista agregada en /perfil ---


def _mis_cursos(bd: Session, usuario: Usuario) -> list[Curso]:
    return (
        bd.query(Curso)
        .join(MembresiaCurso, MembresiaCurso.curso_id == Curso.id)
        .filter(
            MembresiaCurso.usuario_id == usuario.id,
            MembresiaCurso.estado == EstadoMembresia.ACTIVA.value,
        )
        .order_by(Curso.nombre)
        .all()
    )


@router.get("/api/perfil/notificaciones", response_model=list[SuscripcionSalida])
def notificaciones_de_todos_mis_cursos(
    bd: Session = Depends(obtener_sesion_bd),
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
) -> list[SuscripcionSalida]:
    usuario, _ = actual
    return [
        _salida(bd, c, bd.get(SuscripcionInforme, (c.id, usuario.id)))
        for c in _mis_cursos(bd, usuario)
    ]


@router.put(
    "/api/perfil/notificaciones",
    response_model=list[SuscripcionSalida],
    dependencies=[Depends(exigir_csrf)],
)
def cambiar_todas(
    datos: CambioSuscripcion,
    bd: Session = Depends(obtener_sesion_bd),
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
) -> list[SuscripcionSalida]:
    """«Suscribirme a todos» / «darme de baja de todos»: N filas, en bitacora."""
    usuario, _ = actual
    salida = []
    for curso in _mis_cursos(bd, usuario):
        fila = suscripciones_repo.cambiar_propia(
            bd, curso_id=curso.id, usuario_id=usuario.id, activa=datos.activa
        )
        registrar_bitacora(
            bd,
            accion="SUSCRIPCION_INFORME",
            entidad="suscripcion_informe",
            entidad_id=f"{curso.id}:{usuario.id}",
            actor_usuario_id=usuario.id,
            curso_id=curso.id,
            despues={"activa": fila.activa, "origen_baja": fila.origen_baja, "todas": True},
        )
        salida.append(_salida(bd, curso, fila))
    return salida


@router.post(
    "/api/perfil/enlaces-de-baja/regenerar",
    dependencies=[Depends(exigir_csrf)],
)
def regenerar_enlaces(
    bd: Session = Depends(obtener_sesion_bd),
    actual: tuple[Usuario, Sesion] = Depends(usuario_actual),
) -> dict[str, int]:
    """Invalida todos los enlaces de baja emitidos antes (S11.4.4)."""
    usuario, _ = actual
    usuario.generacion_enlaces += 1
    bd.flush()
    return {"generacion_enlaces": usuario.generacion_enlaces}


# --- Baja por enlace firmado (publica) ---


class BajaSalida(BaseModel):
    curso_nombre: str
    curso_codigo: str
    activa: bool
    otros_cursos_suscritos: int


def _leer(bd: Session, token: str) -> tuple[Curso, Usuario]:
    datos = informe_repo.leer_token_baja(bd, token, ahora=ahora_utc())
    if datos is None:
        raise HTTPException(
            status_code=404,
            detail="Este enlace ya no es válido. Puedes gestionar tus avisos desde tu perfil.",
        )
    return datos


def _baja_salida(bd: Session, curso: Curso, usuario: Usuario) -> BajaSalida:
    fila = bd.get(SuscripcionInforme, (curso.id, usuario.id))
    otros = (
        bd.query(SuscripcionInforme)
        .filter(
            SuscripcionInforme.usuario_id == usuario.id,
            SuscripcionInforme.curso_id != curso.id,
            SuscripcionInforme.activa.is_(True),
        )
        .count()
    )
    return BajaSalida(
        curso_nombre=curso.nombre,
        curso_codigo=curso.codigo,
        activa=bool(fila and fila.activa),
        otros_cursos_suscritos=otros,
    )


@router.get("/api/baja/{token}", response_model=BajaSalida)
def ver_baja(token: str, bd: Session = Depends(obtener_sesion_bd)) -> BajaSalida:
    """Solo muestra: nunca cambia nada (CA-11.4-03)."""
    curso, usuario = _leer(bd, token)
    return _baja_salida(bd, curso, usuario)


@router.post("/api/baja/{token}", response_model=BajaSalida)
def aplicar_baja(
    token: str,
    accion: str = Query(default="baja", pattern="^(baja|alta)$"),
    bd: Session = Depends(obtener_sesion_bd),
) -> BajaSalida:
    curso, usuario = _leer(bd, token)
    fila = suscripciones_repo.cambiar_propia(
        bd, curso_id=curso.id, usuario_id=usuario.id, activa=accion == "alta"
    )
    registrar_bitacora(
        bd,
        accion="SUSCRIPCION_INFORME",
        entidad="suscripcion_informe",
        entidad_id=f"{curso.id}:{usuario.id}",
        actor_usuario_id=usuario.id,
        curso_id=curso.id,
        despues={"activa": fila.activa, "origen_baja": fila.origen_baja, "via": "enlace"},
    )
    return _baja_salida(bd, curso, usuario)
