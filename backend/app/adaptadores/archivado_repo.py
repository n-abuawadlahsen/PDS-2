"""Archivar y desarchivar los repositorios de una tarea (A-168, A-197, A-227;
Etapa F8).

Los endpoints solo encolan (A-226): la llamada a GitHub la hace el trabajo
`archivar_repositorios`, uno por repositorio, que reevalua las cinco guardas
de `dominio.archivado.puede_archivar` justo antes de tocar cada uno. La tarea
pasa a `ARCHIVADA` en la transaccion del ultimo repositorio, y solo si todos
quedaron `ARCHIVADO`, `INACCESIBLE` o `FUERA_DE_ALCANCE` (A-197 punto 3).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.adaptadores import bitacora_repo, outbox_repo, trabajos_repo, versiones_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_github import (
    ClienteGitHub,
    FalloProveedorGithub,
    RechazoProveedorGithub,
)
from app.adaptadores.modelos_aprovisionamiento import (
    AccesoRepositorio,
    FechaEfectiva,
    MensajeSaliente,
    Repositorio,
)
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_github import AccesoDocenteRepositorio
from app.adaptadores.modelos_infraestructura import Bitacora, Trabajo
from app.adaptadores.modelos_padron import Estudiante
from app.adaptadores.modelos_tarea import Entrega, Tarea
from app.dominio.archivado import (
    AvisoPrevio,
    EntregaDeSujeto,
    RepositorioArchivable,
    ResultadoArchivado,
    puede_archivar,
)
from app.dominio.estados import (
    CanalComunicacionActivo,
    EstadoAccesoRepositorio,
    EstadoFechaEfectiva,
    EstadoMensaje,
    EstadoRepositorio,
    EstadoTarea,
    EstadoTrabajo,
    OrigenMensaje,
)

TIPO_TRABAJO = "archivar_repositorios"
ARCHIVAR = "archivar"
DESARCHIVAR = "desarchivar"
_MAX_INTENTOS = 3  # catalogo S14.7.4

# A-197 punto 3: los estados con los que una tarea ya puede estar ARCHIVADA.
TERMINALES = frozenset(
    {
        EstadoRepositorio.ARCHIVADO.value,
        EstadoRepositorio.INACCESIBLE.value,
        EstadoRepositorio.FUERA_DE_ALCANCE.value,
    }
)
# Quien no tiene acceso al repositorio no tiene nada que perder al archivarlo.
_SIN_AVISO = frozenset(
    {
        EstadoAccesoRepositorio.SIN_MAPEO.value,
        EstadoAccesoRepositorio.DESAPARECIDA.value,
        EstadoAccesoRepositorio.REVOCADO.value,
    }
)


class GithubSinAcceso(Exception):
    pass


# --- Lecturas ---


def repositorios_de_tarea(bd: Session, tarea_id: uuid.UUID) -> list[Repositorio]:
    """Los repositorios que existen en GitHub. Uno que nunca llego a crearse no
    tiene nada que archivar ni impide que la tarea quede ARCHIVADA."""
    return (
        bd.query(Repositorio)
        .filter(Repositorio.tarea_id == tarea_id, Repositorio.github_repo_id.isnot(None))
        .order_by(Repositorio.nombre)
        .all()
    )


def archivables(bd: Session, tarea_id: uuid.UUID) -> list[Repositorio]:
    return [r for r in repositorios_de_tarea(bd, tarea_id) if r.estado not in TERMINALES]


def _hechos_de_repositorio(
    bd: Session, repositorio: Repositorio, entregas: list[Entrega]
) -> RepositorioArchivable:
    filas = []
    for e in entregas:
        fecha = (
            bd.query(FechaEfectiva)
            .filter(
                FechaEfectiva.entrega_id == e.id,
                FechaEfectiva.sujeto_id == repositorio.sujeto_id,
                FechaEfectiva.estado == EstadoFechaEfectiva.VIGENTE.value,
            )
            .one_or_none()
        )
        if fecha is None:
            continue  # la entrega no aplica a este sujeto
        capturada = versiones_repo.version_vigente(bd, e.id, repositorio.sujeto_id) is not None
        filas.append(EntregaDeSujeto(e.nombre, fecha.due_at_utc, capturada))
    docentes = tuple(
        a.estado
        for a in bd.query(AccesoDocenteRepositorio).filter(
            AccesoDocenteRepositorio.repositorio_id == repositorio.id
        )
    )
    estudiantes = tuple(
        a.estado
        for a in bd.query(AccesoRepositorio).filter(
            AccesoRepositorio.repositorio_id == repositorio.id
        )
    )
    return RepositorioArchivable(repositorio.nombre, tuple(filas), docentes, estudiantes)


def _destinatarios(
    bd: Session, repositorios: list[Repositorio]
) -> list[tuple[Repositorio, Estudiante]]:
    salida = []
    for repo in repositorios:
        for acceso, estudiante in (
            bd.query(AccesoRepositorio, Estudiante)
            .join(Estudiante, Estudiante.id == AccesoRepositorio.estudiante_id)
            .filter(AccesoRepositorio.repositorio_id == repo.id)
            .order_by(Estudiante.nombre)
        ):
            if acceso.estado not in _SIN_AVISO:
                salida.append((repo, estudiante))
    return salida


def aviso_previo(
    bd: Session, curso: Curso, tarea: Tarea, repositorios: list[Repositorio]
) -> AvisoPrevio:
    destinatarios = _destinatarios(bd, repositorios)
    encolados = enviados = bloqueados = 0
    ultimo: datetime | None = None
    for repo, estudiante in destinatarios:
        mensaje = (
            bd.query(MensajeSaliente)
            .filter(
                MensajeSaliente.tarea_id == tarea.id,
                MensajeSaliente.repositorio_id == repo.id,
                MensajeSaliente.estudiante_id == estudiante.id,
                MensajeSaliente.evento == outbox_repo.EVENTO_AVISO_ARCHIVADO_PREVIO,
            )
            .order_by(MensajeSaliente.creado_en.desc())
            .first()
        )
        if mensaje is None:
            continue
        encolados += 1
        if mensaje.estado == EstadoMensaje.ENVIADO.value and mensaje.enviado_en is not None:
            enviados += 1
            ultimo = mensaje.enviado_en if ultimo is None else max(ultimo, mensaje.enviado_en)
        elif mensaje.estado in (EstadoMensaje.BLOQUEADO.value, EstadoMensaje.FALLIDO.value):
            bloqueados += 1
    return AvisoPrevio(
        destinatarios=len(destinatarios),
        encolados=encolados,
        enviados=enviados,
        bloqueados=bloqueados,
        ultimo_envio=ultimo,
        canal_bloqueado=curso.canal_comunicacion_activo == CanalComunicacionActivo.BLOQUEADO.value,
    )


def evaluar(
    bd: Session,
    curso: Curso,
    tarea: Tarea,
    *,
    ahora: datetime,
    repositorios: list[Repositorio] | None = None,
    confirmacion_sin_captura: str | None = None,
    confirmacion_sin_aviso: str | None = None,
) -> ResultadoArchivado:
    repos = archivables(bd, tarea.id) if repositorios is None else repositorios
    entregas = bd.query(Entrega).filter(Entrega.tarea_id == tarea.id).order_by(Entrega.orden).all()
    return puede_archivar(
        repositorios=[_hechos_de_repositorio(bd, r, entregas) for r in repos],
        aviso=aviso_previo(bd, curso, tarea, repos),
        correcciones_abiertas=None,  # el modulo de correcciones aun no existe
        ahora=ahora,
        confirmacion_sin_captura=confirmacion_sin_captura,
        confirmacion_sin_aviso=confirmacion_sin_aviso,
    )


def trabajos_en_curso(bd: Session, tarea_id: uuid.UUID) -> int:
    return (
        bd.query(Trabajo)
        .filter(
            Trabajo.tipo == TIPO_TRABAJO,
            Trabajo.payload["tarea_id"].astext == str(tarea_id),
            Trabajo.estado.notin_([EstadoTrabajo.OK.value, EstadoTrabajo.CANCELADO.value]),
        )
        .count()
    )


# --- Acciones del profesor (solo encolan) ---


def encolar_aviso_previo(bd: Session, curso: Curso, tarea: Tarea) -> int:
    nuevos = 0
    for repo, estudiante in _destinatarios(bd, archivables(bd, tarea.id)):
        if outbox_repo.encolar_aviso_archivado(
            bd,
            curso=curso,
            tarea=tarea,
            repositorio=repo,
            estudiante=estudiante,
            evento=outbox_repo.EVENTO_AVISO_ARCHIVADO_PREVIO,
            origen=OrigenMensaje.MANUAL,
        ):
            nuevos += 1
    return nuevos


def _clave(accion: str, repositorio_id: uuid.UUID) -> str:
    return f"{TIPO_TRABAJO}:{accion}:{repositorio_id}"


def solicitar(
    bd: Session,
    curso: Curso,
    tarea: Tarea,
    *,
    accion: str,
    repositorios: list[Repositorio],
    actor_usuario_id: uuid.UUID,
    confirmaciones: dict[str, str | None],
) -> int:
    """Un trabajo por repositorio, clave `(accion, repositorio)`. Uno ya activo
    no se duplica: se comprueba antes para no deshacer los anteriores."""
    encolados = 0
    for repo in repositorios:
        clave = _clave(accion, repo.id)
        activo = (
            bd.query(Trabajo.id)
            .filter(
                Trabajo.clave_idempotencia == clave,
                Trabajo.estado.notin_([EstadoTrabajo.OK.value, EstadoTrabajo.CANCELADO.value]),
            )
            .first()
        )
        if activo is not None:
            continue
        trabajos_repo.encolar(
            bd,
            tipo=TIPO_TRABAJO,
            clave_idempotencia=clave,
            max_intentos=_MAX_INTENTOS,
            curso_id=curso.id,
            payload={
                "accion": accion,
                "tarea_id": str(tarea.id),
                "repositorio_id": str(repo.id),
                "actor_usuario_id": str(actor_usuario_id),
                **confirmaciones,
            },
        )
        encolados += 1
    bitacora_repo.registrar(
        bd,
        accion="ARCHIVADO_SOLICITADO" if accion == ARCHIVAR else "DESARCHIVADO_SOLICITADO",
        entidad="tarea",
        entidad_id=str(tarea.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=curso.id,
        despues={"repositorios": encolados, **confirmaciones},
    )
    return encolados


# --- El trabajo ---


def _token(cliente: ClienteGitHub, curso: Curso) -> tuple[str, str]:
    if curso.github_installation_id is None or curso.github_org_login is None:
        raise GithubSinAcceso("el curso no tiene instalacion de GitHub")
    try:
        return curso.github_org_login, cliente.obtener_token_instalacion(
            curso.github_installation_id
        )
    except (FalloProveedorGithub, RechazoProveedorGithub) as exc:
        raise GithubSinAcceso(str(exc)) from exc


def ejecutar(
    bd: Session, cliente: ClienteGitHub, *, payload: dict[str, Any], trabajo_id: uuid.UUID
) -> None:
    repo = bd.get(Repositorio, uuid.UUID(payload["repositorio_id"]))
    tarea = bd.get(Tarea, uuid.UUID(payload["tarea_id"]))
    if repo is None or tarea is None:
        return
    curso = bd.get(Curso, tarea.curso_id)
    assert curso is not None
    actor = uuid.UUID(payload["actor_usuario_id"])
    if payload["accion"] == ARCHIVAR:
        _archivar(
            bd, cliente, curso, tarea, repo, actor=actor, payload=payload, trabajo_id=trabajo_id
        )
    else:
        _desarchivar(bd, cliente, curso, tarea, repo, actor=actor)


def _archivar(
    bd: Session,
    cliente: ClienteGitHub,
    curso: Curso,
    tarea: Tarea,
    repo: Repositorio,
    *,
    actor: uuid.UUID,
    payload: dict[str, Any],
    trabajo_id: uuid.UUID,
) -> None:
    if repo.estado in TERMINALES:
        _cerrar_tarea_si_corresponde(bd, tarea, actor=actor)
        return
    # A-197: las guardas se reevaluan antes de cada repositorio.
    resultado = evaluar(
        bd,
        curso,
        tarea,
        ahora=ahora_utc(),
        repositorios=[repo],
        confirmacion_sin_captura=payload.get("confirmacion_sin_captura"),
        confirmacion_sin_aviso=payload.get("confirmacion_sin_aviso"),
    )
    fallida = resultado.fallida
    if fallida is not None:
        bitacora_repo.registrar(
            bd,
            accion="ARCHIVADO_OMITIDO",
            entidad="repositorio",
            entidad_id=str(repo.id),
            actor_usuario_id=actor,
            curso_id=curso.id,
            despues={"guarda": fallida.numero, "motivo": fallida.motivo},
        )
        return
    org, token = _token(cliente, curso)
    nombre = (repo.full_name or "").split("/", 1)[-1] or repo.nombre
    cliente.cambiar_archivado(org, nombre, True, token)
    antes = repo.estado
    repo.estado = EstadoRepositorio.ARCHIVADO.value
    repo.actualizado_en = ahora_utc()
    bd.flush()
    bitacora_repo.registrar(
        bd,
        accion="REPOSITORIO_ESTADO",
        entidad="repositorio",
        entidad_id=str(repo.id),
        actor_usuario_id=actor,
        curso_id=curso.id,
        antes={"estado": antes},
        despues={"estado": repo.estado, "origen": "accion del profesor"},
    )
    for r, estudiante in _destinatarios(bd, [repo]):
        outbox_repo.encolar_aviso_archivado(
            bd,
            curso=curso,
            tarea=tarea,
            repositorio=r,
            estudiante=estudiante,
            evento=outbox_repo.EVENTO_AVISO_ARCHIVADO,
            origen=OrigenMensaje.SISTEMA,
            trabajo_id=trabajo_id,
        )
    _cerrar_tarea_si_corresponde(bd, tarea, actor=actor)


def _cerrar_tarea_si_corresponde(bd: Session, tarea: Tarea, *, actor: uuid.UUID) -> None:
    """A-197 punto 3: lo unico que escribe `tarea.estado = ARCHIVADA`."""
    if tarea.estado == EstadoTarea.ARCHIVADA.value:
        return
    repos = repositorios_de_tarea(bd, tarea.id)
    if not repos or any(r.estado not in TERMINALES for r in repos):
        return
    antes = tarea.estado
    tarea.estado = EstadoTarea.ARCHIVADA.value
    bd.flush()
    bitacora_repo.registrar(
        bd,
        accion="TAREA_ARCHIVADA",
        entidad="tarea",
        entidad_id=str(tarea.id),
        actor_usuario_id=actor,
        curso_id=tarea.curso_id,
        antes={"estado": antes},
        despues={"estado": tarea.estado},
    )


def _estado_previo_al_archivado(bd: Session, tarea: Tarea) -> str:
    ultima = (
        bd.query(Bitacora)
        .filter(
            Bitacora.entidad == "tarea",
            Bitacora.entidad_id == str(tarea.id),
            Bitacora.accion == "TAREA_ARCHIVADA",
        )
        .order_by(Bitacora.creado_en.desc())
        .first()
    )
    previo = (ultima.antes or {}).get("estado") if ultima is not None else None
    return str(previo) if previo else EstadoTarea.CERRADA.value


def _desarchivar(
    bd: Session,
    cliente: ClienteGitHub,
    curso: Curso,
    tarea: Tarea,
    repo: Repositorio,
    *,
    actor: uuid.UUID,
) -> None:
    if repo.estado != EstadoRepositorio.ARCHIVADO.value:
        return
    org, token = _token(cliente, curso)
    nombre = (repo.full_name or "").split("/", 1)[-1] or repo.nombre
    cliente.cambiar_archivado(org, nombre, False, token)
    # Como con el webhook `unarchived`: el predicado de OPERATIVO lo reevalua
    # la proxima reconciliacion de accesos.
    repo.estado = EstadoRepositorio.DEGRADADO.value
    repo.actualizado_en = ahora_utc()
    bd.flush()
    for accion in ("REPOSITORIO_ESTADO", "REPOSITORIO_DESARCHIVADO"):
        bitacora_repo.registrar(
            bd,
            accion=accion,
            entidad="repositorio",
            entidad_id=str(repo.id),
            actor_usuario_id=actor,
            curso_id=curso.id,
            antes={"estado": EstadoRepositorio.ARCHIVADO.value},
            despues={"estado": repo.estado, "origen": "accion del profesor"},
        )
    if tarea.estado == EstadoTarea.ARCHIVADA.value:
        previo = _estado_previo_al_archivado(bd, tarea)
        tarea.estado = previo
        bd.flush()
        bitacora_repo.registrar(
            bd,
            accion="TAREA_DESARCHIVADA",
            entidad="tarea",
            entidad_id=str(tarea.id),
            actor_usuario_id=actor,
            curso_id=curso.id,
            antes={"estado": EstadoTarea.ARCHIVADA.value},
            despues={"estado": previo},
        )
