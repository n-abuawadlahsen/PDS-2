"""Aviso manual al profesorado por el outbox, con cuota e idempotencia."""

import html
import uuid
from datetime import datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.adaptadores import bitacora_repo, programacion_repo
from app.adaptadores.correccion_repo import RechazoCorreccion
from app.adaptadores.modelos_aprovisionamiento import MensajeSaliente
from app.adaptadores.modelos_correccion import Correccion
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_identidad import Usuario
from app.adaptadores.modelos_tarea import Entrega
from app.adaptadores.proveedor_correo import FalloCorreo, crear_proveedor_correo, motivo_bloqueo
from app.infraestructura.cerrojos import bloquear_cuota_correo
from app.infraestructura.config import obtener_configuracion

EVENTO = "aviso_sin_corrector"


def cantidad(bd: Session, curso_id: uuid.UUID) -> int:
    return (
        bd.query(Correccion.id)
        .join(Entrega, Entrega.id == Correccion.entrega_id)
        .filter(Entrega.curso_id == curso_id, Correccion.estado == "SIN_CORRECTOR")
        .count()
    )


def encolar(bd: Session, curso: Curso, actor: MembresiaCurso, *, ahora: datetime) -> int:
    # Fila del curso: dos clics simultáneos no generan dos tandas.
    bd.query(Curso).filter_by(id=curso.id).with_for_update().one()
    total = cantidad(bd, curso.id)
    if not total:
        raise RechazoCorreccion("Ya no hay entregas sin corrector.")
    anterior = (
        bd.query(MensajeSaliente)
        .filter_by(curso_id=curso.id, evento=EVENTO)
        .order_by(MensajeSaliente.creado_en.desc())
        .first()
    )
    if anterior and ahora - anterior.creado_en < timedelta(hours=24):
        raise RechazoCorreccion("Ya se solicitó un aviso en las últimas 24 horas.", codigo=429)
    profesores = (
        bd.query(MembresiaCurso, Usuario)
        .join(Usuario, Usuario.id == MembresiaCurso.usuario_id)
        .filter(
            MembresiaCurso.curso_id == curso.id,
            MembresiaCurso.rol == "PROFESOR",
            MembresiaCurso.estado == "ACTIVA",
            Usuario.activo.is_(True),
        )
        .all()
    )
    for m, u in profesores:
        bd.add(
            MensajeSaliente(
                curso_id=curso.id,
                membresia_id=m.id,
                canal="CORREO",
                evento=EVENTO,
                reserva="MARGEN",
                clave_idempotencia=f"{EVENTO}:{curso.id}:{m.id}:{uuid.uuid4()}",
                generacion=1,
                referencia={
                    "actor_membresia_id": str(actor.id),
                    "cantidad": total,
                    "reserva": "MARGEN",
                },
                destinatario=u.email,
                plantilla=EVENTO,
                plantilla_version=1,
                origen="MANUAL",
                caduca_en=ahora + timedelta(days=1),
                estado="PENDIENTE",
                intentos=0,
                creado_en=ahora,
            )
        )
    programacion_repo.asegurar_periodicos_globales(bd)
    bitacora_repo.registrar(
        bd,
        accion="AVISO_SIN_CORRECTOR_SOLICITADO",
        entidad="curso",
        entidad_id=str(curso.id),
        curso_id=curso.id,
        actor_usuario_id=actor.usuario_id,
        despues={"destinatarios": len(profesores), "sin_corrector": total},
    )
    return len(profesores)


def despachar(bd: Session, mensaje: MensajeSaliente, *, ahora: datetime) -> None:
    curso = bd.get(Curso, mensaje.curso_id)
    destinatario = bd.get(MembresiaCurso, mensaje.membresia_id)
    actor = bd.get(MembresiaCurso, uuid.UUID(mensaje.referencia["actor_membresia_id"]))
    total = cantidad(bd, mensaje.curso_id)
    if (
        not curso
        or not destinatario
        or destinatario.estado != "ACTIVA"
        or destinatario.rol != "PROFESOR"
        or not actor
        or actor.estado != "ACTIVA"
        or not total
    ):
        mensaje.estado = "CANCELADO"
        mensaje.motivo_estado = "AVISO_YA_NO_APLICA"
        return
    if mensaje.caduca_en and mensaje.caduca_en <= ahora:
        mensaje.estado = "CADUCADO"
        return
    settings = obtener_configuracion()
    bloqueo = motivo_bloqueo(settings, mensaje.destinatario)
    if bloqueo:
        mensaje.estado = "BLOQUEADO"
        mensaje.motivo_estado = bloqueo
        mensaje.programado_para = ahora + timedelta(minutes=30)
        return
    bloquear_cuota_correo(bd)
    dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    fecha = dia.date().isoformat()
    usados = bd.query(MensajeSaliente).filter(
        MensajeSaliente.canal == "CORREO",
        or_(
            MensajeSaliente.enviado_en >= dia,
            MensajeSaliente.referencia["cuota_fecha"].astext == fecha,
        ),
    )
    margen = usados.filter(
        or_(
            MensajeSaliente.evento.in_((EVENTO, "invitacion_equipo")),
            MensajeSaliente.reserva == "MARGEN",
        )
    ).count()
    if mensaje.referencia.get("cuota_fecha") != fecha and (usados.count() >= 100 or margen >= 10):
        mensaje.estado = "DIFERIDO"
        mensaje.motivo_estado = "CUOTA_AGOTADA"
        mensaje.programado_para = dia + timedelta(days=1)
        return
    primer_intento = mensaje.referencia.get("primer_intento_en")
    if primer_intento and ahora - datetime.fromisoformat(primer_intento) >= timedelta(hours=23):
        mensaje.estado = "REQUIERE_ATENCION"
        mensaje.motivo_estado = "ENVIO_INCIERTO"
        return
    mensaje.referencia = {
        **mensaje.referencia,
        "cuota_fecha": fecha,
        "primer_intento_en": primer_intento or ahora.isoformat(),
    }
    asunto = f"Correcciones sin corrector: {curso.nombre}"
    url = f"{settings.frontend_origen.rstrip('/')}/cursos/{curso.id}/correccion"
    texto = f"Hay {total} entregas sin corrector en {curso.nombre}. Revisa el reparto: {url}"
    mensaje.intentos += 1
    try:
        resultado = crear_proveedor_correo(settings).enviar(
            destinatario=mensaje.destinatario,
            asunto=asunto,
            html=f"<p>{html.escape(texto)}</p>",
            texto=texto,
            clave_idempotencia=mensaje.clave_idempotencia,
            reserva="MARGEN",
        )
    except FalloCorreo as exc:
        mensaje.ultimo_error_literal = str(exc)
        mensaje.estado = (
            "REINTENTAR" if exc.reintentable and mensaje.intentos < 6 else "REQUIERE_ATENCION"
        )
        mensaje.programado_para = ahora + timedelta(minutes=5)
        return
    mensaje.estado = "SUPRIMIDO" if resultado.simulado else "ENVIADO"
    mensaje.motivo_estado = "SIMULADO_LOCAL" if resultado.simulado else None
    mensaje.enviado_en = None if resultado.simulado else ahora
    mensaje.canal_efectivo = "CORREO"
    mensaje.asunto = asunto
    mensaje.cuerpo_renderizado = texto
    mensaje.canvas_id_resultante = {"proveedor_id": resultado.id, "simulado": resultado.simulado}
    mensaje.ultimo_error_literal = None
    bd.flush()
