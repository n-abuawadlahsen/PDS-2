"""Captura y versiones de entrega con I/O (SPEC 09 S9.6-S9.10; A-101 a A-104,
A-172, A-204, A-213; Etapa F4). Las decisiones viven en `app/dominio/versiones.py`.

Dos fases con dos claves (S9.6.2): `resolver_sha` inserta la fila en un estado
terminal en cuanto el SHA queda resuelto -- nunca antes (S9.6.1) -- y
`crear_etiqueta` solo mueve la etiqueta. Un `403` al etiquetar nunca impide
registrar la evidencia.

Simplificaciones de esta etapa, cada una con su TODO donde toca:
- El espejo propio de actividad (`commit`) llega con la ingesta del Bloque 2:
  hasta entonces GitHub es la unica fuente del commit de cierre y
  `verificacion.espejo_sha` queda nulo. Por lo mismo no hay `precierre_actividad`
  ni el indicador de commits posteriores al cierre, ni la deteccion de push
  retrodatado o historia reescrita (S9.8.3-S9.8.4). TODO(etapa-F5).
- `HAY_COMMITS_EN_OTRAS_RAMAS` exige listar ramas y su actividad: queda para
  cuando exista el espejo. TODO(etapa-F5).
- Sin receptor de webhooks, la etiqueta borrada o movida la detecta solo la
  verificacion diaria (S9.8.5).
"""

from __future__ import annotations

import base64
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.adaptadores import incidencia_repo, trabajos_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.bitacora_repo import registrar as registrar_bitacora
from app.adaptadores.cliente_github import (
    ClienteGitHub,
    FalloProveedorGithub,
    RechazoProveedorGithub,
)
from app.adaptadores.modelos_aprovisionamiento import (
    FechaEfectiva,
    ReglaFecha,
    Repositorio,
    Sujeto,
)
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_mapeo import CuentaGithub, MapeoGithub
from app.adaptadores.modelos_padron import Estudiante, Grupo, Matricula, PertenenciaGrupo, Seccion
from app.adaptadores.modelos_tarea import Entrega, Tarea
from app.adaptadores.modelos_version import VersionEntrega
from app.dominio.alcance import instante_retirada
from app.dominio.estados import (
    EstadoFechaEfectiva,
    EstadoMapeoGithub,
    EstadoRepositorio,
    EstadoTarea,
    EstadoValidacionEntrega,
    EstadoVersion,
    MotivoVersion,
    OrigenCaptura,
    TagEstado,
    TagMotivo,
    WorkflowStatePertenenciaGrupo,
)
from app.dominio.versiones import (
    CommitCierre,
    EntregaDelSujeto,
    ResultadoCaptura,
    advertencias_de_captura,
    entrega_anterior,
    estado_tras_etiqueta,
    motivo_de_supersede,
    motivo_por_alcance,
    nombre_tag,
    resolver_captura,
    seleccionar_commit_cierre,
    tag_tras_rechazo,
    validar_cambios,
)

TIPO_RESOLVER = "resolver_sha"
TIPO_ETIQUETA = "crear_etiqueta"
MAX_INTENTOS = 8  # «8 en ~2 h» (S14.7.4)
GRACIA = timedelta(seconds=60)  # A-101: desfase de relojes
REEVALUACION_SIN_ACCESO = timedelta(minutes=30)  # S9.10.4


class GithubSinAcceso(Exception):
    """Sin token de instalacion no hay forma de leer el SHA (S9.10.4): no es un
    fallo del trabajo, se reevalua cada 30 minutos sin consumir reintentos."""


class RechazoVersion(Exception):
    def __init__(self, motivo: str, detalle: str) -> None:
        self.motivo = motivo
        self.detalle = detalle
        super().__init__(detalle)


# --- La funcion unica de transicion (S9.8.1) ---


def transicionar(bd: Session, version: VersionEntrega, **cambios: Any) -> None:
    """Toda escritura posterior a la insercion pasa por aqui; la base la
    respalda con el disparador `version_entrega_inmutable`."""
    validar_cambios({k: getattr(version, k) for k in cambios}, cambios)
    for columna, valor in cambios.items():
        setattr(version, columna, valor)
    bd.flush()


# --- Lecturas ---


def version_vigente(
    bd: Session, entrega_id: uuid.UUID, sujeto_id: uuid.UUID
) -> VersionEntrega | None:
    return (
        bd.query(VersionEntrega)
        .filter(
            VersionEntrega.entrega_id == entrega_id,
            VersionEntrega.sujeto_id == sujeto_id,
            VersionEntrega.vigente.is_(True),
        )
        .one_or_none()
    )


def entrega_tiene_versiones(bd: Session, entrega_id: uuid.UUID) -> bool:
    return (
        bd.query(VersionEntrega.id).filter(VersionEntrega.entrega_id == entrega_id).first()
        is not None
    )


def _fecha_vigente(
    bd: Session, entrega_id: uuid.UUID, sujeto_id: uuid.UUID
) -> FechaEfectiva | None:
    return (
        bd.query(FechaEfectiva)
        .filter(
            FechaEfectiva.entrega_id == entrega_id,
            FechaEfectiva.sujeto_id == sujeto_id,
            FechaEfectiva.estado == EstadoFechaEfectiva.VIGENTE.value,
        )
        .one_or_none()
    )


