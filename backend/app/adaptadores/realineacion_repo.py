"""Revisión del criterio original; jamás reasigna al sincronizar el padrón."""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.adaptadores import bitacora_repo, correccion_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_aprovisionamiento import Sujeto
from app.adaptadores.modelos_correccion import AsignacionCorreccion, Correccion
from app.adaptadores.modelos_tarea import Entrega
from app.dominio.correccion import TERMINALES, Corrector, SujetoReparto, reparto_equitativo
from app.dominio.estados import CriterioAsignacion


def guardar_contexto(
    bd: Session,
    a: AsignacionCorreccion,
    sujeto: Sujeto,
    *,
    criterio: CriterioAsignacion,
    por_seccion: dict[str, str],
) -> None:
    secciones = correccion_repo.secciones_de_sujeto(bd, sujeto)
    a.criterio = criterio.value
    a.criterio_seccion_id = (
        secciones[0] if criterio == CriterioAsignacion.SECCION and len(secciones) == 1 else None
    )
    a.criterio_contexto = {
        "secciones": [str(s) for s in secciones],
        "integrantes": [str(e.id) for e in correccion_repo.integrantes(bd, sujeto)],
        "por_seccion": por_seccion,
    }
    a.desalineada_motivo = None
    a.desalineada_en = None


def revisar(bd: Session, entrega: Entrega) -> int:
    bd.flush()
    cambios = 0
    for a, sujeto in (
        bd.query(AsignacionCorreccion, Sujeto)
        .join(Sujeto, Sujeto.id == AsignacionCorreccion.sujeto_id)
        .filter(AsignacionCorreccion.entrega_id == entrega.id)
    ):
        if a.criterio == "MANUAL" or not a.criterio_contexto or a.membresia_id is None:
            continue
        contexto = a.criterio_contexto
        motivo = None
        if sujeto.grupo_id and contexto["integrantes"] != [
            str(e.id) for e in correccion_repo.integrantes(bd, sujeto)
        ]:
            motivo = "CAMBIO_DE_GRUPO"
        if a.criterio == "SECCION" and contexto["secciones"] != [
            str(s) for s in correccion_repo.secciones_de_sujeto(bd, sujeto)
        ]:
            motivo = "CAMBIO_DE_SECCION"
        if a.desalineada_motivo != motivo:
            antes = a.desalineada_motivo
            a.desalineada_motivo = motivo
            a.desalineada_en = ahora_utc() if motivo else None
            bitacora_repo.registrar(
                bd,
                accion="REPARTO_DESALINEACION",
                entidad="asignacion_correccion",
                entidad_id=str(a.id),
                curso_id=entrega.curso_id,
                antes={"motivo": antes},
                despues={"motivo": motivo},
            )
            cambios += 1
    bd.flush()
    return cambios


def previsualizar(bd: Session, entrega: Entrega) -> correccion_repo.Propuesta:
    filas = (
        bd.query(AsignacionCorreccion, Correccion, Sujeto)
        .join(
            Correccion,
            (Correccion.entrega_id == AsignacionCorreccion.entrega_id)
            & (Correccion.sujeto_id == AsignacionCorreccion.sujeto_id),
        )
        .join(Sujeto, Sujeto.id == AsignacionCorreccion.sujeto_id)
        .filter(AsignacionCorreccion.entrega_id == entrega.id)
        .all()
    )
    objetivos = {
        s.id
        for a, c, s in filas
        if a.desalineada_motivo
        and a.criterio != "MANUAL"
        and c.estado not in TERMINALES
        and c.estado != "PUBLICANDO"
    }
    miembros = correccion_repo.correctores(bd, entrega.curso_id)
    elegibles = {m.id for m, _ in miembros}
    equitativos = {s.id for a, _, s in filas if s.id in objetivos and a.criterio == "EQUITATIVO"}
    sujetos = [
        SujetoReparto(
            s.id,
            correccion_repo.nombre_de_sujeto(bd, s)[1],
            (),
            None if s.id in equitativos else a.membresia_id,
            False,
            c.publicable,
        )
        for a, c, s in filas
        if s.id in equitativos or a.membresia_id is not None
    ]
    asignados = (
        reparto_equitativo(
            sujetos, [Corrector(m.id, u.nombre, correccion_repo.peso_de(m)) for m, u in miembros]
        )
        if equitativos
        else {}
    )
    propuesta = correccion_repo.Propuesta()
    anteriores = correccion_repo.previsualizar(
        bd, entrega, criterio=CriterioAsignacion.COPIA_ENTREGA_ANTERIOR, reasignar=True
    )
    copia = {f.sujeto_id: f.propuesto for f in anteriores.filas}
    for a, c, sujeto in filas:
        if sujeto.id not in objetivos:
            continue
        propuesto = a.membresia_id
        if a.criterio == "SECCION":
            secciones = correccion_repo.secciones_de_sujeto(bd, sujeto)
            mapa: dict[str, Any] = (a.criterio_contexto or {}).get("por_seccion", {})
            if len(secciones) != 1 or str(secciones[0]) not in mapa:
                propuesta.requiere_decision.append(sujeto.id)
                continue
            propuesto = uuid.UUID(mapa[str(secciones[0])])
        elif a.criterio == "EQUITATIVO":
            propuesto = asignados.get(sujeto.id)
        elif a.criterio == "COPIA_ENTREGA_ANTERIOR":
            propuesto = copia.get(sujeto.id)
        if propuesto not in elegibles:
            propuesta.requiere_decision.append(sujeto.id)
            continue
        propuesta.filas.append(
            correccion_repo.FilaPropuesta(
                sujeto.id,
                correccion_repo.nombre_de_sujeto(bd, sujeto)[0],
                a.membresia_id,
                propuesto,
                c.estado,
                a.membresia_id != propuesto,
            )
        )
        clave = str(propuesto)
        propuesta.totales[clave] = propuesta.totales.get(clave, 0) + 1
    return propuesta
