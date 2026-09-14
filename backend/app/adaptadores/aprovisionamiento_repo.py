"""Aprovisionamiento automatico de repositorios (SPEC 08 S8.5-S8.11; A-092 a
A-097, A-163, A-164, A-202, A-211, A-212; Etapa P8).

Orquesta la maquina 2 (repositorio) y la maquina 3 (acceso del estudiante) con
I/O real contra GitHub. Las decisiones viven en `app/dominio/aprovisionamiento.py`.

Simplificaciones de esta etapa, cada una con su TODO donde toca:
- Solo tareas `INDIVIDUAL` (la grupal es la bandera `tarea_modalidad_grupal`).
- Sin receptor de webhooks: la aceptacion de una invitacion la detecta la
  reconciliacion (`GET collaborators/{login}`), no el webhook `member`.
- Un repositorio sin base se crea con `auto_init` (+ `.gitignore` si la tarea lo
  declara): es el camino alternativo que RG-089 declara de antemano, porque la
  Git Data API no opera sobre un repositorio vacio. La guia de acceso viaja por
  Canvas (R2.3.12).
- Ritmo: el trabajador procesa un trabajo a la vez y el barrido toma un tope
  por ciclo; el freno por cabeceras de limite medidas (S8.7.2) no esta aun.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.adaptadores import fechas_repo, incidencia_repo, outbox_repo, trabajos_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.bitacora_repo import registrar as registrar_bitacora
from app.adaptadores.cliente_github import (
    ClienteGitHub,
    FalloProveedorGithub,
    RechazoProveedorGithub,
)
from app.adaptadores.modelos_aprovisionamiento import AccesoRepositorio, Repositorio, Sujeto
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_github import AccesoDocenteRepositorio, EquipoGithubCurso
from app.adaptadores.modelos_mapeo import CuentaGithub, MapeoGithub
from app.adaptadores.modelos_padron import Estudiante
from app.adaptadores.modelos_tarea import (
    Entrega,
    RepositorioBase,
    Tarea,
    VisibilidadEntrega,
)
from app.dominio.aprovisionamiento import (
    ESPERA_LIMITE_POR_DEFECTO,
    ESTADOS_ACCESO_CUBIERTO,
    ESTADOS_EN_CURSO,
    MAX_INTENTOS_TRANSITORIOS,
    REEVALUACION_BLOQUEADO,
    SONDEOS_CONTENIDO_SEGUNDOS,
    clasificar_rechazo_github,
    destino_al_reintentar,
    espera_reintento,
    estado_acceso_tras_invitar,
    evaluar_predicado_operativo,
    listo_para_reintentar,
    minutos_restantes,
    motivo_espera_individual,
    motivo_no_es_sujeto_individual,
)
from app.dominio.estados import (
    EstadoAccesoDocente,
    EstadoAccesoRepositorio,
    EstadoMapeoGithub,
    EstadoRepositorio,
    EstadoRepositorioBase,
    EstadoTarea,
    EstadoValidacionEntrega,
    FamiliaError,
    ModalidadTarea,
    SubtipoErrorPermanente,
    TipoSujeto,
    ViaAccesoDocente,
)
from app.dominio.nombres_repositorio import (
    SujetoNombre,
    marcador_descripcion,
    nombre_repositorio,
    topics_repositorio,
)
from app.dominio.repositorio_github import RepoGithubInfo
from app.dominio.tareas import condiciones_adopcion_fallidas

TIPO_TRABAJO = "aprovisionar_repositorios"
_ESTADOS_QUE_EL_TRABAJO_AVANZA = frozenset(
    {
        EstadoRepositorio.LISTO_PARA_CREAR.value,
        EstadoRepositorio.CREANDO.value,
        EstadoRepositorio.CREADO_SIN_CONTENIDO.value,
        EstadoRepositorio.CONTENIDO_LISTO.value,
        EstadoRepositorio.CONFIGURANDO_ACCESOS.value,
        EstadoRepositorio.ERROR_TRANSITORIO.value,
        EstadoRepositorio.ESPERANDO_LIMITE.value,
        EstadoRepositorio.BLOQUEADO.value,
    }
)
_ESTADOS_QUE_RECONCILIA = frozenset(
    {
        EstadoRepositorio.DEGRADADO.value,
        EstadoRepositorio.OPERATIVO.value,
        EstadoRepositorio.FUERA_DE_ALCANCE.value,
    }
)


def _mapeos_vigentes(bd: Session, curso_id: uuid.UUID) -> dict[uuid.UUID, MapeoGithub]:
    """El mapeo vivo (no `SUPERSEDIDO`) de cada estudiante del curso."""
    return {
        m.estudiante_id: m
        for m in bd.query(MapeoGithub).filter(
            MapeoGithub.curso_id == curso_id,
            MapeoGithub.estado != EstadoMapeoGithub.SUPERSEDIDO.value,
        )
    }


def _nombre_del_sujeto(curso: Curso, tarea: Tarea, estudiante: Estudiante) -> str:
    return nombre_repositorio(
        curso_slug=curso.slug,
        tarea_slug=tarea.slug,
        sujeto=SujetoNombre(
            tipo="e",
            canvas_id=estudiante.canvas_user_id,
            texto_legible=estudiante.nombre_ordenable or estudiante.nombre,
        ),
    )


def encolar_aprovisionamiento(
    bd: Session, repositorio: Repositorio, *, sufijo: str = "", cuando: datetime | None = None
) -> None:
    """S8.7.1: clave `repo:<tarea>:<sujeto>`; encolar dos veces es un no-op por
    indice unico (CA-8.7-01)."""
    trabajo = trabajos_repo.encolar(
        bd,
        tipo=TIPO_TRABAJO,
        clave_idempotencia=f"repo:{repositorio.tarea_id}:{repositorio.sujeto_id}{sufijo}",
        max_intentos=MAX_INTENTOS_TRANSITORIOS,
        curso_id=repositorio.curso_id,
        payload={"repositorio_id": str(repositorio.id)},
    )
    if trabajo is not None and cuando is not None:
        trabajo.proximo_intento_en = cuando
        bd.flush()


# --- A-164: materializar sujetos, y la guarda de A-093 ---


def materializar_sujetos(bd: Session, *, curso: Curso) -> int:
    """Recalcula el conjunto de sujetos de cada tarea activa y deja cada
    repositorio pendiente en `ESPERANDO_INFORMACION` (con motivo) o en
    `LISTO_PARA_CREAR`, encolando el aprovisionamiento de estos ultimos.
    Devuelve cuantos quedaron listos para crear. No llama a ningun proveedor."""
    ahora = ahora_utc()
    listos = 0
    estudiantes = bd.query(Estudiante).filter(Estudiante.curso_id == curso.id).all()
    mapeos = _mapeos_vigentes(bd, curso.id)
    tareas = (
        bd.query(Tarea)
        .filter(Tarea.curso_id == curso.id, Tarea.estado.in_([EstadoTarea.ACTIVA.value]))
        .all()
    )
    for tarea in tareas:
        if tarea.modalidad != ModalidadTarea.INDIVIDUAL.value:
            continue  # TODO(etapa-F1): sujetos de grupo (A-164 paso 2, tarea grupal)
        visibles = {
            estudiante_id
            for (estudiante_id,) in bd.query(VisibilidadEntrega.estudiante_id)
            .join(Entrega, Entrega.id == VisibilidadEntrega.entrega_id)
            .filter(
                Entrega.tarea_id == tarea.id,
                Entrega.estado_validacion == EstadoValidacionEntrega.VIGENTE.value,
                VisibilidadEntrega.visible.is_(True),
            )
        }
        sujetos = {
            s.estudiante_id: s
            for s in bd.query(Sujeto).filter(
                Sujeto.tarea_id == tarea.id, Sujeto.tipo == TipoSujeto.ESTUDIANTE.value
            )
        }
        for estudiante in estudiantes:
            motivo_baja = motivo_no_es_sujeto_individual(
                estado_estudiante=estudiante.estado,
                visible_en_alguna_entrega=estudiante.id in visibles,
            )
            sujeto = sujetos.get(estudiante.id)
            if motivo_baja is not None:
                if sujeto is not None and sujeto.activo:
                    _desactivar_sujeto(bd, sujeto, motivo=motivo_baja.value, ahora=ahora)
                continue
            if sujeto is None:
                sujeto = Sujeto(
                    tarea_id=tarea.id,
                    tipo=TipoSujeto.ESTUDIANTE.value,
                    estudiante_id=estudiante.id,
                    activo=True,
                    creado_en=ahora,
                )
                bd.add(sujeto)
                bd.flush()
            elif not sujeto.activo:
                _reactivar_sujeto(bd, sujeto, ahora=ahora)

            repositorio = _repositorio_vivo(bd, sujeto.id)
            if repositorio is None:
                nombre = _nombre_del_sujeto(curso, tarea, estudiante)
                repositorio = Repositorio(
                    curso_id=curso.id,
                    tarea_id=tarea.id,
                    sujeto_id=sujeto.id,
                    nombre=nombre,
                    nombre_canonico=nombre,
                    estado=EstadoRepositorio.ESPERANDO_INFORMACION.value,
                    intentos=0,
                    sondeos_contenido=0,
                    creado_en=ahora,
                    actualizado_en=ahora,
                )
                bd.add(repositorio)
                bd.flush()
            if repositorio.estado in (
                EstadoRepositorio.ESPERANDO_INFORMACION.value,
                EstadoRepositorio.LISTO_PARA_CREAR.value,
            ):
                mapeo = mapeos.get(estudiante.id)
                motivo = motivo_espera_individual(
                    estado_mapeo=mapeo.estado if mapeo is not None else None,
                    estado_tarea=tarea.estado,
                )
                if motivo is None:
                    repositorio.estado = EstadoRepositorio.LISTO_PARA_CREAR.value
                    repositorio.motivo = None
                    listos += 1
                    encolar_aprovisionamiento(bd, repositorio)
                else:
                    repositorio.estado = EstadoRepositorio.ESPERANDO_INFORMACION.value
                    repositorio.motivo = motivo.value
                repositorio.actualizado_en = ahora
        bd.flush()
        fechas_repo.recalcular_fechas_tarea(bd, curso_id=curso.id, tarea_id=tarea.id)
    return listos


def _repositorio_vivo(bd: Session, sujeto_id: uuid.UUID) -> Repositorio | None:
    """A-202: el repositorio del sujeto que no esta `INACCESIBLE` (a lo sumo uno)."""
    return (
        bd.query(Repositorio)
        .filter(
            Repositorio.sujeto_id == sujeto_id,
            Repositorio.estado != EstadoRepositorio.INACCESIBLE.value,
        )
        .one_or_none()
    )


def _desactivar_sujeto(bd: Session, sujeto: Sujeto, *, motivo: str, ahora: datetime) -> None:
    """A-095: nunca se borra; el repositorio que ya existe pasa a
    `FUERA_DE_ALCANCE` conservando todo (CA-8.5-03)."""
    sujeto.activo = False
    sujeto.desactivado_en = ahora
    sujeto.motivo_desactivacion = motivo
    repositorio = _repositorio_vivo(bd, sujeto.id)
    if repositorio is not None and repositorio.github_repo_id is not None:
        repositorio.estado = EstadoRepositorio.FUERA_DE_ALCANCE.value
        repositorio.motivo = None
        repositorio.actualizado_en = ahora
    bd.flush()


def _reactivar_sujeto(bd: Session, sujeto: Sujeto, *, ahora: datetime) -> None:
    """S8.11.5: se reactiva la misma fila; el estado del repositorio lo dicta el
    predicado en la proxima reconciliacion, nunca se escribe `OPERATIVO` por
    suposicion."""
    sujeto.activo = True
    sujeto.desactivado_en = None
    sujeto.motivo_desactivacion = None
    repositorio = _repositorio_vivo(bd, sujeto.id)
    if repositorio is not None and repositorio.estado == EstadoRepositorio.FUERA_DE_ALCANCE.value:
        repositorio.estado = EstadoRepositorio.DEGRADADO.value
        repositorio.actualizado_en = ahora
    bd.flush()


# --- La maquina 2, paso a paso ---


@dataclass(frozen=True)
class _Contexto:
    curso: Curso
    tarea: Tarea
    sujeto: Sujeto
    estudiante: Estudiante
    org: str
    token: str


def aprovisionar_repositorio(
    bd: Session,
    cliente: ClienteGitHub,
    *,
    repositorio: Repositorio,
    trabajo_id: uuid.UUID | None = None,
) -> None:
    """Avanza un repositorio todo lo que pueda en este ciclo. Nunca crea un
    repositorio para un sujeto que ya tiene uno vivo (guarda anti-bucle, A-202):
    la creacion solo ocurre si la fila aun no tiene `github_repo_id`."""
    ahora = ahora_utc()
    if repositorio.estado not in _ESTADOS_QUE_EL_TRABAJO_AVANZA:
        return
    if not listo_para_reintentar(repositorio.proximo_intento_en, ahora):
        return
    if (
        repositorio.estado == EstadoRepositorio.ERROR_TRANSITORIO.value
        and repositorio.intentos >= MAX_INTENTOS_TRANSITORIOS
    ):
        return  # CA-8.7-05: agotado, no se reintenta solo
    sujeto = bd.get(Sujeto, repositorio.sujeto_id)
    tarea = bd.get(Tarea, repositorio.tarea_id)
    curso = bd.get(Curso, repositorio.curso_id)
    assert sujeto is not None and tarea is not None and curso is not None
    if not sujeto.activo or tarea.estado != EstadoTarea.ACTIVA.value:
        return
    if curso.github_org_login is None or curso.github_installation_id is None:
        return
    estudiante = bd.get(Estudiante, sujeto.estudiante_id)
    assert estudiante is not None

    try:
        token = cliente.obtener_token_instalacion(curso.github_installation_id)
        contexto = _Contexto(
            curso=curso,
            tarea=tarea,
            sujeto=sujeto,
            estudiante=estudiante,
            org=curso.github_org_login,
            token=token,
        )
        if repositorio.github_repo_id is None:
            if not _crear(bd, cliente, contexto, repositorio):
                return
        else:
            repositorio.estado = _estado_de_reanudacion(repositorio)
        if repositorio.estado == EstadoRepositorio.CREADO_SIN_CONTENIDO.value:
            if not _sondear_contenido(bd, cliente, contexto, repositorio):
                return
        if repositorio.estado == EstadoRepositorio.CONTENIDO_LISTO.value:
            repositorio.estado = EstadoRepositorio.CONFIGURANDO_ACCESOS.value
            bd.flush()
        if repositorio.estado == EstadoRepositorio.CONFIGURANDO_ACCESOS.value:
            _configurar_accesos(bd, cliente, contexto, repositorio, trabajo_id=trabajo_id)
    except RechazoProveedorGithub as exc:
        _aplicar_rechazo(bd, repositorio, exc.status_code, exc.mensaje_literal)
    except FalloProveedorGithub as exc:
        _aplicar_rechazo(bd, repositorio, 503, str(exc))


def _estado_de_reanudacion(repositorio: Repositorio) -> str:
    """Tras `ESPERANDO_LIMITE`/`ERROR_TRANSITORIO`/`BLOQUEADO` con el
    repositorio ya creado, se vuelve al paso en que quedo (S8.6.1)."""
    if repositorio.estado not in (
        EstadoRepositorio.ESPERANDO_LIMITE.value,
        EstadoRepositorio.ERROR_TRANSITORIO.value,
        EstadoRepositorio.BLOQUEADO.value,
        EstadoRepositorio.CREANDO.value,
    ):
        return repositorio.estado
    if repositorio.commit_inicial_sha is None and repositorio.sondeos_contenido < len(
        SONDEOS_CONTENIDO_SEGUNDOS
    ):
        return EstadoRepositorio.CREADO_SIN_CONTENIDO.value
    return EstadoRepositorio.CONFIGURANDO_ACCESOS.value


def _crear(bd: Session, cliente: ClienteGitHub, c: _Contexto, repositorio: Repositorio) -> bool:
    """`LISTO_PARA_CREAR -> CREANDO -> CREADO_SIN_CONTENIDO` (o, si se adopta un
    repositorio ya existente, directo a `CONFIGURANDO_ACCESOS`). Devuelve
    `False` si el repositorio quedo esperando o en error."""
    mapeo = _mapeos_vigentes(bd, c.curso.id).get(c.estudiante.id)
    motivo = motivo_espera_individual(
        estado_mapeo=mapeo.estado if mapeo is not None else None, estado_tarea=c.tarea.estado
    )
    if motivo is not None:
        repositorio.estado = EstadoRepositorio.ESPERANDO_INFORMACION.value
        repositorio.motivo = motivo.value
        bd.flush()
        return False

    base = (
        bd.get(RepositorioBase, c.tarea.repositorio_base_id)
        if c.tarea.repositorio_base_id
        else None
    )
    if base is not None and base.estado not in (
        EstadoRepositorioBase.LISTO.value,
        EstadoRepositorioBase.CREADO_VACIO.value,
    ):
        # S8.3.2: con el base en ERROR o INACCESIBLE el aprovisionamiento de la
        # tarea se detiene con el motivo escrito, sin afectar a los ya creados.
        repositorio.estado = EstadoRepositorio.BLOQUEADO.value
        repositorio.error_mensaje_literal = "El repositorio base de la tarea no está disponible."
        repositorio.proximo_intento_en = ahora_utc() + REEVALUACION_BLOQUEADO
        bd.flush()
        return False

    repositorio.estado = EstadoRepositorio.CREANDO.value
    repositorio.motivo = None
    bd.flush()

    existente = cliente.obtener_repo(c.org, repositorio.nombre, c.token)
    if existente is not None:
        return _adoptar_o_rechazar(bd, c, repositorio, existente)

    descripcion = (
        f"Repositorio de {c.estudiante.nombre} — {c.tarea.nombre} — {c.curso.nombre} "
        + marcador_descripcion(
            curso_slug=c.curso.slug,
            tarea_slug=c.tarea.slug,
            sujeto=f"e{c.estudiante.canvas_user_id}",
        )
    )
    try:
        if base is not None:
            info = cliente.generar_desde_plantilla(
                c.org,
                base.nombre,
                org_login=c.org,
                nombre=repositorio.nombre,
                descripcion=descripcion,
                token_instalacion=c.token,
            )
        else:
            info = cliente.crear_repo_organizacion(
                c.org,
                nombre=repositorio.nombre,
                descripcion=descripcion,
                token_instalacion=c.token,
                gitignore_template=c.tarea.gitignore_template,
            )
    except RechazoProveedorGithub as exc:
        if exc.status_code == 422 and "already exists" in exc.mensaje_literal:
            # Carrera o reintento tras fallo parcial: se relee y se evalua la
            # adopcion, nunca se trata el 422 como exito a ciegas (A-097).
            existente = cliente.obtener_repo(c.org, repositorio.nombre, c.token)
            if existente is not None:
                return _adoptar_o_rechazar(bd, c, repositorio, existente)
        raise

    cliente.reemplazar_topics(
        c.org,
        info.nombre,
        topics_repositorio(curso_slug=c.curso.slug, tarea_slug=c.tarea.slug),
        c.token,
    )
    _guardar_identidad(repositorio, info)
    repositorio.estado = EstadoRepositorio.CREADO_SIN_CONTENIDO.value
    repositorio.intentos = 0
    repositorio.proximo_intento_en = None
    repositorio.error_mensaje_literal = None
    repositorio.clase_error = None
    bd.flush()
    registrar_bitacora(
        bd,
        accion="REPOSITORIO_CREADO",
        entidad="repositorio",
        entidad_id=str(repositorio.id),
        curso_id=c.curso.id,
        despues={"full_name": repositorio.full_name, "github_repo_id": repositorio.github_repo_id},
    )
    return True


def _guardar_identidad(repositorio: Repositorio, info: RepoGithubInfo) -> None:
    repositorio.github_repo_id = info.github_repo_id
    repositorio.full_name = info.full_name
    repositorio.url_html = info.url_html
    repositorio.rama_por_defecto = info.rama_por_defecto  # A-068: leida, nunca supuesta
    repositorio.actualizado_en = ahora_utc()


def _adoptar_o_rechazar(
    bd: Session, c: _Contexto, repositorio: Repositorio, existente: RepoGithubInfo
) -> bool:
    """S8.6.5 (A-097). La condicion (e) -- historia sin commits ajenos -- no se
    comprueba todavia: exige leer la historia completa (Bloque 2, ingesta de
    actividad). TODO(etapa-F5). Se comprueban (a) a (d)."""
    otro_con_mismo_id = (
        bd.query(Repositorio.id)
        .filter(
            Repositorio.github_repo_id == existente.github_repo_id,
            Repositorio.id != repositorio.id,
        )
        .first()
    )
    fallidas = condiciones_adopcion_fallidas_sujeto(
        existente,
        org_login=c.org,
        curso_slug=c.curso.slug,
        tarea_slug=c.tarea.slug,
        sujeto=f"e{c.estudiante.canvas_user_id}",
    )
    if otro_con_mismo_id is not None:
        fallidas.append("ya pertenece a otro sujeto de la aplicación")
    if fallidas:
        repositorio.estado = EstadoRepositorio.ERROR_PERMANENTE.value
        repositorio.clase_error = FamiliaError.PERMANENTE.value
        repositorio.error_codigo = SubtipoErrorPermanente.NOMBRE_OCUPADO_POR_TERCERO.value
        repositorio.error_mensaje_literal = (
            f"Ya existe en GitHub un repositorio llamado {repositorio.nombre} que no es el de "
            f"este estudiante ({'; '.join(fallidas)})."
        )
        bd.flush()
        incidencia_repo.abrir_o_actualizar(
            bd,
            tipo="REPO_NOMBRE_OCUPADO",
            severidad="BLOQUEANTE",
            sujeto_tipo="REPOSITORIO",
            curso_id=c.curso.id,
            sujeto_id=repositorio.id,
            detalle={"nombre": repositorio.nombre, "condiciones_fallidas": fallidas},
        )
        return False
    _guardar_identidad(repositorio, existente)
    # A-097: cumplidas las condiciones se salta directo a CONFIGURANDO_ACCESOS.
    repositorio.estado = EstadoRepositorio.CONFIGURANDO_ACCESOS.value
    repositorio.intentos = 0
    repositorio.error_mensaje_literal = None
    bd.flush()
    registrar_bitacora(
        bd,
        accion="REPOSITORIO_ADOPTADO",
        entidad="repositorio",
        entidad_id=str(repositorio.id),
        curso_id=c.curso.id,
        despues={"full_name": repositorio.full_name},
    )
    return True


def condiciones_adopcion_fallidas_sujeto(
    repo: RepoGithubInfo, *, org_login: str, curso_slug: str, tarea_slug: str, sujeto: str
) -> list[str]:
    """Las mismas condiciones (a)-(d) que el base, con el marcador del sujeto."""
    fallidas = [
        f
        for f in condiciones_adopcion_fallidas(
            repo, org_login=org_login, curso_slug=curso_slug, tarea_slug=tarea_slug
        )
        if not f.startswith("d:")
    ]
    marcador = marcador_descripcion(curso_slug=curso_slug, tarea_slug=tarea_slug, sujeto=sujeto)
    if marcador not in (repo.descripcion or ""):
        fallidas.append(f"d: su descripción no contiene el marcador {marcador}")
    return fallidas


def _sondear_contenido(
    bd: Session, cliente: ClienteGitHub, c: _Contexto, repositorio: Repositorio
) -> bool:
    """S8.6.3 (A-096): un sondeo por ciclo, con retroceso y tope de ocho. Agotado
    el tope se avanza igual, con incidencia informativa y nunca error."""
    sha = cliente.obtener_primer_commit(c.org, repositorio.nombre, c.token)
    if sha is not None:
        repositorio.commit_inicial_sha = sha
        repositorio.estado = EstadoRepositorio.CONTENIDO_LISTO.value
        bd.flush()
        return True
    if repositorio.sondeos_contenido < len(SONDEOS_CONTENIDO_SEGUNDOS):
        espera = SONDEOS_CONTENIDO_SEGUNDOS[repositorio.sondeos_contenido]
        repositorio.sondeos_contenido += 1
        cuando = ahora_utc() + timedelta(seconds=espera)
        repositorio.proximo_intento_en = cuando
        bd.flush()
        encolar_aprovisionamiento(
            bd, repositorio, sufijo=f":sondeo:{repositorio.sondeos_contenido}", cuando=cuando
        )
        return False
    repositorio.estado = EstadoRepositorio.CONTENIDO_LISTO.value
    repositorio.proximo_intento_en = None
    bd.flush()
    incidencia_repo.abrir_o_actualizar(
        bd,
        tipo="CONTENIDO_INICIAL_NO_OBSERVADO",
        severidad="INFORMATIVA",
        sujeto_tipo="REPOSITORIO",
        curso_id=c.curso.id,
        sujeto_id=repositorio.id,
        detalle={"sondeos": repositorio.sondeos_contenido},
    )
    return True


# --- CONFIGURANDO_ACCESOS: estudiante (maquina 3) y equipo docente ---


def _configurar_accesos(
    bd: Session,
    cliente: ClienteGitHub,
    c: _Contexto,
    repositorio: Repositorio,
    *,
    trabajo_id: uuid.UUID | None,
) -> None:
    _asegurar_acceso_estudiante(bd, cliente, c, repositorio, trabajo_id=trabajo_id)
    _asegurar_acceso_docente(bd, cliente, c, repositorio)
    _evaluar_predicado(bd, c.curso, repositorio)


def _asegurar_acceso_estudiante(
    bd: Session,
    cliente: ClienteGitHub,
    c: _Contexto,
    repositorio: Repositorio,
    *,
    trabajo_id: uuid.UUID | None,
) -> AccesoRepositorio:
    ahora = ahora_utc()
    acceso = (
        bd.query(AccesoRepositorio)
        .filter(
            AccesoRepositorio.repositorio_id == repositorio.id,
            AccesoRepositorio.estudiante_id == c.estudiante.id,
        )
        .one_or_none()
    )
    mapeo = _mapeos_vigentes(bd, c.curso.id).get(c.estudiante.id)
    cuenta = (
        bd.get(CuentaGithub, mapeo.cuenta_github_id)
        if mapeo is not None
        and mapeo.estado == EstadoMapeoGithub.VIGENTE.value
        and mapeo.cuenta_github_id
        else None
    )
    if acceso is None:
        acceso = AccesoRepositorio(
            repositorio_id=repositorio.id,
            estudiante_id=c.estudiante.id,
            estado=EstadoAccesoRepositorio.SIN_MAPEO.value,
            reenvios=0,
            actualizado_en=ahora,
        )
        bd.add(acceso)
    if cuenta is None:
        if acceso.estado not in ESTADOS_ACCESO_CUBIERTO:
            acceso.estado = EstadoAccesoRepositorio.SIN_MAPEO.value
        bd.flush()
        return acceso

    acceso.cuenta_github_id = cuenta.id
    if acceso.estado in (
        EstadoAccesoRepositorio.SIN_MAPEO.value,
        EstadoAccesoRepositorio.POR_INVITAR.value,
    ):
        acceso.estado = EstadoAccesoRepositorio.POR_INVITAR.value
        # S8.8.2, orden obligatorio: primero, ¿ya es colaborador? Si lo es, no se
        # toca nada en GitHub (CA-8.8-01).
        try:
            if cliente.es_colaborador(c.org, repositorio.nombre, cuenta.login, c.token):
                acceso.estado = EstadoAccesoRepositorio.ACCESO_DIRECTO.value
            else:
                resultado = cliente.invitar_colaborador(
                    c.org, repositorio.nombre, cuenta.login, c.token
                )
                acceso.estado = estado_acceso_tras_invitar(resultado.status_code).value
                acceso.github_invitation_id = resultado.invitation_id
                acceso.invitacion_html_url = resultado.html_url
            acceso.invitado_en = ahora
            acceso.ultimo_error = None
        except RechazoProveedorGithub as exc:
            clasificacion = clasificar_rechazo_github(
                exc.status_code, exc.mensaje_literal, en_ventana_de_creacion=False
            )
            if clasificacion.familia != FamiliaError.PERMANENTE:
                raise
            # Un rechazo permanente al invitar deja el repositorio usable y
            # DEGRADADO con ERROR_AL_CONCEDER_ACCESO, nunca en error (S8.6.2).
            acceso.ultimo_error = f"GitHub respondió {exc.status_code}: {exc.mensaje_literal}"
    acceso.actualizado_en = ahora
    bd.flush()
    _asegurar_aviso_de_acceso(bd, c, repositorio, acceso, trabajo_id=trabajo_id)
    return acceso


def _asegurar_aviso_de_acceso(
    bd: Session,
    c: _Contexto,
    repositorio: Repositorio,
    acceso: AccesoRepositorio,
    *,
    trabajo_id: uuid.UUID | None,
) -> None:
    """S8.10.1: el aviso cuelga del acceso de la persona, no de `OPERATIVO`.
    S8.10.3: sin nombre, URL y fecha de cierre resueltos, no se dispara todavia
    (la reconciliacion lo reintenta; la clave impide duplicarlo)."""
    if acceso.estado not in (
        EstadoAccesoRepositorio.INVITADO.value,
        EstadoAccesoRepositorio.ACCESO_DIRECTO.value,
        EstadoAccesoRepositorio.ACEPTADO.value,
    ):
        return
    if not repositorio.url_html:
        return
    resuelta, fecha = fechas_repo.fecha_cierre_primera_entrega(
        bd, tarea_id=c.tarea.id, sujeto_id=c.sujeto.id
    )
    if not resuelta:
        return
    outbox_repo.encolar_aviso_acceso(
        bd,
        curso=c.curso,
        tarea=c.tarea,
        sujeto=c.sujeto,
        repositorio=repositorio,
        estudiante=c.estudiante,
        acceso=acceso,
        evento=outbox_repo.EVENTO_REPOSITORIO_DISPONIBLE,
        fecha_cierre=fecha,
        trabajo_id=trabajo_id,
    )
    if acceso.estado == EstadoAccesoRepositorio.ACEPTADO.value:
        outbox_repo.encolar_aviso_acceso(
            bd,
            curso=c.curso,
            tarea=c.tarea,
            sujeto=c.sujeto,
            repositorio=repositorio,
            estudiante=c.estudiante,
            acceso=acceso,
            evento=outbox_repo.EVENTO_INVITACION_ACEPTADA,
            fecha_cierre=fecha,
            trabajo_id=trabajo_id,
        )


def _asegurar_acceso_docente(
    bd: Session, cliente: ClienteGitHub, c: _Contexto, repositorio: Repositorio
) -> AccesoDocenteRepositorio:
    """A-163 via principal: una sola llamada por repositorio con el equipo
    `docentes`, nunca una por docente."""
    fila = (
        bd.query(AccesoDocenteRepositorio)
        .filter(
            AccesoDocenteRepositorio.repositorio_id == repositorio.id,
            AccesoDocenteRepositorio.via == ViaAccesoDocente.TEAM.value,
        )
        .one_or_none()
    )
    if fila is None:
        fila = AccesoDocenteRepositorio(
            repositorio_id=repositorio.id,
            membresia_id=None,
            via=ViaAccesoDocente.TEAM.value,
            estado=EstadoAccesoDocente.PENDIENTE.value,
            github_permission="pull",
        )
        bd.add(fila)
    if fila.estado == EstadoAccesoDocente.CONCEDIDO.value:
        return fila
    equipo = (
        bd.query(EquipoGithubCurso).filter(EquipoGithubCurso.curso_id == c.curso.id).one_or_none()
    )
    if equipo is None or not equipo.team_slug:
        fila.estado = EstadoAccesoDocente.PENDIENTE.value
        fila.ultimo_error = "El equipo docentes de la organización todavía no existe."
        bd.flush()
        return fila
    try:
        cliente.conceder_lectura_equipo(c.org, equipo.team_slug, repositorio.nombre, c.token)
        fila.estado = EstadoAccesoDocente.CONCEDIDO.value
        fila.concedido_en = ahora_utc()
        fila.ultimo_error = None
    except RechazoProveedorGithub as exc:
        clasificacion = clasificar_rechazo_github(
            exc.status_code, exc.mensaje_literal, en_ventana_de_creacion=False
        )
        if clasificacion.familia != FamiliaError.PERMANENTE:
            raise
        fila.estado = EstadoAccesoDocente.ERROR.value
        fila.ultimo_error = f"GitHub respondió {exc.status_code}: {exc.mensaje_literal}"
    bd.flush()
    return fila


def _evaluar_predicado(bd: Session, curso: Curso, repositorio: Repositorio) -> None:
    accesos = (
        bd.query(AccesoRepositorio).filter(AccesoRepositorio.repositorio_id == repositorio.id).all()
    )
    docente = (
        bd.query(AccesoDocenteRepositorio)
        .filter(AccesoDocenteRepositorio.repositorio_id == repositorio.id)
        .first()
    )
    resultado = evaluar_predicado_operativo(
        estados_acceso_estudiantes=[a.estado for a in accesos],
        hay_errores_al_invitar=any(
            a.ultimo_error and a.estado not in ESTADOS_ACCESO_CUBIERTO for a in accesos
        ),
        # TODO(etapa-F1): integrantes invited/requested en Canvas (tarea grupal).
        integrantes_pendientes_en_canvas=False,
        estado_acceso_docente=docente.estado if docente is not None else None,
    )
    anterior = repositorio.estado
    repositorio.estado = resultado.estado.value
    repositorio.motivo = resultado.motivo.value if resultado.motivo is not None else None
    repositorio.proximo_intento_en = None
    repositorio.intentos = 0
    repositorio.error_mensaje_literal = None
    repositorio.clase_error = None
    repositorio.error_codigo = None
    if repositorio.listo_en is None:
        repositorio.listo_en = ahora_utc()
    repositorio.actualizado_en = ahora_utc()
    bd.flush()
    if anterior != repositorio.estado:
        registrar_bitacora(
            bd,
            accion="REPOSITORIO_ESTADO",
            entidad="repositorio",
            entidad_id=str(repositorio.id),
            curso_id=curso.id,
            antes={"estado": anterior},
            despues={"estado": repositorio.estado, "motivo": repositorio.motivo},
        )


def _aplicar_rechazo(bd: Session, repositorio: Repositorio, status_code: int, mensaje: str) -> None:
    """S8.6.4: la familia decide el comportamiento y lo que ve el docente."""
    ahora = ahora_utc()
    clasificacion = clasificar_rechazo_github(
        status_code,
        mensaje,
        en_ventana_de_creacion=repositorio.estado
        in (EstadoRepositorio.CREANDO.value, EstadoRepositorio.CREADO_SIN_CONTENIDO.value),
    )
    repositorio.clase_error = clasificacion.familia.value
    repositorio.error_mensaje_literal = f"GitHub respondió {status_code}: {mensaje}"[:1000]
    repositorio.estado = clasificacion.estado.value
    if clasificacion.estado == EstadoRepositorio.ESPERANDO_LIMITE:
        repositorio.proximo_intento_en = ahora + ESPERA_LIMITE_POR_DEFECTO
    elif clasificacion.estado == EstadoRepositorio.BLOQUEADO:
        repositorio.proximo_intento_en = ahora + REEVALUACION_BLOQUEADO
    elif clasificacion.estado == EstadoRepositorio.ERROR_TRANSITORIO:
        repositorio.intentos += 1
        repositorio.proximo_intento_en = (
            ahora + espera_reintento(repositorio.intentos)
            if repositorio.intentos < MAX_INTENTOS_TRANSITORIOS
            else None
        )
    else:
        repositorio.error_codigo = (
            clasificacion.subtipo.value if clasificacion.subtipo is not None else None
        )
        repositorio.proximo_intento_en = None
    repositorio.actualizado_en = ahora
    bd.flush()


# --- Barridos ---


def barrido_aprovisionamiento(
    bd: Session, cliente: ClienteGitHub, *, curso: Curso, tope: int = 10
) -> int:
    """S8.7.1: re-evalua lo que sigue pendiente, tambien si un evento se perdio."""
    ahora = ahora_utc()
    candidatos = (
        bd.query(Repositorio)
        .join(Sujeto, Sujeto.id == Repositorio.sujeto_id)
        .filter(
            Repositorio.curso_id == curso.id,
            Repositorio.estado.in_(list(_ESTADOS_QUE_EL_TRABAJO_AVANZA)),
            Sujeto.activo.is_(True),
            (Repositorio.proximo_intento_en.is_(None)) | (Repositorio.proximo_intento_en <= ahora),
        )
        .order_by(Repositorio.creado_en)
        .limit(tope)
        .all()
    )
    for repositorio in candidatos:
        aprovisionar_repositorio(bd, cliente, repositorio=repositorio)
    return len(candidatos)


def reconciliar_accesos(bd: Session, cliente: ClienteGitHub, *, curso: Curso) -> int:
    """`reconciliar_accesos` (15 min). Sin receptor de webhooks, es la unica
    via por la que se detecta que un estudiante acepto su invitacion.
    TODO(receptor-webhooks): el webhook `member/added` la adelantaria.

    Aplica el orden de S8.8.2 antes de tocar nada: ¿ya es colaborador?, ¿la
    invitacion sigue viva?, y solo si expiro o desaparecio se vuelve a invitar,
    con tope de 3 reenvios separados 24 h."""
    if curso.github_org_login is None or curso.github_installation_id is None:
        return 0
    repositorios = (
        bd.query(Repositorio)
        .join(Tarea, Tarea.id == Repositorio.tarea_id)
        .join(Sujeto, Sujeto.id == Repositorio.sujeto_id)
        .filter(
            Repositorio.curso_id == curso.id,
            Repositorio.estado.in_(list(_ESTADOS_QUE_RECONCILIA)),
            Tarea.estado == EstadoTarea.ACTIVA.value,
            Sujeto.activo.is_(True),
        )
        .all()
    )
    if not repositorios:
        return 0
    token = cliente.obtener_token_instalacion(curso.github_installation_id)
    for repositorio in repositorios:
        sujeto = bd.get(Sujeto, repositorio.sujeto_id)
        tarea = bd.get(Tarea, repositorio.tarea_id)
        assert sujeto is not None and tarea is not None
        estudiante = bd.get(Estudiante, sujeto.estudiante_id)
        assert estudiante is not None
        c = _Contexto(
            curso=curso,
            tarea=tarea,
            sujeto=sujeto,
            estudiante=estudiante,
            org=curso.github_org_login,
            token=token,
        )
        try:
            _reconciliar_repositorio(bd, cliente, c, repositorio)
        except RechazoProveedorGithub as exc:
            repositorio.error_mensaje_literal = (
                f"GitHub respondió {exc.status_code}: {exc.mensaje_literal}"
            )
            bd.flush()
        except FalloProveedorGithub:
            continue
    return len(repositorios)


def _reconciliar_repositorio(
    bd: Session, cliente: ClienteGitHub, c: _Contexto, repositorio: Repositorio
) -> None:
    ahora = ahora_utc()
    accesos = (
        bd.query(AccesoRepositorio).filter(AccesoRepositorio.repositorio_id == repositorio.id).all()
    )
    invitaciones = None
    for acceso in accesos:
        cuenta = bd.get(CuentaGithub, acceso.cuenta_github_id) if acceso.cuenta_github_id else None
        if acceso.estado == EstadoAccesoRepositorio.INVITADO.value and cuenta is not None:
            if cliente.es_colaborador(c.org, repositorio.nombre, cuenta.login, c.token):
                acceso.estado = EstadoAccesoRepositorio.ACEPTADO.value
                acceso.aceptado_en = ahora
            else:
                if invitaciones is None:
                    invitaciones = {
                        i.login.lower(): i
                        for i in cliente.listar_invitaciones(c.org, repositorio.nombre, c.token)
                    }
                invitacion = invitaciones.get(cuenta.login.lower())
                if invitacion is None:
                    acceso.estado = EstadoAccesoRepositorio.DESAPARECIDA.value
                elif invitacion.expirada:
                    acceso.estado = EstadoAccesoRepositorio.EXPIRADA.value
            acceso.actualizado_en = ahora
        if acceso.estado in (
            EstadoAccesoRepositorio.EXPIRADA.value,
            EstadoAccesoRepositorio.DESAPARECIDA.value,
        ) and _puede_reenviar(acceso, ahora):
            acceso.estado = EstadoAccesoRepositorio.POR_INVITAR.value
            acceso.reenvios += 1
            acceso.ultimo_reenvio_en = ahora
    bd.flush()
    # SIN_MAPEO que ahora tiene mapeo vigente, POR_INVITAR y los avisos que aun
    # no salieron: el mismo camino que la creacion, con sus lecturas previas.
    _asegurar_acceso_estudiante(bd, cliente, c, repositorio, trabajo_id=None)
    _asegurar_acceso_docente(bd, cliente, c, repositorio)
    if repositorio.estado != EstadoRepositorio.FUERA_DE_ALCANCE.value:
        _evaluar_predicado(bd, c.curso, repositorio)


def _puede_reenviar(acceso: AccesoRepositorio, ahora: datetime) -> bool:
    """S8.8.2 / CA-8.8-06: maximo 3 reenvios, separados al menos 24 horas."""
    if acceso.reenvios >= 3:
        return False
    return acceso.ultimo_reenvio_en is None or ahora - acceso.ultimo_reenvio_en >= timedelta(
        hours=24
    )


# --- Acciones del docente (encolan, A-226) ---


class AccionNoPermitida(Exception):
    def __init__(self, detalle: str) -> None:
        self.detalle = detalle
        super().__init__(detalle)


def reintentar(bd: Session, *, repositorio: Repositorio, actor_usuario_id: uuid.UUID) -> None:
    """S8.11.3: el destino depende del subtipo; encola, no llama a GitHub."""
    if repositorio.estado == EstadoRepositorio.ERROR_PERMANENTE.value:
        destino = destino_al_reintentar(repositorio.error_codigo)
        if destino == EstadoRepositorio.ESPERANDO_INFORMACION:
            raise AccionNoPermitida(
                "Este repositorio no se puede reintentar: primero corrige la cuenta de GitHub "
                "del estudiante en Personas."
            )
    elif repositorio.estado not in (
        EstadoRepositorio.ERROR_TRANSITORIO.value,
        EstadoRepositorio.BLOQUEADO.value,
        EstadoRepositorio.ESPERANDO_LIMITE.value,
    ):
        raise AccionNoPermitida("Este repositorio no tiene nada que reintentar.")
    antes = {"estado": repositorio.estado, "error": repositorio.error_mensaje_literal}
    repositorio.estado = (
        EstadoRepositorio.LISTO_PARA_CREAR.value
        if repositorio.github_repo_id is None
        else EstadoRepositorio.CONFIGURANDO_ACCESOS.value
    )
    repositorio.intentos = 0
    repositorio.proximo_intento_en = None
    repositorio.error_codigo = None
    repositorio.clase_error = None
    repositorio.actualizado_en = ahora_utc()
    bd.flush()
    encolar_aprovisionamiento(bd, repositorio, sufijo=f":reintento:{ahora_utc().isoformat()}")
    registrar_bitacora(
        bd,
        accion="REPOSITORIO_REINTENTO",
        entidad="repositorio",
        entidad_id=str(repositorio.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=repositorio.curso_id,
        antes=antes,
    )


def sustituir(bd: Session, *, repositorio: Repositorio, actor_usuario_id: uuid.UUID) -> Repositorio:
    """S8.11.2 (A-202): solo desde `INACCESIBLE`. Crea una fila nueva con
    `reemplaza_a_id`; la anterior se conserva integra como evidencia."""
    if repositorio.estado != EstadoRepositorio.INACCESIBLE.value:
        raise AccionNoPermitida(
            "Solo se sustituye un repositorio que ya no es accesible en GitHub."
        )
    ahora = ahora_utc()
    nuevo = Repositorio(
        curso_id=repositorio.curso_id,
        tarea_id=repositorio.tarea_id,
        sujeto_id=repositorio.sujeto_id,
        nombre=repositorio.nombre_canonico,
        nombre_canonico=repositorio.nombre_canonico,
        estado=EstadoRepositorio.LISTO_PARA_CREAR.value,
        intentos=0,
        sondeos_contenido=0,
        reemplaza_a_id=repositorio.id,
        recreado_en=ahora,
        creado_en=ahora,
        actualizado_en=ahora,
    )
    bd.add(nuevo)
    bd.flush()
    encolar_aprovisionamiento(bd, nuevo, sufijo=f":sustitucion:{nuevo.id}")
    registrar_bitacora(
        bd,
        accion="REPOSITORIO_SUSTITUIDO",
        entidad="repositorio",
        entidad_id=str(nuevo.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=repositorio.curso_id,
        antes={"repositorio_id": str(repositorio.id), "github_repo_id": repositorio.github_repo_id},
    )
    return nuevo


# --- Lectura para pantalla (sin proveedores) ---


@dataclass(frozen=True)
class ResumenRepositorios:
    """S8.9.1: columnas nunca mezcladas; `DEGRADADO` jamas suma a problemas."""

    operativos: int
    degradados: int
    bloqueados: int
    esperando_limite: int
    error_transitorio: int
    error_permanente: int
    inaccesibles: int
    fuera_de_alcance: int
    archivados: int
    esperando_informacion: int
    listos_para_crear: int
    creando: int
    sujetos_activos: int
    sujetos_inactivos: int
    en_curso: bool
    creados: int
    minutos_restantes: int


def resumen_repositorios(bd: Session, *, tarea_id: uuid.UUID) -> ResumenRepositorios:
    filas = (
        bd.query(Repositorio.estado, Repositorio.github_repo_id, Sujeto.activo)
        .join(Sujeto, Sujeto.id == Repositorio.sujeto_id)
        .filter(Repositorio.tarea_id == tarea_id)
        .all()
    )
    conteo: dict[str, int] = {}
    creados = 0
    for estado, github_repo_id, activo in filas:
        # Un sujeto inactivo sin repositorio creado deja de aprovisionarse:
        # no cuenta como "esperando".
        if not activo and github_repo_id is None:
            continue
        conteo[estado] = conteo.get(estado, 0) + 1
        if github_repo_id is not None and estado != EstadoRepositorio.INACCESIBLE.value:
            creados += 1
    activos = bd.query(Sujeto).filter(Sujeto.tarea_id == tarea_id, Sujeto.activo.is_(True)).count()
    inactivos = (
        bd.query(Sujeto).filter(Sujeto.tarea_id == tarea_id, Sujeto.activo.is_(False)).count()
    )
    creando = sum(
        conteo.get(e.value, 0)
        for e in (
            EstadoRepositorio.CREANDO,
            EstadoRepositorio.CREADO_SIN_CONTENIDO,
            EstadoRepositorio.CONTENIDO_LISTO,
            EstadoRepositorio.CONFIGURANDO_ACCESOS,
        )
    )
    pendientes_de_crear = conteo.get(EstadoRepositorio.LISTO_PARA_CREAR.value, 0) + creando
    return ResumenRepositorios(
        operativos=conteo.get(EstadoRepositorio.OPERATIVO.value, 0),
        degradados=conteo.get(EstadoRepositorio.DEGRADADO.value, 0),
        bloqueados=conteo.get(EstadoRepositorio.BLOQUEADO.value, 0),
        esperando_limite=conteo.get(EstadoRepositorio.ESPERANDO_LIMITE.value, 0),
        error_transitorio=conteo.get(EstadoRepositorio.ERROR_TRANSITORIO.value, 0),
        error_permanente=conteo.get(EstadoRepositorio.ERROR_PERMANENTE.value, 0),
        inaccesibles=conteo.get(EstadoRepositorio.INACCESIBLE.value, 0),
        fuera_de_alcance=conteo.get(EstadoRepositorio.FUERA_DE_ALCANCE.value, 0),
        archivados=conteo.get(EstadoRepositorio.ARCHIVADO.value, 0),
        esperando_informacion=conteo.get(EstadoRepositorio.ESPERANDO_INFORMACION.value, 0),
        listos_para_crear=conteo.get(EstadoRepositorio.LISTO_PARA_CREAR.value, 0),
        creando=creando,
        sujetos_activos=activos,
        sujetos_inactivos=inactivos,
        en_curso=any(conteo.get(e, 0) for e in ESTADOS_EN_CURSO),
        creados=creados,
        minutos_restantes=minutos_restantes(pendientes=pendientes_de_crear),
    )
