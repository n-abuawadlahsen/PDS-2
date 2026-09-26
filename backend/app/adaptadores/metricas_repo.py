"""Motor de metricas de seguimiento: `agregar_metricas` (SPEC 10 S10.4-S10.6;
A-114, A-118 a A-124, A-171, A-221; Etapa F6).

Cada ciclo, siempre los tres pasos y en este orden: reatribucion, recomputo de
agregados y evaluacion de alertas (S10.4.1), mas el `resumen_tarea` del que
se pinta la parte superior del tablero. Los agregados se sincronizan fila a
fila con lo recalculado: una segunda ejecucion no cambia ninguna (CA-10.4-01).

Decisiones documentadas:
- Se recomputa el curso entero en cada ciclo (no solo los ultimos 2 dias): a la
  escala de un curso (cientos de repositorios) cuesta poco y deja el pase
  nocturno y el de 10 minutos con el mismo resultado.
- `SIN_PARTICIPACION` no se pronuncia sobre una ventana observada mas corta que
  el umbral del curso, igual que `SIN_ACTIVIDAD`: al primer dia de una entrega
  todos tienen cero commits y marcarlos seria acusar sin evidencia (P4).
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Hashable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.adaptadores import actividad_repo, aprovisionamiento_repo, incidencia_repo, trabajos_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_actividad import AutoriaCommit, Commit, IdentidadGit
from app.adaptadores.modelos_aprovisionamiento import (
    AccesoRepositorio,
    FechaEfectiva,
    Repositorio,
    Sujeto,
)
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_infraestructura import Incidencia
from app.adaptadores.modelos_metricas import (
    MetricaRepositorioDia,
    ParticipacionEntrega,
    ResumenTarea,
)
from app.adaptadores.modelos_padron import Estudiante, PertenenciaGrupo
from app.adaptadores.modelos_tarea import Entrega, Tarea
from app.adaptadores.modelos_version import VersionEntrega
from app.dominio.actividad import normalizar_email
from app.dominio.estados import (
    EstadoAccesoRepositorio,
    EstadoFechaEfectiva,
    EstadoIdentidadGit,
    EstadoTarea,
    MotivoExclusionCommit,
    ReglaAtribucion,
    WorkflowStatePertenenciaGrupo,
)
from app.dominio.metricas import (
    SujetoEntrega,
    Ventana,
    causa_sin_participacion,
    dia_del_curso,
    en_ventana,
    estado_entrega,
    evaluar_actividad,
    umbral_aplicable,
    ventana_entrega,
)
from app.dominio.versiones import EntregaDelSujeto, entrega_anterior

TIPO_AGREGAR = "agregar_metricas"
_NS_PARTICIPACION = uuid.UUID("6f0a1c2e-5d7b-4c1a-9e3f-2b8d4a6c0f11")
_TAREAS_CON_SEGUIMIENTO = (
    EstadoTarea.ACTIVA.value,
    EstadoTarea.INCONSISTENTE.value,
    EstadoTarea.CERRADA.value,
    EstadoTarea.ARCHIVADA.value,
)


def encolar(bd: Session, *, curso_id: uuid.UUID, motivo: str) -> None:
    """S10.3.4 regla 5, S10.6.6: recomputo inmediato tras una correccion de
    atribucion o un cambio de fecha."""
    trabajos_repo.encolar(
        bd,
        tipo=TIPO_AGREGAR,
        clave_idempotencia=f"metricas:{curso_id}:{motivo}",
        max_intentos=2,
        curso_id=curso_id,
    )


# --- Lectura compartida: commits, integrantes y participacion por rango ---


@dataclass(frozen=True)
class CommitResumen:
    """Lo que las metricas necesitan de un commit, con sus acreditados."""

    id: uuid.UUID
    sha: str
    fecha: datetime
    contable: bool
    es_merge: bool
    autor_es_bot: bool
    autor_es_docente: bool
    acreditados: frozenset[uuid.UUID]
    sin_atribuir: bool
    adiciones: int | None
    eliminaciones: int | None


def commits_de_repositorio(bd: Session, repositorio: Repositorio) -> list[CommitResumen]:
    """Todos los commits del repositorio, cada uno con los estudiantes que lo
    acreditan segun `autoria_commit` (nunca `commit.estudiante_id`)."""
    acreditados: dict[uuid.UUID, set[uuid.UUID]] = defaultdict(set)
    for commit_id, estudiante_id in (
        bd.query(AutoriaCommit.commit_id, AutoriaCommit.estudiante_id)
        .join(Commit, Commit.id == AutoriaCommit.commit_id)
        .filter(Commit.repositorio_id == repositorio.id, AutoriaCommit.estudiante_id.isnot(None))
    ):
        acreditados[commit_id].add(estudiante_id)
    no_es_estudiante = {
        i.id
        for i in bd.query(IdentidadGit).filter(
            IdentidadGit.repositorio_id == repositorio.id,
            IdentidadGit.estado == EstadoIdentidadGit.NO_ES_ESTUDIANTE.value,
        )
    }
    salida = []
    for c in bd.query(Commit).filter(Commit.repositorio_id == repositorio.id):
        salida.append(
            CommitResumen(
                id=c.id,
                sha=c.sha,
                fecha=c.fecha_committer,
                contable=c.motivo_exclusion == MotivoExclusionCommit.NINGUNO.value,
                es_merge=c.motivo_exclusion == MotivoExclusionCommit.MERGE.value,
                autor_es_bot=c.autor_es_bot,
                autor_es_docente=c.autor_es_docente,
                acreditados=frozenset(acreditados.get(c.id, set())),
                sin_atribuir=(
                    c.regla_atribucion == ReglaAtribucion.SIN_ATRIBUIR.value
                    and c.identidad_git_id is not None
                    and not c.autor_es_bot
                    and _identidad_sigue_sin_resolver(bd, c, no_es_estudiante)
                ),
                adiciones=c.adiciones,
                eliminaciones=c.eliminaciones,
            )
        )
    return salida


def _identidad_sigue_sin_resolver(bd: Session, c: Commit, no_es_estudiante: set[uuid.UUID]) -> bool:
    email = normalizar_email(c.autor_email)
    vigente = actividad_repo.identidad_vigente(bd, c.repositorio_id, email) if email else None
    return vigente is None or vigente.id not in no_es_estudiante


@dataclass(frozen=True)
class Integrante:
    estudiante_id: uuid.UUID
    nombre: str
    estado: str
    activa_desde: datetime | None
    activa_hasta: datetime | None


def integrantes_de_sujeto(bd: Session, sujeto: Sujeto) -> list[Integrante]:
    """El estudiante de un sujeto individual, o todos los que estuvieron
    `accepted` en el grupo, con su intervalo de pertenencia (S10.6.2)."""
    if sujeto.grupo_id is None:
        estudiante = bd.get(Estudiante, sujeto.estudiante_id)
        if estudiante is None:
            return []
        return [Integrante(estudiante.id, estudiante.nombre, estudiante.estado, None, None)]
    return [
        Integrante(e.id, e.nombre, e.estado, pg.activa_desde, pg.activa_hasta)
        for e, pg in bd.query(Estudiante, PertenenciaGrupo)
        .join(PertenenciaGrupo, PertenenciaGrupo.estudiante_id == Estudiante.id)
        .filter(
            PertenenciaGrupo.grupo_id == sujeto.grupo_id,
            PertenenciaGrupo.workflow_state == WorkflowStatePertenenciaGrupo.ACCEPTED.value,
        )
        .order_by(Estudiante.nombre_ordenable, Estudiante.nombre)
    ]


@dataclass(frozen=True)
class FilaParticipacion:
    estudiante_id: uuid.UUID
    commits: int
    adiciones: int | None
    eliminaciones: int | None
    dias_activos: int
    primer_commit_en: datetime | None
    ultimo_commit_en: datetime | None
    commits_coautorados: int
    ventana: Ventana


def participacion(
    commits: list[CommitResumen],
    integrantes: list[Integrante],
    *,
    ventana_sujeto: Ventana,
    zona: str,
) -> tuple[list[FilaParticipacion], int]:
    """La unica funcion de participacion (P2): la usan el recomputo, la
    comparacion del tablero y la franja del timeline. Devuelve las filas por
    integrante --ventana recortada a su pertenencia-- y los commits sin
    atribuir del repositorio en la ventana del sujeto. La coautoria pesa 1
    completo por persona; las lineas van solo al autor git."""
    filas = []
    for i in integrantes:
        inicio = (
            max(ventana_sujeto.inicio, i.activa_desde) if i.activa_desde else ventana_sujeto.inicio
        )
        fin = min(ventana_sujeto.fin, i.activa_hasta) if i.activa_hasta else ventana_sujeto.fin
        ventana = Ventana(inicio=inicio, fin=max(fin, inicio))
        propios = [
            c
            for c in commits
            if c.contable and i.estudiante_id in c.acreditados and en_ventana(c.fecha, ventana)
        ]
        con_lineas = [c for c in propios if c.adiciones is not None]
        filas.append(
            FilaParticipacion(
                estudiante_id=i.estudiante_id,
                commits=len(propios),
                adiciones=sum(c.adiciones or 0 for c in con_lineas) if con_lineas else None,
                eliminaciones=sum(c.eliminaciones or 0 for c in con_lineas) if con_lineas else None,
                dias_activos=len({dia_del_curso(c.fecha, zona) for c in propios}),
                primer_commit_en=min((c.fecha for c in propios), default=None),
                ultimo_commit_en=max((c.fecha for c in propios), default=None),
                commits_coautorados=0,  # sin GraphQL no hay co-autores (S10.3.3 regla 7)
                ventana=ventana,
            )
        )
    sin_atribuir = sum(
        1 for c in commits if c.contable and c.sin_atribuir and en_ventana(c.fecha, ventana_sujeto)
    )
    return filas, sin_atribuir


def fechas_del_sujeto(
    bd: Session, tarea_id: uuid.UUID, sujeto_id: uuid.UUID
) -> list[EntregaDelSujeto]:
    """Las entregas de la tarea con la fecha efectiva vigente de ese sujeto."""
    return [
        EntregaDelSujeto(entrega_id=e_id, orden=orden, due_at=due)
        for e_id, orden, due in bd.query(Entrega.id, Entrega.orden, FechaEfectiva.due_at_utc)
        .join(FechaEfectiva, FechaEfectiva.entrega_id == Entrega.id)
        .filter(
            Entrega.tarea_id == tarea_id,
            FechaEfectiva.sujeto_id == sujeto_id,
            FechaEfectiva.estado == EstadoFechaEfectiva.VIGENTE.value,
        )
    ]


def ventana_de(
    fechas: list[EntregaDelSujeto],
    entrega_id: uuid.UUID,
    repositorio: Repositorio,
    ahora: datetime,
) -> Ventana | None:
    """S10.6.2-S10.6.3 por sujeto; `None` si la entrega no aplica al sujeto."""
    propia = next((f for f in fechas if f.entrega_id == entrega_id), None)
    if propia is None:
        return None
    anterior_id = entrega_anterior(fechas, actual=entrega_id)
    anterior = next((f for f in fechas if f.entrega_id == anterior_id), None)
    return ventana_entrega(
        due_anterior=anterior.due_at if anterior is not None else None,
        repositorio_creado_en=repositorio.listo_en or repositorio.creado_en,
        due_actual=propia.due_at,
        ahora=ahora,
    )


def entrega_vigente(fechas: list[EntregaDelSujeto], ahora: datetime) -> Hashable | None:
    """S10.7.4: la de menor `orden` cuya fecha aun no vence; si todas
    vencieron, la ultima."""
    ordenadas = sorted(fechas, key=lambda f: f.orden)
    abiertas = [f for f in ordenadas if f.due_at is None or f.due_at > ahora]
    if abiertas:
        return abiertas[0].entrega_id
    return ordenadas[-1].entrega_id if ordenadas else None


# --- Paso 1: reatribucion (S10.3.4) ---


def reatribuir(bd: Session, curso: Curso) -> int:
    contexto = actividad_repo.contexto_curso(bd, curso.id)
    cambios = 0
    repositorios = {r.id: r for r in bd.query(Repositorio).filter(Repositorio.curso_id == curso.id)}
    for commit in bd.query(Commit).filter(
        Commit.repositorio_id.in_(list(repositorios)),
        Commit.regla_atribucion != ReglaAtribucion.AUTOR_GITHUB.value,
        Commit.n_padres.isnot(None),
    ):
        if actividad_repo.atribuir_commit(
            bd, commit, repositorios[commit.repositorio_id], contexto, solo_si_mejora=True
        ):
            cambios += 1
    return cambios


# --- Paso 2: agregados ---


def _sincronizar(
    bd: Session,
    existentes: Any,
    deseadas: dict[Hashable, dict[str, Any]],
    crear: Any,
) -> None:
    """Sustituye lo recalculado sin tocar las filas que no cambiaron."""
    for clave, valores in deseadas.items():
        fila = existentes.get(clave)
        if fila is None:
            bd.add(crear(**valores))
            continue
        for columna, valor in valores.items():
            if getattr(fila, columna) != valor:
                setattr(fila, columna, valor)
    for clave, fila in existentes.items():
        if clave not in deseadas:
            bd.delete(fila)
    bd.flush()


def recomputar(
    bd: Session, curso: Curso, *, ahora: datetime
) -> dict[uuid.UUID, list[CommitResumen]]:
    """`metrica_repositorio_dia` y `participacion_entrega` del curso."""
    repositorios = (
        bd.query(Repositorio)
        .filter(Repositorio.curso_id == curso.id, Repositorio.github_repo_id.isnot(None))
        .all()
    )
    por_repo = {r.id: commits_de_repositorio(bd, r) for r in repositorios}

    deseadas_dia: dict[Hashable, dict[str, Any]] = {}
    for repo in repositorios:
        dias: dict[date, dict[str, int]] = defaultdict(
            lambda: {
                "commits": 0,
                "commits_estudiantiles": 0,
                "commits_excluidos": 0,
                "commits_merge": 0,
                "commits_de_bot": 0,
                "commits_docentes": 0,
            }
        )
        for c in por_repo[repo.id]:
            cuenta = dias[dia_del_curso(c.fecha, curso.zona_horaria)]
            if c.contable:
                cuenta["commits"] += 1
                cuenta["commits_estudiantiles"] += 1 if c.acreditados else 0
                cuenta["commits_de_bot"] += 1 if c.autor_es_bot else 0
                cuenta["commits_docentes"] += 1 if c.autor_es_docente else 0
            else:
                cuenta["commits_excluidos"] += 1
                cuenta["commits_merge"] += 1 if c.es_merge else 0
        acumulados = 0
        for dia in sorted(dias):
            if dias[dia]["commits"]:
                acumulados += 1
            deseadas_dia[(repo.id, dia)] = {
                "repositorio_id": repo.id,
                "dia": dia,
                **dias[dia],
                "dias_activos_acumulados": acumulados,
            }
    existentes_dia = {
        (m.repositorio_id, m.dia): m
        for m in bd.query(MetricaRepositorioDia).filter(
            MetricaRepositorioDia.repositorio_id.in_([r.id for r in repositorios])
        )
    }
    _sincronizar(bd, existentes_dia, deseadas_dia, MetricaRepositorioDia)

    deseadas_part: dict[Hashable, dict[str, Any]] = {}
    for repo in repositorios:
        sujeto = bd.get(Sujeto, repo.sujeto_id)
        tarea = bd.get(Tarea, repo.tarea_id)
        if sujeto is None or tarea is None or tarea.estado not in _TAREAS_CON_SEGUIMIENTO:
            continue
        fechas = fechas_del_sujeto(bd, tarea.id, sujeto.id)
        integrantes = integrantes_de_sujeto(bd, sujeto)
        for f in fechas:
            ventana = ventana_de(fechas, f.entrega_id, repo, ahora)  # type: ignore[arg-type]
            if ventana is None:
                continue
            filas, sin_atribuir = participacion(
                por_repo[repo.id], integrantes, ventana_sujeto=ventana, zona=curso.zona_horaria
            )
            for fila in filas:
                deseadas_part[(f.entrega_id, repo.id, fila.estudiante_id)] = {
                    "entrega_id": f.entrega_id,
                    "repositorio_id": repo.id,
                    "estudiante_id": fila.estudiante_id,
                    "commits": fila.commits,
                    "adiciones": fila.adiciones,
                    "eliminaciones": fila.eliminaciones,
                    "dias_activos": fila.dias_activos,
                    "primer_commit_en": fila.primer_commit_en,
                    "ultimo_commit_en": fila.ultimo_commit_en,
                    "commits_coautorados": fila.commits_coautorados,
                    "commits_sin_atribuir_repo": sin_atribuir,
                    "ventana_inicio": fila.ventana.inicio,
                    "ventana_fin": fila.ventana.fin,
                }
    existentes_part = {
        (p.entrega_id, p.repositorio_id, p.estudiante_id): p
        for p in bd.query(ParticipacionEntrega).filter(
            ParticipacionEntrega.repositorio_id.in_([r.id for r in repositorios])
        )
    }
    _sincronizar(bd, existentes_part, deseadas_part, ParticipacionEntrega)
    return por_repo


# --- Paso 3: alertas (S10.4.3, S10.5.3) ---


@dataclass(frozen=True)
class EstadoActividadRepo:
    repositorio_id: uuid.UUID
    estado: str  # SIN_DATOS_TODAVIA | SIN_DATO_SUFICIENTE | SIN_ACTIVIDAD | CON_ACTIVIDAD
    dias_observados: int
    umbral_dias: int
    ultimo_commit_estudiantil: datetime | None


def estado_actividad(
    bd: Session,
    curso: Curso,
    repositorio: Repositorio,
    commits: list[CommitResumen],
    *,
    ahora: datetime,
) -> EstadoActividadRepo:
    """Una sola evaluacion para el tablero, Pendientes y el informe (P2)."""
    proximo = (
        bd.query(FechaEfectiva.due_at_utc)
        .filter(
            FechaEfectiva.sujeto_id == repositorio.sujeto_id,
            FechaEfectiva.estado == EstadoFechaEfectiva.VIGENTE.value,
            FechaEfectiva.due_at_utc > ahora,
        )
        .order_by(FechaEfectiva.due_at_utc)
        .first()
    )
    umbral = umbral_aplicable(
        curso.umbral_dias_sin_actividad, proximo_cierre=proximo[0] if proximo else None, ahora=ahora
    )
    ultimo = max((c.fecha for c in commits if c.contable and c.acreditados), default=None)
    if not actividad_repo.espejo_fiable(bd, repositorio):
        # S10.7.7: «sin datos todavia»; nunca abre una alerta.
        return EstadoActividadRepo(repositorio.id, "SIN_DATOS_TODAVIA", 0, umbral, ultimo)
    desde = max(
        t
        for t in (repositorio.listo_en or repositorio.creado_en, curso.ingesta_actividad_desde)
        if t is not None
    )
    resultado = evaluar_actividad(
        observado_desde=desde, ultimo_commit_estudiantil=ultimo, umbral_dias=umbral, ahora=ahora
    )
    return EstadoActividadRepo(
        repositorio.id, resultado.estado, resultado.dias_observados, umbral, ultimo
    )


def clave_participacion(repositorio_id: uuid.UUID, estudiante_id: uuid.UUID) -> uuid.UUID:
    """`incidencia.sujeto_id` de un `SIN_PARTICIPACION`: el par repositorio y
    estudiante, determinista para que reevaluar no abra una segunda fila."""
    return uuid.uuid5(_NS_PARTICIPACION, f"{repositorio_id}:{estudiante_id}")


def evaluar_alertas(
    bd: Session, curso: Curso, por_repo: dict[uuid.UUID, list[CommitResumen]], *, ahora: datetime
) -> None:
    abiertas_actividad: set[uuid.UUID] = set()
    abiertas_participacion: set[uuid.UUID] = set()
    for repo in actividad_repo.repositorios_en_ingesta(bd, curso):
        commits = por_repo.get(repo.id, [])
        estado = estado_actividad(bd, curso, repo, commits, ahora=ahora)
        sujeto = bd.get(Sujeto, repo.sujeto_id)
        tarea = bd.get(Tarea, repo.tarea_id)
        assert sujeto is not None and tarea is not None
        if estado.estado == "SIN_ACTIVIDAD":
            abiertas_actividad.add(repo.id)
            if (
                incidencia_repo.abierta(
                    bd, tipo="SIN_ACTIVIDAD", curso_id=curso.id, sujeto_id=repo.id
                )
                is None
            ):
                incidencia_repo.abrir_o_actualizar(
                    bd,
                    tipo="SIN_ACTIVIDAD",
                    severidad="ADVERTENCIA",
                    sujeto_tipo="REPOSITORIO",
                    curso_id=curso.id,
                    sujeto_id=repo.id,
                    detalle={
                        "repositorio": repo.nombre,
                        "tarea_id": str(tarea.id),
                        "umbral_dias": estado.umbral_dias,
                        "ultimo_commit_en": estado.ultimo_commit_estudiantil.isoformat()
                        if estado.ultimo_commit_estudiantil
                        else None,
                    },
                )
        if estado.estado in ("SIN_DATOS_TODAVIA", "SIN_DATO_SUFICIENTE"):
            continue
        fechas = fechas_del_sujeto(bd, tarea.id, sujeto.id)
        vigente = entrega_vigente(fechas, ahora)
        if vigente is None:
            continue
        ventana = ventana_de(fechas, vigente, repo, ahora)  # type: ignore[arg-type]
        if ventana is None or ahora - ventana.inicio < timedelta(
            days=curso.umbral_dias_sin_actividad
        ):
            continue
        filas, sin_atribuir = participacion(
            commits,
            integrantes_de_sujeto(bd, sujeto),
            ventana_sujeto=ventana,
            zona=curso.zona_horaria,
        )
        accesos = {
            a.estudiante_id: a.estado
            for a in bd.query(AccesoRepositorio).filter(AccesoRepositorio.repositorio_id == repo.id)
        }
        estados = {i.estudiante_id: i for i in integrantes_de_sujeto(bd, sujeto)}
        for fila in filas:
            integrante = estados[fila.estudiante_id]
            if integrante.estado not in ("ACTIVO", "INVITADO") or integrante.activa_hasta:
                continue  # retirado o fuera del grupo: fuera de las alertas (S10.10.2)
            causa = causa_sin_participacion(
                acceso=accesos.get(fila.estudiante_id),
                commits=fila.commits,
                hay_sin_atribuir=sin_atribuir > 0,
            )
            if causa is None:
                continue
            clave = clave_participacion(repo.id, fila.estudiante_id)
            abiertas_participacion.add(clave)
            detalle = {
                "causa": causa,
                "estudiante": integrante.nombre,
                "estudiante_id": str(fila.estudiante_id),
                "repositorio": repo.nombre,
                "repositorio_id": str(repo.id),
                "tarea_id": str(tarea.id),
                "entrega_id": str(vigente),
            }
            actual = incidencia_repo.abierta(
                bd, tipo="SIN_PARTICIPACION", curso_id=curso.id, sujeto_id=clave
            )
            if actual is None or actual.detalle != detalle:
                incidencia_repo.abrir_o_actualizar(
                    bd,
                    tipo="SIN_PARTICIPACION",
                    severidad="ADVERTENCIA",
                    sujeto_tipo="PARTICIPACION",
                    curso_id=curso.id,
                    sujeto_id=clave,
                    detalle=detalle,
                )
    for tipo, abiertas in (
        ("SIN_ACTIVIDAD", abiertas_actividad),
        ("SIN_PARTICIPACION", abiertas_participacion),
    ):
        for inc in bd.query(Incidencia).filter(
            Incidencia.curso_id == curso.id, Incidencia.tipo == tipo, Incidencia.abierta.is_(True)
        ):
            if inc.sujeto_id not in abiertas:
                # Cerrada por el sistema; nunca se borra (P6).
                inc.abierta = False
                inc.resuelta_en = ahora
                inc.detalle = {**inc.detalle, "resuelta_por": "SISTEMA"}
    bd.flush()


# --- Resumen de la tarea (S10.4.2, S10.6.1, S10.7.1) ---


def resumen_de_tarea(bd: Session, tarea: Tarea, *, ahora: datetime) -> dict[str, Any]:
    entregas = []
    for entrega in bd.query(Entrega).filter(Entrega.tarea_id == tarea.id).order_by(Entrega.orden):
        fechas = {
            f.sujeto_id: f.due_at_utc
            for f in bd.query(FechaEfectiva).filter(
                FechaEfectiva.entrega_id == entrega.id,
                FechaEfectiva.estado == EstadoFechaEfectiva.VIGENTE.value,
            )
        }
        versiones = {
            v.sujeto_id: v.estado
            for v in bd.query(VersionEntrega).filter(
                VersionEntrega.entrega_id == entrega.id, VersionEntrega.vigente.is_(True)
            )
        }
        sujetos = [SujetoEntrega(due, versiones.get(s)) for s, due in fechas.items()]
        conteo: dict[str, int] = defaultdict(int)
        for estado in versiones.values():
            conteo[estado] += 1
        entregas.append(
            {
                "entrega_id": str(entrega.id),
                "orden": entrega.orden,
                "nombre": entrega.nombre,
                "tipo": entrega.tipo,
                "estado": estado_entrega(
                    estado_validacion=entrega.estado_validacion,
                    publicada=entrega.publicada,
                    sujetos=sujetos,
                    ahora=ahora,
                ).value,
                "due_at_base": entrega.due_at_base.isoformat() if entrega.due_at_base else None,
                "fechas_distintas": len({d for d in fechas.values() if d is not None}),
                "sujetos": len(fechas),
                "cerrados": sum(1 for d in fechas.values() if d is not None and d <= ahora),
                "sin_fecha": sum(1 for d in fechas.values() if d is None),
                "versiones_registradas": sum(conteo.values()),
                "por_estado_version": dict(conteo),
            }
        )
    resumen = aprovisionamiento_repo.resumen_repositorios(bd, tarea_id=tarea.id)
    invitaciones = (
        bd.query(AccesoRepositorio)
        .join(Repositorio, Repositorio.id == AccesoRepositorio.repositorio_id)
        .filter(
            Repositorio.tarea_id == tarea.id,
            AccesoRepositorio.estado == EstadoAccesoRepositorio.INVITADO.value,
        )
        .count()
    )
    return {
        "entregas": entregas,
        "repositorios": resumen.__dict__,
        "invitaciones_sin_aceptar": invitaciones,
    }


def recomputar_resumenes(bd: Session, curso: Curso, *, ahora: datetime) -> None:
    for tarea in bd.query(Tarea).filter(
        Tarea.curso_id == curso.id, Tarea.estado.in_(_TAREAS_CON_SEGUIMIENTO)
    ):
        contadores = resumen_de_tarea(bd, tarea, ahora=ahora)
        fila = bd.query(ResumenTarea).filter(ResumenTarea.tarea_id == tarea.id).one_or_none()
        if fila is None:
            bd.add(ResumenTarea(tarea_id=tarea.id, calculado_en=ahora, contadores=contadores))
        elif fila.contadores != contadores:
            fila.contadores = contadores
            fila.calculado_en = ahora
    bd.flush()


def agregar_metricas(bd: Session, *, curso: Curso, ahora: datetime | None = None) -> None:
    """S10.4.1: reatribucion, recomputo y alertas, siempre en este orden."""
    ahora = ahora or ahora_utc()
    reatribuir(bd, curso)
    por_repo = recomputar(bd, curso, ahora=ahora)
    evaluar_alertas(bd, curso, por_repo, ahora=ahora)
    recomputar_resumenes(bd, curso, ahora=ahora)
