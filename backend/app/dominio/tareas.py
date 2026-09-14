"""Reglas puras de tarea, entrega y repositorio base (SPEC 08 S8.2-S8.3; A-080,
A-097, A-164, A-203, A-208; Etapa P7).

Recibe datos ya leidos y decide. Las escrituras y las llamadas a Canvas y
GitHub viven en `app/adaptadores/tareas_repo.py` y
`app/adaptadores/repositorio_base_repo.py`.
"""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass
from enum import StrEnum

from app.dominio.alcance import bandera_activa, motivo_capa_3
from app.dominio.estados import (
    EstadoEstudiante,
    EstadoRepositorioBase,
    EstadoTarea,
    EstadoValidacionEntrega,
    ModalidadTarea,
    OrigenVisibilidadEntrega,
    TipoEntrega,
)
from app.dominio.nombres_repositorio import TOPIC_APLICACION, marcador_descripcion
from app.dominio.repositorio_github import RepoGithubInfo
from app.dominio.tareas_canvas import OverrideCanvasCrudo

# A-164: los unicos estados de estudiante que pueden ser sujeto de una tarea.
ESTADOS_ESTUDIANTE_SUJETO: frozenset[str] = frozenset(
    {EstadoEstudiante.ACTIVO.value, EstadoEstudiante.INVITADO.value}
)

# A-208: el README que crea `auto_init` no cuenta como contenido del base.
ARCHIVO_AUTO_INIT = "README.md"

# Tope propio de subida por la API de contenidos. El SPEC no fija uno; 1 MB
# alcanza para enunciados y codigo de partida y mantiene la escritura sincrona
# por debajo del tope duro de 20 s de A-169. Decision documentada.
TAMANO_MAXIMO_ARCHIVO_BYTES = 1_000_000

# S6.11.5: la aplicacion no sube archivos bajo `.github/workflows/`, como
# decision de producto y no como consecuencia del permiso concedido.
_PREFIJOS_PROHIBIDOS = (".github/workflows/", ".git/")

# Lista fija de plantillas `.gitignore` de GitHub ofrecidas al configurar la
# tarea (S8.3.4: "resuelto desde una lista fija"). Nombres exactos de
# github/gitignore, que es lo que acepta `gitignore_template`.
PLANTILLAS_GITIGNORE: tuple[str, ...] = (
    "C",
    "C++",
    "Go",
    "Java",
    "Node",
    "Python",
    "Ruby",
    "Rust",
    "VisualStudio",
)


class MotivoRechazoTarea(StrEnum):
    SLUG_INVALIDO = "SLUG_INVALIDO"
    SLUG_OCUPADO = "SLUG_OCUPADO"
    CANVAS_NO_VINCULADO = "CANVAS_NO_VINCULADO"
    GITHUB_NO_VINCULADO = "GITHUB_NO_VINCULADO"
    ASSIGNMENT_NO_SINCRONIZADO = "ASSIGNMENT_NO_SINCRONIZADO"
    ASSIGNMENT_YA_VINCULADO = "ASSIGNMENT_YA_VINCULADO"
    ASSIGNMENT_ES_REGISTRO = "ASSIGNMENT_ES_REGISTRO"
    ASSIGNMENT_ELIMINADO = "ASSIGNMENT_ELIMINADO"
    MODALIDAD_INCOMPATIBLE = "MODALIDAD_INCOMPATIBLE"
    MODALIDAD_GRUPAL_NO_DISPONIBLE = "MODALIDAD_GRUPAL_NO_DISPONIBLE"
    MULTIENTREGA_NO_DISPONIBLE = "MULTIENTREGA_NO_DISPONIBLE"
    FINAL_NO_ELEGIDA = "FINAL_NO_ELEGIDA"
    DESVINCULAR_NO_PERMITIDO = "DESVINCULAR_NO_PERMITIDO"
    TAREA_NO_EDITABLE = "TAREA_NO_EDITABLE"
    GITIGNORE_FUERA_DE_LISTA = "GITIGNORE_FUERA_DE_LISTA"
    RUTA_INVALIDA = "RUTA_INVALIDA"
    ARCHIVO_DEMASIADO_GRANDE = "ARCHIVO_DEMASIADO_GRANDE"
    REPOSITORIO_BASE_YA_EXISTE = "REPOSITORIO_BASE_YA_EXISTE"
    REPOSITORIO_BASE_NO_EXISTE = "REPOSITORIO_BASE_NO_EXISTE"
    REPOSITORIO_BASE_NO_OPERABLE = "REPOSITORIO_BASE_NO_OPERABLE"
    NO_ACTIVABLE = "NO_ACTIVABLE"


