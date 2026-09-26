"""Tablero de la tarea, comparacion y vista de seguimiento del curso (SPEC 10
S10.6-S10.8, S10.10.5-S10.10.6; Etapa F6).

Todo se pinta del espejo y de los agregados: ninguna vista llama a GitHub ni a
Canvas, y cada respuesta lo declara con `X-Llamadas-Externas: 0` (P1). Las
cifras salen de las mismas funciones de dominio que usan el timeline y el
informe diario (P2).
"""

from __future__ import annotations

import csv
import io
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.adaptadores import aprovisionamiento_repo, metricas_repo, trabajos_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.bitacora_repo import registrar as registrar_bitacora
from app.adaptadores.modelos_actividad import Commit
from app.adaptadores.modelos_aprovisionamiento import AccesoRepositorio, Repositorio, Sujeto
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_infraestructura import CursorSincronizacion, Incidencia, Trabajo
from app.adaptadores.modelos_metricas import ResumenTarea
from app.adaptadores.modelos_padron import Estudiante, Grupo, Matricula, Seccion
from app.adaptadores.modelos_tarea import Entrega, Tarea
from app.api.dependencias import exigir_csrf, obtener_sesion_bd, requiere
from app.dominio.estados import EstadoTarea, ModalidadTarea
from app.dominio.metricas import (
    Ventana,
    causa_sin_participacion,
    cuartiles,
    dia_del_curso,
    en_ventana,
    indice_desequilibrio,
    progreso_frente_al_cierre,
    racha_sin_actividad,
    senal_reparto_concentrado,
)
from app.dominio.permisos import Permiso

router = APIRouter(tags=["tablero"])

DEFINICION_COMMIT_CONTABLE = (
    "Commit contable: todo commit del repositorio salvo merges, el commit inicial de la "
    "plantilla y los que dejaron de ser alcanzables tras reescribir la historia. Los de bots "
    "y del equipo docente cuentan."
)
AVISO_ALCANCE = (
    "La participación se mide por commits atribuidos; la actividad en issues, pull requests "
    "y revisiones no se recopila."
)
COOLDOWN_TAREA = timedelta(minutes=5)
COOLDOWN_USUARIO = timedelta(minutes=2)
TAMANO_PAGINA = 50

# S10.7.2: seis segmentos de la barra, mas tres fuera de ella.
_GRUPO_ESTADO = {
    "OPERATIVO": "LISTOS",
    "DEGRADADO": "FUNCIONANDO_INCOMPLETO",
    "ESPERANDO_INFORMACION": "FALTA_INFORMACION",
    "LISTO_PARA_CREAR": "EN_CURSO",
    "CREANDO": "EN_CURSO",
    "CREADO_SIN_CONTENIDO": "EN_CURSO",
    "CONTENIDO_LISTO": "EN_CURSO",
    "CONFIGURANDO_ACCESOS": "EN_CURSO",
    "ERROR_TRANSITORIO": "ESPERANDO",
    "ESPERANDO_LIMITE": "ESPERANDO",
    "BLOQUEADO": "ESPERANDO",
    "ERROR_PERMANENTE": "REQUIERE_ACCION",
    "FUERA_DE_ALCANCE": "FUERA_DE_ALCANCE",
    "ARCHIVADO": "ARCHIVADO",
    "INACCESIBLE": "INACCESIBLE",
}


def _tarea(bd: Session, curso_id: uuid.UUID, tarea_id: uuid.UUID) -> tuple[Curso, Tarea]:
    tarea = bd.query(Tarea).filter(Tarea.id == tarea_id, Tarea.curso_id == curso_id).one_or_none()
    curso = bd.get(Curso, curso_id)
    if tarea is None or curso is None:
        raise HTTPException(status_code=404)
    return curso, tarea


# --- Periodos (S10.7.4) ---


class PeriodoSalida(BaseModel):
    clave: str
    etiqueta: str