def _repositorio_del_sujeto(bd: Session, sujeto_id: uuid.UUID) -> Repositorio | None:
    return (
        bd.query(Repositorio)
        .filter(
            Repositorio.sujeto_id == sujeto_id,
            Repositorio.estado != EstadoRepositorio.INACCESIBLE.value,
        )
        .order_by(Repositorio.creado_en.desc())
        .first()
    )


# --- El disparador (S9.6.1) ---


def clave_resolver(entrega_id: uuid.UUID, sujeto_id: uuid.UUID, corte: datetime) -> str:
    """A-103: la fecha de corte en epoch en la clave; la misma fecha nunca
    captura dos veces y una distinta siempre captura de nuevo."""
    return f"version:{entrega_id}:{sujeto_id}:{int(corte.timestamp())}"


def candidatos(bd: Session, *, ahora: datetime, limite: int = 500) -> list[FechaEfectiva]:
    """Una fecha efectiva vigente, vencida mas la gracia, de una entrega
    `VIGENTE` de una tarea activa, y sin version vigente. `VINCULADA_TRAS_EL_CIERRE`
    no entra: exige que alguien confirme (S9.6.7)."""
    con_version = (
        bd.query(VersionEntrega.id)
        .filter(
            VersionEntrega.entrega_id == FechaEfectiva.entrega_id,
            VersionEntrega.sujeto_id == FechaEfectiva.sujeto_id,
            VersionEntrega.vigente.is_(True),
        )
        .exists()
    )
    return (
        bd.query(FechaEfectiva)
        .join(Entrega, Entrega.id == FechaEfectiva.entrega_id)
        .join(Tarea, Tarea.id == Entrega.tarea_id)
        .filter(
            FechaEfectiva.estado == EstadoFechaEfectiva.VIGENTE.value,
            FechaEfectiva.due_at_utc.isnot(None),
            FechaEfectiva.due_at_utc <= ahora - GRACIA,
            Entrega.estado_validacion == EstadoValidacionEntrega.VIGENTE.value,
            Tarea.estado == EstadoTarea.ACTIVA.value,
            ~con_version,
        )
        .order_by(FechaEfectiva.due_at_utc)
        .limit(limite)
        .all()
    )


def encolar_captura(
    bd: Session,
    *,
    entrega: Entrega,
    sujeto_id: uuid.UUID,
    corte: datetime,
    origen: OrigenCaptura = OrigenCaptura.AUTOMATICA,
    actor_usuario_id: uuid.UUID | None = None,
    motivo_manual: str | None = None,
) -> bool:
    trabajo = trabajos_repo.encolar(
        bd,
        tipo=TIPO_RESOLVER,
        clave_idempotencia=clave_resolver(entrega.id, sujeto_id, corte),
        max_intentos=MAX_INTENTOS,
        curso_id=entrega.curso_id,
        payload={
            "entrega_id": str(entrega.id),
            "sujeto_id": str(sujeto_id),
            "corte": corte.isoformat(),
            "origen": origen.value,
            "actor_usuario_id": str(actor_usuario_id) if actor_usuario_id else None,
            "motivo_manual": motivo_manual,
        },
    )
    return trabajo is not None


def barrido(bd: Session, *, ahora: datetime | None = None) -> int:
    """El tick de `resolver_sha` (cada minuto, global): encola una captura por
    cada `(entrega, sujeto)` vencido. Devuelve cuantas encolo."""
    ahora = ahora or ahora_utc()
    encoladas = 0
    for fecha in candidatos(bd, ahora=ahora):
        entrega = bd.get(Entrega, fecha.entrega_id)
        assert entrega is not None and fecha.due_at_utc is not None
        if encolar_captura(bd, entrega=entrega, sujeto_id=fecha.sujeto_id, corte=fecha.due_at_utc):
            encoladas += 1
    return encoladas


# --- Fase 1: resolver el SHA y escribir la fila ---


