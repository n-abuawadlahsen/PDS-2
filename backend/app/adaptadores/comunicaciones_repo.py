"""Comunicaciones ampliadas: reglas, programacion, cambios de fecha, mensajes
manuales y la bandeja (SPEC 11 S11.2, S11.6-S11.8, S11.10; A-125..A-130,
A-224..A-228; Etapa F10).

Nada de aqui llama a Canvas: todo se inserta en `mensaje_saliente` y lo envia
`despachar_outbox`, que reevalua las siete guardas justo antes de cada
intento. `comunicaciones_programadas` evalua y encola siempre, incluso con un
interruptor apagado, para que los topes y el historial queden completos.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.adaptadores import bitacora_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_aprovisionamiento import (
    AccesoRepositorio,
    FechaEfectiva,
    MensajeSaliente,
    Repositorio,
    Sujeto,
)
from app.adaptadores.modelos_comunicacion import (
    CambioFecha,
    ReglaComunicacion,
    SupresionComunicacion,
    VentanaSupresion,
)
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_identidad import Usuario
from app.adaptadores.modelos_mapeo import MapeoGithub
from app.adaptadores.modelos_padron import Estudiante, Grupo, Matricula, PertenenciaGrupo, Seccion
from app.adaptadores.modelos_tarea import Entrega, Tarea
from app.dominio.comunicaciones import (
    DIAS_SUSPENSION_MAXIMA,
    EVENTOS,
    PLANTILLAS,
    anuncio_cambio_fecha,
    clave_idempotencia,
)
from app.dominio.estados import (
    CanalComunicacionActivo,
    CanalMensaje,
    EstadoAccesoRepositorio,
    EstadoMensaje,
    OrigenMensaje,
)
from app.dominio.fechas import formatear_fecha

# S11.8.3: agrupar 20 minutos; anunciar solo si algo se movio mas de 60.
VENTANA_AGRUPACION = timedelta(minutes=20)
UMBRAL_ANUNCIO = timedelta(minutes=60)
MAX_REENVIOS = 3
HORA_RECORDATORIO_MAPEO = 9
_NO_TERMINALES = (
    EstadoMensaje.PROGRAMADO.value,
    EstadoMensaje.DIFERIDO.value,
    EstadoMensaje.PENDIENTE.value,
    EstadoMensaje.REINTENTAR.value,
    EstadoMensaje.ESPERANDO_LIMITE.value,
    EstadoMensaje.ESPERANDO_CREDENCIAL.value,
    EstadoMensaje.BLOQUEADO.value,
    EstadoMensaje.REQUIERE_ATENCION.value,
)
_TERMINALES = (
    EstadoMensaje.ENVIADO.value,
    EstadoMensaje.FALLIDO.value,
    EstadoMensaje.CANCELADO.value,
    EstadoMensaje.SUPRIMIDO.value,
    EstadoMensaje.CADUCADO.value,
    EstadoMensaje.RETRACTADO.value,
)
_AMBITO_POR_ORIGEN = {"BASE": "CURSO", "SECCION": "SECCION", "GRUPO": "GRUPO", "ADHOC": "ADHOC"}
_AMPLITUD = {"CURSO": 3, "SECCION": 2, "GRUPO": 1, "ADHOC": 0}


class AccionNoPermitida(Exception):
    """La accion no aplica al estado del mensaje (la ruta responde 409)."""


# --- Hechos para las guardas ---


def regla_activa(bd: Session, curso_id: uuid.UUID, tarea_id: uuid.UUID | None, evento: str) -> bool:
    """Sin fila, el valor por defecto del catalogo (S11.6.3)."""
    definicion = EVENTOS.get(evento)
    if definicion is None:
        return True
    consulta = bd.query(ReglaComunicacion).filter(
        ReglaComunicacion.curso_id == curso_id, ReglaComunicacion.evento == evento
    )
    if definicion.alcance == "CURSO":
        fila = consulta.filter(ReglaComunicacion.tarea_id.is_(None)).one_or_none()
    else:
        fila = consulta.filter(ReglaComunicacion.tarea_id == tarea_id).one_or_none()
    return fila.activa if fila is not None else definicion.activo_por_defecto


def supresion_vigente(
    bd: Session, curso_id: uuid.UUID, estudiante_id: uuid.UUID, ahora: datetime
) -> str | None:
    fila = (
        bd.query(SupresionComunicacion)
        .filter(
            SupresionComunicacion.curso_id == curso_id,
            SupresionComunicacion.estudiante_id == estudiante_id,
            SupresionComunicacion.levantada_en.is_(None),
        )
        .one_or_none()
    )
    if fila is None or (fila.vigente_hasta is not None and fila.vigente_hasta <= ahora):
        return None
    return fila.alcance


def en_ventana_supresion(bd: Session, curso_id: uuid.UUID, ahora: datetime) -> bool:
    return (
        bd.query(VentanaSupresion.id)
        .filter(
            (VentanaSupresion.curso_id == curso_id) | VentanaSupresion.curso_id.is_(None),
            VentanaSupresion.desde <= ahora,
            VentanaSupresion.hasta > ahora,
        )
        .first()
        is not None
    )


def _inicio_del_dia(curso: Curso, ahora: datetime) -> datetime:
    local = ahora.astimezone(ZoneInfo(curso.zona_horaria))
    return local.replace(hour=0, minute=0, second=0, microsecond=0)


def automaticos_enviados_hoy(
    bd: Session, curso: Curso, estudiante_id: uuid.UUID, ahora: datetime
) -> int:
    """Automaticos ya enviados a esa persona en el dia del curso. Un
    recordatorio fusionado dentro de otro mensaje no cuenta dos veces."""
    return (
        bd.query(MensajeSaliente)
        .filter(
            MensajeSaliente.curso_id == curso.id,
            MensajeSaliente.estudiante_id == estudiante_id,
            MensajeSaliente.origen == OrigenMensaje.AUTOMATICO.value,
            MensajeSaliente.evento.in_(list(EVENTOS)),
            MensajeSaliente.canal != CanalMensaje.CANVAS_ANUNCIO.value,
            MensajeSaliente.estado == EstadoMensaje.ENVIADO.value,
            MensajeSaliente.enviado_en >= _inicio_del_dia(curso, ahora),
            ~MensajeSaliente.referencia.has_key("fusionado_en"),
        )
        .count()
    )


def proximidad_para_fusionar(bd: Session, mensaje: MensajeSaliente) -> MensajeSaliente | None:
    """S11.6.5: un aviso de cierre pendiente para la misma persona y tarea
    viaja dentro del aviso de repositorio, si su interruptor esta encendido."""
    if mensaje.tarea_id is None or mensaje.estudiante_id is None:
        return None
    if not regla_activa(bd, mensaje.curso_id, mensaje.tarea_id, "proximidad_cierre"):
        return None
    return (
        bd.query(MensajeSaliente)
        .filter(
            MensajeSaliente.evento == "proximidad_cierre",
            MensajeSaliente.tarea_id == mensaje.tarea_id,
            MensajeSaliente.estudiante_id == mensaje.estudiante_id,
            MensajeSaliente.estado.in_(
                (EstadoMensaje.PENDIENTE.value, EstadoMensaje.PROGRAMADO.value)
            ),
        )
        .order_by(MensajeSaliente.creado_en)
        .first()
    )


# --- Encolado generico a un estudiante ---


def _canal_estudiante(curso: Curso) -> CanalMensaje:
    if curso.canal_comunicacion_activo == CanalComunicacionActivo.COMENTARIO_ENTREGA.value:
        return CanalMensaje.CANVAS_COMENTARIO
    return CanalMensaje.CANVAS_CONVERSACION


def encolar_a_estudiante(
    bd: Session,
    *,
    curso: Curso,
    estudiante: Estudiante,
    evento: str,
    plantilla: str,
    entidad: str,
    referencia: dict[str, Any] | None = None,
    tarea_id: uuid.UUID | None = None,
    entrega_id: uuid.UUID | None = None,
    sujeto_id: uuid.UUID | None = None,
    repositorio_id: uuid.UUID | None = None,
    caduca_en: datetime | None = None,
    origen: OrigenMensaje = OrigenMensaje.AUTOMATICO,
    disparado_por: uuid.UUID | None = None,
    generacion: int = 1,
    reemplaza_a_id: uuid.UUID | None = None,
) -> MensajeSaliente | None:
    canal = _canal_estudiante(curso)
    clave = clave_idempotencia(
        canal=canal.value,
        destinatario=str(estudiante.canvas_user_id),
        plantilla=evento if origen != OrigenMensaje.MANUAL else plantilla,
        entidad=entidad,
        generacion=generacion,
    )
    if bd.query(MensajeSaliente.id).filter(MensajeSaliente.clave_idempotencia == clave).first():
        return None
    mensaje = MensajeSaliente(
        curso_id=curso.id,
        canal=canal.value,
        evento=evento,
        clave_idempotencia=clave,
        generacion=generacion,
        reemplaza_a_id=reemplaza_a_id,
        tarea_id=tarea_id,
        entrega_id=entrega_id,
        sujeto_id=sujeto_id,
        repositorio_id=repositorio_id,
        estudiante_id=estudiante.id,
        referencia=referencia or {},
        destinatario=estudiante.nombre,
        destinatario_canvas_user_id=estudiante.canvas_user_id,
        plantilla=plantilla,
        plantilla_version=PLANTILLAS[plantilla].version,
        origen=origen.value,
        disparado_por_usuario_id=disparado_por,
        caduca_en=caduca_en,
        estado=EstadoMensaje.PENDIENTE.value,
        intentos=0,
        creado_en=ahora_utc(),
    )
    bd.add(mensaje)
    bd.flush()
    return mensaje


def destinatarios_del_sujeto(bd: Session, sujeto: Sujeto) -> list[Estudiante]:
    """Un sujeto grupal se expande a sus integrantes `accepted` vigentes:
    cada uno recibe su propio mensaje (S11.7.2)."""
    if sujeto.estudiante_id is not None:
        estudiante = bd.get(Estudiante, sujeto.estudiante_id)
        return [estudiante] if estudiante is not None else []
    return (
        bd.query(Estudiante)
        .join(PertenenciaGrupo, PertenenciaGrupo.estudiante_id == Estudiante.id)
        .filter(
            PertenenciaGrupo.grupo_id == sujeto.grupo_id,
            PertenenciaGrupo.workflow_state == "accepted",
            PertenenciaGrupo.activa_hasta.is_(None),
        )
        .order_by(Estudiante.nombre_ordenable)
        .all()
    )


# --- Programacion (trabajo `comunicaciones_programadas`, S11.6.2) ---


def _tareas_en_curso(bd: Session, curso: Curso) -> list[Tarea]:
    return (
        bd.query(Tarea)
        .filter(Tarea.curso_id == curso.id, Tarea.estado.in_(("ACTIVA", "INCONSISTENTE")))
        .all()
    )


def _ultimo_cierre(bd: Session, tarea_id: uuid.UUID) -> datetime | None:
    from sqlalchemy import func

    valor = (
        bd.query(func.max(FechaEfectiva.due_at_utc))
        .join(Entrega, Entrega.id == FechaEfectiva.entrega_id)
        .filter(Entrega.tarea_id == tarea_id, FechaEfectiva.estado == "VIGENTE")
        .scalar()
    )
    return valor if isinstance(valor, datetime) else None


def _previos(bd: Session, evento: str, **filtros: Any) -> list[MensajeSaliente]:
    consulta = bd.query(MensajeSaliente).filter(MensajeSaliente.evento == evento)
    for campo, valor in filtros.items():
        if campo.startswith("ref_"):
            consulta = consulta.filter(MensajeSaliente.referencia[campo[4:]].astext == str(valor))
        else:
            consulta = consulta.filter(getattr(MensajeSaliente, campo) == valor)
    return consulta.order_by(MensajeSaliente.creado_en).all()


def _programar_recordatorio_invitacion(
    bd: Session, curso: Curso, tareas: list[Tarea], ahora: datetime
) -> int:
    nuevos = 0
    for tarea in tareas:
        caduca = _ultimo_cierre(bd, tarea.id)
        for acceso, repo, est in (
            bd.query(AccesoRepositorio, Repositorio, Estudiante)
            .join(Repositorio, Repositorio.id == AccesoRepositorio.repositorio_id)
            .join(Estudiante, Estudiante.id == AccesoRepositorio.estudiante_id)
            .filter(Repositorio.tarea_id == tarea.id)
        ):
            previos = _previos(bd, "recordatorio_invitacion", ref_acceso_repositorio_id=acceso.id)
            if acceso.estado != EstadoAccesoRepositorio.INVITADO.value:
                # Ya acepto: lo pendiente no se envia (YA_ACEPTADO).
                for m in previos:
                    if m.estado in _NO_TERMINALES:
                        m.estado, m.motivo_estado = EstadoMensaje.SUPRIMIDO.value, "YA_ACEPTADO"
                continue
            if acceso.invitado_en is None or ahora - acceso.invitado_en < timedelta(hours=48):
                continue
            if len(previos) >= 3 or (
                previos and ahora - previos[-1].creado_en < timedelta(hours=24)
            ):
                continue
            if encolar_a_estudiante(
                bd,
                curso=curso,
                estudiante=est,
                evento="recordatorio_invitacion",
                plantilla="recordatorio_invitacion",
                entidad=f"{acceso.id}:{len(previos) + 1}",
                referencia={
                    "acceso_repositorio_id": str(acceso.id),
                    "via_invitacion": True,
                    "invitacion_url": acceso.invitacion_html_url,
                },
                tarea_id=tarea.id,
                sujeto_id=repo.sujeto_id,
                repositorio_id=repo.id,
                caduca_en=caduca,
            ):
                nuevos += 1
    return nuevos


def _programar_proximidad(bd: Session, curso: Curso, tareas: list[Tarea], ahora: datetime) -> int:
    """48 h y 6 h antes de la fecha efectiva de cada sujeto, nunca la base."""
    nuevos = 0
    ids = [t.id for t in tareas]
    if not ids:
        return 0
    for fecha, entrega, sujeto in (
        bd.query(FechaEfectiva, Entrega, Sujeto)
        .join(Entrega, Entrega.id == FechaEfectiva.entrega_id)
        .join(Sujeto, Sujeto.id == FechaEfectiva.sujeto_id)
        .filter(
            Entrega.tarea_id.in_(ids),
            Entrega.publicada.is_(True),
            Sujeto.activo.is_(True),
            FechaEfectiva.estado == "VIGENTE",
            FechaEfectiva.due_at_utc > ahora,
            FechaEfectiva.due_at_utc <= ahora + timedelta(hours=48),
        )
    ):
        due = fecha.due_at_utc
        assert due is not None
        ventana = "H6" if due - ahora <= timedelta(hours=6) else "H48"
        for est in destinatarios_del_sujeto(bd, sujeto):
            previos = [
                m
                for m in _previos(
                    bd, "proximidad_cierre", entrega_id=entrega.id, estudiante_id=est.id
                )
                if (m.referencia or {}).get("ventana") == ventana
            ]
            if len(previos) >= 3 or any(
                (m.referencia or {}).get("fecha_cierre") == due.isoformat() for m in previos
            ):
                continue
            cambio = bool(previos)
            if encolar_a_estudiante(
                bd,
                curso=curso,
                estudiante=est,
                evento="proximidad_cierre",
                plantilla="proximidad_cierre_fecha_cambio" if cambio else "proximidad_cierre",
                entidad=f"{entrega.id}:{est.id}:{ventana}:{due.isoformat()}",
                referencia={
                    "entrega_nombre": entrega.nombre,
                    "fecha_cierre": due.isoformat(),
                    "ventana": ventana,
                },
                tarea_id=entrega.tarea_id,
                entrega_id=entrega.id,
                sujeto_id=sujeto.id,
                caduca_en=due,
            ):
                nuevos += 1
    return nuevos


def _programar_recordatorio_mapeo(bd: Session, curso: Curso, ahora: datetime) -> int:
    """09:00 del curso, a quien no tiene cuenta de GitHub vigente: hasta 3 por
    persona, nunca en dias consecutivos, desde 24 h despues de crear la tarea
    de registro."""
    if curso.canvas_assignment_id_registro is None or curso.registro_creado_en is None:
        return 0
    local = ahora.astimezone(ZoneInfo(curso.zona_horaria))
    vigentes = {
        m.estudiante_id
        for m in bd.query(MapeoGithub.estudiante_id).filter(
            MapeoGithub.curso_id == curso.id, MapeoGithub.estado == "VIGENTE"
        )
    }
    nuevos = 0
    for est in bd.query(Estudiante).filter(Estudiante.curso_id == curso.id):
        previos = _previos(bd, "recordatorio_mapeo", curso_id=curso.id, estudiante_id=est.id)
        if est.id in vigentes:
            for m in previos:
                if m.estado in _NO_TERMINALES:
                    m.estado, m.motivo_estado = EstadoMensaje.SUPRIMIDO.value, "MAPEO_YA_VIGENTE"
            continue
        if est.estado != "ACTIVO" or local.hour < HORA_RECORDATORIO_MAPEO:
            continue
        if ahora - curso.registro_creado_en < timedelta(hours=24) or len(previos) >= 3:
            continue
        if previos:
            ultimo = previos[-1].creado_en.astimezone(ZoneInfo(curso.zona_horaria)).date()
            if (local.date() - ultimo).days < 2:
                continue
        if encolar_a_estudiante(
            bd,
            curso=curso,
            estudiante=est,
            evento="recordatorio_mapeo",
            plantilla="recordatorio_mapeo",
            entidad=f"{curso.id}:{est.id}:{len(previos) + 1}",
        ):
            nuevos += 1
    return nuevos


def programar(bd: Session, curso: Curso, *, ahora: datetime | None = None) -> dict[str, int]:
    ahora = ahora or ahora_utc()
    tareas = _tareas_en_curso(bd, curso)
    resumen = {
        "recordatorio_invitacion": _programar_recordatorio_invitacion(bd, curso, tareas, ahora),
        "proximidad_cierre": _programar_proximidad(bd, curso, tareas, ahora),
        "recordatorio_mapeo": _programar_recordatorio_mapeo(bd, curso, ahora),
        "cambio_de_fecha": anunciar_cambios(bd, curso, ahora=ahora),
    }
    bd.flush()
    return resumen


# --- Cambios de fecha (S11.8.2-S11.8.3) ---


def al_cambiar_fecha(
    bd: Session,
    *,
    entrega: Entrega,
    sujeto: Sujeto,
    anterior: datetime | None,
    nueva: datetime | None,
    origen: str | None,
    ahora: datetime,
) -> None:
    """En la misma transaccion que recalcula la fecha: el aviso de cierre
    pendiente con la fecha vieja deja de tener sentido, y el cambio se agrupa
    en su `cambio_fecha` abierto (sin alargar la ventana)."""
    for m in bd.query(MensajeSaliente).filter(
        MensajeSaliente.evento == "proximidad_cierre",
        MensajeSaliente.entrega_id == entrega.id,
        MensajeSaliente.sujeto_id == sujeto.id,
        MensajeSaliente.estado.in_(_NO_TERMINALES),
    ):
        if (m.referencia or {}).get("fecha_cierre") != (nueva.isoformat() if nueva else None):
            m.estado, m.motivo_estado = EstadoMensaje.CADUCADO.value, "CADUCIDAD_ALCANZADA"
            m.caduca_en = ahora
    if not entrega.publicada:
        return
    clave = str(sujeto.id)
    abierto = (
        bd.query(CambioFecha)
        .filter(
            CambioFecha.entrega_id == entrega.id,
            CambioFecha.anunciado_en.is_(None),
            CambioFecha.ventana_cierra_en > ahora,
        )
        .order_by(CambioFecha.detectado_en.desc())
        .first()
    )
    ambito = _AMBITO_POR_ORIGEN.get(origen or "BASE", "CURSO")
    valor_nuevo = nueva.isoformat() if nueva else None
    if abierto is None:
        bd.add(
            CambioFecha(
                entrega_id=entrega.id,
                huella_anterior=json.dumps({clave: anterior.isoformat() if anterior else None}),
                huella_nueva=json.dumps({clave: valor_nuevo}),
                ambito=ambito,
                seccion_ids=[],
                sujeto_ids=[sujeto.id],
                detectado_en=ahora,
                ventana_cierra_en=ahora + VENTANA_AGRUPACION,
            )
        )
    else:
        anteriores = json.loads(abierto.huella_anterior)
        anteriores.setdefault(clave, anterior.isoformat() if anterior else None)
        nuevas = json.loads(abierto.huella_nueva)
        nuevas[clave] = valor_nuevo
        abierto.huella_anterior = json.dumps(anteriores)
        abierto.huella_nueva = json.dumps(nuevas)
        if sujeto.id not in abierto.sujeto_ids:
            abierto.sujeto_ids = [*abierto.sujeto_ids, sujeto.id]
        if _AMPLITUD[ambito] > _AMPLITUD[abierto.ambito]:
            abierto.ambito = ambito
    bd.flush()


def _secciones_de(bd: Session, estudiantes: list[Estudiante]) -> list[Seccion]:
    if not estudiantes:
        return []
    return (
        bd.query(Seccion)
        .join(Matricula, Matricula.seccion_id == Seccion.id)
        .filter(
            Matricula.estudiante_id.in_([e.id for e in estudiantes]), Matricula.activa.is_(True)
        )
        .distinct()
        .order_by(Seccion.nombre)
        .all()
    )


def _encolar_anuncio(
    bd: Session,
    *,
    curso: Curso,
    entidad: str,
    titulo: str,
    cuerpo_html: str,
    cuerpo_plan_b: str | None,
    secciones: list[Seccion],
    destinatario: str,
    evento: str,
    tarea_id: uuid.UUID | None,
    entrega_id: uuid.UUID | None,
    caduca_en: datetime | None,
    origen: OrigenMensaje,
    disparado_por: uuid.UUID | None = None,
) -> MensajeSaliente | None:
    clave = clave_idempotencia(
        canal=CanalMensaje.CANVAS_ANUNCIO.value,
        destinatario=destinatario,
        plantilla="cambio_de_fecha_anuncio" if evento == "cambio_de_fecha" else "anuncio_manual",
        entidad=entidad,
    )
    if bd.query(MensajeSaliente.id).filter(MensajeSaliente.clave_idempotencia == clave).first():
        return None
    mensaje = MensajeSaliente(
        curso_id=curso.id,
        canal=CanalMensaje.CANVAS_ANUNCIO.value,
        evento=evento,
        clave_idempotencia=clave,
        generacion=1,
        tarea_id=tarea_id,
        entrega_id=entrega_id,
        referencia={
            "titulo": titulo,
            "cuerpo_html": cuerpo_html,
            "cuerpo_html_plan_b": cuerpo_plan_b,
            "secciones_canvas": [s.canvas_section_id for s in secciones],
        },
        destinatario=destinatario,
        plantilla="cambio_de_fecha_anuncio" if evento == "cambio_de_fecha" else "anuncio_manual",
        plantilla_version=1,
        origen=origen.value,
        disparado_por_usuario_id=disparado_por,
        caduca_en=caduca_en,
        estado=EstadoMensaje.PENDIENTE.value,
        intentos=0,
        creado_en=ahora_utc(),
    )
    bd.add(mensaje)
    bd.flush()
    return mensaje


def anunciar_cambios(bd: Session, curso: Curso, *, ahora: datetime) -> int:
    """Al cerrar la ventana: se anuncia el cambio neto de mas de 60 minutos.
    Base -> anuncio del curso; seccion -> anuncio a esas secciones (o plan
    B); grupo o ADHOC -> mensaje directo a los afectados, nunca anuncio."""
    creados = 0
    pendientes = (
        bd.query(CambioFecha, Entrega)
        .join(Entrega, Entrega.id == CambioFecha.entrega_id)
        .filter(
            Entrega.curso_id == curso.id,
            CambioFecha.anunciado_en.is_(None),
            CambioFecha.ventana_cierra_en <= ahora,
        )
        .all()
    )
    for cambio, entrega in pendientes:
        tarea = bd.get(Tarea, entrega.tarea_id)
        assert tarea is not None
        anteriores: dict[str, str | None] = json.loads(cambio.huella_anterior)
        por_origen: dict[str, list[tuple[Sujeto, datetime | None, datetime | None]]] = {}
        for clave, antes_iso in anteriores.items():
            sujeto = bd.get(Sujeto, uuid.UUID(clave))
            vigente = (
                bd.query(FechaEfectiva)
                .filter(
                    FechaEfectiva.entrega_id == entrega.id,
                    FechaEfectiva.sujeto_id == uuid.UUID(clave),
                    FechaEfectiva.estado == "VIGENTE",
                )
                .one_or_none()
            )
            antes = datetime.fromisoformat(antes_iso) if antes_iso else None
            ahora_fecha = vigente.due_at_utc if vigente is not None else None
            if sujeto is None or vigente is None:
                continue
            movido = (
                antes is None or ahora_fecha is None or abs(ahora_fecha - antes) > UMBRAL_ANUNCIO
            )
            if movido:
                por_origen.setdefault(vigente.origen, []).append((sujeto, antes, ahora_fecha))
        cambio.anunciado_en = ahora
        if not por_origen:
            continue  # cambio neto menor o igual a 60 minutos: no se anuncia
        zona = curso.zona_horaria
        caduca_base = cambio.detectado_en + timedelta(hours=24)
        primero: MensajeSaliente | None = None

        def texto(fecha: datetime | None, zona: str = zona) -> str:
            return formatear_fecha(fecha, zona) if fecha else "sin fecha de cierre"

        if "BASE" in por_origen:
            _, antes, despues = por_origen["BASE"][0]
            titulo, cuerpo = anuncio_cambio_fecha(
                tarea=tarea.nombre,
                entrega=entrega.nombre,
                anterior=texto(antes),
                nueva=texto(despues),
                a_quien="todo el curso",
                salvaguarda=len(por_origen) > 1,
            )
            primero = (
                _encolar_anuncio(
                    bd,
                    curso=curso,
                    entidad=f"{cambio.id}:CURSO",
                    titulo=titulo,
                    cuerpo_html=cuerpo,
                    cuerpo_plan_b=None,
                    secciones=[],
                    destinatario="Todo el curso",
                    evento="cambio_de_fecha",
                    tarea_id=tarea.id,
                    entrega_id=entrega.id,
                    caduca_en=min(caduca_base, despues) if despues else caduca_base,
                    origen=OrigenMensaje.AUTOMATICO,
                )
                or primero
            )
        if "SECCION" in por_origen and curso.via_anuncio_seccion != "NINGUNA":
            estudiantes = [
                e for s, _, _ in por_origen["SECCION"] for e in destinatarios_del_sujeto(bd, s)
            ]
            secciones = _secciones_de(bd, estudiantes)
            _, antes, despues = por_origen["SECCION"][0]
            nombres = ", ".join(s.nombre for s in secciones) or "las secciones afectadas"
            a_curso = curso.via_anuncio_seccion == "CURSO" or len(secciones) > 3
            tabla = [(s.nombre, texto(despues)) for s in secciones] if len(secciones) > 3 else None
            titulo, cuerpo = anuncio_cambio_fecha(
                tarea=tarea.nombre,
                entrega=entrega.nombre,
                anterior=texto(antes),
                nueva=texto(despues),
                a_quien=nombres,
                seccion_afectada=nombres if a_curso and not tabla else None,
                salvaguarda=True,
                tabla_secciones=tabla,
            )
            _, plan_b = anuncio_cambio_fecha(
                tarea=tarea.nombre,
                entrega=entrega.nombre,
                anterior=texto(antes),
                nueva=texto(despues),
                a_quien=nombres,
                seccion_afectada=nombres,
                salvaguarda=True,
            )
            primero = (
                _encolar_anuncio(
                    bd,
                    curso=curso,
                    entidad=f"{cambio.id}:SECCION",
                    titulo=titulo,
                    cuerpo_html=cuerpo,
                    cuerpo_plan_b=plan_b,
                    secciones=[] if a_curso else secciones,
                    destinatario=nombres,
                    evento="cambio_de_fecha",
                    tarea_id=tarea.id,
                    entrega_id=entrega.id,
                    caduca_en=min(caduca_base, despues) if despues else caduca_base,
                    origen=OrigenMensaje.AUTOMATICO,
                )
                or primero
            )
        for origen_fecha, plantilla in (
            ("GRUPO", "cambio_fecha_grupo"),
            ("ADHOC", "cambio_fecha_directo"),
        ):
            for sujeto, _, despues in por_origen.get(origen_fecha, []):
                grupo = bd.get(Grupo, sujeto.grupo_id) if sujeto.grupo_id else None
                for est in destinatarios_del_sujeto(bd, sujeto):
                    m = encolar_a_estudiante(
                        bd,
                        curso=curso,
                        estudiante=est,
                        evento="cambio_de_fecha",
                        plantilla=plantilla,
                        entidad=f"{cambio.id}:{est.id}",
                        referencia={
                            "entrega_nombre": entrega.nombre,
                            "fecha_cierre": despues.isoformat() if despues else None,
                            "grupo_nombre": grupo.nombre if grupo else "",
                        },
                        tarea_id=tarea.id,
                        entrega_id=entrega.id,
                        sujeto_id=sujeto.id,
                        caduca_en=min(caduca_base, despues) if despues else caduca_base,
                    )
                    primero = primero or m
        if primero is not None:
            cambio.mensaje_saliente_id = primero.id
            creados += 1
    bd.flush()
    return creados


# --- Interruptores (S11.6.3-S11.6.4) ---


def cambiar_regla(
    bd: Session,
    *,
    curso: Curso,
    tarea_id: uuid.UUID | None,
    evento: str,
    activa: bool,
    actor_id: uuid.UUID,
    ahora: datetime | None = None,
) -> dict[str, int]:
    ahora = ahora or ahora_utc()
    definicion = EVENTOS[evento]
    fila = (
        bd.query(ReglaComunicacion)
        .filter(
            ReglaComunicacion.curso_id == curso.id,
            ReglaComunicacion.evento == evento,
            ReglaComunicacion.tarea_id.is_(None)
            if tarea_id is None
            else ReglaComunicacion.tarea_id == tarea_id,
        )
        .one_or_none()
    )
    if fila is None:
        fila = ReglaComunicacion(
            curso_id=curso.id,
            tarea_id=tarea_id,
            alcance=definicion.alcance,
            evento=evento,
            activa=activa,
            actualizada_en=ahora,
        )
        bd.add(fila)
    fila.activa = activa
    fila.actualizada_por = actor_id
    fila.actualizada_en = ahora
    bd.flush()
    mensajes = bd.query(MensajeSaliente).filter(
        MensajeSaliente.curso_id == curso.id,
        MensajeSaliente.evento == evento,
        MensajeSaliente.origen == OrigenMensaje.AUTOMATICO.value,
        MensajeSaliente.tarea_id.is_(None)
        if tarea_id is None
        else MensajeSaliente.tarea_id == tarea_id,
    )
    if not activa:
        # Lo que aun no salio queda filtrado; lo que esta EN_CURSO termina.
        cancelados = en_curso = 0
        for m in mensajes:
            if m.estado in _NO_TERMINALES:
                m.estado, m.motivo_estado = EstadoMensaje.SUPRIMIDO.value, "REGLA_DESACTIVADA"
                cancelados += 1
            elif m.estado == EstadoMensaje.EN_CURSO.value:
                en_curso += 1
        resumen = {"cancelados": cancelados, "en_curso": en_curso}
    else:
        # Recalcula desde cero: lo que sigue siendo verdad sale, con la
        # generacion siguiente (A-224).
        programados = descartados = 0
        filtrados = [
            m
            for m in mensajes
            if m.estado == EstadoMensaje.SUPRIMIDO.value and m.motivo_estado == "REGLA_DESACTIVADA"
        ]
        reemplazados = (
            {
                m.reemplaza_a_id
                for m in bd.query(MensajeSaliente.reemplaza_a_id).filter(
                    MensajeSaliente.reemplaza_a_id.in_([f.id for f in filtrados])
                )
            }
            if filtrados
            else set()
        )
        for m in filtrados:
            if m.id in reemplazados:
                continue
            if m.caduca_en is not None and m.caduca_en <= ahora:
                descartados += 1
                continue
            estudiante = bd.get(Estudiante, m.estudiante_id) if m.estudiante_id else None
            if estudiante is None:
                continue
            if reemitir(bd, m, curso=curso, estudiante=estudiante) is not None:
                programados += 1
        resumen = {"programados": programados, "descartados_por_fecha": descartados}
    bitacora_repo.registrar(
        bd,
        accion="REGLA_COMUNICACION",
        entidad="regla_comunicacion",
        entidad_id=str(fila.id),
        actor_usuario_id=actor_id,
        curso_id=curso.id,
        despues={
            "evento": evento,
            "tarea_id": str(tarea_id) if tarea_id else None,
            "activa": activa,
            **resumen,
        },
    )
    return resumen


def reemitir(
    bd: Session,
    original: MensajeSaliente,
    *,
    curso: Curso,
    estudiante: Estudiante,
    origen: OrigenMensaje | None = None,
    disparado_por: uuid.UUID | None = None,
) -> MensajeSaliente | None:
    """Una fila nueva con la misma entidad y `generacion + 1`; las dos filas
    conviven (CA-11.2-02)."""
    generacion = original.generacion + 1
    clave = clave_idempotencia(
        canal=original.canal,
        destinatario=str(estudiante.canvas_user_id),
        plantilla=original.evento
        if original.origen != OrigenMensaje.MANUAL.value
        else original.plantilla,
        entidad=f"reemision:{original.id}",
        generacion=generacion,
    )
    if bd.query(MensajeSaliente.id).filter(MensajeSaliente.clave_idempotencia == clave).first():
        return None
    nuevo = MensajeSaliente(
        curso_id=original.curso_id,
        canal=original.canal,
        evento=original.evento,
        clave_idempotencia=clave,
        generacion=generacion,
        reemplaza_a_id=original.id,
        tarea_id=original.tarea_id,
        entrega_id=original.entrega_id,
        sujeto_id=original.sujeto_id,
        repositorio_id=original.repositorio_id,
        estudiante_id=original.estudiante_id,
        membresia_id=original.membresia_id,
        referencia=dict(original.referencia or {}),
        destinatario=original.destinatario,
        destinatario_canvas_user_id=original.destinatario_canvas_user_id,
        plantilla=original.plantilla,
        plantilla_version=original.plantilla_version,
        origen=(origen or OrigenMensaje(original.origen)).value,
        disparado_por_usuario_id=disparado_por,
        caduca_en=original.caduca_en,
        estado=EstadoMensaje.PENDIENTE.value,
        intentos=0,
        creado_en=ahora_utc(),
    )
    bd.add(nuevo)
    bd.flush()
    return nuevo


# --- Mensajes y anuncios manuales (S11.7.1, S11.8.5) ---


def componer_mensajes(
    bd: Session,
    *,
    curso: Curso,
    estudiantes: list[Estudiante],
    asunto: str,
    cuerpo: str,
    autor: Usuario,
    tarea_id: uuid.UUID | None,
) -> int:
    """Una fila por destinatario, nunca una conversacion grupal (CA-11.7-01)."""
    lote = uuid.uuid4().hex
    creados = 0
    for est in estudiantes:
        if encolar_a_estudiante(
            bd,
            curso=curso,
            estudiante=est,
            evento="MANUAL",
            plantilla="manual",
            entidad=f"manual:{lote}:{est.id}",
            referencia={"asunto": asunto, "cuerpo": cuerpo, "autor": autor.nombre},
            tarea_id=tarea_id,
            origen=OrigenMensaje.MANUAL,
            disparado_por=autor.id,
        ):
            creados += 1
    return creados


def componer_anuncio(
    bd: Session,
    *,
    curso: Curso,
    titulo: str,
    cuerpo_html: str,
    secciones: list[Seccion],
    autor: Usuario,
    tarea_id: uuid.UUID | None,
) -> MensajeSaliente | None:
    return _encolar_anuncio(
        bd,
        curso=curso,
        entidad=f"manual:{uuid.uuid4().hex}",
        titulo=titulo[:255],
        cuerpo_html=cuerpo_html,
        cuerpo_plan_b=None,
        secciones=secciones,
        destinatario=", ".join(s.nombre for s in secciones) or "Todo el curso",
        evento="MANUAL",
        tarea_id=tarea_id,
        entrega_id=None,
        caduca_en=None,
        origen=OrigenMensaje.MANUAL,
        disparado_por=autor.id,
    )


def estudiantes_de_grupo(bd: Session, grupo_id: uuid.UUID) -> list[Estudiante]:
    return (
        bd.query(Estudiante)
        .join(PertenenciaGrupo, PertenenciaGrupo.estudiante_id == Estudiante.id)
        .filter(
            PertenenciaGrupo.grupo_id == grupo_id,
            PertenenciaGrupo.workflow_state == "accepted",
            PertenenciaGrupo.activa_hasta.is_(None),
        )
        .order_by(Estudiante.nombre_ordenable)
        .all()
    )


# --- Acciones de la bandeja (S11.10) ---


def reintentar(bd: Session, mensaje: MensajeSaliente) -> None:
    """Solo FALLIDO o CADUCADO; la misma fila y la misma clave."""
    if mensaje.estado not in (EstadoMensaje.FALLIDO.value, EstadoMensaje.CADUCADO.value):
        raise AccionNoPermitida("Solo se reintenta un mensaje que no se pudo enviar o que caducó.")
    mensaje.estado = EstadoMensaje.PENDIENTE.value
    mensaje.motivo_estado = None
    mensaje.caduca_en = None
    mensaje.programado_para = None
    mensaje.intentos = 0
    bd.flush()


def reenviar(bd: Session, mensaje: MensajeSaliente, *, actor_id: uuid.UUID) -> MensajeSaliente:
    """Solo ENVIADO: fila nueva con `generacion + 1`, hasta tres reenvios."""
    if mensaje.estado != EstadoMensaje.ENVIADO.value:
        raise AccionNoPermitida("Solo se reenvía un mensaje ya enviado.")
    if mensaje.canal == CanalMensaje.CANVAS_ANUNCIO.value or mensaje.estudiante_id is None:
        raise AccionNoPermitida("Un anuncio no se reenvía: publica una corrección.")
    raiz = mensaje
    while raiz.reemplaza_a_id is not None:
        anterior = bd.get(MensajeSaliente, raiz.reemplaza_a_id)
        if anterior is None:
            break
        raiz = anterior
    reenvios = bd.query(MensajeSaliente).filter(MensajeSaliente.reemplaza_a_id == raiz.id).count()
    if reenvios >= MAX_REENVIOS:
        raise AccionNoPermitida("Este mensaje ya se reenvió tres veces.")
    estudiante = bd.get(Estudiante, mensaje.estudiante_id)
    curso = bd.get(Curso, mensaje.curso_id)
    assert estudiante is not None and curso is not None
    nuevo = reemitir(
        bd,
        mensaje,
        curso=curso,
        estudiante=estudiante,
        origen=OrigenMensaje.MANUAL,
        disparado_por=actor_id,
    )
    if nuevo is None:
        raise AccionNoPermitida("Ya existe un reenvío de este mensaje.")
    return nuevo


def cancelar(bd: Session, mensaje: MensajeSaliente) -> None:
    if mensaje.estado not in _NO_TERMINALES:
        raise AccionNoPermitida("Solo se cancela un mensaje que todavía no sale.")
    mensaje.estado, mensaje.motivo_estado = EstadoMensaje.CANCELADO.value, "ACCION_DOCENTE"
    bd.flush()


def solicitar_retractacion(bd: Session, mensaje: MensajeSaliente, *, actor_id: uuid.UUID) -> None:
    if (
        mensaje.canal != CanalMensaje.CANVAS_ANUNCIO.value
        or mensaje.estado != EstadoMensaje.ENVIADO.value
    ):
        raise AccionNoPermitida(
            "Solo se retira un anuncio publicado; mensajes y comentarios no se pueden retirar."
        )
    mensaje.retraccion_solicitada = True
    mensaje.retractado_por = actor_id
    bd.flush()


# --- Suspension del curso y supresion por estudiante (A-225, S11.2.6) ---


def cambiar_suspension(
    bd: Session, curso: Curso, *, suspendidas: bool, motivo: str | None, actor_id: uuid.UUID
) -> None:
    if curso.modo_escritura == "SOLO_LECTURA" and not suspendidas:
        raise AccionNoPermitida("Un curso en solo lectura mantiene las comunicaciones suspendidas.")
    antes = curso.comunicaciones_salientes
    curso.comunicaciones_salientes = "SUSPENDIDAS" if suspendidas else "ACTIVAS"
    curso.suspension_motivo = motivo if suspendidas else None
    curso.suspension_desde = ahora_utc() if suspendidas else None
    curso.suspension_por = actor_id if suspendidas else None
    bd.flush()
    bitacora_repo.registrar(
        bd,
        accion="COMUNICACIONES_SUSPENDIDAS" if suspendidas else "COMUNICACIONES_REANUDADAS",
        entidad="curso",
        entidad_id=str(curso.id),
        actor_usuario_id=actor_id,
        curso_id=curso.id,
        antes={"comunicaciones_salientes": antes},
        despues={"comunicaciones_salientes": curso.comunicaciones_salientes, "motivo": motivo},
    )


def crear_supresion(
    bd: Session,
    *,
    curso_id: uuid.UUID,
    estudiante_id: uuid.UUID,
    alcance: str,
    motivo: str,
    actor_id: uuid.UUID,
) -> SupresionComunicacion:
    vigente = (
        bd.query(SupresionComunicacion)
        .filter(
            SupresionComunicacion.curso_id == curso_id,
            SupresionComunicacion.estudiante_id == estudiante_id,
            SupresionComunicacion.levantada_en.is_(None),
        )
        .one_or_none()
    )
    if vigente is not None:
        raise AccionNoPermitida("Ese estudiante ya tiene una supresión vigente.")
    fila = SupresionComunicacion(
        curso_id=curso_id,
        estudiante_id=estudiante_id,
        alcance=alcance,
        motivo=motivo,
        creada_por=actor_id,
        creada_en=ahora_utc(),
    )
    bd.add(fila)
    bd.flush()
    return fila


def levantar_supresion(
    bd: Session, *, curso_id: uuid.UUID, estudiante_id: uuid.UUID, actor_id: uuid.UUID
) -> None:
    fila = (
        bd.query(SupresionComunicacion)
        .filter(
            SupresionComunicacion.curso_id == curso_id,
            SupresionComunicacion.estudiante_id == estudiante_id,
            SupresionComunicacion.levantada_en.is_(None),
        )
        .one_or_none()
    )
    if fila is None:
        raise AccionNoPermitida("Ese estudiante no tiene una supresión vigente.")
    fila.levantada_en = ahora_utc()
    fila.levantada_por = actor_id
    bd.flush()


# --- Purga (trabajo `purga_retencion`, 03:00) ---


def purgar(bd: Session, *, ahora: datetime | None = None) -> int:
    """Lo DIFERIDO por las guardas 5, 6 o 7 por mas de siete dias caduca. Nunca
    borra nada de `mensaje_saliente` (A-090)."""
    ahora = ahora or ahora_utc()
    n = 0
    for m in bd.query(MensajeSaliente).filter(
        MensajeSaliente.estado == EstadoMensaje.DIFERIDO.value,
        MensajeSaliente.motivo_estado.in_(
            ("MODO_SOLO_LECTURA", "SUSPENSION_DE_CURSO", "VENTANA_TRAS_RESTAURACION")
        ),
        MensajeSaliente.creado_en < ahora - timedelta(days=DIAS_SUSPENSION_MAXIMA),
    ):
        m.estado, m.motivo_estado = EstadoMensaje.CADUCADO.value, "SUSPENSION_PROLONGADA"
        n += 1
    bd.flush()
    return n
