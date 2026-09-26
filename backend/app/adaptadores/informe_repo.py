"""Informe docente diario: hechos del espejo, generacion y envio (SPEC 11
S11.3-S11.5; A-131, A-132, A-228, A-229; Etapa F9).

Todo sale de la base propia: ni Canvas ni GitHub se llaman para generar. Los
nombrados vienen de las mismas tablas que Pendientes y el tablero
(`incidencia`, `repositorio`, `acceso_repositorio`...), asi el informe nunca
contradice a esas pantallas.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.adaptadores import canvas_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.modelos_actividad import Commit
from app.adaptadores.modelos_aprovisionamiento import (
    AccesoRepositorio,
    FechaEfectiva,
    MensajeSaliente,
    Repositorio,
    Sujeto,
)
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_identidad import Usuario
from app.adaptadores.modelos_informe import InformeDiario, SuscripcionInforme
from app.adaptadores.modelos_infraestructura import CursorSincronizacion, Incidencia
from app.adaptadores.modelos_mapeo import MapeoGithub
from app.adaptadores.modelos_padron import Estudiante
from app.adaptadores.modelos_tarea import Entrega, Tarea
from app.adaptadores.modelos_version import VersionEntrega
from app.dominio.comunicaciones import clave_idempotencia
from app.dominio.estados import (
    CanalComunicacionActivo,
    CanalMensaje,
    EstadoAccesoRepositorio,
    EstadoMembresia,
    EstadoMensaje,
    EstadoRepositorio,
    OrigenMensaje,
)
from app.dominio.fechas import formatear_fecha
from app.dominio.informe import (
    FRESCURA_MAXIMA_CANVAS,
    DocumentoInforme,
    HechosTarea,
    Item,
    Seccion,
    armar_secciones,
    asunto_informe,
    renderizar_html,
    renderizar_texto,
    tarea_activa,
    ventana_del_informe,
)

EVENTO = "INFORME_DIARIO"
PLANTILLA = "informe_diario_correo"
_TIPOS_VERSION = ("VERSION_REVISAR", "VERSION_ERROR")
_REPO_PENDIENTE_EXCLUIDOS = (
    EstadoRepositorio.OPERATIVO.value,
    EstadoRepositorio.FUERA_DE_ALCANCE.value,
    EstadoRepositorio.ARCHIVADO.value,
)
_TEXTO_SIN_TAREAS = (
    "Este curso no tiene tareas activas: el informe diario solo se genera mientras "
    "hay alguna tarea activa."
)


def dia_del_curso(curso: Curso, instante: datetime) -> date:
    return instante.astimezone(ZoneInfo(curso.zona_horaria)).date()


# --- Tareas activas (S11.3.1) ---


def _hechos_tarea(bd: Session, curso: Curso, tarea: Tarea, ahora: datetime) -> HechosTarea:
    cierre_futuro = (
        bd.query(FechaEfectiva.id)
        .join(Entrega, Entrega.id == FechaEfectiva.entrega_id)
        .filter(
            Entrega.tarea_id == tarea.id,
            Entrega.publicada.is_(True),
            FechaEfectiva.estado == "VIGENTE",
            FechaEfectiva.due_at_utc > ahora,
        )
        .first()
        is not None
    )
    repo_pendiente = (
        bd.query(Repositorio.id)
        .join(Sujeto, Sujeto.id == Repositorio.sujeto_id)
        .filter(
            Repositorio.tarea_id == tarea.id,
            Sujeto.activo.is_(True),
            Repositorio.estado.notin_(_REPO_PENDIENTE_EXCLUIDOS),
        )
        .first()
        is not None
    )
    versiones = [
        v.id
        for v in bd.query(VersionEntrega.id)
        .join(Entrega, Entrega.id == VersionEntrega.entrega_id)
        .filter(Entrega.tarea_id == tarea.id)
    ]
    repos = [r.id for r in bd.query(Repositorio.id).filter(Repositorio.tarea_id == tarea.id)]
    relevante = (
        bd.query(Incidencia.id)
        .filter(
            Incidencia.curso_id == curso.id,
            Incidencia.abierta.is_(True),
            Incidencia.sujeto_id.in_(versiones + repos),
            (Incidencia.severidad == "BLOQUEANTE") | Incidencia.tipo.in_(_TIPOS_VERSION),
        )
        .first()
        is not None
    )
    return HechosTarea(
        estado_tarea=tarea.estado,
        estado_curso=curso.estado,
        hay_cierre_futuro_publicado=cierre_futuro,
        hay_repositorio_pendiente=repo_pendiente,
        hay_incidencia_relevante=relevante,
    )


def tareas_activas(bd: Session, curso: Curso, ahora: datetime) -> list[Tarea]:
    tareas = bd.query(Tarea).filter(Tarea.curso_id == curso.id).order_by(Tarea.nombre).all()
    return [t for t in tareas if tarea_activa(_hechos_tarea(bd, curso, t, ahora))]


# --- Frescura (S11.3.5) ---


def _frescura(bd: Session, curso: Curso, ahora: datetime) -> dict[str, Any]:
    def ultimo(recursos: tuple[str, ...]) -> datetime | None:
        valor = (
            bd.query(func.max(CursorSincronizacion.ultimo_exito_en))
            .filter(
                CursorSincronizacion.curso_id == curso.id,
                CursorSincronizacion.recurso.in_(recursos),
            )
            .scalar()
        )
        return valor if isinstance(valor, datetime) else None

    canvas = ultimo(("roster", "grupos"))
    github = ultimo(("commits",))
    credencial = canvas_repo.obtener_credencial_operativa(bd, curso.id)
    return {
        "canvas": {
            "ultimo_exito": canvas.isoformat() if canvas else None,
            "estado": credencial.estado if credencial is not None else "SIN_CREDENCIAL",
        },
        "github": {
            "ultimo_exito": github.isoformat() if github else None,
            "estado": "INSTALADA" if curso.github_installation_id else "SIN_INSTALACION",
        },
        "canvas_desactualizado": canvas is None or ahora - canvas > FRESCURA_MAXIMA_CANVAS,
    }


def _texto_frescura(curso: Curso, frescura: dict[str, Any]) -> list[str]:
    salida = []
    for fuente, nombre in (("canvas", "Canvas"), ("github", "GitHub")):
        valor = frescura[fuente]["ultimo_exito"]
        cuando = (
            formatear_fecha(datetime.fromisoformat(valor), curso.zona_horaria)
            if valor
            else "todavía sin sincronizar"
        )
        salida.append(f"{nombre}: última sincronización {cuando}.")
    return salida


# --- Hechos por seccion (S11.3.4) ---


def _enlace_tarea(curso: Curso, tarea_id: uuid.UUID) -> str:
    return f"/cursos/{curso.id}/tareas/{tarea_id}"


def _candidatos(
    bd: Session,
    curso: Curso,
    tareas: list[Tarea],
    *,
    ahora: datetime,
    desde: datetime,
) -> tuple[dict[int, list[tuple[str, Item]]], dict[int, list[tuple[str, str]]], dict[int, str]]:
    c: dict[int, list[tuple[str, Item]]] = {1: [], 2: [], 3: [], 4: []}
    cifras: dict[int, list[tuple[str, str]]] = {}
    encabezados: dict[int, str] = {}
    nombre_tarea = {t.id: t.nombre for t in tareas}
    ids_tareas = list(nombre_tarea)
    repos = (
        bd.query(Repositorio).filter(Repositorio.tarea_id.in_(ids_tareas)).all()
        if ids_tareas
        else []
    )
    repo_por_id = {r.id: r for r in repos}

    # 1. Requiere tu atencion hoy
    for r in repos:
        if r.estado in (
            EstadoRepositorio.BLOQUEADO.value,
            EstadoRepositorio.ERROR_PERMANENTE.value,
        ):
            c[1].append(
                (
                    "Repositorios bloqueados o con error",
                    Item(
                        f"repo:{r.id}",
                        f"{r.nombre}: {r.motivo or r.error_codigo or r.estado.lower()}",
                        _enlace_tarea(curso, r.tarea_id),
                        "BLOQUEANTE",
                        r.actualizado_en or r.creado_en,
                        nombre_tarea.get(r.tarea_id),
                    ),
                )
            )
    abiertas = (
        bd.query(Incidencia)
        .filter(Incidencia.curso_id == curso.id, Incidencia.abierta.is_(True))
        .all()
    )
    for inc in abiertas:
        if inc.severidad == "BLOQUEANTE" and inc.tipo not in ("SIN_ACTIVIDAD", "SIN_PARTICIPACION"):
            clave = f"repo:{inc.sujeto_id}" if inc.sujeto_id in repo_por_id else f"inc:{inc.id}"
            c[1].append(
                (
                    "Incidencias bloqueantes",
                    Item(
                        clave,
                        inc.tipo.replace("_", " ").capitalize(),
                        f"/cursos/{curso.id}/pendientes",
                        "BLOQUEANTE",
                        inc.creado_en,
                    ),
                )
            )
    versiones = (
        bd.query(VersionEntrega, Entrega)
        .join(Entrega, Entrega.id == VersionEntrega.entrega_id)
        .filter(
            Entrega.tarea_id.in_(ids_tareas),
            VersionEntrega.vigente.is_(True),
            VersionEntrega.estado.in_(("REVISAR", "ERROR")),
        )
        .all()
        if ids_tareas
        else []
    )
    for v, e in versiones:
        c[1].append(
            (
                "Versiones por revisar",
                Item(
                    f"version:{v.id}",
                    f"{v.sujeto_etiqueta}: {e.nombre}",
                    f"/cursos/{curso.id}/tareas/{e.tarea_id}/entregas",
                    "ADVERTENCIA",
                    v.capturada_en,
                    nombre_tarea.get(e.tarea_id),
                ),
            )
        )
    fallidos = (
        bd.query(MensajeSaliente)
        .filter(
            MensajeSaliente.curso_id == curso.id,
            MensajeSaliente.estado == EstadoMensaje.FALLIDO.value,
            MensajeSaliente.creado_en >= desde,
        )
        .all()
    )
    for m in fallidos:
        c[1].append(
            (
                "Comunicaciones que no se pudieron enviar",
                Item(
                    f"mensaje:{m.id}",
                    f"{m.evento.replace('_', ' ')} a {m.destinatario}",
                    f"/cursos/{curso.id}/pendientes",
                    "ADVERTENCIA",
                    m.creado_en,
                ),
            )
        )
    canal = curso.canal_comunicacion_activo
    if canal and canal != CanalComunicacionActivo.CONVERSACION.value:
        c[1].append(
            (
                "Canal de comunicación con estudiantes",
                Item(
                    "canal",
                    "Los avisos a estudiantes salen por "
                    + (
                        "comentario en la tarea de registro"
                        if canal != "BLOQUEADO"
                        else "ningún canal"
                    ),
                    f"/cursos/{curso.id}/verificacion",
                    "BLOQUEANTE" if canal == "BLOQUEADO" else "ADVERTENCIA",
                    ahora,
                ),
            )
        )

    # 2. Informacion pendiente
    vigentes = {
        m.estudiante_id
        for m in bd.query(MapeoGithub.estudiante_id).filter(
            MapeoGithub.curso_id == curso.id, MapeoGithub.estado == "VIGENTE"
        )
    }
    for est in (
        bd.query(Estudiante)
        .filter(Estudiante.curso_id == curso.id, Estudiante.estado == "ACTIVO")
        .order_by(Estudiante.nombre_ordenable)
    ):
        if est.id not in vigentes:
            c[2].append(
                (
                    "Estudiantes sin cuenta de GitHub",
                    Item(
                        f"est:{est.id}",
                        est.nombre,
                        f"/cursos/{curso.id}/pendientes",
                        "INFORMATIVA",
                        est.primera_vista_en or ahora,
                    ),
                )
            )
    for acceso, est in (
        bd.query(AccesoRepositorio, Estudiante)
        .join(Estudiante, Estudiante.id == AccesoRepositorio.estudiante_id)
        .filter(
            AccesoRepositorio.repositorio_id.in_(list(repo_por_id)),
            AccesoRepositorio.estado == EstadoAccesoRepositorio.INVITADO.value,
            AccesoRepositorio.invitado_en < ahora - timedelta(hours=48),
        )
        if repo_por_id
        else []
    ):
        repo = repo_por_id[acceso.repositorio_id]
        c[2].append(
            (
                "Invitaciones sin aceptar hace más de 48 horas",
                Item(
                    f"acceso:{acceso.id}",
                    f"{est.nombre} ({repo.nombre})",
                    _enlace_tarea(curso, repo.tarea_id),
                    "INFORMATIVA",
                    acceso.invitado_en or ahora,
                    nombre_tarea.get(repo.tarea_id),
                ),
            )
        )
    for r in repos:
        if r.estado == EstadoRepositorio.ESPERANDO_INFORMACION.value:
            c[2].append(
                (
                    "Repositorios esperando información",
                    Item(
                        f"repo:{r.id}",
                        f"{r.nombre}: {(r.motivo or 'sin motivo').replace('_', ' ').lower()}",
                        _enlace_tarea(curso, r.tarea_id),
                        "INFORMATIVA",
                        r.creado_en,
                        nombre_tarea.get(r.tarea_id),
                    ),
                )
            )
    for inc in abiertas:
        if inc.tipo == "GRUPO_INCOMPLETO":
            c[2].append(
                (
                    "Grupos incompletos",
                    Item(
                        f"inc:{inc.id}",
                        str((inc.detalle or {}).get("grupo") or "Grupo"),
                        f"/cursos/{curso.id}/pendientes",
                        inc.severidad,
                        inc.creado_en,
                    ),
                )
            )
    for e in (
        bd.query(Entrega)
        .filter(Entrega.tarea_id.in_(ids_tareas), Entrega.publicada.is_(False))
        .all()
        if ids_tareas
        else []
    ):
        c[2].append(
            (
                "Entregas vinculadas sin publicar en Canvas",
                Item(
                    f"entrega:{e.id}",
                    e.nombre,
                    _enlace_tarea(curso, e.tarea_id),
                    "INFORMATIVA",
                    ahora,
                    nombre_tarea.get(e.tarea_id),
                ),
            )
        )

    # 3. Sin actividad (solo alertas con dato suficiente y no silenciadas)
    for inc in abiertas:
        if inc.tipo not in ("SIN_ACTIVIDAD", "SIN_PARTICIPACION") or inc.silenciada:
            continue
        detalle = inc.detalle or {}
        repo_id = inc.sujeto_id if inc.tipo == "SIN_ACTIVIDAD" else detalle.get("repositorio_id")
        repo_inc = repo_por_id.get(uuid.UUID(str(repo_id))) if repo_id else None
        texto = (
            f"{repo_inc.nombre if repo_inc else 'Repositorio'}: sin commits contables"
            if inc.tipo == "SIN_ACTIVIDAD"
            else f"{detalle.get('estudiante', 'Un integrante')}: sin participación"
            + (f" en {repo_inc.nombre}" if repo_inc else "")
        )
        clave_repo = f"repo:{repo_inc.id}" if repo_inc else None
        c[3].append(
            (
                "Repositorios sin actividad"
                if inc.tipo == "SIN_ACTIVIDAD"
                else "Estudiantes sin participación",
                Item(
                    (clave_repo or f"inc:{inc.id}")
                    if inc.tipo == "SIN_ACTIVIDAD"
                    else f"inc:{inc.id}",
                    texto,
                    _enlace_tarea(curso, repo_inc.tarea_id)
                    if repo_inc
                    else f"/cursos/{curso.id}/seguimiento",
                    inc.severidad,
                    inc.creado_en,
                    nombre_tarea.get(repo_inc.tarea_id) if repo_inc else None,
                    relacionado=clave_repo if inc.tipo == "SIN_PARTICIPACION" else None,
                ),
            )
        )
    if curso.ingesta_actividad_desde:
        observada = dia_del_curso(curso, curso.ingesta_actividad_desde)
        encabezados[3] = f"Actividad observada desde el {observada:%d-%m-%Y}."

    # 4. Proximos cierres (72 h, en UTC y mostrados en la zona del curso)
    proximas = (
        bd.query(FechaEfectiva, Entrega)
        .join(Entrega, Entrega.id == FechaEfectiva.entrega_id)
        .filter(
            Entrega.tarea_id.in_(ids_tareas),
            FechaEfectiva.estado == "VIGENTE",
            FechaEfectiva.due_at_utc > ahora,
            FechaEfectiva.due_at_utc <= ahora + timedelta(hours=72),
        )
        .all()
        if ids_tareas
        else []
    )
    por_entrega: dict[uuid.UUID, tuple[Entrega, datetime, set[uuid.UUID]]] = {}
    for f, e in proximas:
        _, primera, sujetos = por_entrega.get(e.id, (e, f.due_at_utc, set()))
        sujetos.add(f.sujeto_id)
        por_entrega[e.id] = (e, min(primera, f.due_at_utc or primera), sujetos)
    for e, primera, sujetos in por_entrega.values():
        repos_sujetos = [r for r in repos if r.sujeto_id in sujetos]
        con_commits = {
            rid
            for (rid,) in bd.query(Commit.repositorio_id)
            .filter(
                Commit.repositorio_id.in_([r.id for r in repos_sujetos]),
                Commit.motivo_exclusion.is_(None),
            )
            .distinct()
        }
        sin_commits = len(sujetos) - sum(1 for r in repos_sujetos if r.id in con_commits)
        c[4].append(
            (
                "Entregas que cierran en las próximas 72 horas",
                Item(
                    f"entrega:{e.id}",
                    f"{e.nombre}: cierra el {formatear_fecha(primera, curso.zona_horaria)}; "
                    f"{sin_commits} sujetos sin commits",
                    f"/cursos/{curso.id}/tareas/{e.tarea_id}/entregas",
                    "INFORMATIVA",
                    primera,
                    nombre_tarea.get(e.tarea_id),
                ),
            )
        )
    cambios = (
        bd.query(Entrega.nombre, func.count(FechaEfectiva.id))
        .join(Entrega, Entrega.id == FechaEfectiva.entrega_id)
        .filter(
            Entrega.tarea_id.in_(ids_tareas),
            FechaEfectiva.vigente_hasta.isnot(None),
            FechaEfectiva.vigente_hasta >= desde,
        )
        .group_by(Entrega.nombre)
        .all()
        if ids_tareas
        else []
    )
    if cambios:
        cifras[4] = [
            (f"Fechas cambiadas en Canvas · {nombre}", f"{n} sujetos") for nombre, n in cambios
        ]
    return c, cifras, encabezados


def _resumen(
    bd: Session, curso: Curso, tareas: list[Tarea], *, desde: datetime, hasta: datetime
) -> list[tuple[str, str]]:
    ids = [t.id for t in tareas]
    repos = (
        [r.id for r in bd.query(Repositorio.id).filter(Repositorio.tarea_id.in_(ids))]
        if ids
        else []
    )
    commits = (
        bd.query(Commit.repositorio_id)
        .filter(
            Commit.repositorio_id.in_(repos),
            Commit.motivo_exclusion.is_(None),
            Commit.fecha_committer > desde,
            Commit.fecha_committer <= hasta,
        )
        .all()
        if repos
        else []
    )
    versiones = (
        bd.query(VersionEntrega.estado, func.count(VersionEntrega.id))
        .filter(
            VersionEntrega.repositorio_id.in_(repos),
            VersionEntrega.capturada_en > desde,
            VersionEntrega.capturada_en <= hasta,
        )
        .group_by(VersionEntrega.estado)
        .all()
        if repos
        else []
    )
    operativos = (
        bd.query(Repositorio.id)
        .filter(
            Repositorio.id.in_(repos), Repositorio.listo_en > desde, Repositorio.listo_en <= hasta
        )
        .count()
        if repos
        else 0
    )
    salida = [
        ("Commits contables", str(len(commits))),
        ("Repositorios con actividad", str(len({r for (r,) in commits}))),
        ("Repositorios que quedaron listos", str(operativos)),
    ]
    if versiones:
        salida.append(
            (
                "Versiones capturadas",
                ", ".join(f"{n} {estado.lower().replace('_', ' ')}" for estado, n in versiones),
            )
        )
    return salida


# --- Documento ---


def construir(
    bd: Session, curso: Curso, *, ahora: datetime, desde: datetime, fecha: date
) -> tuple[DocumentoInforme, dict[str, Any], bool]:
    """Devuelve el documento, la frescura y si hay tareas activas. Lo usan el
    trabajo y la vista previa: la misma funcion para los dos (S11.3.1)."""
    tareas = tareas_activas(bd, curso, ahora)
    frescura = _frescura(bd, curso, ahora)
    candidatos, cifras, encabezados = _candidatos(bd, curso, tareas, ahora=ahora, desde=desde)
    viejo = bool(frescura["canvas_desactualizado"])
    if not viejo:
        cifras[5] = _resumen(bd, curso, tareas, desde=desde, hasta=ahora)
    secciones: list[Seccion] = armar_secciones(candidatos, cifras=cifras, encabezados=encabezados)
    horas = (ahora - desde).total_seconds() / 3600
    ventana = (
        "Período: las últimas 24 horas."
        if horas <= 25
        else f"Período: desde el {formatear_fecha(desde, curso.zona_horaria)} "
        f"({round(horas)} horas, porque no hubo informe en el medio)."
    )
    doc = DocumentoInforme(
        curso_nombre=curso.nombre,
        curso_codigo=curso.codigo,
        fecha=fecha,
        ventana_texto=ventana,
        frescura_texto=_texto_frescura(curso, frescura),
        aviso_datos_viejos=(
            "Canvas no se sincroniza hace más de 24 horas: estos datos pueden estar "
            "desactualizados y se omite el resumen del período."
            if viejo
            else None
        ),
        secciones=secciones,
        sin_alertas=not any(s.numero == 1 for s in secciones),
    )
    return doc, frescura, bool(tareas)


def _url_app() -> str:
    from app.infraestructura.config import obtener_configuracion

    return obtener_configuracion().frontend_origen.rstrip("/")


def pie_generico(curso: Curso) -> str:
    return (
        f"Recibes este correo porque formas parte del equipo docente de {curso.nombre} "
        "y estás suscrito al informe docente diario. Puedes darte de baja en un clic "
        "desde el enlace de este correo o en Mis notificaciones."
    )


def presentar(curso: Curso, doc: DocumentoInforme, fecha: date) -> tuple[str, str]:
    url_app = _url_app()
    url_informe = f"{url_app}/cursos/{curso.id}/informes/{fecha.isoformat()}"
    pie = pie_generico(curso)
    return (
        renderizar_html(doc, url_base=url_informe, url_app=url_app, pie=pie),
        renderizar_texto(doc, url_base=url_informe, pie=pie),
    )


def _contenido_json(doc: DocumentoInforme, asunto: str) -> dict[str, Any]:
    datos = asdict(doc)
    datos["fecha"] = doc.fecha.isoformat()
    for s in datos["secciones"]:
        for li in s["lineas"]:
            for i in li["items"]:
                i["desde"] = i["desde"].isoformat()
    datos["asunto"] = asunto
    return datos


# --- Generacion idempotente (S11.3.3) ---


def informe_del_dia(bd: Session, curso_id: uuid.UUID, fecha: date) -> InformeDiario | None:
    return (
        bd.query(InformeDiario)
        .filter(InformeDiario.curso_id == curso_id, InformeDiario.fecha == fecha)
        .one_or_none()
    )


def _marcar_dias_perdidos(bd: Session, curso: Curso, hoy: date, ahora: datetime) -> None:
    """Un dia del curso que termino sin informe queda NO_GENERADO; nunca se
    genera retroactivamente."""
    ultimo = (
        bd.query(InformeDiario)
        .filter(InformeDiario.curso_id == curso.id)
        .order_by(InformeDiario.fecha.desc())
        .first()
    )
    if ultimo is None:
        return
    dia = ultimo.fecha + timedelta(days=1)
    while dia < hoy:
        bd.add(
            InformeDiario(
                curso_id=curso.id,
                fecha=dia,
                estado="NO_GENERADO",
                motivo="SISTEMA_DETENIDO",
                ventana_desde_utc=ahora,
                ventana_hasta_utc=ahora,
                origen="PROGRAMADO",
                frescura={},
                generado_en=ahora,
            )
        )
        dia += timedelta(days=1)
    bd.flush()


def generar(
    bd: Session,
    curso: Curso,
    *,
    ahora: datetime | None = None,
    origen: str = "PROGRAMADO",
    usuario_id: uuid.UUID | None = None,
) -> tuple[InformeDiario, bool]:
    """La fila del dia y si se creo ahora. Si ya existia no se toca (Ley 2)."""
    ahora = ahora or ahora_utc()
    hoy = dia_del_curso(curso, ahora)
    existente = informe_del_dia(bd, curso.id, hoy)
    if existente is not None:
        return existente, False
    _marcar_dias_perdidos(bd, curso, hoy, ahora)
    ultimo = (
        bd.query(InformeDiario)
        .filter(InformeDiario.curso_id == curso.id, InformeDiario.estado == "GENERADO")
        .order_by(InformeDiario.fecha.desc())
        .first()
    )
    desde, hasta = ventana_del_informe(
        ultimo_generado_hasta=ultimo.ventana_hasta_utc if ultimo else None,
        ahora=ahora,
        curso_creado_en=curso.creado_en,
    )
    doc, frescura, hay_tareas = construir(bd, curso, ahora=ahora, desde=desde, fecha=hoy)
    informe = InformeDiario(
        curso_id=curso.id,
        fecha=hoy,
        estado="GENERADO" if hay_tareas else "SIN_TAREAS_ACTIVAS",
        ventana_desde_utc=desde,
        ventana_hasta_utc=hasta,
        origen=origen,
        disparado_por_usuario_id=usuario_id,
        frescura=frescura,
        generado_en=ahora,
    )
    if hay_tareas:
        asunto = asunto_informe(curso.codigo, hoy, requiere_atencion=not doc.sin_alertas)
        html, texto = presentar(curso, doc, hoy)
        informe.contenido = _contenido_json(doc, asunto)
        informe.contenido_html = html
        informe.contenido_texto = texto
    bd.add(informe)
    bd.flush()
    return informe, True


# --- Envio (S11.5) ---


def suscriptores(bd: Session, curso_id: uuid.UUID) -> list[tuple[MembresiaCurso, Usuario]]:
    filas = (
        bd.query(MembresiaCurso, Usuario)
        .join(Usuario, Usuario.id == MembresiaCurso.usuario_id)
        .join(
            SuscripcionInforme,
            (SuscripcionInforme.curso_id == MembresiaCurso.curso_id)
            & (SuscripcionInforme.usuario_id == MembresiaCurso.usuario_id),
        )
        .filter(
            MembresiaCurso.curso_id == curso_id,
            MembresiaCurso.estado == EstadoMembresia.ACTIVA.value,
            SuscripcionInforme.activa.is_(True),
        )
        .order_by(Usuario.email)
        .all()
    )
    return [(m, u) for m, u in filas]


def _generacion_siguiente(bd: Session, informe: InformeDiario, membresia_id: uuid.UUID) -> int:
    previos = (
        bd.query(func.max(MensajeSaliente.generacion))
        .filter(
            MensajeSaliente.evento == EVENTO,
            MensajeSaliente.membresia_id == membresia_id,
            MensajeSaliente.referencia["informe_diario_id"].astext == str(informe.id),
        )
        .scalar()
    )
    return int(previos or 0) + 1


def encolar_correos(
    bd: Session,
    informe: InformeDiario,
    destinatarios: list[tuple[MembresiaCurso, Usuario]],
    *,
    reserva: str,
    origen: OrigenMensaje,
    disparado_por: uuid.UUID | None = None,
    reenvio: bool = False,
) -> int:
    """Un correo por (curso, suscriptor), nunca uno con varios destinatarios.
    Un reenvio del mismo documento sube `generacion` (A-224)."""
    if informe.estado != "GENERADO":
        return 0
    nuevos = 0
    for membresia, usuario in destinatarios:
        generacion = _generacion_siguiente(bd, informe, membresia.id) if reenvio else 1
        clave = clave_idempotencia(
            canal=CanalMensaje.CORREO.value,
            destinatario=usuario.email,
            plantilla=PLANTILLA,
            entidad=str(informe.id),
            generacion=generacion,
        )
        if bd.query(MensajeSaliente.id).filter(MensajeSaliente.clave_idempotencia == clave).first():
            continue
        bd.add(
            MensajeSaliente(
                curso_id=informe.curso_id,
                canal=CanalMensaje.CORREO.value,
                evento=EVENTO,
                clave_idempotencia=clave,
                generacion=generacion,
                membresia_id=membresia.id,
                referencia={"informe_diario_id": str(informe.id)},
                destinatario=usuario.email,
                plantilla=PLANTILLA,
                plantilla_version=1,
                origen=origen.value,
                disparado_por_usuario_id=disparado_por,
                reserva=reserva,
                caduca_en=None,  # S11.2.4: el correo del informe no caduca
                estado=EstadoMensaje.PENDIENTE.value,
                intentos=0,
                creado_en=ahora_utc(),
            )
        )
        nuevos += 1
    bd.flush()
    return nuevos


def envios_manuales_de_hoy(
    bd: Session, curso: Curso, usuario_id: uuid.UUID, ahora: datetime
) -> int:
    inicio = datetime.combine(
        dia_del_curso(curso, ahora), datetime.min.time(), tzinfo=ZoneInfo(curso.zona_horaria)
    )
    return (
        bd.query(MensajeSaliente)
        .filter(
            MensajeSaliente.curso_id == curso.id,
            MensajeSaliente.evento == EVENTO,
            MensajeSaliente.origen == OrigenMensaje.MANUAL.value,
            MensajeSaliente.disparado_por_usuario_id == usuario_id,
            MensajeSaliente.creado_en >= inicio,
        )
        .count()
    )


TEXTO_SIN_TAREAS = _TEXTO_SIN_TAREAS


# --- Enlace de baja (S11.4.4) ---


def emitir_token_baja(curso_id: uuid.UUID, usuario: Usuario, *, ahora: datetime) -> str:
    from app.dominio.informe import VALIDEZ_ENLACE_BAJA
    from app.infraestructura.config import obtener_configuracion
    from app.infraestructura.enlaces_firmados import firmar

    return firmar(
        {
            "c": str(curso_id),
            "u": str(usuario.id),
            "g": usuario.generacion_enlaces,
            "jti": uuid.uuid4().hex,
        },
        obtener_configuracion().signing_key,
        expira_en=ahora + VALIDEZ_ENLACE_BAJA,
    )


def leer_token_baja(bd: Session, token: str, *, ahora: datetime) -> tuple[Curso, Usuario] | None:
    """`None` si la firma no cuadra, vencio o la generacion quedo vieja tras
    «regenerar mis enlaces de baja» (CA-11.4-04)."""
    from app.infraestructura.config import obtener_configuracion
    from app.infraestructura.enlaces_firmados import verificar

    settings = obtener_configuracion()
    carga = verificar(
        token, [settings.signing_key, settings.signing_key_anterior or ""], ahora=ahora
    )
    if carga is None:
        return None
    try:
        curso = bd.get(Curso, uuid.UUID(str(carga["c"])))
        usuario = bd.get(Usuario, uuid.UUID(str(carga["u"])))
    except (KeyError, ValueError):
        return None
    if curso is None or usuario is None or carga.get("g") != usuario.generacion_enlaces:
        return None
    return curso, usuario


def url_baja(token: str) -> str:
    return f"{_url_app()}/api/baja/{token}"
