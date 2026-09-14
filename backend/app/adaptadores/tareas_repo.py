"""Tareas, entregas y espejo de las tareas de Canvas (SPEC 08 S8.2; SPEC 05
S5.4.3; A-080, A-089, A-164, A-203; Etapa P7).

Ninguna funcion de este modulo que atiende a una pantalla llama a Canvas: crear
una tarea o vincular una entrega lee el espejo `assignment_canvas`, que solo
escribe el trabajo `sync_tareas_y_fechas` (Ley 1, A-089).

Fuera de alcance de esta etapa, con TODO citado donde toca: `regla_fecha` y
`fecha_efectiva` (lectura de fechas, Etapa P8) y la materializacion de sujetos
y el aprovisionamiento que dispara la activacion (Etapa P8).
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Hashable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.adaptadores import (
    fechas_repo,
    incidencia_repo,
    programacion_repo,
    sincronizacion_repo,
    trabajos_repo,
)
from app.adaptadores.base import ahora_utc
from app.adaptadores.bitacora_repo import registrar as registrar_bitacora
from app.adaptadores.cliente_canvas import ClienteCanvas, FalloProveedorCanvas
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_padron import Estudiante, Grupo, Matricula, PertenenciaGrupo, Seccion
from app.adaptadores.modelos_tarea import (
    AssignmentCanvas,
    Entrega,
    RepositorioBase,
    Tarea,
    VisibilidadEntrega,
)
from app.dominio.alcance import bandera_activa, motivo_capa_3
from app.dominio.estados import (
    EstadoRepositorioBase,
    EstadoTarea,
    EstadoValidacionEntrega,
    ModalidadTarea,
    ResultadoSincronizacion,
    TipoEntrega,
    WorkflowStatePertenenciaGrupo,
)
from app.dominio.nombres_repositorio import (
    SujetoNombre,
    es_slug_valido,
    nombre_repositorio,
    normalizar,
    slug_entrega,
)
from app.dominio.padron import confirma_ausencia
from app.dominio.tareas import (
    PLANTILLAS_GITIGNORE,
    EntregaActivacion,
    EntregaOrden,
    EstudianteVisibilidad,
    MotivoRechazoTarea,
    RechazoTarea,
    motivo_no_activable,
    ordenar_al_vincular,
    renumerar_al_desvincular,
    resolver_visibilidad,
    validar_modalidad_para_vincular,
    validar_vincular_otra_entrega,
)
from app.dominio.tareas_canvas import AssignmentCanvasCrudo, OverrideCanvasCrudo

_RECURSO_TAREAS = "tareas"
# A-090: el payload del espejo se trunca a 64 KB al escribirse.
_TOPE_PAYLOAD_BYTES = 64 * 1024
_NUEVA = "__nueva__"


def _payload_truncado(payload: dict[str, Any]) -> dict[str, Any]:
    serializado = json.dumps(payload, default=str)
    if len(serializado.encode()) <= _TOPE_PAYLOAD_BYTES:
        completo: dict[str, Any] = json.loads(serializado)
        return completo
    return {
        "truncado": True,
        "id": payload.get("id"),
        "name": payload.get("name"),
        "tamano_original_bytes": len(serializado.encode()),
    }


# --- Sincronizacion (trabajo `sync_tareas_y_fechas`) ---


def sincronizar_tareas(bd: Session, cliente: ClienteCanvas, *, curso: Curso, token: str) -> None:
    """S5.4.3: espeja las tareas de Canvas del curso, refresca las entregas
    vinculadas y recalcula `visibilidad_entrega` (A-164 paso 1).

    Una tarea de Canvas ausente dos ciclos seguidos se confirma con el endpoint
    13 antes de marcar la entrega `ELIMINADA_EN_CANVAS`; un 5xx o un tiempo de
    espera nunca produce esa transicion (A-203 punto 5). Con el listado
    truncado no se concluye ninguna ausencia."""
    assert curso.canvas_course_id is not None
    ahora = ahora_utc()
    resultado = cliente.obtener_assignments_paginado(token, curso.canvas_course_id)
    vistos: dict[int, AssignmentCanvasCrudo] = {a.canvas_assignment_id: a for a in resultado.items}

    espejo = {
        fila.canvas_assignment_id: fila
        for fila in bd.query(AssignmentCanvas).filter(AssignmentCanvas.curso_id == curso.id)
    }
    for crudo in resultado.items:
        fila = espejo.get(crudo.canvas_assignment_id)
        if fila is None:
            fila = AssignmentCanvas(
                curso_id=curso.id, canvas_assignment_id=crudo.canvas_assignment_id
            )
            bd.add(fila)
            espejo[crudo.canvas_assignment_id] = fila
        fila.nombre = crudo.nombre
        fila.es_grupal = crudo.es_grupal
        fila.group_category_id_canvas = crudo.group_category_id
        fila.only_visible_to_overrides = crudo.only_visible_to_overrides
        fila.publicada = crudo.publicada
        fila.due_at = crudo.due_at
        fila.payload = _payload_truncado(crudo.payload)
        fila.ciclos_ausente = 0
        fila.ausente_en_canvas = False
        fila.sincronizado_en = ahora
    if not resultado.truncado:
        for canvas_assignment_id, fila in espejo.items():
            if canvas_assignment_id not in vistos:
                fila.ciclos_ausente += 1
                fila.ausente_en_canvas = confirma_ausencia(fila.ciclos_ausente)
    bd.flush()

    estudiantes = _estudiantes_para_visibilidad(bd, curso.id)
    contadores = {"assignments": len(resultado.items), "entregas": 0, "eliminadas": 0}
    entregas = (
        bd.query(Entrega)
        .filter(
            Entrega.curso_id == curso.id,
            Entrega.estado_validacion != EstadoValidacionEntrega.EXCLUIDA.value,
        )
        .all()
    )
    for entrega in entregas:
        contadores["entregas"] += 1
        vista = vistos.get(entrega.canvas_assignment_id)
        if vista is None:
            if resultado.truncado:
                continue
            if _registrar_ausencia_entrega(bd, cliente, token=token, curso=curso, entrega=entrega):
                contadores["eliminadas"] += 1
            continue
        _refrescar_entrega(bd, entrega=entrega, crudo=vista, curso_id=curso.id)
        # S9.3.1: los overrides del endpoint 14 son la fuente de autoridad de las
        # fechas; se leen en cada ciclo para cada entrega vinculada.
        try:
            overrides = cliente.obtener_overrides_assignment(
                token, curso.canvas_course_id, vista.canvas_assignment_id
            )
        except FalloProveedorCanvas:
            overrides = None
        _recalcular_visibilidad(
            bd,
            curso=curso,
            entrega=entrega,
            crudo=vista,
            overrides=overrides,
            estudiantes=estudiantes,
        )
        if overrides is not None:
            fechas_repo.sincronizar_fechas_entrega(
                bd, curso_id=curso.id, entrega=entrega, crudo=vista, overrides=overrides
            )

    estado = (
        ResultadoSincronizacion.TRUNCADA if resultado.truncado else ResultadoSincronizacion.OK
    ).value
    sincronizacion_repo.actualizar_cursor(
        bd,
        curso_id=curso.id,
        recurso=_RECURSO_TAREAS,
        referencia=str(curso.id),
        per_page_medido=resultado.per_page_medido,
        estado=estado,
    )
    sincronizacion_repo.registrar_ciclo(
        bd, curso_id=curso.id, recurso=_RECURSO_TAREAS, resultado=estado, contadores=contadores
    )
    # S9.4.4: orden fijo del ciclo, tareas y fechas antes que la materializacion.
    encolar_materializacion(bd, curso_id=curso.id)


def encolar_materializacion(bd: Session, *, curso_id: uuid.UUID) -> None:
    """A-164 paso 3: tras cada sincronizacion, sin que nadie pulse nada."""
    trabajos_repo.encolar(
        bd,
        tipo="materializar_sujetos",
        clave_idempotencia=f"materializar:{curso_id}:{ahora_utc().isoformat()}",
        max_intentos=3,
        curso_id=curso_id,
    )


def _refrescar_entrega(
    bd: Session, *, entrega: Entrega, crudo: AssignmentCanvasCrudo, curso_id: uuid.UUID
) -> None:
    """El nombre legible se actualiza; el `slug` no (A-172 punto 4). La
    modalidad de la tarea tampoco se reescribe aqui (A-080: congelada)."""
    entrega.nombre = crudo.nombre
    entrega.puntos_posibles = crudo.puntos_posibles
    entrega.grading_type = crudo.grading_type
    entrega.publicada = crudo.publicada
    entrega.moderated_grading = crudo.moderated_grading
    entrega.anonymous_grading = crudo.anonymous_grading
    entrega.group_category_id_canvas = crudo.group_category_id
    entrega.es_grupal_canvas = crudo.es_grupal
    entrega.only_visible_to_overrides = crudo.only_visible_to_overrides
    entrega.due_at_base = crudo.due_at
    entrega.all_day = crudo.all_day
    entrega.canvas_updated_at = crudo.canvas_updated_at
    entrega.ciclos_ausente = 0
    entrega.detectada_ausente_en = None
    entrega.sincronizado_en = ahora_utc()
    if entrega.estado_validacion == EstadoValidacionEntrega.ELIMINADA_EN_CANVAS.value:
        # A-203: reversible, vuelve sola a VIGENTE si reaparece el mismo id.
        entrega.estado_validacion = EstadoValidacionEntrega.VIGENTE.value
        incidencia_repo.cerrar(
            bd, tipo="ENTREGA_ELIMINADA_EN_CANVAS", curso_id=curso_id, sujeto_id=entrega.id
        )
    bd.flush()


def _registrar_ausencia_entrega(
    bd: Session, cliente: ClienteCanvas, *, token: str, curso: Curso, entrega: Entrega
) -> bool:
    """Devuelve `True` si la entrega quedo `ELIMINADA_EN_CANVAS` en este ciclo."""
    assert curso.canvas_course_id is not None
    if entrega.estado_validacion == EstadoValidacionEntrega.ELIMINADA_EN_CANVAS.value:
        return False
    entrega.ciclos_ausente += 1
    if entrega.detectada_ausente_en is None:
        entrega.detectada_ausente_en = ahora_utc()
    if not confirma_ausencia(entrega.ciclos_ausente):
        bd.flush()
        return False
    try:
        confirmada = cliente.obtener_assignment(
            token, curso.canvas_course_id, entrega.canvas_assignment_id
        )
    except FalloProveedorCanvas:
        bd.flush()
        return False
    if confirmada is not None:
        entrega.ciclos_ausente = 0
        entrega.detectada_ausente_en = None
        bd.flush()
        return False
    entrega.estado_validacion = EstadoValidacionEntrega.ELIMINADA_EN_CANVAS.value
    bd.flush()
    incidencia_repo.abrir_o_actualizar(
        bd,
        tipo="ENTREGA_ELIMINADA_EN_CANVAS",
        severidad="BLOQUEANTE",
        sujeto_tipo="ENTREGA",
        curso_id=curso.id,
        sujeto_id=entrega.id,
        detalle={"canvas_assignment_id": entrega.canvas_assignment_id, "nombre": entrega.nombre},
    )
    return True


def _estudiantes_para_visibilidad(bd: Session, curso_id: uuid.UUID) -> list[EstudianteVisibilidad]:
    secciones: dict[uuid.UUID, set[int]] = {}
    for estudiante_id, canvas_section_id in (
        bd.query(Matricula.estudiante_id, Seccion.canvas_section_id)
        .join(Seccion, Seccion.id == Matricula.seccion_id)
        .filter(Matricula.curso_id == curso_id, Matricula.activa.is_(True))
    ):
        secciones.setdefault(estudiante_id, set()).add(canvas_section_id)
    grupos: dict[uuid.UUID, set[int]] = {}
    for estudiante_id, canvas_group_id in (
        bd.query(PertenenciaGrupo.estudiante_id, Grupo.canvas_group_id)
        .join(Grupo, Grupo.id == PertenenciaGrupo.grupo_id)
        .filter(
            Grupo.curso_id == curso_id,
            PertenenciaGrupo.activa.is_(True),
            PertenenciaGrupo.workflow_state == WorkflowStatePertenenciaGrupo.ACCEPTED.value,
        )
    ):
        grupos.setdefault(estudiante_id, set()).add(canvas_group_id)
    return [
        EstudianteVisibilidad(
            estudiante_id=e.id,
            canvas_user_id=e.canvas_user_id,
            estado=e.estado,
            canvas_section_ids=frozenset(secciones.get(e.id, set())),
            canvas_group_ids=frozenset(grupos.get(e.id, set())),
        )
        for e in bd.query(Estudiante).filter(Estudiante.curso_id == curso_id)
    ]


def _recalcular_visibilidad(
    bd: Session,
    *,
    curso: Curso,
    entrega: Entrega,
    crudo: AssignmentCanvasCrudo,
    overrides: list[OverrideCanvasCrudo] | None,
    estudiantes: list[EstudianteVisibilidad],
) -> None:
    """`overrides = None` significa que no se pudieron leer: con
    `only_visible_to_overrides` eso es `SUPUESTO`, nunca visibilidad universal."""
    resultado = resolver_visibilidad(
        only_visible_to_overrides=crudo.only_visible_to_overrides,
        assignment_visibility=crudo.assignment_visibility,
        overrides=overrides,
        estudiantes=estudiantes,
    )
    ahora = ahora_utc()
    existentes = {
        fila.estudiante_id: fila
        for fila in bd.query(VisibilidadEntrega).filter(VisibilidadEntrega.entrega_id == entrega.id)
    }
    for estudiante in estudiantes:
        fila = existentes.get(estudiante.estudiante_id)  # type: ignore[call-overload]
        if fila is None:
            fila = VisibilidadEntrega(entrega_id=entrega.id, estudiante_id=estudiante.estudiante_id)
            bd.add(fila)
        fila.visible = estudiante.estudiante_id in resultado.visibles
        fila.origen = resultado.origen.value
        fila.sincronizado_en = ahora
    bd.flush()
    if resultado.no_resoluble:
        incidencia_repo.abrir_o_actualizar(
            bd,
            tipo="VISIBILIDAD_NO_RESOLUBLE",
            severidad="ADVERTENCIA",
            sujeto_tipo="ENTREGA",
            curso_id=curso.id,
            sujeto_id=entrega.id,
            detalle={"canvas_assignment_id": entrega.canvas_assignment_id},
        )
    else:
        incidencia_repo.cerrar(
            bd, tipo="VISIBILIDAD_NO_RESOLUBLE", curso_id=curso.id, sujeto_id=entrega.id
        )


# --- Lecturas para pantalla (sin Canvas ni GitHub) ---


@dataclass(frozen=True)
class AssignmentSeleccionable:
    fila: AssignmentCanvas
    seleccionable: bool
    motivo: str | None
    tarea_vinculada: str | None


def listar_assignments_seleccionables(
    bd: Session, *, curso: Curso, perfil_alcance: str
) -> list[AssignmentSeleccionable]:
    """El selector de "crear tarea": cada tarea de Canvas con su motivo si no
    se puede elegir (capa 1 o capa 3 de S1.11), nunca escondida."""
    vinculadas = {
        canvas_assignment_id: nombre
        for canvas_assignment_id, nombre in bd.query(Entrega.canvas_assignment_id, Tarea.nombre)
        .join(Tarea, Tarea.id == Entrega.tarea_id)
        .filter(Entrega.curso_id == curso.id)
    }
    salida = []
    filas = (
        bd.query(AssignmentCanvas)
        .filter(AssignmentCanvas.curso_id == curso.id)
        .order_by(AssignmentCanvas.nombre)
    )
    for fila in filas:
        motivo: str | None = None
        if fila.canvas_assignment_id == curso.canvas_assignment_id_registro:
            motivo = "Es la tarea de registro de cuentas de GitHub."
        elif fila.ausente_en_canvas:
            motivo = "Ya no existe en Canvas."
        elif fila.canvas_assignment_id in vinculadas:
            motivo = f"Ya está vinculada a la tarea «{vinculadas[fila.canvas_assignment_id]}»."
        elif fila.es_grupal and not bandera_activa(perfil_alcance, "tarea_modalidad_grupal"):
            motivo = motivo_capa_3("tarea_modalidad_grupal", "Crear tareas grupales")
        salida.append(
            AssignmentSeleccionable(
                fila=fila,
                seleccionable=motivo is None,
                motivo=motivo,
                tarea_vinculada=vinculadas.get(fila.canvas_assignment_id),
            )
        )
    return salida


@dataclass(frozen=True)
class VistaPreviaNombres:
    slug: str
    slug_valido: bool
    slug_ocupado: bool
    ejemplo_repositorio: str | None
    ejemplo_sujeto: str
    repositorio_base: str | None


def vista_previa_nombres(
    bd: Session, *, curso: Curso, nombre: str, slug: str | None
) -> VistaPreviaNombres:
    """S13.5.1: vista previa en vivo del nombre de repositorio que resultara,
    con la misma funcion de dominio que usara el aprovisionamiento."""
    slug_final = (slug or "").strip() or normalizar(nombre)
    valido = es_slug_valido(slug_final)
    ocupado = (
        valido
        and bd.query(Tarea).filter(Tarea.curso_id == curso.id, Tarea.slug == slug_final).count() > 0
    )
    estudiante = (
        bd.query(Estudiante)
        .filter(Estudiante.curso_id == curso.id)
        .order_by(Estudiante.nombre_ordenable, Estudiante.nombre)
        .first()
    )
    if estudiante is not None:
        sujeto = SujetoNombre(
            tipo="e",
            canvas_id=estudiante.canvas_user_id,
            texto_legible=estudiante.nombre_ordenable or estudiante.nombre,
        )
        ejemplo_sujeto = estudiante.nombre
    else:
        sujeto = SujetoNombre(tipo="e", canvas_id=5310, texto_legible="Gómez, Ana")
        ejemplo_sujeto = "Ana Gómez (ejemplo)"
    return VistaPreviaNombres(
        slug=slug_final,
        slug_valido=valido,
        slug_ocupado=ocupado,
        ejemplo_repositorio=(
            nombre_repositorio(curso_slug=curso.slug, tarea_slug=slug_final, sujeto=sujeto)
            if valido
            else None
        ),
        ejemplo_sujeto=ejemplo_sujeto,
        repositorio_base=(
            nombre_repositorio(curso_slug=curso.slug, tarea_slug=slug_final, sujeto="base")
            if valido
            else None
        ),
    )


def entregas_de_tarea(bd: Session, tarea_id: uuid.UUID) -> list[Entrega]:
    return bd.query(Entrega).filter(Entrega.tarea_id == tarea_id).order_by(Entrega.orden).all()


def repositorio_base_de_tarea(bd: Session, tarea_id: uuid.UUID) -> RepositorioBase | None:
    return bd.query(RepositorioBase).filter(RepositorioBase.tarea_id == tarea_id).one_or_none()


def motivo_activacion(
    bd: Session, *, tarea: Tarea, curso: Curso, perfil_alcance: str
) -> str | None:
    base = repositorio_base_de_tarea(bd, tarea.id)
    return motivo_no_activable(
        estado_tarea=EstadoTarea(tarea.estado),
        modalidad=ModalidadTarea(tarea.modalidad),
        entregas=[
            EntregaActivacion(TipoEntrega(e.tipo), EstadoValidacionEntrega(e.estado_validacion))
            for e in entregas_de_tarea(bd, tarea.id)
        ],
        estado_repositorio_base=EstadoRepositorioBase(base.estado) if base is not None else None,
        github_vinculado=curso.github_installation_id is not None
        and curso.github_org_login is not None,
        perfil_alcance=perfil_alcance,
    )


def motivo_vincular_otra_entrega(bd: Session, *, tarea: Tarea, perfil_alcance: str) -> str | None:
    try:
        validar_vincular_otra_entrega(
            cantidad_actual=len(entregas_de_tarea(bd, tarea.id)), perfil_alcance=perfil_alcance
        )
    except RechazoTarea as exc:
        return exc.detalle
    return None


# --- Escrituras propias (sin llamadas externas) ---


def _assignment_elegible(
    bd: Session, *, curso: Curso, canvas_assignment_id: int
) -> AssignmentCanvas:
    fila = (
        bd.query(AssignmentCanvas)
        .filter(
            AssignmentCanvas.curso_id == curso.id,
            AssignmentCanvas.canvas_assignment_id == canvas_assignment_id,
        )
        .one_or_none()
    )
    if fila is None:
        raise RechazoTarea(
            MotivoRechazoTarea.ASSIGNMENT_NO_SINCRONIZADO,
            "Esa tarea de Canvas todavía no aparece en la aplicación: pulsa «Sincronizar ahora» "
            "y vuelve a intentarlo en unos segundos.",
        )
    if fila.canvas_assignment_id == curso.canvas_assignment_id_registro:
        raise RechazoTarea(
            MotivoRechazoTarea.ASSIGNMENT_ES_REGISTRO,
            "La tarea de registro de cuentas de GitHub no puede ser una entrega.",
        )
    if fila.ausente_en_canvas:
        raise RechazoTarea(
            MotivoRechazoTarea.ASSIGNMENT_ELIMINADO, "Esa tarea ya no existe en Canvas."
        )
    vinculada = (
        bd.query(Tarea.nombre)
        .join(Entrega, Entrega.tarea_id == Tarea.id)
        .filter(Entrega.curso_id == curso.id, Entrega.canvas_assignment_id == canvas_assignment_id)
        .one_or_none()
    )
    if vinculada is not None:
        # A-080: una tarea de Canvas pertenece a una sola entrega, nunca a dos.
        raise RechazoTarea(
            MotivoRechazoTarea.ASSIGNMENT_YA_VINCULADO,
            f"Esa tarea de Canvas ya está vinculada a la tarea «{vinculada[0]}».",
        )
    return fila


def _nueva_entrega(
    *, tarea: Tarea, fila: AssignmentCanvas, orden: int, tipo: TipoEntrega, slugs: set[str]
) -> Entrega:
    payload = fila.payload or {}
    return Entrega(
        tarea_id=tarea.id,
        curso_id=tarea.curso_id,
        canvas_assignment_id=fila.canvas_assignment_id,
        tipo=tipo.value,
        orden=orden,
        nombre=fila.nombre,
        slug=slug_entrega(nombre=fila.nombre, orden=orden, slugs_ocupados=slugs),
        puntos_posibles=payload.get("points_possible"),
        grading_type=payload.get("grading_type"),
        publicada=fila.publicada,
        moderated_grading=bool(payload.get("moderated_grading", False)),
        anonymous_grading=bool(payload.get("anonymous_grading", False)),
        group_category_id_canvas=fila.group_category_id_canvas,
        es_grupal_canvas=fila.es_grupal,
        only_visible_to_overrides=fila.only_visible_to_overrides,
        due_at_base=fila.due_at,
        all_day=bool(payload.get("all_day", False)),
        estado_validacion=EstadoValidacionEntrega.VIGENTE.value,
        validaciones=[],
        advertencias=[],
        ciclos_ausente=0,
        sincronizado_en=fila.sincronizado_en,
    )


def crear_tarea(
    bd: Session,
    *,
    curso: Curso,
    nombre: str,
    slug: str | None,
    canvas_assignment_id: int,
    gitignore_template: str | None,
    actor_usuario_id: uuid.UUID,
    perfil_alcance: str,
) -> Tarea:
    """R2.3.1 en su forma minima: la fila de `tarea` y su primera entrega, que
    nace `FINAL` con `orden = 1` (A-080 regla 4), en la misma transaccion."""
    if curso.canvas_course_id is None:
        raise RechazoTarea(
            MotivoRechazoTarea.CANVAS_NO_VINCULADO, "El curso todavía no tiene Canvas vinculado."
        )
    fila = _assignment_elegible(bd, curso=curso, canvas_assignment_id=canvas_assignment_id)
    modalidad = validar_modalidad_para_vincular(
        modalidad_tarea=None, es_grupal_canvas=fila.es_grupal, perfil_alcance=perfil_alcance
    )

    nombre_final = nombre.strip() or fila.nombre
    slug_final = (slug or "").strip() or normalizar(nombre_final)
    if not es_slug_valido(slug_final):
        raise RechazoTarea(
            MotivoRechazoTarea.SLUG_INVALIDO,
            "El identificador corto debe tener entre 1 y 24 caracteres, solo minúsculas, "
            "números y guiones, sin guion al inicio ni al final.",
        )
    if bd.query(Tarea).filter(Tarea.curso_id == curso.id, Tarea.slug == slug_final).count():
        raise RechazoTarea(
            MotivoRechazoTarea.SLUG_OCUPADO,
            f"Ya existe una tarea con el identificador «{slug_final}» en este curso: elige otro. "
            "Nunca se añade un sufijo automático.",
        )
    if gitignore_template is not None and gitignore_template not in PLANTILLAS_GITIGNORE:
        raise RechazoTarea(
            MotivoRechazoTarea.GITIGNORE_FUERA_DE_LISTA,
            "La plantilla .gitignore no está en la lista disponible.",
        )

    ahora = ahora_utc()
    tarea = Tarea(
        curso_id=curso.id,
        nombre=nombre_final,
        slug=slug_final,
        modalidad=modalidad.value,
        gitignore_template=gitignore_template,
        estado=EstadoTarea.BORRADOR.value,
        creada_por=actor_usuario_id,
        creada_en=ahora,
        actualizada_en=ahora,
    )
    bd.add(tarea)
    bd.flush()
    entrega = _nueva_entrega(tarea=tarea, fila=fila, orden=1, tipo=TipoEntrega.FINAL, slugs=set())
    bd.add(entrega)
    bd.flush()
    registrar_bitacora(
        bd,
        accion="TAREA_CREADA",
        entidad="tarea",
        entidad_id=str(tarea.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=curso.id,
        despues={
            "slug": tarea.slug,
            "modalidad": tarea.modalidad,
            "canvas_assignment_id": canvas_assignment_id,
        },
    )
    return tarea


def _aplicar_orden(
    bd: Session, entregas: dict[Hashable, Entrega], orden: list[EntregaOrden]
) -> None:
    """Reescribe `orden`/`tipo` sin chocar con `uq (tarea_id, orden)` ni con la
    unicidad parcial de `FINAL`: primero se apartan todas, luego se asignan."""
    for posicion, entrega in enumerate(entregas.values(), start=1):
        entrega.orden = 10_000 + posicion
        entrega.tipo = TipoEntrega.PARCIAL.value
    bd.flush()
    for item in orden:
        entregas[item.id].orden = item.orden
        entregas[item.id].tipo = item.tipo.value
    bd.flush()


def vincular_entrega(
    bd: Session,
    *,
    curso: Curso,
    tarea: Tarea,
    canvas_assignment_id: int,
    final_canvas_assignment_id: int | None,
    actor_usuario_id: uuid.UUID,
    perfil_alcance: str,
) -> Entrega:
    """R2.3.2: vincular otra tarea de Canvas como entrega. Bajo `parcial` la
    bandera `tarea_multientrega` la deja deshabilitada con motivo."""
    existentes = entregas_de_tarea(bd, tarea.id)
    validar_vincular_otra_entrega(cantidad_actual=len(existentes), perfil_alcance=perfil_alcance)
    fila = _assignment_elegible(bd, curso=curso, canvas_assignment_id=canvas_assignment_id)
    validar_modalidad_para_vincular(
        modalidad_tarea=ModalidadTarea(tarea.modalidad),
        es_grupal_canvas=fila.es_grupal,
        perfil_alcance=perfil_alcance,
    )

    por_canvas = {e.canvas_assignment_id: e for e in existentes}
    if final_canvas_assignment_id == canvas_assignment_id:
        final_id: Hashable | None = _NUEVA
    elif final_canvas_assignment_id in por_canvas:
        final_id = por_canvas[final_canvas_assignment_id].id
    else:
        final_id = None
    orden = ordenar_al_vincular(
        [EntregaOrden(id=e.id, orden=e.orden, tipo=TipoEntrega(e.tipo)) for e in existentes],
        nueva_id=_NUEVA,
        final_id=final_id,
    )
    posicion_nueva = next(item for item in orden if item.id == _NUEVA)

    _aplicar_orden(bd, {e.id: e for e in existentes}, [i for i in orden if i.id != _NUEVA])
    nueva = _nueva_entrega(
        tarea=tarea,
        fila=fila,
        orden=posicion_nueva.orden,
        tipo=posicion_nueva.tipo,
        slugs={e.slug for e in existentes},
    )
    bd.add(nueva)
    tarea.actualizada_en = ahora_utc()
    bd.flush()
    registrar_bitacora(
        bd,
        accion="ENTREGA_VINCULADA",
        entidad="entrega",
        entidad_id=str(nueva.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=curso.id,
        despues={
            "canvas_assignment_id": canvas_assignment_id,
            "tipo": nueva.tipo,
            "orden": nueva.orden,
        },
    )
    return nueva


def desvincular_entrega(
    bd: Session, *, curso: Curso, tarea: Tarea, entrega: Entrega, actor_usuario_id: uuid.UUID
) -> None:
    """CA-8.2-02: renumera en la misma transaccion. Etapa P7 todavia no
    captura versiones (Bloque 1, 23-sep), asi que nunca hay una que lo impida.
    Una tarea ya activa no puede quedar sin su entrega final (A-080 regla 3)."""
    existentes = entregas_de_tarea(bd, tarea.id)
    restantes = renumerar_al_desvincular(
        [EntregaOrden(id=e.id, orden=e.orden, tipo=TipoEntrega(e.tipo)) for e in existentes],
        quitar_id=entrega.id,
        # TODO(bloque-1): consultar `version_entrega` cuando exista.
        tiene_versiones_capturadas=False,
    )
    if not restantes and tarea.estado != EstadoTarea.BORRADOR.value:
        raise RechazoTarea(
            MotivoRechazoTarea.DESVINCULAR_NO_PERMITIDO,
            "Una tarea activa no puede quedar sin su entrega final.",
        )
    antes = {"canvas_assignment_id": entrega.canvas_assignment_id, "orden": entrega.orden}
    # `visibilidad_entrega` es derivada de la entrega: se va con ella.
    bd.query(VisibilidadEntrega).filter(VisibilidadEntrega.entrega_id == entrega.id).delete()
    bd.delete(entrega)
    bd.flush()
    _aplicar_orden(bd, {e.id: e for e in existentes if e.id != entrega.id}, restantes)
    tarea.actualizada_en = ahora_utc()
    bd.flush()
    registrar_bitacora(
        bd,
        accion="ENTREGA_DESVINCULADA",
        entidad="entrega",
        entidad_id=str(entrega.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=curso.id,
        antes=antes,
    )


def activar_tarea(
    bd: Session, *, curso: Curso, tarea: Tarea, actor_usuario_id: uuid.UUID, perfil_alcance: str
) -> Tarea:
    """`BORRADOR -> ACTIVA`, el unico gesto humano del camino normal (S8 intro)."""
    motivo = motivo_activacion(bd, tarea=tarea, curso=curso, perfil_alcance=perfil_alcance)
    if motivo is not None:
        raise RechazoTarea(MotivoRechazoTarea.NO_ACTIVABLE, motivo)
    ahora = ahora_utc()
    tarea.estado = EstadoTarea.ACTIVA.value
    tarea.activada_en = ahora
    tarea.activada_por = actor_usuario_id
    tarea.actualizada_en = ahora
    bd.flush()
    registrar_bitacora(
        bd,
        accion="TAREA_ACTIVADA",
        entidad="tarea",
        entidad_id=str(tarea.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=curso.id,
        antes={"estado": EstadoTarea.BORRADOR.value},
        despues={"estado": EstadoTarea.ACTIVA.value},
    )
    # R2.3.10: desde aqui todo ocurre solo. Se programan los barridos del curso
    # (S14.7.4) y se dispara la materializacion en la misma transaccion (S8.7.1).
    programacion_repo.asegurar_periodicos_de_curso(bd, curso.id)
    programacion_repo.asegurar_periodicos_globales(bd)
    encolar_materializacion(bd, curso_id=curso.id)
    return tarea