def _periodos(bd: Session, tarea: Tarea) -> list[PeriodoSalida]:
    entregas = bd.query(Entrega).filter(Entrega.tarea_id == tarea.id).order_by(Entrega.orden).all()
    salida = []
    for i, e in enumerate(entregas):
        etiqueta = (
            f"hasta la entrega {e.orden}"
            if i == 0
            else f"entre la entrega {entregas[i - 1].orden} y la {e.orden}"
        )
        salida.append(PeriodoSalida(clave=f"entrega:{e.id}", etiqueta=f"{etiqueta}: {e.nombre}"))
    if entregas:
        salida.append(PeriodoSalida(clave="posterior", etiqueta="Después del cierre final"))
    salida.append(PeriodoSalida(clave="30d", etiqueta="Últimos 30 días"))
    salida.append(PeriodoSalida(clave="todo", etiqueta="Todo"))
    return salida


def _periodo_por_defecto(bd: Session, tarea: Tarea, ahora: datetime) -> str:
    """La entrega vigente: la de menor orden cuya fecha efectiva maxima aun no
    vence, o la final si todas vencieron."""
    entregas = bd.query(Entrega).filter(Entrega.tarea_id == tarea.id).order_by(Entrega.orden).all()
    if not entregas:
        return "30d"
    for e in entregas:
        resumen = next(
            (x for x in _contadores(bd, tarea).get("entregas", []) if x["entrega_id"] == str(e.id)),
            None,
        )
        if resumen is None or resumen["cerrados"] < resumen["sujetos"] or resumen["sujetos"] == 0:
            return f"entrega:{e.id}"
    return f"entrega:{entregas[-1].id}"


def _rango(
    periodo: str,
    fechas: list[Any],
    repositorio: Repositorio,
    ahora: datetime,
) -> Ventana | None:
    """El periodo elegido, por sujeto (S10.6.3). `None` = no aplica."""
    creado = repositorio.listo_en or repositorio.creado_en
    if periodo.startswith("entrega:"):
        return metricas_repo.ventana_de(
            fechas, uuid.UUID(periodo.split(":", 1)[1]), repositorio, ahora
        )
    if periodo == "posterior":
        ultimo = max((f.due_at for f in fechas if f.due_at is not None), default=None)
        if ultimo is None or ultimo >= ahora:
            return None
        return Ventana(inicio=ultimo, fin=ahora)
    if periodo == "30d":
        return Ventana(inicio=ahora - timedelta(days=30), fin=ahora)
    return Ventana(inicio=creado - timedelta(seconds=1), fin=ahora)


def _contadores(bd: Session, tarea: Tarea) -> dict[str, Any]:
    fila = bd.query(ResumenTarea).filter(ResumenTarea.tarea_id == tarea.id).one_or_none()
    return fila.contadores if fila is not None else {}


# --- Filas del bloque 5 ---


class IntegranteSalida(BaseModel):
    estudiante_id: uuid.UUID
    nombre: str
    commits: int
    dias_activos: int
    adiciones: int | None
    eliminaciones: int | None
    causa: str | None
    retirado: bool
    en_grupo_desde: datetime | None
    salio_del_grupo: datetime | None


class FilaTableroSalida(BaseModel):
    repositorio_id: uuid.UUID
    nombre: str
    sujeto: str
    sujeto_tipo: str
    seccion: str | None
    estado: str
    grupo_estado: str
    motivo: str | None
    no_aplica: bool
    actividad: str
    dias_observados: int
    umbral_dias: int
    commits_periodo: int
    commits_sin_atribuir: int
    dias_desde_ultimo_commit: int | None
    sparkline: list[int]
    alertas: list[str]
    integrantes: list[IntegranteSalida]
    indice_desequilibrio: int | None
    reparto_concentrado: bool
    ultimo_commit_antes_del_cierre: datetime | None
    cierre: datetime | None