def capturar(
    bd: Session,
    cliente: ClienteGitHub,
    *,
    entrega_id: uuid.UUID,
    sujeto_id: uuid.UUID,
    corte: datetime,
    origen: OrigenCaptura = OrigenCaptura.AUTOMATICA,
    actor_usuario_id: uuid.UUID | None = None,
    motivo_manual: str | None = None,
    sha_fijado: str | None = None,
    diferida: bool = False,
) -> VersionEntrega | None:
    """Escribe una fila terminal, o nada si ya no corresponde. Levanta
    `GithubSinAcceso` sin escribir, y deja propagar los errores transitorios
    de GitHub para que el trabajo reintente."""
    ahora = ahora_utc()
    entrega = bd.get(Entrega, entrega_id)
    sujeto = bd.get(Sujeto, sujeto_id)
    assert entrega is not None and sujeto is not None
    if entrega.estado_validacion in (
        EstadoValidacionEntrega.ELIMINADA_EN_CANVAS.value,
        EstadoValidacionEntrega.EXCLUIDA.value,
    ):
        return None  # sin assignment no se escribe evidencia (A-203 punto 6)
    tarea = bd.get(Tarea, entrega.tarea_id)
    curso = bd.get(Curso, entrega.curso_id)
    assert tarea is not None and curso is not None
    anterior = version_vigente(bd, entrega.id, sujeto.id)
    if origen == OrigenCaptura.AUTOMATICA and anterior is not None:
        return anterior  # ya capturada: la clave impide duplicar, esto es el respaldo
    fecha = _fecha_vigente(bd, entrega.id, sujeto.id)
    repositorio = _repositorio_del_sujeto(bd, sujeto.id)
    intento = (
        max(
            (
                i
                for (i,) in bd.query(VersionEntrega.intento).filter(
                    VersionEntrega.entrega_id == entrega.id, VersionEntrega.sujeto_id == sujeto.id
                )
            ),
            default=0,
        )
        + 1
    )
    contexto = _contexto_congelado(bd, curso=curso, sujeto=sujeto, fecha=fecha)
    integrantes = _integrantes_congelados(bd, curso=curso, sujeto=sujeto)

    usable = (
        repositorio is not None
        and repositorio.github_repo_id is not None
        and repositorio.listo_en is not None
        and repositorio.listo_en <= corte
    )
    if not usable and sha_fijado is None:
        # S9.6.6 (A-204 punto 5): no se consulta GitHub; nunca «sin entrega».
        motivo = (
            MotivoVersion.SUJETO_MATERIALIZADO_TRAS_EL_CIERRE
            if sujeto.creado_en > corte
            else MotivoVersion.SIN_REPOSITORIO_AL_CIERRE
        )
        resultado = ResultadoCaptura(
            EstadoVersion.SIN_REPOSITORIO,
            TagEstado.NO_APLICA,
            None,
            None,
            {
                "repositorio_listo_en": repositorio.listo_en.isoformat()
                if repositorio is not None and repositorio.listo_en
                else None
            },
        )
        return _insertar(
            bd,
            entrega=entrega,
            sujeto=sujeto,
            repositorio=None,
            corte=corte,
            intento=intento,
            resultado=resultado,
            motivo=motivo.value,
            advertencias=[],
            contexto=contexto,
            integrantes=integrantes,
            anterior=anterior,
            origen=origen,
            actor_usuario_id=actor_usuario_id,
            motivo_manual=motivo_manual,
            ahora=ahora,
        )

    assert repositorio is not None
    org, nombre_repo, token = _acceso_github(cliente, curso, repositorio)
    rama = repositorio.rama_por_defecto
    try:
        if sha_fijado is not None:
            commit = cliente.obtener_commit(org, nombre_repo, sha_fijado, token)
            if commit is None:
                raise RechazoVersion(
                    "SHA_AJENO",
                    "Ese commit no existe en el repositorio de este sujeto. Revisa el SHA: "
                    "solo se puede fijar un commit del propio repositorio.",
                )
            resultado = ResultadoCaptura(
                EstadoVersion.CAPTURADA_SIN_TAG,
                TagEstado.PENDIENTE,
                None,
                commit,
                {"espejo_sha": None, "github_sha": commit.sha, "fijado_a_mano": True},
            )
        else:
            if rama is None:
                info = cliente.obtener_repo(org, nombre_repo, token)
                rama = info.rama_por_defecto if info is not None else None
            commits = cliente.listar_commits_hasta(
                org, nombre_repo, rama=rama or "HEAD", corte=corte, token_instalacion=token
            )
            resultado = resolver_captura(
                # TODO(etapa-F5): el espejo propio como fuente primaria.
                espejo=None,
                github=seleccionar_commit_cierre(commits, corte=corte),
                commit_inicial_sha=repositorio.commit_inicial_sha,
            )
    except RechazoProveedorGithub as exc:
        if exc.status_code == 429 or (
            exc.status_code == 403 and "rate limit" in exc.mensaje_literal.lower()
        ):
            raise  # Ley 5: un limite no es un error propio; el trabajo reintenta
        resultado = ResultadoCaptura(
            EstadoVersion.ERROR,
            TagEstado.NO_APLICA,
            None,
            None,
            {"error": f"GitHub respondió {exc.status_code}: {exc.mensaje_literal}"},
        )
    usa_lfs = tiene_submodulos = False
    if resultado.commit is not None:
        usa_lfs, tiene_submodulos = _contenido_no_representable(
            cliente, org, nombre_repo, resultado.commit.sha, token
        )
    advertencias, abrir_incidencia = advertencias_de_captura(
        sha=resultado.commit.sha if resultado.commit is not None else None,
        sha_entrega_anterior=_sha_entrega_anterior(bd, entrega=entrega, sujeto=sujeto),
        estado_sujeto_al_cierre=contexto["estado_sujeto_al_cierre"],
        fecha_calculada_en=fecha.calculada_en if fecha is not None else None,
        ahora=ahora,
        captura_diferida_por_github=diferida,
        usa_lfs=usa_lfs,
        tiene_submodulos=tiene_submodulos,
    )
    entrada = instante_retirada("versiones_entrega")
    motivo_alcance = (
        motivo_por_alcance(corte=corte, entrada_en_servicio=entrada)
        if origen == OrigenCaptura.AUTOMATICA and entrada is not None
        else None
    )
    version = _insertar(
        bd,
        entrega=entrega,
        sujeto=sujeto,
        repositorio=repositorio,
        corte=corte,
        intento=intento,
        resultado=resultado,
        motivo=motivo_alcance.value if motivo_alcance is not None else None,
        advertencias=[a.value for a in advertencias],
        contexto=contexto,
        integrantes=integrantes,
        anterior=anterior,
        origen=origen,
        actor_usuario_id=actor_usuario_id,
        motivo_manual=motivo_manual,
        ahora=ahora,
        rama=rama,
    )
    if resultado.estado == EstadoVersion.REVISAR:
        _abrir_version_revisar(bd, version, motivo="DISCREPANCIA_SHA")
    if resultado.estado == EstadoVersion.ERROR:
        _abrir_version_revisar(bd, version, motivo="ERROR_AL_RESOLVER_SHA")
    if abrir_incidencia:
        _abrir_version_revisar(
            bd,
            version,
            motivo="FECHAS_POSIBLEMENTE_DESACTUALIZADAS",
            accion="restablece la credencial de Canvas y revisa esta fecha",
        )
    return version


