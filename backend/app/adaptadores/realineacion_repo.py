"""Realinea solo asignaciones marcadas, conservando borradores y criterio original."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.adaptadores import bitacora_repo, correccion_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_aprovisionamiento import Sujeto
from app.adaptadores.modelos_correccion import AsignacionCorreccion, Correccion
from app.adaptadores.modelos_curso import MembresiaCurso
from app.adaptadores.modelos_infraestructura import Bitacora
from app.adaptadores.modelos_tarea import Entrega
from app.dominio.estados import CriterioAsignacion
from app.infraestructura.cerrojos import cerrojo_reparto


def configuracion(bd: Session, asignacion: AsignacionCorreccion) -> dict[str, Any]:
    registro = (
        bd.query(Bitacora)
        .filter(
            Bitacora.entidad == "asignacion_correccion",
            Bitacora.entidad_id == str(asignacion.id),
            Bitacora.accion.in_(["CORRECCION_ASIGNADA", "CORRECCION_REALINEADA"]),
        )
        .order_by(Bitacora.creado_en.desc(), Bitacora.id.desc())
        .first()
    )
    return dict(registro.despues or {}) if registro else {}


def premisa(
    bd: Session, sujeto: Sujeto, por_seccion: dict[uuid.UUID, uuid.UUID] | None
) -> dict[str, Any]:
    return {
        "secciones": [str(s) for s in correccion_repo.secciones_de_sujeto(bd, sujeto)],
        "integrantes": sorted(str(e.id) for e in correccion_repo.integrantes(bd, sujeto)),
        "por_seccion": {str(s): str(m) for s, m in (por_seccion or {}).items()},
    }


def detectar(bd: Session, entrega: Entrega) -> None:
    for a, sujeto in (
        bd.query(AsignacionCorreccion, Sujeto)
        .join(Sujeto, Sujeto.id == AsignacionCorreccion.sujeto_id)
        .filter(
            AsignacionCorreccion.entrega_id == entrega.id, AsignacionCorreccion.criterio != "MANUAL"
        )
    ):
        guardado = configuracion(bd, a)
        actuales = premisa(bd, sujeto, None)
        motivo = None
        if (
            a.criterio == "SECCION"
            and guardado.get("secciones") is not None
            and sorted(guardado["secciones"]) != sorted(actuales["secciones"])
        ):
            motivo = "CAMBIO_DE_SECCION"
        if (
            sujeto.grupo_id
            and guardado.get("integrantes") is not None
            and guardado["integrantes"] != actuales["integrantes"]
        ):
            motivo = "CAMBIO_DE_GRUPO"
        if motivo and a.desalineada_motivo is None:
            a.desalineada_motivo = motivo
            a.desalineada_en = ahora_utc()


def previsualizar(
    bd: Session, entrega: Entrega, por_seccion: dict[uuid.UUID, uuid.UUID] | None = None
) -> correccion_repo.Propuesta:
    correccion_repo.asegurar_filas(bd, entrega)
    activos = {m.id for m, _ in correccion_repo.correctores(bd, entrega.curso_id)}
    propuesta = correccion_repo.Propuesta()
    for a, c, sujeto in (
        bd.query(AsignacionCorreccion, Correccion, Sujeto)
        .join(
            Correccion,
            (Correccion.entrega_id == AsignacionCorreccion.entrega_id)
            & (Correccion.sujeto_id == AsignacionCorreccion.sujeto_id),
        )
        .join(Sujeto, Sujeto.id == AsignacionCorreccion.sujeto_id)
        .filter(
            AsignacionCorreccion.entrega_id == entrega.id,
            AsignacionCorreccion.desalineada_motivo.is_not(None),
        )
    ):
        if c.estado in ("PUBLICANDO", "PUBLICADA", "PUBLICADA_CON_ADVERTENCIA"):
            continue
        propuesto = a.membresia_id
        guardado = configuracion(bd, a)
        if a.criterio == "SECCION":
            reglas = por_seccion or {
                uuid.UUID(k): uuid.UUID(v) for k, v in guardado.get("por_seccion", {}).items()
            }
            secciones = correccion_repo.secciones_de_sujeto(bd, sujeto)
            if len(secciones) == 1 and reglas.get(secciones[0]) in activos:
                propuesto = reglas[secciones[0]]
            else:
                propuesta.requiere_decision.append(sujeto.id)
        elif a.criterio == "COPIA_ENTREGA_ANTERIOR":
            anterior = correccion_repo._entrega_anterior(bd, entrega)
            previa = (
                bd.query(AsignacionCorreccion)
                .filter(
                    AsignacionCorreccion.entrega_id == anterior.id,
                    AsignacionCorreccion.sujeto_id == sujeto.id,
                )
                .first()
                if anterior
                else None
            )
            if previa and previa.membresia_id in activos:
                propuesto = previa.membresia_id
            else:
                propuesta.requiere_decision.append(sujeto.id)
        elif a.criterio != "EQUITATIVO":
            propuesta.requiere_decision.append(sujeto.id)
        nombre, _ = correccion_repo.nombre_de_sujeto(bd, sujeto)
        propuesta.filas.append(
            correccion_repo.FilaPropuesta(
                sujeto.id, nombre, a.membresia_id, propuesto, c.estado, propuesto != a.membresia_id
            )
        )
        clave = str(propuesto) if propuesto else "sin corrector"
        propuesta.totales[clave] = propuesta.totales.get(clave, 0) + 1
    propuesta.filas.sort(key=lambda f: (f.sujeto.lower(), str(f.sujeto_id)))
    return propuesta


def aplicar(
    bd: Session,
    entrega: Entrega,
    actor: MembresiaCurso,
    por_seccion: dict[uuid.UUID, uuid.UUID] | None = None,
) -> int:
    cerrojo_reparto(bd, entrega.id)
    propuesta = previsualizar(bd, entrega, por_seccion)
    cambios = 0
    for fila in propuesta.filas:
        if fila.sujeto_id in propuesta.requiere_decision:
            continue
        c, a = correccion_repo.fila(bd, entrega.id, fila.sujeto_id)
        guardado = configuracion(bd, a)
        reglas = por_seccion or {
            uuid.UUID(k): uuid.UUID(v) for k, v in guardado.get("por_seccion", {}).items()
        }
        criterio = a.criterio
        if fila.propuesto != fila.actual:
            correccion_repo.aplicar(
                bd,
                entrega,
                criterio=CriterioAsignacion.MANUAL,
                actor=actor,
                reasignar=True,
                manual={fila.sujeto_id: fila.propuesto},
            )
        a.criterio = criterio
        a.desalineada_motivo = None
        a.desalineada_en = None
        sujeto = bd.get(Sujeto, fila.sujeto_id)
        assert sujeto is not None
        secciones = correccion_repo.secciones_de_sujeto(bd, sujeto)
        a.criterio_seccion_id = (
            secciones[0] if criterio == "SECCION" and len(secciones) == 1 else None
        )
        bitacora_repo.registrar(
            bd,
            accion="CORRECCION_REALINEADA",
            entidad="asignacion_correccion",
            entidad_id=str(a.id),
            actor_usuario_id=actor.usuario_id,
            curso_id=entrega.curso_id,
            antes={"membresia_id": str(fila.actual) if fila.actual else None},
            despues={
                "membresia_id": str(fila.propuesto) if fila.propuesto else None,
                "criterio": criterio,
                **premisa(bd, sujeto, reglas),
            },
        )
        cambios += 1
    bd.flush()
    return cambios