class RechazoTarea(Exception):
    """Capa 1 de S1.11: rechazo en el momento, con el mensaje que dice que hay,
    que se esperaba y que hacer. No se crea ninguna fila."""

    def __init__(self, motivo: MotivoRechazoTarea, detalle: str) -> None:
        self.motivo = motivo
        self.detalle = detalle
        super().__init__(f"{motivo.value}: {detalle}")


def modalidad_desde_canvas(*, es_grupal: bool) -> ModalidadTarea:
    return ModalidadTarea.GRUPAL if es_grupal else ModalidadTarea.INDIVIDUAL


def validar_modalidad_para_vincular(
    *, modalidad_tarea: ModalidadTarea | None, es_grupal_canvas: bool, perfil_alcance: str
) -> ModalidadTarea:
    """R2.3.3 por construccion (A-080) y CA-8.2-01: una tarea de Canvas con otra
    modalidad se rechaza y no se crea la entrega. La modalidad grupal es la
    bandera `tarea_modalidad_grupal` (capa 3 hasta el 23-sep)."""
    derivada = modalidad_desde_canvas(es_grupal=es_grupal_canvas)
    if modalidad_tarea is not None and modalidad_tarea != derivada:
        raise RechazoTarea(
            MotivoRechazoTarea.MODALIDAD_INCOMPATIBLE,
            f"Esta tarea es {_texto_modalidad(modalidad_tarea)} y la tarea de Canvas elegida "
            f"está configurada como {_texto_modalidad(derivada)}. Todas las entregas de una "
            "misma tarea deben tener la misma configuración: elige otra tarea de Canvas o "
            "cambia su configuración en Canvas.",
        )
    if derivada == ModalidadTarea.GRUPAL and not bandera_activa(
        perfil_alcance, "tarea_modalidad_grupal"
    ):
        raise RechazoTarea(
            MotivoRechazoTarea.MODALIDAD_GRUPAL_NO_DISPONIBLE,
            motivo_capa_3("tarea_modalidad_grupal", "Crear tareas grupales"),
        )
    return derivada


def _texto_modalidad(modalidad: ModalidadTarea) -> str:
    return "individual" if modalidad == ModalidadTarea.INDIVIDUAL else "grupal"


@dataclass(frozen=True)
class EntregaOrden:
    """Lo minimo de una entrega para decidir `orden` y `tipo` (A-080)."""

    id: Hashable
    orden: int
    tipo: TipoEntrega


def ordenar_al_vincular(
    existentes: list[EntregaOrden], *, nueva_id: Hashable, final_id: Hashable | None
) -> list[EntregaOrden]:
    """A-080 reglas 1, 2 y 4.

    - La primera entrega vinculada nace `FINAL` con `orden = 1`.
    - Al vincular otra, el profesor dice cual es la final (la anterior se
      propone por defecto en pantalla, nunca aqui en silencio): sin respuesta
      no se completa la operacion (CA-8.2-04).
    - `FINAL` es la de mayor `orden`, y `orden` queda contiguo desde 1.
    """
    if not existentes:
        return [EntregaOrden(id=nueva_id, orden=1, tipo=TipoEntrega.FINAL)]

    ids_validos = {e.id for e in existentes} | {nueva_id}
    if final_id is None or final_id not in ids_validos:
        raise RechazoTarea(
            MotivoRechazoTarea.FINAL_NO_ELEGIDA,
            "Al vincular una segunda entrega hay que indicar cuál de ellas es la entrega final.",
        )

    parciales = [e.id for e in sorted(existentes, key=lambda e: e.orden) if e.id != final_id]
    if nueva_id != final_id:
        parciales.append(nueva_id)
    secuencia = [*parciales, final_id]
    return [
        EntregaOrden(
            id=identificador,
            orden=posicion,
            tipo=TipoEntrega.FINAL if posicion == len(secuencia) else TipoEntrega.PARCIAL,
        )
        for posicion, identificador in enumerate(secuencia, start=1)
    ]