def _filas(
    bd: Session, curso: Curso, tarea: Tarea, periodo: str, ahora: datetime
) -> list[FilaTableroSalida]:
    silenciadas_o_cerradas = {
        (i.tipo, i.sujeto_id)
        for i in bd.query(Incidencia).filter(
            Incidencia.curso_id == curso.id,
            Incidencia.tipo.in_(["SIN_ACTIVIDAD", "SIN_PARTICIPACION"]),
            Incidencia.abierta.is_(True),
            Incidencia.silenciada.is_(False),
        )
    }
    hoy = dia_del_curso(ahora, curso.zona_horaria)
    filas = []
    consulta = (
        bd.query(Repositorio, Sujeto)
        .join(Sujeto, Sujeto.id == Repositorio.sujeto_id)
        .filter(Repositorio.tarea_id == tarea.id, Repositorio.github_repo_id.isnot(None))
    )
    for repo, sujeto in consulta:
        commits = metricas_repo.commits_de_repositorio(bd, repo)
        fechas = metricas_repo.fechas_del_sujeto(bd, tarea.id, sujeto.id)
        rango = _rango(periodo, fechas, repo, ahora)
        integrantes = metricas_repo.integrantes_de_sujeto(bd, sujeto)
        actividad = metricas_repo.estado_actividad(bd, curso, repo, commits, ahora=ahora)
        accesos = {
            a.estudiante_id: a.estado
            for a in bd.query(AccesoRepositorio).filter(AccesoRepositorio.repositorio_id == repo.id)
        }
        contables = [c for c in commits if c.contable]
        ultimo = max((c.fecha for c in contables), default=None)
        por_dia: dict[Any, int] = defaultdict(int)
        for c in contables:
            por_dia[dia_del_curso(c.fecha, curso.zona_horaria)] += 1
        sparkline = [por_dia.get(hoy - timedelta(days=d), 0) for d in range(29, -1, -1)]
        salida_integrantes: list[IntegranteSalida] = []
        sin_atribuir = 0
        commits_periodo = 0
        if rango is not None:
            partes, sin_atribuir = metricas_repo.participacion(
                commits, integrantes, ventana_sujeto=rango, zona=curso.zona_horaria
            )
            commits_periodo = sum(1 for c in contables if en_ventana(c.fecha, rango))
            por_id = {i.estudiante_id: i for i in integrantes}
            for p in partes:
                i = por_id[p.estudiante_id]
                salida_integrantes.append(
                    IntegranteSalida(
                        estudiante_id=p.estudiante_id,
                        nombre=i.nombre,
                        commits=p.commits,
                        dias_activos=p.dias_activos,
                        adiciones=p.adiciones,
                        eliminaciones=p.eliminaciones,
                        causa=causa_sin_participacion(
                            acceso=accesos.get(p.estudiante_id),
                            commits=p.commits,
                            hay_sin_atribuir=sin_atribuir > 0,
                        ),
                        retirado=i.estado not in ("ACTIVO", "INVITADO"),
                        en_grupo_desde=i.activa_desde if sujeto.grupo_id else None,
                        salio_del_grupo=i.activa_hasta,
                    )
                )
        commits_grupo = [
            i.commits for i in salida_integrantes if not i.retirado and not i.salio_del_grupo
        ]
        con_acceso = sum(
            1
            for i in salida_integrantes
            if accesos.get(i.estudiante_id) in ("ACEPTADO", "ACCESO_DIRECTO")
        )
        alertas = []
        if ("SIN_ACTIVIDAD", repo.id) in silenciadas_o_cerradas:
            alertas.append("SIN_ACTIVIDAD")
        for i in integrantes:
            if (
                "SIN_PARTICIPACION",
                metricas_repo.clave_participacion(repo.id, i.estudiante_id),
            ) in (silenciadas_o_cerradas):
                alertas.append("SIN_PARTICIPACION")
                break
        cierre = rango.fin if rango is not None and periodo.startswith("entrega:") else None
        filas.append(
            FilaTableroSalida(
                repositorio_id=repo.id,
                nombre=repo.nombre,
                sujeto=_nombre_sujeto(bd, sujeto),
                sujeto_tipo=sujeto.tipo,
                seccion=_seccion(bd, sujeto),
                estado=repo.estado,
                grupo_estado=_GRUPO_ESTADO.get(repo.estado, "EN_CURSO"),
                motivo=repo.motivo,
                no_aplica=rango is None,
                actividad=actividad.estado,
                dias_observados=actividad.dias_observados,
                umbral_dias=actividad.umbral_dias,
                commits_periodo=commits_periodo,
                commits_sin_atribuir=sin_atribuir,
                dias_desde_ultimo_commit=racha_sin_actividad(
                    dia_del_curso(ultimo, curso.zona_horaria) if ultimo else None, hoy
                ),
                sparkline=sparkline,
                alertas=alertas,
                integrantes=salida_integrantes,
                indice_desequilibrio=indice_desequilibrio(commits_grupo)
                if tarea.modalidad == ModalidadTarea.GRUPAL.value
                else None,
                reparto_concentrado=tarea.modalidad == ModalidadTarea.GRUPAL.value
                and senal_reparto_concentrado(
                    commits_grupo, con_acceso=con_acceso, umbral_pct=curso.umbral_desbalance_pct
                ),
                ultimo_commit_antes_del_cierre=max(
                    (c.fecha for c in contables if cierre is not None and c.fecha <= cierre),
                    default=None,
                ),
                cierre=cierre,
            )
        )
    return filas