def _insertar(
    bd: Session,
    *,
    entrega: Entrega,
    sujeto: Sujeto,
    repositorio: Repositorio | None,
    corte: datetime,
    intento: int,
    resultado: ResultadoCaptura,
    motivo: str | None,
    advertencias: list[str],
    contexto: dict[str, Any],
    integrantes: list[dict[str, Any]],
    anterior: VersionEntrega | None,
    origen: OrigenCaptura,
    actor_usuario_id: uuid.UUID | None,
    motivo_manual: str | None,
    ahora: datetime,
    rama: str | None = None,
) -> VersionEntrega:
    """Una sola transaccion: la anterior deja de ser vigente (una accion
    manual nunca la modifica en nada mas, S9.8.8) y nace la nueva."""
    if anterior is not None:
        transicionar(bd, anterior, vigente=False)
    commit: CommitCierre | None = resultado.commit
    etiqueta = (
        nombre_tag(orden=entrega.orden, slug=entrega.slug, intento=intento)
        if resultado.tag_estado == TagEstado.PENDIENTE
        else None
    )
    version = VersionEntrega(
        entrega_id=entrega.id,
        sujeto_id=sujeto.id,
        repositorio_id=repositorio.id if repositorio is not None else None,
        intento=intento,
        fecha_corte_utc=corte,
        rama=rama,
        commit_sha=commit.sha if commit is not None else None,
        commit_tree_sha=commit.tree_sha if commit is not None else None,
        commit_fecha_autor=commit.fecha_autor if commit is not None else None,
        commit_fecha_committer=commit.fecha_committer if commit is not None else None,
        commit_mensaje=commit.mensaje if commit is not None else None,
        tag_nombre=etiqueta,
        tag_estado=resultado.tag_estado.value,
        tag_motivo=resultado.tag_motivo.value if resultado.tag_motivo is not None else None,
        tag_creado=False,
        estado=resultado.estado.value,
        motivo=motivo,
        motivo_repositorio=repositorio.motivo if repositorio is not None else None,
        vigente=True,
        reemplaza_a_id=anterior.id if anterior is not None else None,
        advertencias=advertencias,
        verificacion=resultado.verificacion,
        integrantes=integrantes,
        origen_captura=origen.value,
        creada_por_usuario_id=actor_usuario_id,
        motivo_manual=motivo_manual,
        capturada_en=ahora,
        **contexto,
    )
    bd.add(version)
    bd.flush()
    if etiqueta is not None:
        encolar_etiqueta(bd, version)
    registrar_bitacora(
        bd,
        accion="VERSION_REGISTRADA",
        entidad="version_entrega",
        entidad_id=str(version.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=entrega.curso_id,
        antes={"reemplaza_a": str(anterior.id)} if anterior is not None else None,
        despues={
            "estado": version.estado,
            "commit_sha": version.commit_sha,
            "fecha_corte_utc": corte.isoformat(),
            "intento": intento,
            "origen_captura": origen.value,
        },
    )
    return version


def _acceso_github(
    cliente: ClienteGitHub, curso: Curso, repositorio: Repositorio
) -> tuple[str, str, str]:
    if curso.github_installation_id is None or curso.github_org_login is None:
        raise GithubSinAcceso("el curso no tiene instalacion de GitHub")
    try:
        token = cliente.obtener_token_instalacion(curso.github_installation_id)
    except (FalloProveedorGithub, RechazoProveedorGithub) as exc:
        raise GithubSinAcceso(str(exc)) from exc
    nombre = (repositorio.full_name or "").split("/", 1)[-1] or repositorio.nombre
    return curso.github_org_login, nombre, token


def _contenido_no_representable(
    cliente: ClienteGitHub, org: str, repo: str, sha: str, token: str
) -> tuple[bool, bool]:
    """S9.10.5: 1-2 lecturas acotadas, sin descargar el arbol. Informativo:
    si GitHub no responde, no se marca nada y la captura sigue."""
    try:
        atributos = cliente.obtener_archivo(org, repo, ".gitattributes", token, ref=sha)
        submodulos = cliente.obtener_archivo(org, repo, ".gitmodules", token, ref=sha)
    except (FalloProveedorGithub, RechazoProveedorGithub):
        return False, False
    usa_lfs = False
    if atributos is not None and atributos.contenido_base64:
        texto = base64.b64decode(atributos.contenido_base64).decode("utf-8", "ignore")
        usa_lfs = "filter=lfs" in texto
    return usa_lfs, submodulos is not None


def _sha_entrega_anterior(bd: Session, *, entrega: Entrega, sujeto: Sujeto) -> str | None:
    """S9.7.3: el SHA vigente de «la entrega anterior» para este sujeto."""
    filas = (
        bd.query(Entrega.id, Entrega.orden, FechaEfectiva.due_at_utc)
        .join(FechaEfectiva, FechaEfectiva.entrega_id == Entrega.id)
        .filter(
            Entrega.tarea_id == entrega.tarea_id,
            FechaEfectiva.sujeto_id == sujeto.id,
            FechaEfectiva.estado == EstadoFechaEfectiva.VIGENTE.value,
        )
        .all()
    )
    anterior = entrega_anterior(
        [EntregaDelSujeto(entrega_id=i, orden=o, due_at=d) for i, o, d in filas],
        actual=entrega.id,
    )
    if anterior is None:
        return None
    version = version_vigente(bd, anterior, sujeto.id)  # type: ignore[arg-type]
    return version.commit_sha if version is not None else None


def _contexto_congelado(
    bd: Session, *, curso: Curso, sujeto: Sujeto, fecha: FechaEfectiva | None
) -> dict[str, Any]:
    """S9.9.1: lo que hace la fila legible aunque el origen desaparezca."""
    repositorio = _repositorio_del_sujeto(bd, sujeto.id)
    regla = bd.get(ReglaFecha, fecha.regla_fecha_id) if fecha and fecha.regla_fecha_id else None
    if sujeto.grupo_id is not None:
        grupo = bd.get(Grupo, sujeto.grupo_id)
        etiqueta = grupo.nombre if grupo is not None else "—"
        estado_sujeto = grupo.estado if grupo is not None else None
        seccion = None
    else:
        estudiante = bd.get(Estudiante, sujeto.estudiante_id)
        etiqueta = estudiante.nombre if estudiante is not None else "—"
        estado_sujeto = estudiante.estado if estudiante is not None else None
        seccion = _seccion_de(bd, sujeto.estudiante_id) if sujeto.estudiante_id else None
    return {
        "github_repo_id": repositorio.github_repo_id if repositorio is not None else None,
        "repositorio_full_name": repositorio.full_name if repositorio is not None else None,
        "org_login": curso.github_org_login,
        "installation_id": curso.github_installation_id,
        "sujeto_tipo": sujeto.tipo,
        "sujeto_etiqueta": etiqueta,
        "estado_sujeto_al_cierre": estado_sujeto,
        "seccion_nombre": seccion.nombre if seccion is not None else None,
        "canvas_section_id": seccion.canvas_section_id if seccion is not None else None,
        "fecha_origen": fecha.origen if fecha is not None else None,
        "canvas_override_id": regla.canvas_override_id if regla is not None else None,
        "override_titulo": regla.titulo if regla is not None else None,
        "fecha_ambigua": fecha.ambigua if fecha is not None else False,
    }


def _seccion_de(bd: Session, estudiante_id: uuid.UUID) -> Seccion | None:
    return (
        bd.query(Seccion)
        .join(Matricula, Matricula.seccion_id == Seccion.id)
        .filter(Matricula.estudiante_id == estudiante_id, Matricula.activa.is_(True))
        .order_by(Seccion.canvas_section_id)
        .first()
    )


def _integrantes_congelados(bd: Session, *, curso: Curso, sujeto: Sujeto) -> list[dict[str, Any]]:
    """A-204 punto 4: un objeto por integrante `accepted` al corte, con los
    campos exactos de la decision; una tarea individual lleva uno solo."""
    miembros: list[tuple[Estudiante, str | None]]
    if sujeto.grupo_id is not None:
        miembros = [
            (e, pg.workflow_state)
            for e, pg in bd.query(Estudiante, PertenenciaGrupo)
            .join(PertenenciaGrupo, PertenenciaGrupo.estudiante_id == Estudiante.id)
            .filter(
                PertenenciaGrupo.grupo_id == sujeto.grupo_id,
                PertenenciaGrupo.activa.is_(True),
                PertenenciaGrupo.workflow_state == WorkflowStatePertenenciaGrupo.ACCEPTED.value,
            )
        ]
    else:
        estudiante = bd.get(Estudiante, sujeto.estudiante_id)
        miembros = [(estudiante, None)] if estudiante is not None else []
    salida = []
    for estudiante, workflow in miembros:
        mapeo = (
            bd.query(MapeoGithub)
            .filter(
                MapeoGithub.curso_id == curso.id,
                MapeoGithub.estudiante_id == estudiante.id,
                MapeoGithub.estado == EstadoMapeoGithub.VIGENTE.value,
            )
            .first()
        )
        cuenta = (
            bd.get(CuentaGithub, mapeo.cuenta_github_id)
            if mapeo and mapeo.cuenta_github_id
            else None
        )
        seccion = _seccion_de(bd, estudiante.id)
        salida.append(
            {
                "estudiante_id": str(estudiante.id),
                "canvas_user_id": estudiante.canvas_user_id,
                "nombre": estudiante.nombre,
                "github_user_id": cuenta.github_user_id if cuenta is not None else None,
                "github_login": cuenta.login if cuenta is not None else None,
                "mapeo_github_id": str(mapeo.id) if mapeo is not None else None,
                "workflow_state_pertenencia": workflow,
                "estado_matricula": estudiante.estado,
                "seccion_id": str(seccion.id) if seccion is not None else None,
                "canvas_section_id": seccion.canvas_section_id if seccion is not None else None,
            }
        )
    return salida


def _abrir_version_revisar(
    bd: Session, version: VersionEntrega, *, motivo: str, accion: str | None = None
) -> None:
    entrega = bd.get(Entrega, version.entrega_id)
    assert entrega is not None
    incidencia_repo.abrir_o_actualizar(
        bd,
        tipo="VERSION_REVISAR",
        severidad="ADVERTENCIA",
        sujeto_tipo="VERSION",
        curso_id=entrega.curso_id,
        sujeto_id=version.id,
        detalle={
            "motivo": motivo,
            "entrega": entrega.nombre,
            "sujeto": version.sujeto_etiqueta,
            "commit_sha": version.commit_sha,
            "verificacion": version.verificacion,
            **({"accion_sugerida": accion} if accion else {}),
        },
    )


# --- Fase 2: la etiqueta (S9.6.2) ---


def encolar_etiqueta(bd: Session, version: VersionEntrega, *, sufijo: str = "") -> None:
    trabajos_repo.encolar(
        bd,
        tipo=TIPO_ETIQUETA,
        clave_idempotencia=f"tag:{version.entrega_id}:{version.sujeto_id}:{version.intento}{sufijo}",
        max_intentos=MAX_INTENTOS,
        curso_id=bd.get(Entrega, version.entrega_id).curso_id,  # type: ignore[union-attr]
        payload={"version_id": str(version.id)},
    )


def crear_etiqueta(bd: Session, cliente: ClienteGitHub, *, version: VersionEntrega) -> None:
    """Solo mueve `CAPTURADA_SIN_TAG -> CAPTURADA` y `tag_estado PENDIENTE ->
    {CREADO, CONFLICTO, FALLIDO}`. Nunca sobrescribe una etiqueta que apunta a
    otro SHA (S9.8.5). Un limite deja la etiqueta pendiente y relanza para que
    el trabajo reintente: el SHA ya esta registrado (CA-9.6-06)."""
    if version.tag_estado != TagEstado.PENDIENTE.value or version.tag_nombre is None:
        return
    assert version.commit_sha is not None and version.org_login is not None
    entrega = bd.get(Entrega, version.entrega_id)
    curso = bd.get(Curso, entrega.curso_id) if entrega is not None else None
    if curso is None or curso.github_installation_id is None:
        raise GithubSinAcceso("el curso no tiene instalacion de GitHub")
    repo = (version.repositorio_full_name or "").split("/", 1)[-1]
    try:
        token = cliente.obtener_token_instalacion(curso.github_installation_id)
        existente = cliente.obtener_ref_tag(version.org_login, repo, version.tag_nombre, token)
        if existente is None:
            try:
                cliente.crear_ref_tag(
                    version.org_login, repo, version.tag_nombre, version.commit_sha, token
                )
                existente = version.commit_sha
            except RechazoProveedorGithub as exc:
                if exc.status_code != 422:
                    raise
                # Carrera: alguien la creo entre la lectura y la escritura.
                existente = cliente.obtener_ref_tag(
                    version.org_login, repo, version.tag_nombre, token
                )
    except RechazoProveedorGithub as exc:
        tag_estado, tag_motivo, reintentar = tag_tras_rechazo(exc.status_code, exc.mensaje_literal)
        transicionar(
            bd,
            version,
            tag_estado=tag_estado.value,
            tag_motivo=tag_motivo.value,
            tag_error=exc.mensaje_literal,
            estado=estado_tras_etiqueta(EstadoVersion(version.estado), tag_estado).value,
        )
        if tag_motivo == TagMotivo.REPOSITORIO_ARCHIVADO:
            _abrir_version_revisar(
                bd,
                version,
                motivo="REPOSITORIO_ARCHIVADO",
                accion="desarchiva el repositorio y pulsa «reintentar etiqueta»",
            )
        if reintentar:
            raise
        return
    except FalloProveedorGithub:
        transicionar(bd, version, tag_motivo=TagMotivo.DESCONOCIDO.value)
        raise
    if existente == version.commit_sha:
        transicionar(
            bd,
            version,
            tag_estado=TagEstado.CREADO.value,
            tag_motivo=None,
            tag_error=None,
            tag_creado=True,
            estado=estado_tras_etiqueta(EstadoVersion(version.estado), TagEstado.CREADO).value,
        )
        return
    transicionar(
        bd,
        version,
        tag_estado=TagEstado.CONFLICTO.value,
        tag_motivo=TagMotivo.SHA_DISTINTO.value,
        tag_error=f"La etiqueta {version.tag_nombre} ya apunta a {existente}.",
        estado=estado_tras_etiqueta(EstadoVersion(version.estado), TagEstado.CONFLICTO).value,
    )
    _abrir_version_revisar(bd, version, motivo="TAG_OCUPADO")


# --- Verificacion diaria (S9.8.5, S9.10.2) ---


def verificar_versiones(bd: Session, cliente: ClienteGitHub, *, curso: Curso) -> int:
    """Para cada version vigente del curso: la etiqueta creada sigue apuntando
    al mismo SHA y el SHA sigue siendo alcanzable. Nunca toca la evidencia:
    solo la etiqueta, las advertencias y las incidencias (CA-9.10-04)."""
    if curso.github_installation_id is None or curso.github_org_login is None:
        return 0
    versiones = (
        bd.query(VersionEntrega)
        .join(Entrega, Entrega.id == VersionEntrega.entrega_id)
        .filter(
            Entrega.curso_id == curso.id,
            VersionEntrega.vigente.is_(True),
            VersionEntrega.commit_sha.isnot(None),
        )
        .all()
    )
    if not versiones:
        return 0
    token = cliente.obtener_token_instalacion(curso.github_installation_id)
    hoy = ahora_utc().date().isoformat()
    for version in versiones:
        repo = (version.repositorio_full_name or "").split("/", 1)[-1]
        org = version.org_login or curso.github_org_login
        assert version.commit_sha is not None
        try:
            if version.tag_estado == TagEstado.CREADO.value and version.tag_nombre:
                apunta = cliente.obtener_ref_tag(org, repo, version.tag_nombre, token)
                if apunta is None:
                    # Borrada: se recrea desde el SHA guardado (CA-9.8-04).
                    transicionar(
                        bd,
                        version,
                        tag_estado=TagEstado.PENDIENTE.value,
                        tag_creado=False,
                        estado=estado_tras_etiqueta(
                            EstadoVersion(version.estado), TagEstado.PENDIENTE
                        ).value,
                    )
                    _abrir_tag_alterado(bd, curso, version, "TAG_BORRADO", None)
                    encolar_etiqueta(bd, version, sufijo=f":recrear:{hoy}")
                elif apunta != version.commit_sha:
                    # Movida: jamas se sobrescribe.
                    transicionar(
                        bd,
                        version,
                        tag_estado=TagEstado.CONFLICTO.value,
                        tag_motivo=TagMotivo.SHA_DISTINTO.value,
                        tag_error=f"La etiqueta {version.tag_nombre} ahora apunta a {apunta}.",
                        estado=estado_tras_etiqueta(
                            EstadoVersion(version.estado), TagEstado.CONFLICTO
                        ).value,
                    )
                    _abrir_tag_alterado(bd, curso, version, "TAG_MOVIDO", apunta)
            if cliente.obtener_commit(org, repo, version.commit_sha, token) is None:
                if "SHA_PUEDE_SER_INALCANZABLE" not in (version.advertencias or []):
                    transicionar(
                        bd,
                        version,
                        advertencias=[*(version.advertencias or []), "SHA_PUEDE_SER_INALCANZABLE"],
                    )
                _abrir_version_revisar(bd, version, motivo="SHA_NO_ALCANZABLE")
        except (RechazoProveedorGithub, FalloProveedorGithub):
            continue  # se reintenta en la verificacion siguiente
    return len(versiones)


def _abrir_tag_alterado(
    bd: Session, curso: Curso, version: VersionEntrega, motivo: str, apunta: str | None
) -> None:
    incidencia_repo.abrir_o_actualizar(
        bd,
        tipo="TAG_ALTERADO",
        severidad="ADVERTENCIA",
        sujeto_tipo="VERSION",
        curso_id=curso.id,
        sujeto_id=version.id,
        detalle={
            "motivo": motivo,
            "tag": version.tag_nombre,
            "sha_version": version.commit_sha,
            "sha_etiqueta": apunta,
        },
    )


# --- S9.8.2 (A-103): recaptura ante cambio de fecha ---


def al_cambiar_la_fecha(
    bd: Session,
    *,
    entrega_id: uuid.UUID,
    sujeto_id: uuid.UUID,
    fecha_anterior: datetime | None,
    fecha_nueva: datetime | None,
) -> None:
    """Sin confirmacion humana y simetrico: la version capturada con la fecha
    anterior deja de ser vigente (`FECHA_ADELANTADA` o `FECHA_EXTENDIDA`) y el
    barrido captura de nuevo con la fecha nueva cuando corresponda. Una version
    fijada a mano con otro corte no se toca."""
    version = version_vigente(bd, entrega_id, sujeto_id)
    if version is None or fecha_anterior is None or version.fecha_corte_utc != fecha_anterior:
        return
    motivo = motivo_de_supersede(corte_version=version.fecha_corte_utc, nueva_fecha=fecha_nueva)
    if motivo is None:
        return
    transicionar(bd, version, vigente=False, motivo=motivo.value)
    entrega = bd.get(Entrega, entrega_id)
    assert entrega is not None
    registrar_bitacora(
        bd,
        accion="VERSION_SUPERSEDIDA",
        entidad="version_entrega",
        entidad_id=str(version.id),
        curso_id=entrega.curso_id,
        antes={"fecha_corte_utc": version.fecha_corte_utc.isoformat()},
        despues={
            "motivo": motivo.value,
            "fecha_nueva": fecha_nueva.isoformat() if fecha_nueva is not None else None,
        },
    )


# --- S9.6.6: el repositorio que aparece despues del cierre ---


def al_quedar_listo_el_repositorio(bd: Session, repositorio: Repositorio) -> None:
    """No se captura solo (RG-027): se abre `VERSION_REVISAR` con la accion
    sugerida, y «capturar ahora» lo resuelve en un clic."""
    for version in bd.query(VersionEntrega).filter(
        VersionEntrega.sujeto_id == repositorio.sujeto_id,
        VersionEntrega.vigente.is_(True),
        VersionEntrega.estado == EstadoVersion.SIN_REPOSITORIO.value,
    ):
        _abrir_version_revisar(
            bd,
            version,
            motivo="REPOSITORIO_DISPONIBLE_TRAS_EL_CIERRE",
            accion="captura ahora la versión o fija una fecha de corte propia",
        )


# --- Acciones del docente (S9.6.7, S9.8.8) ---

_LARGO_MINIMO_MOTIVO = 10


def validar_motivo_manual(motivo: str) -> str:
    texto = motivo.strip()
    if len(texto) < _LARGO_MINIMO_MOTIVO:
        raise RechazoVersion(
            "MOTIVO_INSUFICIENTE",
            "Escribe por qué haces esta acción (al menos 10 caracteres): queda en la bitácora "
            "y junto a la versión.",
        )
    return texto


def corte_para_capturar_ahora(bd: Session, *, entrega: Entrega, sujeto: Sujeto) -> datetime:
    """«Capturar ahora» adelanta el trabajo sin cambiar la fecha de corte, y
    solo sin version vigente. Excepcion: sobre `SIN_REPOSITORIO` la vigente no
    tiene evidencia que perder y el corte original daria un falso
    `SIN_COMMITS` (S9.6.6): se captura con el instante de la accion, y la
    pantalla lo dice. Decision documentada."""
    vigente = version_vigente(bd, entrega.id, sujeto.id)
    if vigente is not None and vigente.estado != EstadoVersion.SIN_REPOSITORIO.value:
        raise RechazoVersion(
            "YA_HAY_VERSION",
            "Este sujeto ya tiene una versión registrada para esta entrega. Para cambiarla usa "
            "«recapturar con otra fecha» o «fijar en un commit».",
        )
    if vigente is not None:
        return ahora_utc()
    fecha = _fecha_vigente(bd, entrega.id, sujeto.id)
    if fecha is None or fecha.due_at_utc is None or fecha.due_at_utc > ahora_utc():
        raise RechazoVersion(
            "FECHA_NO_VENCIDA",
            "La fecha de cierre de este sujeto aún no llega: la versión se registra sola "
            "al cierre.",
        )
    return fecha.due_at_utc


def validar_corte_manual(bd: Session, *, sujeto: Sujeto, corte: datetime) -> None:
    """S9.8.8 accion 2: una fecha pasada y posterior a la creacion del repositorio."""
    if corte > ahora_utc():
        raise RechazoVersion("CORTE_FUTURO", "La fecha de corte tiene que estar en el pasado.")
    repositorio = _repositorio_del_sujeto(bd, sujeto.id)
    if repositorio is None or repositorio.listo_en is None or corte < repositorio.listo_en:
        raise RechazoVersion(
            "CORTE_ANTERIOR_AL_REPOSITORIO",
            "La fecha de corte tiene que ser posterior a la creación del repositorio.",
        )


def registrar_versiones_tras_cierre(
    bd: Session, *, entrega: Entrega, actor_usuario_id: uuid.UUID
) -> int:
    """S9.6.7: la confirmacion explicita de una entrega vinculada con la fecha
    ya vencida. Encola la captura de cada sujeto con su fecha vencida y deja la
    entrega `VIGENTE`, para que en adelante se capture sola."""
    if entrega.estado_validacion != EstadoValidacionEntrega.VINCULADA_TRAS_EL_CIERRE.value:
        raise RechazoVersion(
            "NO_VINCULADA_TRAS_EL_CIERRE",
            "Esta entrega no está esperando confirmación: sus versiones se registran solas.",
        )
    ahora = ahora_utc()
    encoladas = 0
    for fecha in bd.query(FechaEfectiva).filter(
        FechaEfectiva.entrega_id == entrega.id,
        FechaEfectiva.estado == EstadoFechaEfectiva.VIGENTE.value,
        FechaEfectiva.due_at_utc.isnot(None),
        FechaEfectiva.due_at_utc <= ahora,
    ):
        if version_vigente(bd, entrega.id, fecha.sujeto_id) is not None:
            continue
        assert fecha.due_at_utc is not None
        if encolar_captura(
            bd,
            entrega=entrega,
            sujeto_id=fecha.sujeto_id,
            corte=fecha.due_at_utc,
            origen=OrigenCaptura.MANUAL_AHORA,
            actor_usuario_id=actor_usuario_id,
            motivo_manual="Registro confirmado de una entrega vinculada después de su cierre.",
        ):
            encoladas += 1
    entrega.estado_validacion = EstadoValidacionEntrega.VIGENTE.value
    bd.flush()
    registrar_bitacora(
        bd,
        accion="VERSIONES_REGISTRADAS_TRAS_CIERRE",
        entidad="entrega",
        entidad_id=str(entrega.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=entrega.curso_id,
        despues={"capturas_encoladas": encoladas},
    )
    return encoladas
