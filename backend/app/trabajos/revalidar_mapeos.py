"""Trabajo `revalidar_mapeos` (SPEC 07 S7.6.2). Diario 04:00, global (no de
un curso). Revalida cuentas de GitHub, nunca contra Canvas.

`RENOMBRADO` se autoresuelve (se actualiza `cuenta_github.login`, nada mas).
`CUENTA_ELIMINADA` y `LOGIN_REASIGNADO` invalidan y abren incidencia; nunca
se resuelven solos. Los `INVALIDADO` por `ESTUDIANTE_RETIRADO` cuyo
estudiante volvio a estar activo se re-procesan por el mismo circuito de
validacion que un candidato nuevo (S7.6.1: `INVALIDADO -> RECIBIDO`, no
directo a `VIGENTE`), usando el login ya guardado -- sin pedirselo de nuevo.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.adaptadores import incidencia_repo, mapeo_github_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_github import crear_cliente_github_desde_config
from app.adaptadores.modelos_infraestructura import Trabajo
from app.adaptadores.modelos_mapeo import CuentaGithub, MapeoGithub
from app.adaptadores.modelos_padron import Estudiante
from app.dominio.estados import EstadoEstudiante, EstadoMapeoGithub, MotivoInvalidacionMapeo
from app.infraestructura.config import obtener_configuracion
from app.trabajos.registro import registrar


@registrar("revalidar_mapeos")
def ejecutar(sesion: Session, _trabajo: Trabajo) -> None:
    settings = obtener_configuracion()
    cliente_github = crear_cliente_github_desde_config(settings)

    cuentas_vigentes = (
        sesion.query(CuentaGithub)
        .join(MapeoGithub, MapeoGithub.cuenta_github_id == CuentaGithub.id)
        .filter(MapeoGithub.estado == EstadoMapeoGithub.VIGENTE.value)
        .distinct()
        .all()
    )
    for cuenta in cuentas_vigentes:
        info = cliente_github.obtener_cuenta_usuario(cuenta.login)
        mapeos_de_la_cuenta = (
            sesion.query(MapeoGithub)
            .filter(
                MapeoGithub.cuenta_github_id == cuenta.id,
                MapeoGithub.estado == EstadoMapeoGithub.VIGENTE.value,
            )
            .all()
        )
        if info is None:
            for mapeo in mapeos_de_la_cuenta:
                mapeo_github_repo.invalidar_mapeo_vigente(
                    sesion,
                    curso_id=mapeo.curso_id,
                    estudiante_id=mapeo.estudiante_id,
                    motivo=MotivoInvalidacionMapeo.CUENTA_ELIMINADA,
                )
                incidencia_repo.abrir_o_actualizar(
                    sesion,
                    tipo="MAPEO_INVALIDADO",
                    severidad="ADVERTENCIA",
                    sujeto_tipo="ESTUDIANTE",
                    sujeto_id=mapeo.estudiante_id,
                    curso_id=mapeo.curso_id,
                    detalle={
                        "motivo": MotivoInvalidacionMapeo.CUENTA_ELIMINADA.value,
                        "login": cuenta.login,
                    },
                )
            continue

        if info.github_user_id != cuenta.github_user_id:
            # El login guardado ahora resuelve a OTRA cuenta: alguien lo reclamo.
            for mapeo in mapeos_de_la_cuenta:
                mapeo_github_repo.invalidar_mapeo_vigente(
                    sesion,
                    curso_id=mapeo.curso_id,
                    estudiante_id=mapeo.estudiante_id,
                    motivo=MotivoInvalidacionMapeo.LOGIN_REASIGNADO,
                )
                incidencia_repo.abrir_o_actualizar(
                    sesion,
                    tipo="MAPEO_INVALIDADO",
                    severidad="ADVERTENCIA",
                    sujeto_tipo="ESTUDIANTE",
                    sujeto_id=mapeo.estudiante_id,
                    curso_id=mapeo.curso_id,
                    detalle={
                        "motivo": MotivoInvalidacionMapeo.LOGIN_REASIGNADO.value,
                        "login": cuenta.login,
                    },
                )
            continue

        if info.login != cuenta.login:
            cuenta.login = info.login  # RENOMBRADO: se actualiza sola, sin incidencia (S7.6.2)
        cuenta.revalidado_en = ahora_utc()
        for mapeo in mapeos_de_la_cuenta:
            mapeo.revalidado_en = ahora_utc()
    sesion.flush()

    invalidados_por_retiro = (
        sesion.query(MapeoGithub)
        .join(Estudiante, Estudiante.id == MapeoGithub.estudiante_id)
        .filter(
            MapeoGithub.estado == EstadoMapeoGithub.INVALIDADO.value,
            MapeoGithub.motivo_invalidacion == MotivoInvalidacionMapeo.ESTUDIANTE_RETIRADO.value,
            Estudiante.estado.in_([EstadoEstudiante.ACTIVO.value, EstadoEstudiante.INVITADO.value]),
        )
        .all()
    )
    for mapeo in invalidados_por_retiro:
        estudiante = sesion.query(Estudiante).filter(Estudiante.id == mapeo.estudiante_id).one()
        cuenta_a_reintentar = (
            sesion.query(CuentaGithub)
            .filter(CuentaGithub.id == mapeo.cuenta_github_id)
            .one_or_none()
        )
        if cuenta_a_reintentar is None:
            continue
        mapeo_github_repo.procesar_candidato(
            sesion,
            cliente_github,
            curso_id=mapeo.curso_id,
            estudiante=estudiante,
            login=cuenta_a_reintentar.login,
            texto_crudo=mapeo.evidencia.get("texto_crudo"),
            origen=mapeo.origen or "AUTOSERVICIO_CANVAS",
            es_puerta_docente=False,
        )