def renumerar_al_desvincular(
    existentes: list[EntregaOrden], *, quitar_id: Hashable, tiene_versiones_capturadas: bool
) -> list[EntregaOrden]:
    """A-080 regla 1 y CA-8.2-02/03: renumera en la misma transaccion, y solo
    mientras no haya ninguna version capturada; despues solo cabe excluir.
    Si se quita la final, la regla 2 (FINAL = mayor orden) decide la nueva."""
    if tiene_versiones_capturadas:
        raise RechazoTarea(
            MotivoRechazoTarea.DESVINCULAR_NO_PERMITIDO,
            "Esta tarea ya tiene versiones registradas: la entrega no se puede desvincular, "
            "solo marcarla como excluida.",
        )
    restantes = [e for e in sorted(existentes, key=lambda e: e.orden) if e.id != quitar_id]
    return [
        EntregaOrden(
            id=e.id,
            orden=posicion,
            tipo=TipoEntrega.FINAL if posicion == len(restantes) else TipoEntrega.PARCIAL,
        )
        for posicion, e in enumerate(restantes, start=1)
    ]


def validar_vincular_otra_entrega(*, cantidad_actual: int, perfil_alcance: str) -> None:
    """Bandera `tarea_multientrega` (S1.11): en la parcial una tarea tiene una
    sola entrega; la segunda es un control presente y deshabilitado con motivo."""
    if cantidad_actual >= 1 and not bandera_activa(perfil_alcance, "tarea_multientrega"):
        raise RechazoTarea(
            MotivoRechazoTarea.MULTIENTREGA_NO_DISPONIBLE,
            motivo_capa_3("tarea_multientrega", "Vincular varias entregas a una misma tarea"),
        )


@dataclass(frozen=True)
class EntregaActivacion:
    tipo: TipoEntrega
    estado_validacion: EstadoValidacionEntrega


def motivo_no_activable(
    *,
    estado_tarea: EstadoTarea,
    modalidad: ModalidadTarea,
    entregas: list[EntregaActivacion],
    estado_repositorio_base: EstadoRepositorioBase | None,
    github_vinculado: bool,
    perfil_alcance: str,
) -> str | None:
    """`tarea_activable(tarea)` de A-208. `None` = se puede activar; si no, el
    motivo escrito que la pantalla muestra junto al boton deshabilitado.

    El base se exige `LISTO` solo si la tarea lo declara (CA-8.3-01)."""
    if estado_tarea != EstadoTarea.BORRADOR:
        return "La tarea ya no está en borrador."
    finales = [e for e in entregas if e.tipo == TipoEntrega.FINAL]
    if len(finales) != 1:
        return "La tarea necesita exactamente una entrega final vinculada."
    if any(e.estado_validacion == EstadoValidacionEntrega.ELIMINADA_EN_CANVAS for e in entregas):
        return "Una entrega vinculada ya no existe en Canvas: restáurala en Canvas o desvincúlala."
    if modalidad == ModalidadTarea.GRUPAL and not bandera_activa(
        perfil_alcance, "tarea_modalidad_grupal"
    ):
        return motivo_capa_3("tarea_modalidad_grupal", "Activar tareas grupales")
    if not github_vinculado:
        return "El curso todavía no tiene GitHub vinculado."
    if (
        estado_repositorio_base is not None
        and estado_repositorio_base != EstadoRepositorioBase.LISTO
    ):
        return _MOTIVO_POR_ESTADO_BASE[estado_repositorio_base]
    return None


_MOTIVO_POR_ESTADO_BASE: dict[EstadoRepositorioBase, str] = {
    EstadoRepositorioBase.CREANDO: "El repositorio base todavía se está creando.",
    # CA-8.3-02, texto literal.
    EstadoRepositorioBase.CREADO_VACIO: "El repositorio base no tiene contenido.",
    EstadoRepositorioBase.ERROR: "El repositorio base quedó con un error al crearse.",
    EstadoRepositorioBase.INACCESIBLE: "El repositorio base no es accesible en GitHub.",
}


def estado_base_segun_archivos(rutas: set[str]) -> EstadoRepositorioBase:
    """A-208: `LISTO` si el arbol tiene al menos un archivo mas que el README de
    `auto_init`; si no, `CREADO_VACIO` (incluido el caso en que el profesor
    borro todo lo que habia subido, A-067)."""
    if any(ruta != ARCHIVO_AUTO_INIT for ruta in rutas):
        return EstadoRepositorioBase.LISTO
    return EstadoRepositorioBase.CREADO_VACIO