def _nombre_sujeto(bd: Session, sujeto: Sujeto) -> str:
    if sujeto.grupo_id is not None:
        grupo = bd.get(Grupo, sujeto.grupo_id)
        return grupo.nombre if grupo is not None else "—"
    estudiante = bd.get(Estudiante, sujeto.estudiante_id)
    return estudiante.nombre if estudiante is not None else "—"


def _seccion(bd: Session, sujeto: Sujeto) -> str | None:
    if sujeto.estudiante_id is None:
        return None
    fila = (
        bd.query(Seccion.nombre)
        .join(Matricula, Matricula.seccion_id == Seccion.id)
        .filter(Matricula.estudiante_id == sujeto.estudiante_id, Matricula.activa.is_(True))
        .order_by(Seccion.canvas_section_id)
        .first()
    )
    return fila[0] if fila else None


# --- El tablero ---


class DiaSerieSalida(BaseModel):
    dia: str
    commits: int


class TarjetasSalida(BaseModel):
    repositorios_creados: int
    sin_actividad: int
    sin_dato_suficiente: int
    sin_datos_todavia: int
    sin_participacion: dict[str, int]
    invitaciones_sin_aceptar: int
    bloqueantes: int


class PosicionSalida(BaseModel):
    commits: tuple[float, float, float] | None
    dias_activos: tuple[float, float, float] | None
    mediana_por_seccion: dict[str, float]
    sujetos: int
    excluidos: int


class TableroSalida(BaseModel):
    tarea: dict[str, Any]
    procedencia: dict[str, Any]
    periodos: list[PeriodoSalida]
    periodo: str
    entregas: list[dict[str, Any]]
    repositorios: dict[str, Any]
    tarjetas: TarjetasSalida
    serie: list[DiaSerieSalida]
    cierres: list[str]
    histograma_previo_al_cierre: list[DiaSerieSalida]
    progreso_frente_al_cierre: int | None
    posicion_frente_al_curso: PosicionSalida | None
    filas: list[FilaTableroSalida]
    total_filas: int
    pagina: int
    definicion_commit_contable: str
    aviso_alcance: str


