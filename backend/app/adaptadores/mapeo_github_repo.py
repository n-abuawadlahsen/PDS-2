"""Orquesta el mapeo estudiante <-> GitHub: las cuatro vias de SPEC 07 S7.4,
la elegibilidad de S7.5, y la maquina de nueve estados de S7.6.

`_escribir_mapeo` es el unico punto que toca `mapeo_github`: decide si la fila
`SIN_DATO` se completa in situ (todavia no hay nada que preservar) o si hay
que superseder y crear una fila nueva (Ley 2, ya hay un valor declarado que
no se pierde). El SPEC no dice literalmente cual de las dos aplica a la
transicion SIN_DATO -> RECIBIDO; esta es la lectura mas consistente con
CA-7.2-06 ("exactamente una fila... en la misma transaccion") y con "append
only" leido como "nunca se pierde un valor ya declarado" (S7.2.2): SIN_DATO
no tiene valor que perder.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_github import ClienteGitHub
from app.adaptadores.modelos_curso import MembresiaCurso
from app.adaptadores.modelos_identidad import Usuario
from app.adaptadores.modelos_mapeo import CuentaGithub, MapeoGithub
from app.adaptadores.modelos_padron import Estudiante
from app.dominio.estados import (
    EstadoCuentaGithub,
    EstadoMapeoGithub,
    EstadoMembresia,
    MotivoInvalidacionMapeo,
)
from app.dominio.mapeo_github import (
    ContextoElegibilidad,
    MotivoRechazoMapeo,
    RechazoMapeo,
    es_cuenta_elegible,
    extraer_candidato,
    resultado_recibido,
)
from app.dominio.vinculacion_github import CuentaUsuarioInfo, es_cuenta_de_organizacion
from app.infraestructura.cerrojos import bloquear_equipo


def crear_mapeo_sin_dato(
    bd: Session, *, curso_id: uuid.UUID, estudiante_id: uuid.UUID
) -> MapeoGithub:
    """S7.2.6 criterio 3: se llama desde `padron_repo` en la MISMA transaccion
    en que se espeja un estudiante nuevo, nunca cuando llega el primer
    candidato."""
    fila = MapeoGithub(
        curso_id=curso_id,
        estudiante_id=estudiante_id,
        estado=EstadoMapeoGithub.SIN_DATO.value,
        evidencia={},
        creado_en=ahora_utc(),
    )
    bd.add(fila)
    bd.flush()
    return fila


def _mapeo_vivo(bd: Session, *, curso_id: uuid.UUID, estudiante_id: uuid.UUID) -> MapeoGithub:
    fila = (
        bd.query(MapeoGithub)
        .filter(
            MapeoGithub.curso_id == curso_id,
            MapeoGithub.estudiante_id == estudiante_id,
            MapeoGithub.estado != EstadoMapeoGithub.SUPERSEDIDO.value,
        )
        .one_or_none()
    )
    if fila is None:
        # Defensivo: un estudiante espejado antes de existir esta tabla no
        # tendria fila. No deberia ocurrir en un curso nuevo de aqui en mas.
        fila = crear_mapeo_sin_dato(bd, curso_id=curso_id, estudiante_id=estudiante_id)
    return fila


def _upsert_cuenta_github(bd: Session, cuenta: CuentaUsuarioInfo) -> CuentaGithub:
    """S7.6.2 `RENOMBRADO`: si el login cambio pero el id numerico es el
    mismo, se actualiza sola, sin abrir incidencia ni tocar `mapeo_github`."""
    fila = (
        bd.query(CuentaGithub)
        .filter(CuentaGithub.github_user_id == cuenta.github_user_id)
        .one_or_none()
    )
    ahora = ahora_utc()
    if fila is None:
        fila = CuentaGithub(
            github_user_id=cuenta.github_user_id,
            login=cuenta.login,
            estado=EstadoCuentaGithub.VALIDA.value,
            revalidado_en=ahora,
        )
        bd.add(fila)
        bd.flush()
    else:
        fila.login = cuenta.login
        fila.estado = EstadoCuentaGithub.VALIDA.value
        fila.revalidado_en = ahora
    return fila


def construir_contexto_elegibilidad(
    bd: Session, *, cuenta: CuentaUsuarioInfo, curso_id: uuid.UUID, estudiante_id: uuid.UUID
) -> ContextoElegibilidad:
    """S7.5.1-S7.5.2. Simplificaciones documentadas (no infraestructura
    todavia para comprobarlas): `es_owner_de_la_organizacion` y
    `es_cuenta_bot_de_la_app` quedan siempre en `False` -- no hay forma de
    listar owners por login ni una cuenta bot propia registrada hoy.
    `es_miembro_equipo_lectura_github` se funde con `es_del_equipo_docente_activo`
    porque no existe un padron propio de quien esta en el equipo `docentes`
    de GitHub (solo se persiste `team_id`/`team_slug`, no sus miembros);
    en la practica son la misma poblacion.

    `tiene_mapeo_vigente_en_otro_lado` excluye deliberadamente el curso
    actual: la ampliacion de RG-199/A-187 ("ambito de toda la aplicacion")
    agrega la comprobacion entre cursos DISTINTOS, no reemplaza la deteccion
    de conflicto DENTRO del mismo curso (S7.6.3), que tiene su propio
    mecanismo -- `EN_CONFLICTO`, resoluble por el docente -- y que dejaria de
    ser alcanzable si esta funcion ya rechazara el mismo caso como no
    elegible."""
    login_lower = cuenta.login.lower()

    es_docente_activo = (
        bd.query(MembresiaCurso)
        .join(Usuario, Usuario.id == MembresiaCurso.usuario_id)
        .filter(
            MembresiaCurso.estado == EstadoMembresia.ACTIVA.value,
            Usuario.github_login_declarado.is_not(None),
        )
        .filter(
            or_(
                Usuario.cuenta_github_id == cuenta.github_user_id,
                Usuario.github_login_declarado.ilike(cuenta.login),
            )
        )
        .first()
        is not None
    )

    tiene_mapeo_vigente_en_otro_lado = (
        bd.query(MapeoGithub)
        .join(CuentaGithub, CuentaGithub.id == MapeoGithub.cuenta_github_id)
        .filter(
            CuentaGithub.github_user_id == cuenta.github_user_id,
            MapeoGithub.estado == EstadoMapeoGithub.VIGENTE.value,
            MapeoGithub.estudiante_id != estudiante_id,
            MapeoGithub.curso_id != curso_id,
        )
        .first()
        is not None
    )

    _ = login_lower  # ilike ya es case-insensitive; se deja documentado el criterio
    return ContextoElegibilidad(
        es_del_equipo_docente_activo=es_docente_activo,
        es_miembro_equipo_lectura_github=False,
        es_owner_de_la_organizacion=False,
        es_cuenta_bot_de_la_app=False,
        tiene_mapeo_vigente_en_otro_lado=tiene_mapeo_vigente_en_otro_lado,
    )


def _escribir_mapeo(
    bd: Session,
    *,
    curso_id: uuid.UUID,
    estudiante_id: uuid.UUID,
    estado: EstadoMapeoGithub,
    origen: str | None,
    cuenta: CuentaGithub | None,
    evidencia: dict[str, Any],
    motivo_invalidacion: str | None = None,
    creado_por: uuid.UUID | None = None,
) -> MapeoGithub:
    ahora = ahora_utc()
    vivo = _mapeo_vivo(bd, curso_id=curso_id, estudiante_id=estudiante_id)

    if vivo.estado == EstadoMapeoGithub.SIN_DATO.value:
        vivo.origen = origen
        vivo.cuenta_github_id = cuenta.id if cuenta else None
        vivo.evidencia = evidencia
        vivo.estado = estado.value
        vivo.motivo_invalidacion = motivo_invalidacion
        vivo.creado_por = creado_por
        if estado == EstadoMapeoGithub.VIGENTE:
            vivo.vigente_desde = ahora
        return vivo

    vivo.estado = EstadoMapeoGithub.SUPERSEDIDO.value
    vivo.vigente_hasta = ahora
    nueva = MapeoGithub(
        curso_id=curso_id,
        estudiante_id=estudiante_id,
        cuenta_github_id=cuenta.id if cuenta else None,
        origen=origen,
        evidencia=evidencia,
        estado=estado.value,
        motivo_invalidacion=motivo_invalidacion,
        vigente_desde=ahora if estado == EstadoMapeoGithub.VIGENTE else None,
        creado_por=creado_por,
        creado_en=ahora,
    )
    bd.add(nueva)
    bd.flush()
    return nueva


@dataclass(frozen=True)
class ResultadoProcesarCandidato:
    mapeo: MapeoGithub
    texto_no_resuelto: str | None = (
        None  # motivo legible para el comentario de vuelta a Canvas (S7.4.6)
    )


def _buscar_conflicto_vigente(
    bd: Session, *, curso_id: uuid.UUID, cuenta_github_id: uuid.UUID, estudiante_id: uuid.UUID
) -> MapeoGithub | None:
    return (
        bd.query(MapeoGithub)
        .filter(
            MapeoGithub.curso_id == curso_id,
            MapeoGithub.cuenta_github_id == cuenta_github_id,
            MapeoGithub.estado == EstadoMapeoGithub.VIGENTE.value,
            MapeoGithub.estudiante_id != estudiante_id,
        )
        .one_or_none()
    )


def procesar_candidato(
    bd: Session,
    cliente_github: ClienteGitHub,
    *,
    curso_id: uuid.UUID,
    estudiante: Estudiante,
    login: str | None,
    texto_crudo: str | None,
    origen: str,
    es_puerta_docente: bool,
    creado_por: uuid.UUID | None = None,
) -> ResultadoProcesarCandidato:
    """Nucleo compartido de las vias 1-3 (S7.4). `es_puerta_docente=True` es
    la puerta de S7.5.3 "del docente": rechazo inmediato via `RechazoMapeo`,
    sin persistir nada. `es_puerta_docente=False` es la puerta "de la
    ingesta": nunca lanza, siempre persiste algun estado (S7.6.1 via
    `resultado_recibido`, la funcion pura que decide el estado)."""
    evidencia: dict[str, Any] = {"texto_crudo": texto_crudo} if texto_crudo is not None else {}
    if login is not None:
        evidencia["login_declarado"] = login

    if login is None:
        if es_puerta_docente:
            raise RechazoMapeo(
                MotivoRechazoMapeo.CUENTA_NO_EXISTE, detalle="no se pudo interpretar el texto"
            )
        mapeo = _escribir_mapeo(
            bd,
            curso_id=curso_id,
            estudiante_id=estudiante.id,
            estado=EstadoMapeoGithub.NO_RESUELTO,
            origen=origen,
            cuenta=None,
            evidencia=evidencia,
        )
        return ResultadoProcesarCandidato(mapeo=mapeo, texto_no_resuelto=texto_crudo)

    bloquear_equipo(bd)
    existe_usuario = cliente_github.existe_como_usuario(login)
    existe_org = cliente_github.existe_como_organizacion(login)
    es_org = es_cuenta_de_organizacion(existe_como_organizacion=existe_org)

    cuenta_info = (
        cliente_github.obtener_cuenta_usuario(login) if existe_usuario and not es_org else None
    )
    elegible = False
    cuenta_fila: CuentaGithub | None = None
    conflicto: MapeoGithub | None = None
    if cuenta_info is not None:
        ctx = construir_contexto_elegibilidad(
            bd, cuenta=cuenta_info, curso_id=curso_id, estudiante_id=estudiante.id
        )
        elegible = es_cuenta_elegible(ctx)
        if elegible:
            cuenta_fila = _upsert_cuenta_github(bd, cuenta_info)
            conflicto = _buscar_conflicto_vigente(
                bd, curso_id=curso_id, cuenta_github_id=cuenta_fila.id, estudiante_id=estudiante.id
            )

    estado = resultado_recibido(
        existe_como_usuario=existe_usuario,
        es_organizacion=es_org,
        elegible=elegible,
        hay_conflicto_en_el_curso=conflicto is not None,
    )

    if es_puerta_docente and estado != EstadoMapeoGithub.VIGENTE:
        motivo = {
            EstadoMapeoGithub.NO_EXISTE: MotivoRechazoMapeo.CUENTA_NO_EXISTE,
            EstadoMapeoGithub.ES_ORGANIZACION: MotivoRechazoMapeo.ES_ORGANIZACION,
            EstadoMapeoGithub.NO_RESUELTO: MotivoRechazoMapeo.CUENTA_NO_ELEGIBLE,
            EstadoMapeoGithub.EN_CONFLICTO: MotivoRechazoMapeo.CUENTA_YA_ASIGNADA,
        }[estado]
        raise RechazoMapeo(motivo, detalle=login)

    # Solo la puerta de la ingesta persiste NO_EXISTE/ES_ORGANIZACION/cuenta
    # no elegible; la puerta del docente ya salio por RechazoMapeo arriba.
    if estado in (EstadoMapeoGithub.NO_EXISTE, EstadoMapeoGithub.ES_ORGANIZACION):
        mapeo = _escribir_mapeo(
            bd,
            curso_id=curso_id,
            estudiante_id=estudiante.id,
            estado=estado,
            origen=origen,
            cuenta=None,
            evidencia=evidencia,
        )
        return ResultadoProcesarCandidato(mapeo=mapeo)

    if estado == EstadoMapeoGithub.NO_RESUELTO:
        mapeo = _escribir_mapeo(
            bd,
            curso_id=curso_id,
            estudiante_id=estudiante.id,
            estado=estado,
            origen=origen,
            cuenta=cuenta_fila,
            evidencia=evidencia,
            motivo_invalidacion=MotivoInvalidacionMapeo.CUENTA_NO_ELEGIBLE.value,
        )
        return ResultadoProcesarCandidato(
            mapeo=mapeo, texto_no_resuelto="esa cuenta pertenece al equipo docente"
        )

    assert cuenta_fila is not None

    if estado == EstadoMapeoGithub.EN_CONFLICTO:
        assert conflicto is not None
        # S7.6.3: ninguno de los dos recibe repositorio hasta resolucion
        # docente -- el mapeo previamente vigente tambien pasa a conflicto.
        _escribir_mapeo(
            bd,
            curso_id=curso_id,
            estudiante_id=conflicto.estudiante_id,
            estado=EstadoMapeoGithub.EN_CONFLICTO,
            origen=conflicto.origen,
            cuenta=cuenta_fila,
            evidencia={**conflicto.evidencia, "conflicto_con_estudiante_id": str(estudiante.id)},
        )
        mapeo = _escribir_mapeo(
            bd,
            curso_id=curso_id,
            estudiante_id=estudiante.id,
            estado=EstadoMapeoGithub.EN_CONFLICTO,
            origen=origen,
            cuenta=cuenta_fila,
            evidencia={**evidencia, "conflicto_con_estudiante_id": str(conflicto.estudiante_id)},
            creado_por=creado_por,
        )
        return ResultadoProcesarCandidato(
            mapeo=mapeo, texto_no_resuelto="esa cuenta ya fue declarada por otra persona"
        )

    mapeo = _escribir_mapeo(
        bd,
        curso_id=curso_id,
        estudiante_id=estudiante.id,
        estado=EstadoMapeoGithub.VIGENTE,
        origen=origen,
        cuenta=cuenta_fila,
        evidencia=evidencia,
        creado_por=creado_por,
    )

    # Resolucion automatica del lado perdedor de un conflicto anterior, si lo
    # hay (S7.6.3 "el otro queda NO_RESUELTO"): esta declaracion explicita
    # decide a favor de este estudiante entre los que estuvieran EN_CONFLICTO
    # por la misma cuenta.
    otros_en_conflicto = (
        bd.query(MapeoGithub)
        .filter(
            MapeoGithub.curso_id == curso_id,
            MapeoGithub.cuenta_github_id == cuenta_fila.id,
            MapeoGithub.estado == EstadoMapeoGithub.EN_CONFLICTO.value,
            MapeoGithub.estudiante_id != estudiante.id,
        )
        .all()
    )
    for otro in otros_en_conflicto:
        _escribir_mapeo(
            bd,
            curso_id=curso_id,
            estudiante_id=otro.estudiante_id,
            estado=EstadoMapeoGithub.NO_RESUELTO,
            origen=otro.origen,
            cuenta=None,
            evidencia={**otro.evidencia, "resuelto_a_favor_de_estudiante_id": str(estudiante.id)},
        )

    return ResultadoProcesarCandidato(mapeo=mapeo)


def declarar_manual(
    bd: Session,
    cliente_github: ClienteGitHub,
    *,
    curso_id: uuid.UUID,
    estudiante: Estudiante,
    login: str,
    actor_usuario_id: uuid.UUID,
) -> MapeoGithub:
    """Via 2 (S7.4.3): edicion manual con `mapeo.editar`, puerta del docente."""
    resultado = procesar_candidato(
        bd,
        cliente_github,
        curso_id=curso_id,
        estudiante=estudiante,
        login=login,
        texto_crudo=None,
        origen="CARGA_DOCENTE",
        es_puerta_docente=True,
        creado_por=actor_usuario_id,
    )
    return resultado.mapeo


def invalidar_mapeo_vigente(
    bd: Session, *, curso_id: uuid.UUID, estudiante_id: uuid.UUID, motivo: MotivoInvalidacionMapeo
) -> MapeoGithub | None:
    """S7.6.2: el mapeo `VIGENTE` (si lo hay) pasa a `INVALIDADO`, conservando
    cuenta y evidencia. `None` si no habia nada `VIGENTE` que invalidar."""
    vivo = _mapeo_vivo(bd, curso_id=curso_id, estudiante_id=estudiante_id)
    if vivo.estado != EstadoMapeoGithub.VIGENTE.value:
        return None
    cuenta = bd.query(CuentaGithub).filter(CuentaGithub.id == vivo.cuenta_github_id).one_or_none()
    return _escribir_mapeo(
        bd,
        curso_id=curso_id,
        estudiante_id=estudiante_id,
        estado=EstadoMapeoGithub.INVALIDADO,
        origen=vivo.origen,
        cuenta=cuenta,
        evidencia=vivo.evidencia,
        motivo_invalidacion=motivo.value,
    )


def invalidar_por_retiro(bd: Session, *, curso_id: uuid.UUID, estudiante_id: uuid.UUID) -> None:
    """S7.6.2 `ESTUDIANTE_RETIRADO`: la revalidacion diaria puede devolver el
    mapeo a `VIGENTE` sola si la persona se reincorpora (S7.9.1), sin volver
    a pedirle el dato."""
    invalidar_mapeo_vigente(
        bd,
        curso_id=curso_id,
        estudiante_id=estudiante_id,
        motivo=MotivoInvalidacionMapeo.ESTUDIANTE_RETIRADO,
    )


def procesar_entrega_autoservicio(
    bd: Session,
    cliente_github: ClienteGitHub,
    *,
    curso_id: uuid.UUID,
    estudiante: Estudiante,
    texto_html: str,
) -> ResultadoProcesarCandidato | None:
    """Vias 1 y 4 (S7.4.1, S7.4.5): la extraccion del candidato ocurre aqui,
    antes de entrar al nucleo compartido. Devuelve `None` sin escribir nada
    si el texto es identico al ya procesado (el volcado completo cada hora,
    S7.4.1, re-lee entregas viejas sin que nada haya cambiado; sin este
    corte cada pasada crearia una fila `mapeo_github` nueva por reenvio
    identico, contradiciendo el espiritu de "append-only" -- preservar
    correcciones reales, no ruido)."""
    candidato = extraer_candidato(texto_html)
    vivo = _mapeo_vivo(bd, curso_id=curso_id, estudiante_id=estudiante.id)
    if (
        vivo.evidencia.get("texto_crudo") == candidato.texto_crudo
        and vivo.estado != EstadoMapeoGithub.SIN_DATO.value
    ):
        return None
    return procesar_candidato(
        bd,
        cliente_github,
        curso_id=curso_id,
        estudiante=estudiante,
        login=candidato.login,
        texto_crudo=candidato.texto_crudo,
        origen="AUTOSERVICIO_CANVAS",
        es_puerta_docente=False,
    )