def validar_ruta_archivo(ruta: str) -> str:
    """Ruta relativa al raiz del repositorio base, con `/` como separador."""
    limpia = ruta.strip()
    segmentos = limpia.split("/")
    if (
        not limpia
        or len(limpia) > 255
        or "\\" in limpia
        or limpia.startswith("/")
        or any(s in ("", ".", "..") for s in segmentos)
    ):
        raise RechazoTarea(
            MotivoRechazoTarea.RUTA_INVALIDA,
            "La ruta del archivo no es válida: usa una ruta relativa como `src/main.py`, "
            "sin `..` ni barras al inicio.",
        )
    if any(limpia.startswith(prefijo) for prefijo in _PREFIJOS_PROHIBIDOS):
        raise RechazoTarea(
            MotivoRechazoTarea.RUTA_INVALIDA,
            "La aplicación no sube archivos dentro de `.github/workflows/` ni de `.git/`.",
        )
    return limpia


def validar_tamano_archivo(tamano_bytes: int) -> None:
    if tamano_bytes > TAMANO_MAXIMO_ARCHIVO_BYTES:
        raise RechazoTarea(
            MotivoRechazoTarea.ARCHIVO_DEMASIADO_GRANDE,
            f"El archivo pesa {tamano_bytes} bytes; el máximo por archivo es "
            f"{TAMANO_MAXIMO_ARCHIVO_BYTES} bytes.",
        )


def condiciones_adopcion_fallidas(
    repo: RepoGithubInfo, *, org_login: str, curso_slug: str, tarea_slug: str
) -> list[str]:
    """A-097 aplicado al repositorio base: lista vacia = se adopta.

    La condicion (e) -- "su historia no contiene commits ajenos a la
    plantilla" -- no aplica al base: por definicion recibe commits con los
    archivos que el profesor sube, todos escritos por la propia App. Se
    comprueban (a)-(d); decision documentada."""
    fallidas: list[str] = []
    if TOPIC_APLICACION not in repo.topics:
        fallidas.append("a: no tiene el topic gestor-tareas")
    if repo.owner_login.lower() != org_login.lower():
        fallidas.append("b: no pertenece a la organización vinculada")
    if f"curso-{curso_slug}" not in repo.topics:
        fallidas.append(f"c: no tiene el topic curso-{curso_slug}")
    marcador = marcador_descripcion(curso_slug=curso_slug, tarea_slug=tarea_slug, sujeto="base")
    if marcador not in (repo.descripcion or ""):
        fallidas.append(f"d: su descripción no contiene el marcador {marcador}")
    return fallidas


@dataclass(frozen=True)
class EstudianteVisibilidad:
    estudiante_id: Hashable
    canvas_user_id: int
    estado: str
    canvas_section_ids: frozenset[int]
    canvas_group_ids: frozenset[int]


@dataclass(frozen=True)
class ResultadoVisibilidad:
    origen: OrigenVisibilidadEntrega
    visibles: frozenset[Hashable]

    @property
    def no_resoluble(self) -> bool:
        return self.origen == OrigenVisibilidadEntrega.SUPUESTO


def resolver_visibilidad(
    *,
    only_visible_to_overrides: bool,
    assignment_visibility: list[int] | None,
    overrides: list[OverrideCanvasCrudo] | None,
    estudiantes: list[EstudianteVisibilidad],
) -> ResultadoVisibilidad:
    """A-164 paso 1, las cuatro filas en orden. Nunca se supone visibilidad
    universal cuando `only_visible_to_overrides` es verdadero."""
    if not only_visible_to_overrides:
        return ResultadoVisibilidad(
            origen=OrigenVisibilidadEntrega.TODOS,
            visibles=frozenset(
                e.estudiante_id for e in estudiantes if e.estado in ESTADOS_ESTUDIANTE_SUJETO
            ),
        )
    if assignment_visibility is not None:
        permitidos = set(assignment_visibility)
        return ResultadoVisibilidad(
            origen=OrigenVisibilidadEntrega.ASSIGNMENT_VISIBILITY,
            visibles=frozenset(
                e.estudiante_id for e in estudiantes if e.canvas_user_id in permitidos
            ),
        )
    if overrides is not None:
        alcanzados: set[Hashable] = set()
        for override in overrides:
            for e in estudiantes:
                if (
                    (override.student_ids is not None and e.canvas_user_id in override.student_ids)
                    or (
                        override.course_section_id is not None
                        and override.course_section_id in e.canvas_section_ids
                    )
                    or (override.group_id is not None and override.group_id in e.canvas_group_ids)
                ):
                    alcanzados.add(e.estudiante_id)
        return ResultadoVisibilidad(
            origen=OrigenVisibilidadEntrega.OVERRIDE, visibles=frozenset(alcanzados)
        )
    return ResultadoVisibilidad(origen=OrigenVisibilidadEntrega.SUPUESTO, visibles=frozenset())