@router.get("/api/cursos/{curso_id}/tareas/{tarea_id}/tablero", response_model=TableroSalida)
def tablero(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    response: Response,
    periodo: str | None = None,
    seccion: str | None = None,
    grupo_estado: str | None = None,
    solo_alertas: bool = False,
    pagina: int = Query(1, ge=1),
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> TableroSalida:
    """R2.5.1: una sola pagina de cinco bloques, pintada del espejo."""
    inicio_render = ahora_utc()
    curso, tarea = _tarea(bd, curso_id, tarea_id)
    ahora = ahora_utc()
    periodos = _periodos(bd, tarea)
    periodo = periodo or _periodo_por_defecto(bd, tarea, ahora)
    if periodo not in {p.clave for p in periodos}:
        raise HTTPException(
            status_code=422, detail={"motivo": "PERIODO_INVALIDO", "detalle": periodo}
        )
    todas = _filas(bd, curso, tarea, periodo, ahora)
    filas = [
        f
        for f in todas
        if (seccion is None or f.seccion == seccion)
        and (grupo_estado is None or f.grupo_estado == grupo_estado)
        and (not solo_alertas or f.alertas)
    ]
    filas.sort(
        key=lambda f: (
            -(f.dias_desde_ultimo_commit if f.dias_desde_ultimo_commit is not None else 10**6),
            f.sujeto,
        )
    )
    contadores = _contadores(bd, tarea)
    resumen = aprovisionamiento_repo.resumen_repositorios(bd, tarea_id=tarea.id)
    repos_ids = [f.repositorio_id for f in todas]

    causas: dict[str, int] = defaultdict(int)
    for inc in bd.query(Incidencia).filter(
        Incidencia.curso_id == curso.id,
        Incidencia.tipo == "SIN_PARTICIPACION",
        Incidencia.abierta.is_(True),
        Incidencia.silenciada.is_(False),
    ):
        if inc.detalle.get("tarea_id") == str(tarea.id):
            causas[inc.detalle.get("causa", "SIN_COMMITS")] += 1
    tarjetas = TarjetasSalida(
        repositorios_creados=len(todas),
        sin_actividad=sum(1 for f in todas if "SIN_ACTIVIDAD" in f.alertas),
        sin_dato_suficiente=sum(1 for f in todas if f.actividad == "SIN_DATO_SUFICIENTE"),
        sin_datos_todavia=sum(1 for f in todas if f.actividad == "SIN_DATOS_TODAVIA"),
        sin_participacion=dict(causas),
        invitaciones_sin_aceptar=int(contadores.get("invitaciones_sin_aceptar", 0)),
        bloqueantes=bd.query(Incidencia)
        .filter(
            Incidencia.curso_id == curso.id,
            Incidencia.abierta.is_(True),
            Incidencia.severidad == "BLOQUEANTE",
        )
        .count(),
    )

    # Bloque 4: una serie por dia, nunca por commit.
    repos_tarea = bd.query(Repositorio).filter(Repositorio.id.in_(repos_ids)).all()
    rangos = [
        _rango(periodo, metricas_repo.fechas_del_sujeto(bd, tarea.id, r.sujeto_id), r, ahora)
        for r in repos_tarea
    ]
    validos = [r for r in rangos if r is not None]
    serie: list[DiaSerieSalida] = []
    cierres: list[str] = []
    histograma: list[DiaSerieSalida] = []
    progreso: int | None = None
    if validos:
        desde = dia_del_curso(min(r.inicio for r in validos), curso.zona_horaria) - timedelta(
            days=7
        )
        hasta = dia_del_curso(max(r.fin for r in validos), curso.zona_horaria) + timedelta(days=7)
        totales = _serie(bd, repos_ids, desde, hasta)
        serie = [DiaSerieSalida(dia=d.isoformat(), commits=n) for d, n in totales]
        if periodo.startswith("entrega:"):
            cierres = sorted({r.fin.isoformat() for r in validos})
            ultimo_cierre = dia_del_curso(max(r.fin for r in validos), curso.zona_horaria)
            histograma = [
                DiaSerieSalida(dia=d.isoformat(), commits=n)
                for d, n in _serie(bd, repos_ids, ultimo_cierre - timedelta(days=13), ultimo_cierre)
            ]
            progreso = progreso_frente_al_cierre(
                [
                    (f.cierre, f.ultimo_commit_antes_del_cierre)
                    for f in todas
                    if f.cierre is not None
                ],
                ahora=ahora,
            )

    posicion = None
    if tarea.modalidad == ModalidadTarea.INDIVIDUAL.value:
        medidas = [
            (f, f.integrantes[0])
            for f in todas
            if not f.no_aplica and f.integrantes and not f.integrantes[0].retirado
        ]
        por_seccion: dict[str, list[float]] = defaultdict(list)
        for f, i in medidas:
            por_seccion[f.seccion or "—"].append(i.commits)
        posicion = PosicionSalida(
            commits=cuartiles([i.commits for _, i in medidas]),
            dias_activos=cuartiles([i.dias_activos for _, i in medidas]),
            mediana_por_seccion={s: (cuartiles(v) or (0, 0, 0))[1] for s, v in por_seccion.items()},
            sujetos=len(medidas),
            excluidos=len(todas) - len(medidas),
        )

    ultima_ingesta = (
        bd.query(func.max(Commit.ingresado_en))
        .filter(Commit.repositorio_id.in_(repos_ids))
        .scalar()
        if repos_ids
        else None
    )
    ultima_reconciliacion = (
        bd.query(func.max(CursorSincronizacion.ultimo_exito_en))
        .filter(
            CursorSincronizacion.curso_id == curso.id, CursorSincronizacion.recurso == "commits"
        )
        .scalar()
    )
    response.headers["X-Llamadas-Externas"] = "0"
    return TableroSalida(
        tarea={
            "id": str(tarea.id),
            "nombre": tarea.nombre,
            "modalidad": tarea.modalidad,
            "estado": tarea.estado,
        },
        procedencia={
            "ultima_ingesta": ultima_ingesta.isoformat() if ultima_ingesta else None,
            "ultima_reconciliacion": ultima_reconciliacion.isoformat()
            if ultima_reconciliacion
            else None,
            # S10.7.8: sin una lectura correcta en 60 minutos, banda ambar.
            "datos_posiblemente_desactualizados": ultima_reconciliacion is None
            or ahora - ultima_reconciliacion > timedelta(minutes=60),
            "calculado_en": (
                bd.query(ResumenTarea.calculado_en)
                .filter(ResumenTarea.tarea_id == tarea.id)
                .scalar()
            ),
            "llamadas_externas": 0,
            "render_ms": int((ahora_utc() - inicio_render).total_seconds() * 1000),
        },
        periodos=periodos,
        periodo=periodo,
        entregas=contadores.get("entregas", []),
        repositorios=resumen.__dict__,
        tarjetas=tarjetas,
        serie=serie,
        cierres=cierres,
        histograma_previo_al_cierre=histograma,
        progreso_frente_al_cierre=progreso,
        posicion_frente_al_curso=posicion,
        filas=filas[(pagina - 1) * TAMANO_PAGINA : pagina * TAMANO_PAGINA],
        total_filas=len(filas),
        pagina=pagina,
        definicion_commit_contable=DEFINICION_COMMIT_CONTABLE,
        aviso_alcance=AVISO_ALCANCE,
    )


def _serie(
    bd: Session, repos_ids: list[uuid.UUID], desde: Any, hasta: Any
) -> list[tuple[Any, int]]:
    from app.adaptadores.modelos_metricas import MetricaRepositorioDia

    por_dia = {
        d: int(n)
        for d, n in bd.query(MetricaRepositorioDia.dia, func.sum(MetricaRepositorioDia.commits))
        .filter(
            MetricaRepositorioDia.repositorio_id.in_(repos_ids),
            MetricaRepositorioDia.dia >= desde,
            MetricaRepositorioDia.dia <= hasta,
        )
        .group_by(MetricaRepositorioDia.dia)
    }
    dias = []
    actual = desde
    while actual <= hasta:
        dias.append((actual, por_dia.get(actual, 0)))
        actual += timedelta(days=1)
    return dias


# --- Actualizar ahora (S10.7.8) ---


@router.post(
    "/api/cursos/{curso_id}/tareas/{tarea_id}/tablero/actualizar",
    status_code=202,
    dependencies=[Depends(exigir_csrf)],
)
def actualizar_ahora(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> dict[str, Any]:
    """Encola la reconciliacion y el recomputo; nunca llama a GitHub dentro de
    la peticion. Cooldown: 2 minutos por usuario y tarea, 5 por tarea."""
    curso, tarea = _tarea(bd, curso_id, tarea_id)
    ahora = ahora_utc()
    recientes = [
        t
        for t in bd.query(Trabajo).filter(
            Trabajo.tipo == "reconciliar_actividad",
            Trabajo.curso_id == curso.id,
            Trabajo.creado_en > ahora - COOLDOWN_TAREA,
        )
        if (t.payload or {}).get("tarea_id") == str(tarea.id)
    ]
    del_usuario = [
        t
        for t in recientes
        if t.payload.get("usuario_id") == str(membresia.usuario_id)
        and t.creado_en > ahora - COOLDOWN_USUARIO
    ]
    if recientes:
        limite = (
            min(t.creado_en for t in del_usuario) + COOLDOWN_USUARIO
            if del_usuario
            else min(t.creado_en for t in recientes) + COOLDOWN_TAREA
        )
        return {"encolada": False, "en_curso": True, "disponible_en": limite.isoformat()}
    trabajos_repo.encolar(
        bd,
        tipo="reconciliar_actividad",
        clave_idempotencia=f"actualizar:{tarea.id}:{ahora.isoformat()}",
        max_intentos=2,
        curso_id=curso.id,
        payload={"tarea_id": str(tarea.id), "usuario_id": str(membresia.usuario_id)},
    )
    metricas_repo.encolar(bd, curso_id=curso.id, motivo=f"actualizar:{ahora.isoformat()}")
    return {
        "encolada": True,
        "en_curso": False,
        "disponible_en": (ahora + COOLDOWN_TAREA).isoformat(),
    }


# --- Exportacion CSV (S10.10.5) ---


@router.get("/api/cursos/{curso_id}/tareas/{tarea_id}/tablero.csv")
def exportar(
    curso_id: uuid.UUID,
    tarea_id: uuid.UUID,
    periodo: str | None = None,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> Response:
    """Una fila por repositorio; la definicion de commit contable y la fecha
    de generacion van en comentarios antes del encabezado. Queda en bitacora."""
    curso, tarea = _tarea(bd, curso_id, tarea_id)
    ahora = ahora_utc()
    periodo = periodo or _periodo_por_defecto(bd, tarea, ahora)
    filas = _filas(bd, curso, tarea, periodo, ahora)
    salida = io.StringIO()
    salida.write(f"# {DEFINICION_COMMIT_CONTABLE}\n")
    salida.write(f"# Generado el {ahora.isoformat()} · periodo {periodo}\n")
    escritor = csv.writer(salida)
    escritor.writerow(
        [
            "repositorio",
            "sujeto",
            "seccion",
            "estado",
            "commits_periodo",
            "commits_sin_atribuir",
            "dias_desde_ultimo_commit",
            "alertas",
        ]
    )
    for f in filas:
        escritor.writerow(
            [
                f.nombre,
                f.sujeto,
                f.seccion or "",
                f.estado,
                f.commits_periodo,
                f.commits_sin_atribuir,
                "" if f.dias_desde_ultimo_commit is None else f.dias_desde_ultimo_commit,
                " ".join(f.alertas),
            ]
        )
    registrar_bitacora(
        bd,
        accion="EXPORTACION_TABLERO",
        entidad="tarea",
        entidad_id=str(tarea.id),
        actor_usuario_id=membresia.usuario_id,
        curso_id=curso.id,
        despues={"periodo": periodo, "filas": len(filas)},
    )
    return Response(
        salida.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="tablero-{tarea.slug}.csv"',
            "X-Llamadas-Externas": "0",
        },
    )


# --- Silenciar una alerta (S10.4.3) ---


@router.post(
    "/api/cursos/{curso_id}/incidencias/{incidencia_id}/silenciar",
    dependencies=[Depends(exigir_csrf)],
)
def silenciar(
    curso_id: uuid.UUID,
    incidencia_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> dict[str, bool]:
    """Oculta del tablero y del informe una alerta no bloqueante; sigue abierta
    y sigue en Pendientes, plegada."""
    inc = bd.get(Incidencia, incidencia_id)
    if inc is None or inc.curso_id != curso_id:
        raise HTTPException(status_code=404)
    if inc.severidad == "BLOQUEANTE":
        raise HTTPException(
            status_code=409,
            detail={"motivo": "BLOQUEANTE", "detalle": "Una incidencia bloqueante no se silencia."},
        )
    inc.silenciada = True
    registrar_bitacora(
        bd,
        accion="INCIDENCIA_SILENCIADA",
        entidad="incidencia",
        entidad_id=str(inc.id),
        actor_usuario_id=membresia.usuario_id,
        curso_id=curso_id,
    )
    return {"ok": True}


# --- Vista de seguimiento del curso (S10.10.6) ---


class FilaSeguimientoSalida(BaseModel):
    tarea_id: uuid.UUID
    nombre: str
    modalidad: str
    repositorios: dict[str, Any]
    sin_actividad: int
    sin_participacion: int
    invitaciones_sin_aceptar: int


@router.get("/api/cursos/{curso_id}/seguimiento", response_model=list[FilaSeguimientoSalida])
def seguimiento(
    curso_id: uuid.UUID,
    response: Response,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> list[FilaSeguimientoSalida]:
    """Una fila por tarea activa, en vivo sobre el espejo y la misma tabla de
    incidencias que el tablero (P2)."""
    salida = []
    abiertas = (
        bd.query(Incidencia)
        .filter(
            Incidencia.curso_id == curso_id,
            Incidencia.tipo.in_(["SIN_ACTIVIDAD", "SIN_PARTICIPACION"]),
            Incidencia.abierta.is_(True),
            Incidencia.silenciada.is_(False),
        )
        .all()
    )
    for tarea in (
        bd.query(Tarea)
        .filter(Tarea.curso_id == curso_id, Tarea.estado == EstadoTarea.ACTIVA.value)
        .order_by(Tarea.creada_en)
    ):
        repos = {r.id for r in bd.query(Repositorio).filter(Repositorio.tarea_id == tarea.id)}
        resumen = aprovisionamiento_repo.resumen_repositorios(bd, tarea_id=tarea.id)
        salida.append(
            FilaSeguimientoSalida(
                tarea_id=tarea.id,
                nombre=tarea.nombre,
                modalidad=tarea.modalidad,
                repositorios=resumen.__dict__,
                sin_actividad=sum(
                    1 for i in abiertas if i.tipo == "SIN_ACTIVIDAD" and i.sujeto_id in repos
                ),
                sin_participacion=sum(
                    1
                    for i in abiertas
                    if i.tipo == "SIN_PARTICIPACION" and i.detalle.get("tarea_id") == str(tarea.id)
                ),
                invitaciones_sin_aceptar=int(
                    _contadores(bd, tarea).get("invitaciones_sin_aceptar", 0)
                ),
            )
        )
    response.headers["X-Llamadas-Externas"] = "0"
    return salida
