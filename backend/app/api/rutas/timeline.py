"""Timeline de un repositorio (SPEC 10 S10.9; A-124, A-163; Etapa F7).

Cuatro capas en un eje de dias del curso: commits (todos, con su etiqueta de
exclusion), ciclo de vida del repositorio, marcas de entrega y cambios de
composicion. Ninguna tabla nueva: lee el espejo y la bitacora. La franja de
participacion usa la misma funcion que la comparacion del tablero (P2).

Los hitos manuales se marcan y desmarcan de forma logica en la bitacora
(`HITO_MARCADO` / `HITO_DESMARCADO`): el estado vigente de un commit es su
ultimo evento, y nada se borra.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.adaptadores import metricas_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.bitacora_repo import registrar as registrar_bitacora
from app.adaptadores.modelos_actividad import Commit, EventoPush, IdentidadGit
from app.adaptadores.modelos_aprovisionamiento import AccesoRepositorio, Repositorio, Sujeto
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_github import AccesoDocenteRepositorio
from app.adaptadores.modelos_infraestructura import Bitacora
from app.adaptadores.modelos_padron import Estudiante, PertenenciaGrupo
from app.adaptadores.modelos_tarea import Entrega, Tarea
from app.adaptadores.modelos_version import VersionEntrega
from app.api.dependencias import exigir_csrf, obtener_sesion_bd, requiere
from app.api.rutas.tablero import _nombre_sujeto, _periodo_por_defecto, _periodos, _rango
from app.dominio.actividad import SHA_CEROS, ofuscar_email
from app.dominio.estados import EstadoIdentidadGit, EstadoRepositorio, ReglaAtribucion
from app.dominio.metricas import causa_sin_participacion, dia_del_curso, en_ventana
from app.dominio.permisos import Permiso

router = APIRouter(tags=["timeline"])

DIAS_PARA_COLAPSAR = 3
_ETIQUETA_REGLA_DEBIL = ReglaAtribucion.EMAIL_DIRECTO.value


def _contexto(
    bd: Session, curso_id: uuid.UUID, tarea_id: uuid.UUID, repo_id: uuid.UUID
) -> tuple[Curso, Tarea, Repositorio, Sujeto]:
    repo = (
        bd.query(Repositorio)
        .filter(
            Repositorio.id == repo_id,
            Repositorio.curso_id == curso_id,
            Repositorio.tarea_id == tarea_id,
        )
        .one_or_none()
    )
    if repo is None:
        raise HTTPException(status_code=404)
    curso, tarea, sujeto = (
        bd.get(Curso, curso_id),
        bd.get(Tarea, tarea_id),
        bd.get(Sujeto, repo.sujeto_id),
    )
    assert curso is not None and tarea is not None and sujeto is not None
    return curso, tarea, repo, sujeto


def _hitos(bd: Session, commit_ids: list[uuid.UUID]) -> dict[str, str]:
    """El ultimo evento de cada commit decide si el hito esta vigente."""
    vigentes: dict[str, str | None] = {}
    for b in (
        bd.query(Bitacora)
        .filter(
            Bitacora.entidad == "commit",
            Bitacora.entidad_id.in_([str(i) for i in commit_ids]),
            Bitacora.accion.in_(["HITO_MARCADO", "HITO_DESMARCADO"]),
        )
        .order_by(Bitacora.creado_en)
    ):
        assert b.entidad_id is not None
        vigentes[b.entidad_id] = (
            (b.despues or {}).get("nota") if b.accion == "HITO_MARCADO" else None
        )
    return {k: v for k, v in vigentes.items() if v}


def _motivo_sin_enlace(bd: Session, repo: Repositorio) -> str | None:
    """S10.9.1: el enlace se oculta con su motivo, nunca se entrega roto."""
    if repo.estado == EstadoRepositorio.INACCESIBLE.value:
        return "El repositorio ya no está accesible en GitHub; su historia se conserva aquí."
    acceso = (
        bd.query(AccesoDocenteRepositorio)
        .filter(AccesoDocenteRepositorio.repositorio_id == repo.id)
        .first()
    )
    if acceso is None or acceso.estado != "CONCEDIDO":
        if acceso is not None and acceso.estado == "ERROR":
            return (
                "GitHub rechazó dar lectura al equipo docente: reintenta desde la pestaña de "
                "repositorios."
            )
        return (
            "Preparando tu acceso al repositorio: los enlaces aparecen cuando el equipo docente "
            "tenga lectura."
        )
    return None


class CommitTimelineSalida(BaseModel):
    sha: str
    sha_corto: str
    fecha: datetime
    mensaje: str | None
    autor: str | None
    regla_atribucion: str
    senal_debil: bool
    etiqueta_exclusion: str | None
    huerfano_desde: datetime | None
    rama: str | None
    via_web: bool | None
    adiciones: int | None
    eliminaciones: int | None
    destacado: str | None
    hito: str | None
    posterior_al_cierre_de: int | None
    url: str | None


class DiaTimelineSalida(BaseModel):
    dia: date
    colapsado: bool
    hasta: date | None
    n_dias: int
    commits: list[CommitTimelineSalida]


class TramoSalida(BaseModel):
    periodo: str
    entrega: str
    inicio: datetime
    fin: datetime
    integrantes: list[dict[str, Any]]
    sin_atribuir: int


class TimelineSalida(BaseModel):
    repositorio: dict[str, Any]
    sujeto: str
    periodos: list[Any]
    periodo: str
    dias: list[DiaTimelineSalida]
    ciclo_de_vida: list[dict[str, Any]]
    marcas_entrega: list[dict[str, Any]]
    composicion: list[dict[str, Any]]
    franja: list[TramoSalida]
    enlaces: dict[str, Any]
    identidades_sin_resolver: int
    sin_commits_contables: bool
    causa_vacia: str | None


@router.get(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/repos/{repo_id}/timeline",
    response_model=TimelineSalida,
)
def timeline(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    repo_id: uuid.UUID,
    response: Response,
    periodo: str | None = None,
    integrante: str | None = None,
    rama: str | None = None,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> TimelineSalida:
    curso, tarea, repo, sujeto = _contexto(bd, curso_id, tarea_id, repo_id)
    ahora = ahora_utc()
    zona = curso.zona_horaria
    periodos = _periodos(bd, tarea)
    periodo = periodo or _periodo_por_defecto(bd, tarea, ahora)
    fechas = metricas_repo.fechas_del_sujeto(bd, tarea.id, sujeto.id)
    rango = _rango(periodo, fechas, repo, ahora)
    resumenes = metricas_repo.commits_de_repositorio(bd, repo)
    filas = {c.id: c for c in bd.query(Commit).filter(Commit.repositorio_id == repo.id)}
    integrantes = metricas_repo.integrantes_de_sujeto(bd, sujeto)
    nombres = {i.estudiante_id: i.nombre for i in integrantes}
    for est_curso in bd.query(Estudiante).filter(Estudiante.curso_id == curso.id):
        nombres.setdefault(est_curso.id, est_curso.nombre)
    motivo_enlace = _motivo_sin_enlace(bd, repo)
    hitos = _hitos(bd, list(filas))

    # Reglas de destacado (S10.9.3), sobre la historia entera.
    orden_por_entrega = {
        e.id: e.orden for e in bd.query(Entrega).filter(Entrega.tarea_id == tarea.id)
    }
    versiones = bd.query(VersionEntrega).filter(VersionEntrega.sujeto_id == sujeto.id).all()
    version_por_sha = {
        v.commit_sha: orden_por_entrega.get(v.entrega_id) for v in versiones if v.commit_sha
    }
    contables = sorted((c for c in resumenes if c.contable), key=lambda c: c.fecha)
    primera: dict[uuid.UUID, uuid.UUID] = {}
    for c in contables:
        for est in c.acreditados:
            primera.setdefault(est, c.id)
    vuelta: dict[uuid.UUID, int] = {}
    for anterior, actual in zip(contables, contables[1:], strict=False):
        brecha = (actual.fecha - anterior.fecha).days
        if brecha >= curso.umbral_dias_sin_actividad:
            vuelta[actual.id] = brecha

    def destacado(c: metricas_repo.CommitResumen) -> str | None:
        if c.sha in version_por_sha:
            return f"versión de la entrega {version_por_sha[c.sha]}"
        if c.es_merge:
            return "integración de trabajo (merge)"
        for est, commit_id in primera.items():
            if commit_id == c.id:
                return f"primera participación de {nombres.get(est, 'un integrante')}"
        if c.id in vuelta:
            return f"vuelta al trabajo tras {vuelta[c.id]} días"
        if str(c.id) in hitos:
            return f"hito: {hitos[str(c.id)]}"
        return None

    def posterior_de(fecha: datetime) -> int | None:
        previas = [f for f in fechas if f.due_at is not None and f.due_at < fecha]
        if not previas:
            return None
        return max(previas, key=lambda f: f.orden).orden

    def salida(c: metricas_repo.CommitResumen) -> CommitTimelineSalida:
        fila = filas[c.id]
        autor: str | None
        if c.acreditados:
            autor = ", ".join(sorted(nombres.get(e, "—") for e in c.acreditados))
        else:
            # Sin atribuir: el nombre que el autor publico y el correo ofuscado.
            autor = (
                " ".join(x for x in (fila.autor_nombre, ofuscar_email(fila.autor_email)) if x)
                or None
            )
        return CommitTimelineSalida(
            sha=fila.sha,
            sha_corto=fila.sha[:7],
            fecha=fila.fecha_committer,
            mensaje=fila.mensaje_resumen,
            autor=autor,
            regla_atribucion=fila.regla_atribucion,
            senal_debil=fila.regla_atribucion == _ETIQUETA_REGLA_DEBIL,
            etiqueta_exclusion=None if c.contable else fila.motivo_exclusion,
            huerfano_desde=fila.huerfano_desde,
            rama=fila.rama_detectada,
            via_web=fila.via_web,
            adiciones=fila.adiciones,
            eliminaciones=fila.eliminaciones,
            destacado=destacado(c),
            hito=hitos.get(str(c.id)),
            posterior_al_cierre_de=posterior_de(fila.fecha_committer),
            url=None if motivo_enlace else f"https://github.com/{repo.full_name}/commit/{fila.sha}",
        )

    visibles = [
        c
        for c in resumenes
        if (rango is None or en_ventana(c.fecha, rango))
        and (
            integrante is None
            or (integrante == "sin_atribuir" and c.sin_atribuir)
            or (integrante not in ("sin_atribuir",) and uuid.UUID(integrante) in c.acreditados)
        )
        and (rama is None or filas[c.id].rama_detectada == rama)
    ]
    dias = _agrupar(visibles, salida, zona, rango)

    ciclo = _ciclo_de_vida(bd, repo, nombres)
    marcas = []
    for e in bd.query(Entrega).filter(Entrega.tarea_id == tarea.id).order_by(Entrega.orden):
        propia = next((f for f in fechas if f.entrega_id == e.id), None)
        marcas.append(
            {
                "orden": e.orden,
                "entrega": e.nombre,
                "fecha": propia.due_at.isoformat() if propia and propia.due_at else None,
                "aplica": propia is not None,
                "versiones": [
                    {
                        "intento": v.intento,
                        "vigente": v.vigente,
                        "estado": v.estado,
                        "motivo": v.motivo,
                        "commit_sha": v.commit_sha,
                        "tag": v.tag_nombre,
                    }
                    for v in sorted(
                        (v for v in versiones if v.entrega_id == e.id), key=lambda v: v.intento
                    )
                ],
            }
        )
    composicion: list[dict[str, Any]] = []
    if sujeto.grupo_id is not None:
        for pg, miembro in (
            bd.query(PertenenciaGrupo, Estudiante)
            .join(Estudiante, Estudiante.id == PertenenciaGrupo.estudiante_id)
            .filter(PertenenciaGrupo.grupo_id == sujeto.grupo_id)
        ):
            composicion.append(
                {
                    "estudiante": miembro.nombre,
                    "estado": pg.workflow_state,
                    "desde": pg.activa_desde.isoformat(),
                    "hasta": pg.activa_hasta.isoformat() if pg.activa_hasta else None,
                }
            )
    if sujeto.desactivado_en is not None:
        composicion.append(
            {
                "sujeto_fuera_de_alcance": sujeto.desactivado_en.isoformat(),
                "motivo": sujeto.motivo_desactivacion,
            }
        )

    accesos = {
        a.estudiante_id: a.estado
        for a in bd.query(AccesoRepositorio).filter(AccesoRepositorio.repositorio_id == repo.id)
    }
    franja = []
    for p in periodos:
        if not p.clave.startswith("entrega:"):
            continue
        ventana = _rango(p.clave, fechas, repo, ahora)
        if ventana is None:
            continue
        partes, sin_atribuir = metricas_repo.participacion(
            resumenes, integrantes, ventana_sujeto=ventana, zona=zona
        )
        franja.append(
            TramoSalida(
                periodo=p.clave,
                entrega=p.etiqueta,
                inicio=ventana.inicio,
                fin=ventana.fin,
                sin_atribuir=sin_atribuir,
                integrantes=[
                    {
                        "estudiante_id": str(x.estudiante_id),
                        "nombre": nombres.get(x.estudiante_id, "—"),
                        "commits": x.commits,
                        "dias_activos": x.dias_activos,
                        "causa": causa_sin_participacion(
                            acceso=accesos.get(x.estudiante_id),
                            commits=x.commits,
                            hay_sin_atribuir=sin_atribuir > 0,
                        ),
                        "ventana_inicio": x.ventana.inicio.isoformat(),
                        "ventana_fin": x.ventana.fin.isoformat(),
                    }
                    for x in partes
                ],
            )
        )

    sin_contables = not contables
    causa_vacia = None
    if sin_contables:
        actividad = metricas_repo.estado_actividad(bd, curso, repo, resumenes, ahora=ahora)
        if actividad.estado == "SIN_DATOS_TODAVIA":
            causa_vacia = "SIN_DATOS_TODAVIA"
        else:
            causa_vacia = causa_sin_participacion(
                acceso=next(iter(accesos.values()), None) if sujeto.estudiante_id else "ACEPTADO",
                commits=0,
                hay_sin_atribuir=any(c.sin_atribuir for c in resumenes),
            )
    response.headers["X-Llamadas-Externas"] = "0"
    return TimelineSalida(
        repositorio={
            "id": str(repo.id),
            "nombre": repo.nombre,
            "estado": repo.estado,
            "rama_por_defecto": repo.rama_por_defecto,
        },
        sujeto=_nombre_sujeto(bd, sujeto),
        periodos=periodos,
        periodo=periodo,
        dias=dias,
        ciclo_de_vida=ciclo,
        marcas_entrega=marcas,
        composicion=composicion,
        franja=franja,
        enlaces={"motivo": motivo_enlace},
        identidades_sin_resolver=bd.query(IdentidadGit)
        .filter(
            IdentidadGit.repositorio_id == repo.id,
            IdentidadGit.estado == EstadoIdentidadGit.SIN_RESOLVER.value,
        )
        .count(),
        sin_commits_contables=sin_contables,
        causa_vacia=causa_vacia,
    )


def _agrupar(
    commits: list[metricas_repo.CommitResumen],
    salida: Any,
    zona: str,
    rango: Any,
) -> list[DiaTimelineSalida]:
    """Agrupado por dia del curso; los tramos de tres o mas dias seguidos sin
    commits contables se pliegan en una fila, y al desplegarla no se pierde
    ninguno (los no contables de esos dias viajan dentro)."""
    por_dia: dict[date, list[metricas_repo.CommitResumen]] = defaultdict(list)
    for c in commits:
        por_dia[dia_del_curso(c.fecha, zona)].append(c)
    if not por_dia:
        return []
    inicio = min(por_dia)
    fin = max(por_dia)
    if rango is not None:
        inicio = min(inicio, dia_del_curso(rango.inicio, zona) + timedelta(days=1))
        fin = max(fin, dia_del_curso(min(rango.fin, ahora_utc()), zona))
    dias: list[DiaTimelineSalida] = []
    vacio: list[date] = []
    contenido_vacio: list[metricas_repo.CommitResumen] = []

    def cerrar_vacio() -> None:
        if not vacio:
            return
        if len(vacio) >= DIAS_PARA_COLAPSAR:
            dias.append(
                DiaTimelineSalida(
                    dia=vacio[0],
                    colapsado=True,
                    hasta=vacio[-1],
                    n_dias=len(vacio),
                    commits=[salida(c) for c in sorted(contenido_vacio, key=lambda c: c.fecha)],
                )
            )
        else:
            for d in vacio:
                dias.append(
                    DiaTimelineSalida(
                        dia=d,
                        colapsado=False,
                        hasta=None,
                        n_dias=1,
                        commits=[
                            salida(c) for c in sorted(por_dia.get(d, []), key=lambda c: c.fecha)
                        ],
                    )
                )
        vacio.clear()
        contenido_vacio.clear()

    actual = inicio
    while actual <= fin:
        del_dia = por_dia.get(actual, [])
        if any(c.contable for c in del_dia):
            cerrar_vacio()
            dias.append(
                DiaTimelineSalida(
                    dia=actual,
                    colapsado=False,
                    hasta=None,
                    n_dias=1,
                    commits=[salida(c) for c in sorted(del_dia, key=lambda c: c.fecha)],
                )
            )
        else:
            vacio.append(actual)
            contenido_vacio.extend(del_dia)
        actual += timedelta(days=1)
    cerrar_vacio()
    return dias


def _ciclo_de_vida(
    bd: Session, repo: Repositorio, nombres: dict[uuid.UUID, str]
) -> list[dict[str, Any]]:
    eventos: list[dict[str, Any]] = [
        {"fecha": repo.creado_en.isoformat(), "tipo": "REPOSITORIO_CREADO", "detalle": {}}
    ]
    if repo.listo_en:
        eventos.append(
            {"fecha": repo.listo_en.isoformat(), "tipo": "REPOSITORIO_LISTO", "detalle": {}}
        )
    for a in bd.query(AccesoRepositorio).filter(AccesoRepositorio.repositorio_id == repo.id):
        nombre = nombres.get(a.estudiante_id, "—")
        if a.invitado_en:
            eventos.append(
                {
                    "fecha": a.invitado_en.isoformat(),
                    "tipo": "INVITACION_EMITIDA",
                    "detalle": {"estudiante": nombre},
                }
            )
        if a.aceptado_en:
            eventos.append(
                {
                    "fecha": a.aceptado_en.isoformat(),
                    "tipo": "INVITACION_ACEPTADA",
                    "detalle": {"estudiante": nombre},
                }
            )
    for p in bd.query(EventoPush).filter(EventoPush.repositorio_id == repo.id):
        if p.divergido:
            tipo = "HISTORIA_REESCRITA"
        elif p.before_sha == SHA_CEROS:
            tipo = "RAMA_CREADA"
        elif p.after_sha == SHA_CEROS:
            tipo = "RAMA_BORRADA"
        else:
            continue
        eventos.append(
            {
                "fecha": p.recibido_en.isoformat(),
                "tipo": tipo,
                "detalle": {
                    "ref": p.ref,
                    "before": p.before_sha,
                    "after": p.after_sha,
                    "n_commits_huerfanos": p.n_commits_huerfanos,
                },
            }
        )
    for b in bd.query(Bitacora).filter(
        Bitacora.entidad == "repositorio",
        Bitacora.entidad_id == str(repo.id),
        Bitacora.accion == "REPOSITORIO_ESTADO",
    ):
        if (b.despues or {}).get("estado") == "ARCHIVADO":
            eventos.append({"fecha": b.creado_en.isoformat(), "tipo": "ARCHIVADO", "detalle": {}})
        elif (b.antes or {}).get("estado") == "ARCHIVADO":
            eventos.append(
                {"fecha": b.creado_en.isoformat(), "tipo": "DESARCHIVADO", "detalle": {}}
            )
    return sorted(eventos, key=lambda e: e["fecha"])


# --- Hitos manuales (S10.9.3 regla e) ---


class HitoEntrada(BaseModel):
    nota: str = Field(min_length=1, max_length=140)


def _commit(bd: Session, repo: Repositorio, sha: str) -> Commit:
    fila = (
        bd.query(Commit).filter(Commit.repositorio_id == repo.id, Commit.sha == sha).one_or_none()
    )
    if fila is None:
        raise HTTPException(status_code=404)
    return fila


@router.post(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/repos/{repo_id}/commits/{sha}/hito",
    dependencies=[Depends(exigir_csrf)],
)
def marcar_hito(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    repo_id: uuid.UUID,
    sha: str,
    datos: HitoEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.TAREA_ADMINISTRAR)),
) -> dict[str, bool]:
    _, _, repo, _ = _contexto(bd, curso_id, tarea_id, repo_id)
    commit = _commit(bd, repo, sha)
    registrar_bitacora(
        bd,
        accion="HITO_MARCADO",
        entidad="commit",
        entidad_id=str(commit.id),
        actor_usuario_id=membresia.usuario_id,
        curso_id=curso_id,
        despues={"nota": datos.nota.strip()},
    )
    return {"ok": True}


@router.delete(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/repos/{repo_id}/commits/{sha}/hito",
    dependencies=[Depends(exigir_csrf)],
)
def desmarcar_hito(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    repo_id: uuid.UUID,
    sha: str,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.TAREA_ADMINISTRAR)),
) -> dict[str, bool]:
    """El desmarcado es logico: queda en la bitacora, no se borra nada."""
    _, _, repo, _ = _contexto(bd, curso_id, tarea_id, repo_id)
    commit = _commit(bd, repo, sha)
    registrar_bitacora(
        bd,
        accion="HITO_DESMARCADO",
        entidad="commit",
        entidad_id=str(commit.id),
        actor_usuario_id=membresia.usuario_id,
        curso_id=curso_id,
    )
    return {"ok": True}
