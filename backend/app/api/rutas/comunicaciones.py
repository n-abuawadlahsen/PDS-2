"""Comunicaciones del curso (SPEC 11 S11.6-S11.8, S11.10; A-225; Etapa F10).

La bandeja la lee cualquier miembro con `curso.ver`, con el cuerpo exacto; las
acciones exigen `comunicacion.enviar`. Ninguna ruta llama a Canvas: todo se
encola en `mensaje_saliente` (A-226) y cada respuesta lo declara con
`X-Llamadas-Externas: 0`.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.adaptadores import comunicaciones_repo
from app.adaptadores.modelos_aprovisionamiento import (
    AccesoRepositorio,
    FechaEfectiva,
    MensajeSaliente,
    Repositorio,
)
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_identidad import Usuario
from app.adaptadores.modelos_padron import Estudiante, Matricula, Seccion
from app.adaptadores.modelos_tarea import Entrega, Tarea
from app.api.dependencias import exigir_csrf, obtener_sesion_bd, requiere
from app.dominio.comunicaciones import EVENTOS, PLANTILLAS, renderizar
from app.dominio.permisos import Permiso

router = APIRouter(tags=["comunicaciones"])

ETIQUETA_ESTADO = {
    "PROGRAMADO": "Programado",
    "DIFERIDO": "En espera",
    "PENDIENTE": "En cola",
    "EN_CURSO": "Enviando",
    "ENVIADO": "Enviado",
    "REINTENTAR": "Reintentando",
    "ESPERANDO_LIMITE": "Esperando a Canvas por límite de uso",
    "ESPERANDO_CREDENCIAL": "Esperando credencial de Canvas",
    "BLOQUEADO": "Bloqueado por permisos de Canvas",
    "REQUIERE_ATENCION": "Pudo haberse enviado",
    "FALLIDO": "No se pudo enviar",
    "CANCELADO": "Cancelado",
    "SUPRIMIDO": "No se envió (filtrado)",
    "CADUCADO": "Ya no tenía sentido",
    "RETRACTADO": "Retirado",
}
ETIQUETA_MOTIVO = {
    "CADUCIDAD_ALCANZADA": "pasó la fecha en que tenía sentido",
    "SUSPENSION_PROLONGADA": "estuvo retenido más de siete días",
    "MATRICULA_NO_ACTIVA": "el destinatario ya no está activo",
    "SUPRESION_POR_ESTUDIANTE": "el estudiante pidió no recibir avisos automáticos",
    "REGLA_DESACTIVADA": "el aviso estaba apagado",
    "YA_ACEPTADO": "ya había aceptado la invitación",
    "MAPEO_YA_VIGENTE": "ya registró su cuenta de GitHub",
    "ENTREGA_EXCLUIDA": "la entrega quedó excluida",
    "NO_ES_DESTINATARIO_VALIDO": "Canvas no lo admite como destinatario",
    "FUERA_DEL_GRUPO": "ya no está en el grupo",
    "TAREA_REGISTRO_AUSENTE": "no existe la tarea de registro",
    "MODO_SOLO_LECTURA": "el curso está en solo lectura",
    "SUSPENSION_DE_CURSO": "las comunicaciones del curso están suspendidas",
    "VENTANA_TRAS_RESTAURACION": "ventana de espera tras una restauración",
    "PUBLICACION_PENDIENTE": "espera la publicación",
    "CUOTA_AGOTADA": "se agotó la cuota diaria de correo",
    "CURSO_ARCHIVADO": "el curso se archivó",
    "TAREA_ARCHIVADA": "la tarea se archivó",
    "ENTREGA_ELIMINADA": "la entrega se eliminó en Canvas",
    "ACCION_DOCENTE": "lo canceló el equipo docente",
    "AVISO_YA_NO_APLICA": "ya no hay entregas pendientes o el destinatario dejó el equipo",
    "SIMULADO_LOCAL": "el proveedor local simuló el envío; no salió un correo real",
    "ENVIO_INCIERTO": "no se pudo confirmar el envío; revisa antes de solicitar otro aviso",
}
TITULO_EVENTO = {
    "repositorio_disponible": "Repositorio disponible",
    "invitacion_aceptada": "Invitación aceptada",
    "recordatorio_mapeo": "Recordatorio de cuenta de GitHub",
    "recordatorio_invitacion": "Recordatorio de invitación",
    "proximidad_cierre": "Aviso de cierre próximo",
    "cambio_de_fecha": "Anuncio de cambio de fecha",
    "correccion_publicada": "Nota publicada",
}
ADVERTENCIA_AL_APAGAR = {
    "repositorio_disponible": (
        "Los estudiantes de esta tarea no recibirán la dirección de su repositorio; "
        "tendrás que dársela tú."
    ),
}
_ETIQUETA_HTML = re.compile(r"</?\s*([a-zA-Z0-9]+)[^>]*>")


def _curso(bd: Session, curso_id: uuid.UUID) -> Curso:
    curso = bd.get(Curso, curso_id)
    if curso is None:
        raise HTTPException(status_code=404)
    return curso


def _conflicto(exc: comunicaciones_repo.AccionNoPermitida) -> HTTPException:
    return HTTPException(
        status_code=409, detail={"codigo": "ACCION_NO_PERMITIDA", "motivo": str(exc)}
    )


# --- Bandeja ---


class MensajeSalida(BaseModel):
    id: uuid.UUID
    canal: str
    evento: str
    estado: str
    etiqueta_estado: str
    motivo: str | None
    destinatario: str
    asunto: str | None
    cuerpo: str | None
    origen: str
    generacion: int
    reemplaza_a_id: uuid.UUID | None
    tarea_id: uuid.UUID | None
    creado_en: datetime
    enviado_en: datetime | None
    programado_para: datetime | None
    enlace_canvas: str | None
    motivo_sin_enlace: str | None
    ultimo_error: str | None


class BandejaSalida(BaseModel):
    comunicaciones_salientes: str
    suspension_motivo: str | None
    canal_activo: str | None
    mensajes: list[MensajeSalida]


def _salida(m: MensajeSaliente) -> MensajeSalida:
    enlace = m.canvas_html_url
    motivo_sin_enlace = None
    if m.canal == "CORREO":
        motivo_sin_enlace = "Este aviso se envía por correo; no tiene enlace en Canvas."
    elif enlace is None:
        motivo_sin_enlace = (
            "Canvas no devolvió un enlace para este envío."
            if m.estado == "ENVIADO"
            else "Todavía no se ha publicado en Canvas."
        )
    return MensajeSalida(
        id=m.id,
        canal=m.canal,
        evento=m.evento,
        estado=m.estado,
        etiqueta_estado=ETIQUETA_ESTADO.get(m.estado, m.estado),
        motivo=ETIQUETA_MOTIVO.get(m.motivo_estado or "", None),
        destinatario=m.destinatario,
        asunto=m.asunto,
        cuerpo=m.cuerpo_renderizado,
        origen=m.origen,
        generacion=m.generacion,
        reemplaza_a_id=m.reemplaza_a_id,
        tarea_id=m.tarea_id,
        creado_en=m.creado_en,
        enviado_en=m.enviado_en,
        programado_para=m.programado_para,
        enlace_canvas=enlace,
        motivo_sin_enlace=motivo_sin_enlace,
        ultimo_error=m.ultimo_error_literal,
    )


@router.get("/api/cursos/{curso_id}/comunicaciones", response_model=BandejaSalida)
def bandeja(
    curso_id: uuid.UUID,
    response: Response,
    canal: str | None = None,
    evento: str | None = None,
    estado: str | None = None,
    tarea_id: uuid.UUID | None = None,
    estudiante_id: uuid.UUID | None = None,
    repositorio_id: uuid.UUID | None = None,
    limite: int = Query(default=200, le=500),
    bd: Session = Depends(obtener_sesion_bd),
    _m: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> BandejaSalida:
    curso = _curso(bd, curso_id)
    consulta = bd.query(MensajeSaliente).filter(
        MensajeSaliente.curso_id == curso_id,
        or_(MensajeSaliente.canal != "CORREO", MensajeSaliente.evento == "aviso_sin_corrector"),
    )
    for campo, valor in (
        (MensajeSaliente.canal, canal),
        (MensajeSaliente.evento, evento),
        (MensajeSaliente.estado, estado),
        (MensajeSaliente.tarea_id, tarea_id),
        (MensajeSaliente.estudiante_id, estudiante_id),
        (MensajeSaliente.repositorio_id, repositorio_id),
    ):
        if valor is not None:
            consulta = consulta.filter(campo == valor)
    mensajes = consulta.order_by(MensajeSaliente.creado_en.desc()).limit(limite).all()
    response.headers["X-Llamadas-Externas"] = "0"
    return BandejaSalida(
        comunicaciones_salientes=curso.comunicaciones_salientes,
        suspension_motivo=curso.suspension_motivo,
        canal_activo=curso.canal_comunicacion_activo,
        mensajes=[_salida(m) for m in mensajes],
    )


def _mensaje(bd: Session, curso_id: uuid.UUID, mensaje_id: uuid.UUID) -> MensajeSaliente:
    mensaje = bd.get(MensajeSaliente, mensaje_id)
    if mensaje is None or mensaje.curso_id != curso_id:
        raise HTTPException(status_code=404)
    return mensaje


@router.post(
    "/api/cursos/{curso_id}/comunicaciones/{mensaje_id}/{accion}",
    response_model=MensajeSalida,
    dependencies=[Depends(exigir_csrf)],
)
def accion_sobre_mensaje(
    curso_id: uuid.UUID,
    mensaje_id: uuid.UUID,
    accion: str,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.COMUNICACION_ENVIAR)),
) -> MensajeSalida:
    mensaje = _mensaje(bd, curso_id, mensaje_id)
    if mensaje.canal == "CORREO" and accion != "cancelar":
        raise HTTPException(
            status_code=409, detail="Solicita un nuevo aviso desde Corrección cuando corresponda."
        )
    try:
        if accion == "reintentar":
            comunicaciones_repo.reintentar(bd, mensaje)
            return _salida(mensaje)
        if accion == "reenviar":
            return _salida(comunicaciones_repo.reenviar(bd, mensaje, actor_id=membresia.usuario_id))
        if accion == "cancelar":
            comunicaciones_repo.cancelar(bd, mensaje)
            return _salida(mensaje)
        if accion == "retractar":
            comunicaciones_repo.solicitar_retractacion(bd, mensaje, actor_id=membresia.usuario_id)
            return _salida(mensaje)
    except comunicaciones_repo.AccionNoPermitida as exc:
        raise _conflicto(exc) from exc
    raise HTTPException(status_code=404)


# --- Composicion manual (S11.7.1) y anuncios (S11.8.5) ---


class MensajeManualEntrada(BaseModel):
    estudiante_ids: list[uuid.UUID] = []
    grupo_id: uuid.UUID | None = None
    tarea_id: uuid.UUID | None = None
    asunto: str = Field(min_length=1, max_length=200)
    cuerpo: str = Field(min_length=1, max_length=4000)
    confirmar_no_activos: bool = False


@router.post(
    "/api/cursos/{curso_id}/comunicaciones/mensajes",
    status_code=202,
    dependencies=[Depends(exigir_csrf)],
)
def enviar_mensaje_manual(
    curso_id: uuid.UUID,
    datos: MensajeManualEntrada,
    response: Response,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.COMUNICACION_ENVIAR)),
) -> dict[str, Any]:
    curso = _curso(bd, curso_id)
    if _ETIQUETA_HTML.search(datos.cuerpo):
        raise HTTPException(
            status_code=422, detail="El mensaje es de texto plano: sin etiquetas HTML."
        )
    estudiantes = (
        bd.query(Estudiante)
        .filter(Estudiante.curso_id == curso.id, Estudiante.id.in_(datos.estudiante_ids))
        .all()
        if datos.estudiante_ids
        else []
    )
    if datos.grupo_id is not None:
        estudiantes += comunicaciones_repo.estudiantes_de_grupo(bd, datos.grupo_id)
    unicos = {e.id: e for e in estudiantes}
    if not unicos:
        raise HTTPException(status_code=422, detail="Elige al menos un destinatario.")
    no_activos = [e.nombre for e in unicos.values() if e.estado not in ("ACTIVO", "INVITADO")]
    if no_activos and not datos.confirmar_no_activos:
        raise HTTPException(
            status_code=409,
            detail={
                "codigo": "CONFIRMAR_NO_ACTIVOS",
                "motivo": "Hay destinatarios que ya no están activos en el curso: "
                + ", ".join(no_activos)
                + ". Confirma si igual quieres escribirles.",
            },
        )
    autor = bd.get(Usuario, membresia.usuario_id)
    assert autor is not None
    encolados = comunicaciones_repo.componer_mensajes(
        bd,
        curso=curso,
        estudiantes=list(unicos.values()),
        asunto=datos.asunto,
        cuerpo=datos.cuerpo,
        autor=autor,
        tarea_id=datos.tarea_id,
    )
    response.headers["X-Llamadas-Externas"] = "0"
    return {
        "encolados": encolados,
        "aviso": f"Se enviarán {encolados} mensajes; puedes seguir el estado en la bandeja.",
    }


class AnuncioEntrada(BaseModel):
    titulo: str = Field(min_length=1, max_length=120)
    cuerpo_html: str = Field(min_length=1, max_length=8000)
    seccion_ids: list[uuid.UUID] = []
    tarea_id: uuid.UUID | None = None
    confirmacion_destinatarios: int | None = None


@router.post(
    "/api/cursos/{curso_id}/comunicaciones/anuncios",
    status_code=202,
    dependencies=[Depends(exigir_csrf)],
)
def publicar_anuncio(
    curso_id: uuid.UUID,
    datos: AnuncioEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.COMUNICACION_ENVIAR)),
) -> dict[str, Any]:
    curso = _curso(bd, curso_id)
    etiquetas = {e.lower() for e in _ETIQUETA_HTML.findall(datos.cuerpo_html)}
    if etiquetas - {"p", "ul", "li", "a", "strong"}:
        raise HTTPException(
            status_code=422, detail="Solo se admiten las etiquetas p, ul, li, a y strong."
        )
    secciones = (
        bd.query(Seccion)
        .filter(Seccion.curso_id == curso.id, Seccion.id.in_(datos.seccion_ids))
        .all()
        if datos.seccion_ids
        else []
    )
    consulta = bd.query(Estudiante.id).filter(
        Estudiante.curso_id == curso.id, Estudiante.estado == "ACTIVO"
    )
    if secciones:
        consulta = consulta.join(Matricula, Matricula.estudiante_id == Estudiante.id).filter(
            Matricula.seccion_id.in_([s.id for s in secciones])
        )
    alcanzados = consulta.distinct().count()
    # S11.8.8: confirmacion reforzada para anuncios al curso o a mas de 10.
    if (not secciones or alcanzados > 10) and datos.confirmacion_destinatarios != alcanzados:
        raise HTTPException(
            status_code=409,
            detail={
                "codigo": "CONFIRMAR_DESTINATARIOS",
                "motivo": f"Este anuncio llega a {alcanzados} estudiantes. "
                "Escribe ese número para confirmar.",
                "destinatarios": alcanzados,
            },
        )
    autor = bd.get(Usuario, membresia.usuario_id)
    assert autor is not None
    mensaje = comunicaciones_repo.componer_anuncio(
        bd,
        curso=curso,
        titulo=datos.titulo,
        cuerpo_html=datos.cuerpo_html,
        secciones=secciones,
        autor=autor,
        tarea_id=datos.tarea_id,
    )
    return {"mensaje_id": str(mensaje.id) if mensaje else None, "destinatarios": alcanzados}


# --- Suspension del curso (A-225) ---


class SuspensionEntrada(BaseModel):
    suspendidas: bool
    motivo: str | None = None


@router.patch("/api/cursos/{curso_id}/comunicaciones", dependencies=[Depends(exigir_csrf)])
def suspender(
    curso_id: uuid.UUID,
    datos: SuspensionEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_ADMINISTRAR)),
) -> dict[str, str | None]:
    curso = _curso(bd, curso_id)
    if datos.suspendidas and not (datos.motivo or "").strip():
        raise HTTPException(status_code=422, detail="Escribe por qué suspendes las comunicaciones.")
    try:
        comunicaciones_repo.cambiar_suspension(
            bd,
            curso,
            suspendidas=datos.suspendidas,
            motivo=datos.motivo,
            actor_id=membresia.usuario_id,
        )
    except comunicaciones_repo.AccionNoPermitida as exc:
        raise _conflicto(exc) from exc
    return {
        "comunicaciones_salientes": curso.comunicaciones_salientes,
        "motivo": curso.suspension_motivo,
    }


# --- Interruptores por tarea (S11.6.3) y recordatorio de mapeo del curso ---


class ReglaSalida(BaseModel):
    evento: str
    titulo: str
    activa: bool
    por_defecto: bool
    advertencia_al_apagar: str | None
    destinatarios_hoy: int | None
    vista_previa_asunto: str
    vista_previa_cuerpo: str
    vista_previa_con_ejemplo: bool


def _valores_de_ejemplo(
    bd: Session, curso: Curso, tarea: Tarea | None
) -> tuple[dict[str, str], bool]:
    estudiante = (
        bd.query(Estudiante)
        .filter(Estudiante.curso_id == curso.id, Estudiante.estado == "ACTIVO")
        .order_by(Estudiante.nombre_ordenable)
        .first()
    )
    # Solo un repositorio ya creado tiene URL; uno que espera informacion
    # dejaria `repositorio.url` vacia y la plantilla no se construiria (500).
    repo = (
        bd.query(Repositorio)
        .filter(
            Repositorio.tarea_id == tarea.id,
            Repositorio.url_html.isnot(None),
            Repositorio.url_html != "",
        )
        .order_by(Repositorio.nombre)
        .first()
        if tarea is not None
        else None
    )
    entrega = (
        bd.query(Entrega).filter(Entrega.tarea_id == tarea.id).order_by(Entrega.orden).first()
        if tarea is not None
        else None
    )
    real = estudiante is not None and (tarea is None or repo is not None)
    return (
        {
            "estudiante.nombre": estudiante.nombre if estudiante else "Estudiante de ejemplo",
            "tarea.nombre": tarea.nombre if tarea else "",
            "curso.nombre": curso.nombre,
            "curso.codigo": curso.codigo,
            "curso.titular": "el profesor del curso",
            "organizacion.nombre": curso.github_org_login or "organizacion",
            "repositorio.nombre": repo.nombre if repo else "repositorio-de-ejemplo",
            "repositorio.url": repo.url_html
            if repo and repo.url_html
            else "https://github.com/organizacion/repositorio",
            "acceso.instrucciones": "Te enviamos una invitación de GitHub para ese repositorio.",
            "entrega.nombre": entrega.nombre if entrega else "Entrega",
            "entrega.fecha_cierre": "la fecha de cierre de cada estudiante",
            "cuenta_github.login": "tu-usuario",
            "grupo.nombre": "Grupo",
            "correccion.nota": "6,5",
            "mensaje.asunto": "",
            "mensaje.cuerpo": "",
            "docente.nombre": "",
        },
        not real,
    )


def _destinatarios_hoy(bd: Session, curso: Curso, tarea: Tarea, evento: str) -> int | None:
    from datetime import timedelta

    from app.adaptadores.base import ahora_utc

    ahora = ahora_utc()
    if evento in ("repositorio_disponible", "recordatorio_invitacion"):
        consulta = (
            bd.query(AccesoRepositorio.id)
            .join(Repositorio, Repositorio.id == AccesoRepositorio.repositorio_id)
            .filter(Repositorio.tarea_id == tarea.id, AccesoRepositorio.estado == "INVITADO")
        )
        if evento == "recordatorio_invitacion":
            consulta = consulta.filter(AccesoRepositorio.invitado_en <= ahora - timedelta(hours=48))
        return consulta.count()
    if evento == "proximidad_cierre":
        return (
            bd.query(FechaEfectiva.id)
            .join(Entrega, Entrega.id == FechaEfectiva.entrega_id)
            .filter(
                Entrega.tarea_id == tarea.id,
                FechaEfectiva.estado == "VIGENTE",
                FechaEfectiva.due_at_utc > ahora,
                FechaEfectiva.due_at_utc <= ahora + timedelta(hours=48),
            )
            .count()
        )
    return None


def _regla(bd: Session, curso: Curso, tarea: Tarea | None, evento: str) -> ReglaSalida:
    valores, ejemplo = _valores_de_ejemplo(bd, curso, tarea)
    plantilla = PLANTILLAS[evento] if evento in PLANTILLAS else None
    asunto = cuerpo = ""
    if plantilla is not None:
        asunto = renderizar(
            plantilla.asunto, plantilla, {**valores, "repositorio.url": valores["repositorio.url"]}
        )
        cuerpo = renderizar(plantilla.cuerpo, plantilla, valores)
    elif evento == "cambio_de_fecha":
        asunto = "Cambio de fecha — (tarea) · (entrega)"
        cuerpo = (
            "Anuncio automático con la fecha anterior, la nueva y a quién aplica. No es editable."
        )
    return ReglaSalida(
        evento=evento,
        titulo=TITULO_EVENTO[evento],
        activa=comunicaciones_repo.regla_activa(bd, curso.id, tarea.id if tarea else None, evento),
        por_defecto=EVENTOS[evento].activo_por_defecto,
        advertencia_al_apagar=ADVERTENCIA_AL_APAGAR.get(evento),
        destinatarios_hoy=_destinatarios_hoy(bd, curso, tarea, evento) if tarea else None,
        vista_previa_asunto=asunto,
        vista_previa_cuerpo=cuerpo,
        vista_previa_con_ejemplo=ejemplo,
    )


def _tarea(bd: Session, curso_id: uuid.UUID, tarea_id: uuid.UUID) -> tuple[Curso, Tarea]:
    tarea = bd.get(Tarea, tarea_id)
    curso = bd.get(Curso, curso_id)
    if tarea is None or curso is None or tarea.curso_id != curso_id:
        raise HTTPException(status_code=404)
    return curso, tarea


@router.get(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/comunicaciones", response_model=list[ReglaSalida]
)
def reglas_de_tarea(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    response: Response,
    bd: Session = Depends(obtener_sesion_bd),
    _m: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> list[ReglaSalida]:
    curso, tarea = _tarea(bd, curso_id, tarea_id)
    response.headers["X-Llamadas-Externas"] = "0"
    return [_regla(bd, curso, tarea, e) for e, d in EVENTOS.items() if d.alcance == "TAREA"]


class CambioRegla(BaseModel):
    activa: bool


@router.put(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/comunicaciones/{evento}",
    dependencies=[Depends(exigir_csrf)],
)
def cambiar_regla_de_tarea(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    evento: str,
    datos: CambioRegla,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.COMUNICACION_ENVIAR)),
) -> dict[str, Any]:
    curso, tarea = _tarea(bd, curso_id, tarea_id)
    if evento not in EVENTOS or EVENTOS[evento].alcance != "TAREA":
        raise HTTPException(status_code=404, detail="Ese aviso no existe para una tarea.")
    resumen = comunicaciones_repo.cambiar_regla(
        bd,
        curso=curso,
        tarea_id=tarea.id,
        evento=evento,
        activa=datos.activa,
        actor_id=membresia.usuario_id,
    )
    return {"evento": evento, "activa": datos.activa, **resumen}


@router.get(
    "/api/cursos/{curso_id}/comunicaciones-curso/recordatorio-mapeo", response_model=ReglaSalida
)
def regla_recordatorio_mapeo(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _m: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> ReglaSalida:
    return _regla(bd, _curso(bd, curso_id), None, "recordatorio_mapeo")


@router.put(
    "/api/cursos/{curso_id}/comunicaciones-curso/recordatorio-mapeo",
    dependencies=[Depends(exigir_csrf)],
)
def cambiar_recordatorio_mapeo(
    curso_id: uuid.UUID,
    datos: CambioRegla,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.COMUNICACION_ENVIAR)),
) -> dict[str, Any]:
    curso = _curso(bd, curso_id)
    resumen = comunicaciones_repo.cambiar_regla(
        bd,
        curso=curso,
        tarea_id=None,
        evento="recordatorio_mapeo",
        activa=datos.activa,
        actor_id=membresia.usuario_id,
    )
    return {"evento": "recordatorio_mapeo", "activa": datos.activa, **resumen}


# --- Supresion por estudiante (S11.2.6) ---


class SupresionEntrada(BaseModel):
    alcance: str = Field(pattern="^(TODAS_AUTOMATICAS|SOLO_RECORDATORIOS)$")
    motivo: str = Field(min_length=3, max_length=500)


@router.post(
    "/api/cursos/{curso_id}/estudiantes/{estudiante_id}/supresion",
    dependencies=[Depends(exigir_csrf)],
)
def suprimir(
    curso_id: uuid.UUID,
    estudiante_id: uuid.UUID,
    datos: SupresionEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.COMUNICACION_ENVIAR)),
) -> dict[str, str]:
    estudiante = bd.get(Estudiante, estudiante_id)
    if estudiante is None or estudiante.curso_id != curso_id:
        raise HTTPException(status_code=404)
    try:
        fila = comunicaciones_repo.crear_supresion(
            bd,
            curso_id=curso_id,
            estudiante_id=estudiante_id,
            alcance=datos.alcance,
            motivo=datos.motivo,
            actor_id=membresia.usuario_id,
        )
    except comunicaciones_repo.AccionNoPermitida as exc:
        raise _conflicto(exc) from exc
    return {"alcance": fila.alcance}


@router.delete(
    "/api/cursos/{curso_id}/estudiantes/{estudiante_id}/supresion",
    dependencies=[Depends(exigir_csrf)],
)
def levantar_supresion(
    curso_id: uuid.UUID,
    estudiante_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.COMUNICACION_ENVIAR)),
) -> dict[str, bool]:
    try:
        comunicaciones_repo.levantar_supresion(
            bd, curso_id=curso_id, estudiante_id=estudiante_id, actor_id=membresia.usuario_id
        )
    except comunicaciones_repo.AccionNoPermitida as exc:
        raise _conflicto(exc) from exc
    return {"levantada": True}
