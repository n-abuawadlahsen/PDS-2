"""`ClienteCanvas`: interfaz con dos implementaciones (SPEC 05 S5.2.1, A-133 patron).

`ClienteCanvasReal` habla con una instancia de Canvas real por HTTPS.
`ClienteCanvasDoble` es una version simplificada de "modo doble" para
desarrollo local y `ensayo` sin credenciales reales: un conjunto de datos
fijo y determinista. El SPEC (S14.4) describe "modo doble" como grabaciones
reales de Canvas; esa mecanica de grabar/reproducir todavia no existe (queda
para cuando haya un entorno de `ensayo` real) -- por ahora `ClienteCanvasDoble`
alcanza para desarrollar y probar el asistente de vinculacion sin depender de
una instancia de Canvas de verdad.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

import httpx

from app.adaptadores import paginacion
from app.dominio.padron_canvas import (
    ConjuntoGruposCrudo,
    GrupoCrudo,
    MatriculaCruda,
    PertenenciaCruda,
    ResultadoPaginado,
    SeccionCruda,
)
from app.dominio.registro_canvas import (
    ConfiguracionTareaRegistro,
    EntregaRegistro,
    TareaRegistroCreada,
)
from app.dominio.tareas_canvas import AssignmentCanvasCrudo, OverrideCanvasCrudo
from app.dominio.vinculacion_canvas import (
    CursoCanvas,
    DetalleCursoCanvas,
    MatriculaCanvas,
    MotivoRechazoVinculacion,
    PeriodoCalificacionCanvas,
    RechazoVinculacion,
    RosterCanvas,
    SeccionCanvas,
    UsuarioCanvas,
)
from app.infraestructura.scopes_canvas import EndpointCanvas

_TIMEOUT_SEGUNDOS = 20.0

# Prueba de arquitectura (S5.3 CA-1): cada llamada real registra aqui el
# endpoint que uso, y una prueba contrasta esta lista contra SCOPES_CANVAS.
LLAMADAS_REGISTRADAS: list[EndpointCanvas] = []

# Unico estado mutable de `ClienteCanvasDoble` (el resto del doble es puro):
# simula que "Canvas" recuerda la ultima configuracion escrita de la tarea de
# registro, para que la deteccion de desviacion (S7.2.3) compare contra lo
# que de verdad se escribio la ultima vez, no contra un valor fijo del
# fixture. Un archivo en disco, no un dict en memoria: el servicio web (que
# crea la tarea) y el trabajador (que la verifica, S14.5.1) son DOS PROCESOS
# separados incluso en desarrollo local, y un dict de modulo no sobrevive ese
# salto -- un archivo compartido si. Ruta fija bajo el repo, no el directorio
# temporal del sistema operativo: dos procesos locales pueden heredar un
# `TEMP` distinto segun como se lancen, pero ambos comparten el mismo checkout.
_ARCHIVO_ESTADO_REGISTRO_DOBLE = (
    Path(__file__).resolve().parent.parent.parent / ".doble_registro_github.json"
)


def _leer_config_registro_doble(canvas_assignment_id: int) -> ConfiguracionTareaRegistro | None:
    try:
        datos = json.loads(_ARCHIVO_ESTADO_REGISTRO_DOBLE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    fila = datos.get(str(canvas_assignment_id))
    if fila is None:
        return None
    return ConfiguracionTareaRegistro(**fila)


def _escribir_config_registro_doble(
    canvas_assignment_id: int, config: ConfiguracionTareaRegistro
) -> None:
    try:
        datos = json.loads(_ARCHIVO_ESTADO_REGISTRO_DOBLE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        datos = {}
    datos[str(canvas_assignment_id)] = {
        "nombre": config.nombre,
        "descripcion_html": config.descripcion_html,
        "submission_types": config.submission_types,
        "points_possible": config.points_possible,
        "omit_from_final_grade": config.omit_from_final_grade,
        "published": config.published,
        "due_at_iso": config.due_at_iso,
        "grading_type": config.grading_type,
    }
    _ARCHIVO_ESTADO_REGISTRO_DOBLE.write_text(json.dumps(datos))


@dataclass(frozen=True)
class AnuncioCreado:
    topic_id: int
    html_url: str | None


RUBRICA_DOBLE: list[dict[str, Any]] = [
    {
        "id": "c1",
        "description": "Correctitud",
        "points": 60,
        "ratings": [
            {"id": "r11", "description": "Completa", "points": 60},
            {"id": "r12", "description": "Parcial", "points": 30},
            {"id": "r13", "description": "No funciona", "points": 0},
        ],
    },
    {
        "id": "c2",
        "description": "Estilo",
        "points": 40,
        "ratings": [
            {"id": "r21", "description": "Claro", "points": 40},
            {"id": "r22", "description": "Mejorable", "points": 20},
        ],
    },
]


@dataclass(frozen=True)
class RespuestaCanvas:
    codigo_http: int
    cuerpo: dict[str, Any]


@dataclass(frozen=True)
class CalificacionCanvas:
    canvas_user_id: int
    workflow_state: str | None
    score: float | None
    entered_score: float | None
    grade: str | None
    graded_at: datetime | None
    grader_id: int | None
    excused: bool | None
    late: bool | None
    seconds_late: int | None
    points_deducted: float | None
    submitted_at: datetime | None
    posted_at: datetime | None


def _calificacion_desde_json(d: dict[str, Any]) -> CalificacionCanvas:
    def num(v: Any) -> float | None:
        return None if v is None else float(v)

    return CalificacionCanvas(
        canvas_user_id=int(d["user_id"]),
        workflow_state=d.get("workflow_state"),
        score=num(d.get("score")),
        entered_score=num(d.get("entered_score")),
        grade=d.get("grade"),
        graded_at=_fecha_canvas(d.get("graded_at")),
        grader_id=d.get("grader_id"),
        excused=d.get("excused"),
        late=d.get("late"),
        seconds_late=d.get("seconds_late"),
        points_deducted=num(d.get("points_deducted")),
        submitted_at=_fecha_canvas(d.get("submitted_at")),
        posted_at=_fecha_canvas(d.get("posted_at")),
    )


# Solo para pruebas: notas que el doble «guarda» y lo que se le «publico».
calificaciones_doble: dict[tuple[int, int], dict[str, Any]] = {}
publicaciones_doble: list[dict[str, Any]] = []
no_calificables_doble: set[int] = set()
periodo_cerrado_doble = False
descuento_doble = 0.0


def calificar_en_canvas_doble(
    canvas_assignment_id: int, canvas_user_id: int, score: float, graded_at: datetime
) -> None:
    """Solo para pruebas: alguien califico en SpeedGrader."""
    calificaciones_doble[(canvas_assignment_id, canvas_user_id)] = {
        "user_id": canvas_user_id,
        "score": score,
        "entered_score": score,
        "grade": str(score),
        "graded_at": graded_at.isoformat(),
        "grader_id": 9999,
        "workflow_state": "graded",
    }


# Solo para pruebas: lo que el doble «publico» y «envio».
conversaciones_doble: list[dict[str, Any]] = []
anuncios_doble: list[dict[str, Any]] = []
anuncios_borrados_doble: list[int] = []
rechazar_secciones_doble = False


class FalloProveedorCanvas(Exception):
    """5xx o timeout de Canvas: nunca se traduce a un diagnostico inventado (Ley 5)."""


class ClienteCanvas(Protocol):
    def obtener_usuario_actual(self, token: str) -> UsuarioCanvas: ...

    def listar_cursos_profesor(self, token: str) -> list[CursoCanvas]: ...

    def obtener_matriculas_profesor(
        self, token: str, canvas_course_id: int
    ) -> list[MatriculaCanvas]: ...

    def obtener_detalle_curso(
        self, token: str, canvas_course_id: int, permisos: list[str]
    ) -> DetalleCursoCanvas: ...

    def obtener_secciones(self, token: str, canvas_course_id: int) -> list[SeccionCanvas]: ...

    def contar_grupos(self, token: str, canvas_course_id: int) -> int: ...

    def existe_politica_entrega_tardia(self, token: str, canvas_course_id: int) -> bool: ...

    def obtener_periodos_calificacion(
        self, token: str, canvas_course_id: int
    ) -> list[PeriodoCalificacionCanvas]: ...

    def obtener_roster(self, token: str, canvas_course_id: int) -> RosterCanvas: ...

    def ejecutar_prueba_anuncio(
        self, token: str, canvas_course_id: int, *, section_id: int | None
    ) -> bool:
        """5-bis (S4.7.2): crea el anuncio de prueba y lo borra de inmediato,
        `section_id=None` = pasada sin `specific_sections`. Devuelve `True` si
        ambos pasos (crear y borrar) terminaron en 2xx."""
        ...

    def ejecutar_prueba_comentario_entrega(self, token: str, canvas_course_id: int) -> bool | None:
        """17-bis: comenta la primera entrega encontrada. `None` si el curso
        no tiene ninguna entrega sobre la que probar (nada que verificar)."""
        ...

    def obtener_roster_paginado(
        self, token: str, canvas_course_id: int, *, roles_extra: list[int] | None = None
    ) -> ResultadoPaginado[MatriculaCruda]:
        """S7.3.1: roster completo, todos los `workflow_state` relevantes
        para derivar `estudiante.estado` (S7.2.1), no solo `active`."""
        ...

    def obtener_secciones_paginado(
        self, token: str, canvas_course_id: int
    ) -> ResultadoPaginado[SeccionCruda]: ...

    def obtener_conjuntos_grupos_paginado(
        self, token: str, canvas_course_id: int
    ) -> ResultadoPaginado[ConjuntoGruposCrudo]: ...

    def obtener_grupos_de_conjunto_paginado(
        self, token: str, canvas_group_category_id: int
    ) -> ResultadoPaginado[GrupoCrudo]: ...

    def obtener_pertenencias_de_grupo_paginado(
        self, token: str, canvas_group_id: int
    ) -> ResultadoPaginado[PertenenciaCruda]: ...

    def crear_tarea_registro(
        self, token: str, canvas_course_id: int, config: ConfiguracionTareaRegistro
    ) -> TareaRegistroCreada:
        """SPEC 07 S7.4.1: escritura sincrona #4 (SPEC 05 S5.5.1)."""
        ...

    def actualizar_tarea_registro(
        self,
        token: str,
        canvas_course_id: int,
        canvas_assignment_id: int,
        config: ConfiguracionTareaRegistro,
    ) -> None:
        """`PUT .../assignments/{id}`: restaura la configuracion canonica
        cuando `registro_estado = ALTERADA` (S7.1 correccion de precedencia)."""
        ...

    def obtener_configuracion_tarea(
        self, token: str, canvas_course_id: int, canvas_assignment_id: int
    ) -> ConfiguracionTareaRegistro | None:
        """`None` si la tarea ya no existe en Canvas (`DESAPARECIDA`, S7.2.3)."""
        ...

    def obtener_entregas_tarea_paginado(
        self, token: str, canvas_course_id: int, canvas_assignment_id: int
    ) -> ResultadoPaginado[EntregaRegistro]: ...

    def comentar_entrega(
        self,
        token: str,
        canvas_course_id: int,
        canvas_assignment_id: int,
        canvas_user_id: int,
        comentario: str,
    ) -> bool:
        """S7.4.6: el bucle se cierra dentro de Canvas, siempre con un
        comentario automatico en la misma entrega."""
        ...

    def enviar_conversacion(
        self, token: str, *, destinatarios_canvas_user_ids: list[int], asunto: str, cuerpo: str
    ) -> bool:
        """SPEC 04 S4.7.2/SPEC 05 S5.5.1: `POST /conversations`, una llamada
        por destinatario con `group_conversation=false` y sin `bulk_message`
        (S11.7.2, CA-11.7-01). `True` si todas terminaron en 2xx."""
        ...

    def crear_anuncio(
        self,
        token: str,
        canvas_course_id: int,
        *,
        titulo: str,
        mensaje_html: str,
        secciones: list[int] | None,
    ) -> AnuncioCreado | None:
        """`POST .../discussion_topics` con `is_announcement=true`, cerrado a
        comentarios. Nunca `published=false` (CA-11.8-01). `None` si Canvas lo
        rechazo con 4xx."""
        ...

    def borrar_anuncio(self, token: str, canvas_course_id: int, topic_id: int) -> bool:
        """`DELETE .../discussion_topics/{id}`: retractar un anuncio publicado."""
        ...

    def publicar_nota(
        self,
        token: str,
        canvas_course_id: int,
        canvas_assignment_id: int,
        canvas_user_id: int,
        payload: dict[str, Any],
    ) -> RespuestaCanvas:
        """Escritura sincrona #5 (A-169): `PUT .../submissions/{user_id}` con
        nota, comentario y rubrica en una sola peticion. Nunca `as_user_id`."""
        ...

    def leer_calificaciones(
        self, token: str, canvas_course_id: int, canvas_assignment_id: int
    ) -> list[CalificacionCanvas]:
        """`GET .../students/submissions` de una tarea, paginado. Nunca
        `submission_summary` (A-206)."""
        ...

    def estudiantes_calificables(
        self, token: str, canvas_course_id: int, canvas_assignment_id: int
    ) -> set[int]:
        """`GET .../assignments/{id}/gradeable_students`."""
        ...

    def obtener_assignments_paginado(
        self, token: str, canvas_course_id: int
    ) -> ResultadoPaginado[AssignmentCanvasCrudo]:
        """Endpoint 12 con `include[]=assignment_visibility` (A-164 paso 1):
        alimenta el espejo `assignment_canvas` desde `sync_tareas_y_fechas`."""
        ...

    def obtener_assignment(
        self, token: str, canvas_course_id: int, canvas_assignment_id: int
    ) -> AssignmentCanvasCrudo | None:
        """Endpoint 13. `None` si Canvas responde 404: es la confirmacion que
        A-203 exige antes de marcar una entrega `ELIMINADA_EN_CANVAS`."""
        ...

    def obtener_overrides_assignment(
        self, token: str, canvas_course_id: int, canvas_assignment_id: int
    ) -> list[OverrideCanvasCrudo]:
        """Endpoint 14: solo se pide cuando `only_visible_to_overrides` es
        verdadero y la instancia no devolvio `assignment_visibility`."""
        ...


def _fecha_canvas(valor: str | None) -> datetime | None:
    if not valor:
        return None
    return datetime.fromisoformat(valor.replace("Z", "+00:00"))


def _assignment_desde_json(d: dict[str, Any]) -> AssignmentCanvasCrudo:
    visibilidad = d.get("assignment_visibility")
    return AssignmentCanvasCrudo(
        canvas_assignment_id=d["id"],
        nombre=d.get("name", ""),
        puntos_posibles=d.get("points_possible"),
        grading_type=d.get("grading_type"),
        publicada=bool(d.get("published", False)),
        moderated_grading=bool(d.get("moderated_grading", False)),
        anonymous_grading=bool(d.get("anonymous_grading", False)),
        group_category_id=d.get("group_category_id"),
        only_visible_to_overrides=bool(d.get("only_visible_to_overrides", False)),
        due_at=_fecha_canvas(d.get("due_at")),
        all_day=bool(d.get("all_day", False)),
        canvas_updated_at=_fecha_canvas(d.get("updated_at")),
        assignment_visibility=[int(u) for u in visibilidad] if visibilidad is not None else None,
        payload=d,
    )


class ClienteCanvasReal:
    def __init__(self, canvas_base_url: str) -> None:
        self._base_url = canvas_base_url.rstrip("/")

    def _get(
        self, plantilla: str, ruta: str, *, token: str, params: dict[str, Any] | None = None
    ) -> httpx.Response:
        LLAMADAS_REGISTRADAS.append(EndpointCanvas("GET", plantilla))
        try:
            return httpx.get(
                f"{self._base_url}{ruta}",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
                timeout=_TIMEOUT_SEGUNDOS,
            )
        except httpx.TimeoutException as exc:
            raise FalloProveedorCanvas("tiempo de espera agotado") from exc

    def _escribir(
        self,
        metodo: str,
        plantilla: str,
        ruta: str,
        *,
        token: str,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        LLAMADAS_REGISTRADAS.append(EndpointCanvas(metodo, plantilla))
        try:
            return httpx.request(
                metodo,
                f"{self._base_url}{ruta}",
                headers={"Authorization": f"Bearer {token}"},
                json=json,
                timeout=_TIMEOUT_SEGUNDOS,
            )
        except httpx.TimeoutException as exc:
            raise FalloProveedorCanvas("tiempo de espera agotado") from exc

    def obtener_usuario_actual(self, token: str) -> UsuarioCanvas:
        respuesta = self._get("/api/v1/users/self", "/api/v1/users/self", token=token)
        if respuesta.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
        if respuesta.status_code != 200:
            # Comprobacion 2.a (S5.2.3): cualquier respuesta que no sea 200 se
            # trata como "el token no sirve", sin distinguir 401 de 403 aqui.
            raise RechazoVinculacion(MotivoRechazoVinculacion.TOKEN_INVALIDO)
        datos = respuesta.json()
        return UsuarioCanvas(canvas_user_id=datos["id"], nombre=datos.get("name", ""))

    def listar_cursos_profesor(self, token: str) -> list[CursoCanvas]:
        respuesta = self._get(
            "/api/v1/courses",
            "/api/v1/courses",
            token=token,
            params={
                "enrollment_type": "teacher",
                "enrollment_state": "active",
                "include[]": ["term", "total_students"],
                "per_page": 100,
            },
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
        respuesta.raise_for_status()
        return [
            CursoCanvas(
                canvas_course_id=c["id"],
                nombre=c.get("name", ""),
                codigo=c.get("course_code", ""),
                termino=(c.get("term") or {}).get("name"),
                total_estudiantes=c.get("total_students"),
            )
            for c in respuesta.json()
        ]

    def obtener_matriculas_profesor(
        self, token: str, canvas_course_id: int
    ) -> list[MatriculaCanvas]:
        respuesta = self._get(
            "/api/v1/courses/{course_id}/enrollments",
            f"/api/v1/courses/{canvas_course_id}/enrollments",
            token=token,
            params={"user_id": "self", "type[]": ["TeacherEnrollment"]},
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
        respuesta.raise_for_status()
        return [
            MatriculaCanvas(
                tipo=m.get("type", ""),
                workflow_state=m.get("enrollment_state", m.get("workflow_state", "")),
                limitada_a_seccion=bool(m.get("limit_privileges_to_course_section", False)),
            )
            for m in respuesta.json()
        ]

    def obtener_detalle_curso(
        self, token: str, canvas_course_id: int, permisos: list[str]
    ) -> DetalleCursoCanvas:
        """Dos llamadas del catalogo cerrado (S5.3): `/courses/:id` para
        existencia/publicacion/zona horaria, `/courses/:id/permissions` para
        los permisos de items 4-7, 16, 17, 19 (item 2 y 13 usan la primera)."""
        respuesta = self._get(
            "/api/v1/courses/{course_id}", f"/api/v1/courses/{canvas_course_id}", token=token
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
        if respuesta.status_code == 404:
            return DetalleCursoCanvas(existe=False, publicado=False, time_zone=None, permisos={})
        respuesta.raise_for_status()
        datos = respuesta.json()

        respuesta_permisos = self._get(
            "/api/v1/courses/{course_id}/permissions",
            f"/api/v1/courses/{canvas_course_id}/permissions",
            token=token,
            params={"permissions[]": permisos},
        )
        if respuesta_permisos.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta_permisos.status_code}")
        respuesta_permisos.raise_for_status()
        permisos_devueltos = respuesta_permisos.json()

        return DetalleCursoCanvas(
            existe=True,
            publicado=datos.get("workflow_state") == "available",
            time_zone=datos.get("time_zone"),
            permisos={p: bool(permisos_devueltos.get(p, False)) for p in permisos},
        )

    def obtener_secciones(self, token: str, canvas_course_id: int) -> list[SeccionCanvas]:
        respuesta = self._get(
            "/api/v1/courses/{course_id}/sections",
            f"/api/v1/courses/{canvas_course_id}/sections",
            token=token,
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
        respuesta.raise_for_status()
        return [
            SeccionCanvas(
                section_id=s["id"],
                nombre=s.get("name", ""),
                es_cross_listed=s.get("nonxlist_course_id") is not None,
            )
            for s in respuesta.json()
        ]

    def contar_grupos(self, token: str, canvas_course_id: int) -> int:
        respuesta = self._get(
            "/api/v1/courses/{course_id}/group_categories",
            f"/api/v1/courses/{canvas_course_id}/group_categories",
            token=token,
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
        respuesta.raise_for_status()
        return len(respuesta.json())

    def existe_politica_entrega_tardia(self, token: str, canvas_course_id: int) -> bool:
        respuesta = self._get(
            "/api/v1/courses/{course_id}/late_policy",
            f"/api/v1/courses/{canvas_course_id}/late_policy",
            token=token,
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
        return respuesta.status_code == 200

    def obtener_periodos_calificacion(
        self, token: str, canvas_course_id: int
    ) -> list[PeriodoCalificacionCanvas]:
        respuesta = self._get(
            "/api/v1/courses/{course_id}/grading_periods",
            f"/api/v1/courses/{canvas_course_id}/grading_periods",
            token=token,
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
        if respuesta.status_code == 404:
            return []
        respuesta.raise_for_status()
        return [
            PeriodoCalificacionCanvas(
                is_closed=bool(p.get("is_closed", False)),
                start_date=_fecha_canvas(p.get("start_date")),
                end_date=_fecha_canvas(p.get("end_date")),
            )
            for p in respuesta.json().get("grading_periods", [])
        ]

    def obtener_roster(self, token: str, canvas_course_id: int) -> RosterCanvas:
        """Reutiliza `/courses/:id/enrollments` (mismo endpoint del item 3, ya
        en el catalogo cerrado de S5.3) filtrado a `StudentEnrollment`: no hay
        un endpoint de roster aparte en las 25 entradas de `SCOPES_CANVAS`."""
        respuesta = self._get(
            "/api/v1/courses/{course_id}/enrollments",
            f"/api/v1/courses/{canvas_course_id}/enrollments",
            token=token,
            params={"type[]": "StudentEnrollment", "per_page": 100},
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
        respuesta.raise_for_status()
        return RosterCanvas(
            cantidad_primera_pagina=len(respuesta.json()),
            hay_siguiente_pagina='rel="next"' in respuesta.headers.get("Link", ""),
        )

    def ejecutar_prueba_anuncio(
        self, token: str, canvas_course_id: int, *, section_id: int | None
    ) -> bool:
        payload: dict[str, Any] = {
            "title": "[verificación app] prueba de escritura",
            "message": "Prueba automatica de verificacion de permisos. Se borra de inmediato.",
            "is_announcement": True,
            "published": True,
            "delayed_post_at": (datetime.now(UTC) + timedelta(days=365)).isoformat(),
        }
        if section_id is not None:
            payload["specific_sections"] = str(section_id)
        creado = self._escribir(
            "POST",
            "/api/v1/courses/{course_id}/discussion_topics",
            f"/api/v1/courses/{canvas_course_id}/discussion_topics",
            token=token,
            json=payload,
        )
        if creado.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {creado.status_code}")
        if creado.status_code not in (200, 201):
            return False
        topic_id = creado.json()["id"]
        borrado = self._escribir(
            "DELETE",
            "/api/v1/courses/{course_id}/discussion_topics/{topic_id}",
            f"/api/v1/courses/{canvas_course_id}/discussion_topics/{topic_id}",
            token=token,
        )
        if borrado.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {borrado.status_code}")
        return borrado.status_code in (200, 204)

    def ejecutar_prueba_comentario_entrega(self, token: str, canvas_course_id: int) -> bool | None:
        respuesta = self._get(
            "/api/v1/courses/{course_id}/students/submissions",
            f"/api/v1/courses/{canvas_course_id}/students/submissions",
            token=token,
            params={"student_ids[]": "all", "per_page": 1},
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
        respuesta.raise_for_status()
        entregas = respuesta.json()
        if not entregas:
            return None
        primera = entregas[0]
        comentado = self._escribir(
            "PUT",
            "/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}",
            f"/api/v1/courses/{canvas_course_id}/assignments/{primera['assignment_id']}"
            f"/submissions/{primera['user_id']}",
            token=token,
            json={"comment": {"text_comment": "[verificación app] prueba de escritura"}},
        )
        if comentado.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {comentado.status_code}")
        return comentado.status_code == 200

    def _paginas(
        self, plantilla: str, ruta: str, *, token: str, params: dict[str, Any] | None = None
    ) -> tuple[list[dict[str, Any]], int, bool]:
        """S5.4.2: sigue siempre el header `Link`, mide `per_page` en la
        primera pagina, corta a las 50 sin fallar."""
        LLAMADAS_REGISTRADAS.append(EndpointCanvas("GET", plantilla))
        url_inicial = str(httpx.URL(f"{self._base_url}{ruta}", params=params or {}))
        encabezados = {"Authorization": f"Bearer {token}"}
        items: list[dict[str, Any]] = []
        per_page_medido = 0
        truncado = False
        try:
            with httpx.Client(timeout=_TIMEOUT_SEGUNDOS) as cliente_http:
                for pagina in paginacion.paginas(
                    cliente_http=cliente_http, url_inicial=url_inicial, encabezados=encabezados
                ):
                    if pagina.numero == 1:
                        per_page_medido = len(pagina.items)
                    items.extend(pagina.items)
                    truncado = pagina.truncada
        except httpx.TimeoutException as exc:
            raise FalloProveedorCanvas("tiempo de espera agotado") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code >= 500:
                raise FalloProveedorCanvas(f"Canvas respondio {exc.response.status_code}") from exc
            raise
        return items, per_page_medido, truncado

    def obtener_roster_paginado(
        self, token: str, canvas_course_id: int, *, roles_extra: list[int] | None = None
    ) -> ResultadoPaginado[MatriculaCruda]:
        items, per_page, truncado = self._paginas(
            "/api/v1/courses/{course_id}/enrollments",
            f"/api/v1/courses/{canvas_course_id}/enrollments",
            token=token,
            params={
                "type[]": "StudentEnrollment",
                "state[]": ["active", "invited", "inactive", "completed"],
                "per_page": 100,
            },
        )
        if roles_extra:
            adicionales, pagina_extra, truncado_extra = self._paginas(
                "/api/v1/courses/{course_id}/enrollments",
                f"/api/v1/courses/{canvas_course_id}/enrollments",
                token=token,
                params={
                    "role_id[]": roles_extra,
                    "state[]": ["active", "invited", "inactive", "completed"],
                    "per_page": 100,
                },
            )
            items = list({e["id"]: e for e in [*items, *adicionales]}.values())
            per_page = min(per_page, pagina_extra) if pagina_extra else per_page
            truncado = truncado or truncado_extra
        matriculas = []
        for e in items:
            # Un role_id configurado nunca convierte a un docente en estudiante.
            if e.get("type", "StudentEnrollment") != "StudentEnrollment":
                continue
            usuario = e.get("user") or {}
            matriculas.append(
                MatriculaCruda(
                    canvas_enrollment_id=e["id"],
                    canvas_user_id=e["user_id"],
                    canvas_section_id=e["course_section_id"],
                    tipo=e.get("type", "StudentEnrollment"),
                    role_id=e.get("role_id"),
                    workflow_state=e.get("enrollment_state", e.get("workflow_state", "")),
                    limitada_a_seccion=bool(e.get("limit_privileges_to_course_section", False)),
                    nombre=usuario.get("name", ""),
                    nombre_ordenable=usuario.get("sortable_name"),
                    login_id=usuario.get("login_id"),
                    sis_user_id=usuario.get("sis_user_id"),
                    email=usuario.get("email"),
                    uuid=usuario.get("uuid"),
                    past_uuid=usuario.get("past_uuid"),
                )
            )
        return ResultadoPaginado(items=matriculas, per_page_medido=per_page, truncado=truncado)

    def obtener_secciones_paginado(
        self, token: str, canvas_course_id: int
    ) -> ResultadoPaginado[SeccionCruda]:
        items, per_page, truncado = self._paginas(
            "/api/v1/courses/{course_id}/sections",
            f"/api/v1/courses/{canvas_course_id}/sections",
            token=token,
            params={"per_page": 100},
        )
        secciones = [
            SeccionCruda(
                canvas_section_id=s["id"],
                nombre=s.get("name", ""),
                sis_section_id=s.get("sis_section_id"),
                nonxlist_course_id=s.get("nonxlist_course_id"),
            )
            for s in items
        ]
        return ResultadoPaginado(items=secciones, per_page_medido=per_page, truncado=truncado)

    def obtener_conjuntos_grupos_paginado(
        self, token: str, canvas_course_id: int
    ) -> ResultadoPaginado[ConjuntoGruposCrudo]:
        items, per_page, truncado = self._paginas(
            "/api/v1/courses/{course_id}/group_categories",
            f"/api/v1/courses/{canvas_course_id}/group_categories",
            token=token,
            params={"per_page": 100},
        )
        conjuntos = [
            ConjuntoGruposCrudo(
                canvas_group_category_id=c["id"],
                nombre=c.get("name", ""),
                no_colaborativo=bool(c.get("non_collaborative", False)),
                self_signup=c.get("self_signup"),
                group_limit=c.get("group_limit"),
                auto_leader=c.get("auto_leader"),
            )
            for c in items
        ]
        return ResultadoPaginado(items=conjuntos, per_page_medido=per_page, truncado=truncado)

    def obtener_grupos_de_conjunto_paginado(
        self, token: str, canvas_group_category_id: int
    ) -> ResultadoPaginado[GrupoCrudo]:
        items, per_page, truncado = self._paginas(
            "/api/v1/group_categories/{group_category_id}/groups",
            f"/api/v1/group_categories/{canvas_group_category_id}/groups",
            token=token,
            params={"per_page": 100},
        )
        grupos = [
            GrupoCrudo(
                canvas_group_id=g["id"],
                canvas_group_category_id=canvas_group_category_id,
                nombre=g.get("name", ""),
                is_full=bool(g.get("is_full", False)),
            )
            for g in items
        ]
        return ResultadoPaginado(items=grupos, per_page_medido=per_page, truncado=truncado)

    def obtener_pertenencias_de_grupo_paginado(
        self, token: str, canvas_group_id: int
    ) -> ResultadoPaginado[PertenenciaCruda]:
        items, per_page, truncado = self._paginas(
            "/api/v1/groups/{group_id}/memberships",
            f"/api/v1/groups/{canvas_group_id}/memberships",
            token=token,
            params={"per_page": 100},
        )
        pertenencias = [
            PertenenciaCruda(
                canvas_user_id=m["user_id"],
                workflow_state=m.get("workflow_state", "accepted"),
            )
            for m in items
        ]
        return ResultadoPaginado(items=pertenencias, per_page_medido=per_page, truncado=truncado)

    def crear_tarea_registro(
        self, token: str, canvas_course_id: int, config: ConfiguracionTareaRegistro
    ) -> TareaRegistroCreada:
        payload = {
            "assignment": {
                "name": config.nombre,
                "description": config.descripcion_html,
                "submission_types": [config.submission_types],
                "points_possible": config.points_possible,
                "omit_from_final_grade": config.omit_from_final_grade,
                "published": config.published,
                "due_at": config.due_at_iso,
                "grading_type": config.grading_type,
            }
        }
        respuesta = self._escribir(
            "POST",
            "/api/v1/courses/{course_id}/assignments",
            f"/api/v1/courses/{canvas_course_id}/assignments",
            token=token,
            json=payload,
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
        respuesta.raise_for_status()
        datos = respuesta.json()
        return TareaRegistroCreada(canvas_assignment_id=datos["id"], configuracion=config)

    def actualizar_tarea_registro(
        self,
        token: str,
        canvas_course_id: int,
        canvas_assignment_id: int,
        config: ConfiguracionTareaRegistro,
    ) -> None:
        payload = {
            "assignment": {
                "name": config.nombre,
                "description": config.descripcion_html,
                "submission_types": [config.submission_types],
                "points_possible": config.points_possible,
                "omit_from_final_grade": config.omit_from_final_grade,
                "published": config.published,
                "due_at": config.due_at_iso,
                "grading_type": config.grading_type,
            }
        }
        respuesta = self._escribir(
            "PUT",
            "/api/v1/courses/{course_id}/assignments/{id}",
            f"/api/v1/courses/{canvas_course_id}/assignments/{canvas_assignment_id}",
            token=token,
            json=payload,
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
        respuesta.raise_for_status()

    def obtener_configuracion_tarea(
        self, token: str, canvas_course_id: int, canvas_assignment_id: int
    ) -> ConfiguracionTareaRegistro | None:
        respuesta = self._get(
            "/api/v1/courses/{course_id}/assignments/{id}",
            f"/api/v1/courses/{canvas_course_id}/assignments/{canvas_assignment_id}",
            token=token,
        )
        if respuesta.status_code == 404:
            return None
        if respuesta.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
        respuesta.raise_for_status()
        d = respuesta.json()
        tipos = d.get("submission_types") or ["online_text_entry"]
        return ConfiguracionTareaRegistro(
            nombre=d.get("name", ""),
            descripcion_html=d.get("description") or "",
            submission_types=tipos[0],
            points_possible=float(d.get("points_possible") or 0),
            omit_from_final_grade=bool(d.get("omit_from_final_grade", False)),
            published=bool(d.get("published", False)),
            due_at_iso=d.get("due_at"),
            grading_type=d.get("grading_type", "points"),
        )

    def obtener_entregas_tarea_paginado(
        self, token: str, canvas_course_id: int, canvas_assignment_id: int
    ) -> ResultadoPaginado[EntregaRegistro]:
        items, per_page, truncado = self._paginas(
            "/api/v1/courses/{course_id}/students/submissions",
            f"/api/v1/courses/{canvas_course_id}/students/submissions",
            token=token,
            params={
                "student_ids[]": "all",
                "assignment_ids[]": str(canvas_assignment_id),
                "per_page": 100,
            },
        )
        entregas = [
            EntregaRegistro(
                canvas_user_id=e["user_id"],
                body_html=e.get("body"),
                submitted_at=(
                    datetime.fromisoformat(e["submitted_at"].replace("Z", "+00:00"))
                    if e.get("submitted_at")
                    else None
                ),
            )
            for e in items
        ]
        return ResultadoPaginado(items=entregas, per_page_medido=per_page, truncado=truncado)

    def comentar_entrega(
        self,
        token: str,
        canvas_course_id: int,
        canvas_assignment_id: int,
        canvas_user_id: int,
        comentario: str,
    ) -> bool:
        respuesta = self._escribir(
            "PUT",
            "/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}",
            f"/api/v1/courses/{canvas_course_id}/assignments/{canvas_assignment_id}/submissions/{canvas_user_id}",
            token=token,
            json={"comment": {"text_comment": comentario}},
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
        return respuesta.status_code == 200

    def enviar_conversacion(
        self, token: str, *, destinatarios_canvas_user_ids: list[int], asunto: str, cuerpo: str
    ) -> bool:
        todas = True
        for destinatario in destinatarios_canvas_user_ids:
            respuesta = self._escribir(
                "POST",
                "/api/v1/conversations",
                "/api/v1/conversations",
                token=token,
                json={
                    "recipients": [str(destinatario)],
                    "subject": asunto,
                    "body": cuerpo,
                    "group_conversation": False,
                },
            )
            if respuesta.status_code >= 500:
                raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
            todas = todas and respuesta.status_code in (200, 201)
        return todas

    def crear_anuncio(
        self,
        token: str,
        canvas_course_id: int,
        *,
        titulo: str,
        mensaje_html: str,
        secciones: list[int] | None,
    ) -> AnuncioCreado | None:
        payload: dict[str, Any] = {
            "title": titulo,
            "message": mensaje_html,
            "is_announcement": True,
            "locked": True,
        }
        if secciones:
            payload["specific_sections"] = ",".join(str(x) for x in secciones)
        respuesta = self._escribir(
            "POST",
            "/api/v1/courses/{course_id}/discussion_topics",
            f"/api/v1/courses/{canvas_course_id}/discussion_topics",
            token=token,
            json=payload,
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
        if respuesta.status_code not in (200, 201):
            return None
        datos = respuesta.json()
        return AnuncioCreado(topic_id=int(datos["id"]), html_url=datos.get("html_url"))

    def borrar_anuncio(self, token: str, canvas_course_id: int, topic_id: int) -> bool:
        respuesta = self._escribir(
            "DELETE",
            "/api/v1/courses/{course_id}/discussion_topics/{topic_id}",
            f"/api/v1/courses/{canvas_course_id}/discussion_topics/{topic_id}",
            token=token,
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
        return respuesta.status_code in (200, 204)

    def publicar_nota(
        self,
        token: str,
        canvas_course_id: int,
        canvas_assignment_id: int,
        canvas_user_id: int,
        payload: dict[str, Any],
    ) -> RespuestaCanvas:
        plantilla = "/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
        respuesta = self._escribir(
            "PUT",
            plantilla,
            f"/api/v1/courses/{canvas_course_id}/assignments/{canvas_assignment_id}"
            f"/submissions/{canvas_user_id}",
            token=token,
            json=payload,
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
        try:
            cuerpo = respuesta.json()
        except ValueError:
            cuerpo = {"texto": respuesta.text[:2000]}
        return RespuestaCanvas(codigo_http=respuesta.status_code, cuerpo=cuerpo)

    def leer_calificaciones(
        self, token: str, canvas_course_id: int, canvas_assignment_id: int
    ) -> list[CalificacionCanvas]:
        items, _, _ = self._paginas(
            "/api/v1/courses/{course_id}/students/submissions",
            f"/api/v1/courses/{canvas_course_id}/students/submissions",
            token=token,
            params={
                "student_ids[]": "all",
                "assignment_ids[]": canvas_assignment_id,
                "per_page": 100,
            },
        )
        return [_calificacion_desde_json(d) for d in items]

    def estudiantes_calificables(
        self, token: str, canvas_course_id: int, canvas_assignment_id: int
    ) -> set[int]:
        items, _, _ = self._paginas(
            "/api/v1/courses/{course_id}/assignments/{assignment_id}/gradeable_students",
            f"/api/v1/courses/{canvas_course_id}/assignments/{canvas_assignment_id}"
            "/gradeable_students",
            token=token,
            params={"per_page": 100},
        )
        return {int(d["id"]) for d in items if "id" in d}

    def obtener_assignments_paginado(
        self, token: str, canvas_course_id: int
    ) -> ResultadoPaginado[AssignmentCanvasCrudo]:
        items, per_page, truncado = self._paginas(
            "/api/v1/courses/{course_id}/assignments",
            f"/api/v1/courses/{canvas_course_id}/assignments",
            token=token,
            # S9.3.1: fuente de aceleracion; los overrides de autoridad siguen
            # saliendo del endpoint 14 (`obtener_overrides_assignment`).
            params={
                "include[]": ["all_dates", "overrides", "assignment_visibility"],
                "per_page": 100,
            },
        )
        return ResultadoPaginado(
            items=[_assignment_desde_json(d) for d in items],
            per_page_medido=per_page,
            truncado=truncado,
        )

    def obtener_assignment(
        self, token: str, canvas_course_id: int, canvas_assignment_id: int
    ) -> AssignmentCanvasCrudo | None:
        respuesta = self._get(
            "/api/v1/courses/{course_id}/assignments/{id}",
            f"/api/v1/courses/{canvas_course_id}/assignments/{canvas_assignment_id}",
            token=token,
            params={"include[]": "assignment_visibility"},
        )
        if respuesta.status_code == 404:
            return None
        if respuesta.status_code >= 500:
            raise FalloProveedorCanvas(f"Canvas respondio {respuesta.status_code}")
        respuesta.raise_for_status()
        return _assignment_desde_json(respuesta.json())

    def obtener_overrides_assignment(
        self, token: str, canvas_course_id: int, canvas_assignment_id: int
    ) -> list[OverrideCanvasCrudo]:
        items, _per_page, _truncado = self._paginas(
            "/api/v1/courses/{course_id}/assignments/{assignment_id}/overrides",
            f"/api/v1/courses/{canvas_course_id}/assignments/{canvas_assignment_id}/overrides",
            token=token,
            params={"per_page": 100},
        )
        return [
            OverrideCanvasCrudo(
                canvas_override_id=o["id"],
                student_ids=o.get("student_ids"),
                course_section_id=o.get("course_section_id"),
                group_id=o.get("group_id"),
                due_at=_fecha_canvas(o.get("due_at")),
                titulo=o.get("title"),
            )
            for o in items
        ]


class ClienteCanvasDoble:
    """Datos fijos y deterministas para desarrollo local sin Canvas real.

    El token `"valido"` es el titular de un curso de Canvas ficticio del que
    SI es profesor; cualquier otro valor de token se trata como invalido.
    """

    _CANVAS_USER_ID = 1001
    _CURSOS = (
        CursoCanvas(
            canvas_course_id=5001,
            nombre="Desarrollo de Software (doble)",
            codigo="ICC4201",
            termino="2026-2",
            total_estudiantes=42,
        ),
    )

    def obtener_usuario_actual(self, token: str) -> UsuarioCanvas:
        if token != "valido":
            raise RechazoVinculacion(MotivoRechazoVinculacion.TOKEN_INVALIDO)
        return UsuarioCanvas(canvas_user_id=self._CANVAS_USER_ID, nombre="Profesora Doble")

    def listar_cursos_profesor(self, token: str) -> list[CursoCanvas]:
        if token != "valido":
            return []
        return list(self._CURSOS)

    def obtener_matriculas_profesor(
        self, token: str, canvas_course_id: int
    ) -> list[MatriculaCanvas]:
        if token != "valido" or canvas_course_id != self._CURSOS[0].canvas_course_id:
            return []
        return [
            MatriculaCanvas(
                tipo="TeacherEnrollment", workflow_state="active", limitada_a_seccion=False
            )
        ]

    def obtener_detalle_curso(
        self, token: str, canvas_course_id: int, permisos: list[str]
    ) -> DetalleCursoCanvas:
        if token != "valido" or canvas_course_id != self._CURSOS[0].canvas_course_id:
            return DetalleCursoCanvas(existe=False, publicado=False, time_zone=None, permisos={})
        return DetalleCursoCanvas(
            existe=True,
            publicado=True,
            time_zone="America/Santiago",
            permisos=dict.fromkeys(permisos, True),
        )

    def obtener_secciones(self, token: str, canvas_course_id: int) -> list[SeccionCanvas]:
        if token != "valido" or canvas_course_id != self._CURSOS[0].canvas_course_id:
            return []
        return [SeccionCanvas(section_id=1, nombre="Seccion unica", es_cross_listed=False)]

    def contar_grupos(self, token: str, canvas_course_id: int) -> int:
        return 0

    def existe_politica_entrega_tardia(self, token: str, canvas_course_id: int) -> bool:
        return True

    def obtener_periodos_calificacion(
        self, token: str, canvas_course_id: int
    ) -> list[PeriodoCalificacionCanvas]:
        if periodo_cerrado_doble:
            return [
                PeriodoCalificacionCanvas(
                    is_closed=True,
                    # Relativo al cierre del doble para que siempre lo contenga.
                    start_date=self._FECHA_CIERRE_DOBLE - timedelta(days=365),
                    end_date=self._FECHA_CIERRE_DOBLE + timedelta(days=365),
                )
            ]
        return []

    def obtener_roster(self, token: str, canvas_course_id: int) -> RosterCanvas:
        if token != "valido" or canvas_course_id != self._CURSOS[0].canvas_course_id:
            return RosterCanvas(cantidad_primera_pagina=0, hay_siguiente_pagina=False)
        total = self._CURSOS[0].total_estudiantes or 0
        return RosterCanvas(cantidad_primera_pagina=total, hay_siguiente_pagina=False)

    # --- Etapa P5: espejo de estudiantes, secciones y grupos (S7.2-S7.3) ---
    # 5 estudiantes fijos en 2 secciones; 1 conjunto de grupos colaborativo
    # con 2 grupos (2001/2002 en el primero, 2003/2004 en el segundo);
    # 2005 queda sin grupo, a proposito, para probar "Pendientes" en P6.
    _SECCIONES_PADRON = ((101, "Sección 1"), (102, "Sección 2"))
    _ESTUDIANTES_PADRON = (
        (2001, "Ana Soto", 101),
        (2002, "Bruno Diaz", 101),
        (2003, "Carla Reyes", 101),
        (2004, "Diego Vera", 102),
        (2005, "Elena Rojas", 102),
    )
    _CONJUNTO_GRUPOS_ID = 501
    _GRUPOS_PADRON = ((601, "Grupo 1", (2001, 2002)), (602, "Grupo 2", (2003, 2004)))

    def obtener_roster_paginado(
        self, token: str, canvas_course_id: int, *, roles_extra: list[int] | None = None
    ) -> ResultadoPaginado[MatriculaCruda]:
        if token != "valido" or canvas_course_id != self._CURSOS[0].canvas_course_id:
            return ResultadoPaginado(items=[], per_page_medido=0, truncado=False)
        matriculas = [
            MatriculaCruda(
                canvas_enrollment_id=10_000 + canvas_user_id,
                canvas_user_id=canvas_user_id,
                canvas_section_id=seccion_id,
                tipo="StudentEnrollment",
                role_id=None,
                workflow_state="active",
                limitada_a_seccion=False,
                nombre=nombre,
                nombre_ordenable=nombre,
                login_id=None,
                sis_user_id=None,
                email=None,
                uuid=None,
                past_uuid=None,
            )
            for canvas_user_id, nombre, seccion_id in self._ESTUDIANTES_PADRON
        ]
        return ResultadoPaginado(items=matriculas, per_page_medido=len(matriculas), truncado=False)

    def obtener_secciones_paginado(
        self, token: str, canvas_course_id: int
    ) -> ResultadoPaginado[SeccionCruda]:
        if token != "valido" or canvas_course_id != self._CURSOS[0].canvas_course_id:
            return ResultadoPaginado(items=[], per_page_medido=0, truncado=False)
        secciones = [
            SeccionCruda(
                canvas_section_id=sid, nombre=nombre, sis_section_id=None, nonxlist_course_id=None
            )
            for sid, nombre in self._SECCIONES_PADRON
        ]
        return ResultadoPaginado(items=secciones, per_page_medido=len(secciones), truncado=False)

    def obtener_conjuntos_grupos_paginado(
        self, token: str, canvas_course_id: int
    ) -> ResultadoPaginado[ConjuntoGruposCrudo]:
        if token != "valido" or canvas_course_id != self._CURSOS[0].canvas_course_id:
            return ResultadoPaginado(items=[], per_page_medido=0, truncado=False)
        conjunto = ConjuntoGruposCrudo(
            canvas_group_category_id=self._CONJUNTO_GRUPOS_ID,
            nombre="Proyecto Final",
            no_colaborativo=False,
            self_signup=None,
            group_limit=None,
            auto_leader=None,
        )
        return ResultadoPaginado(items=[conjunto], per_page_medido=1, truncado=False)

    def obtener_grupos_de_conjunto_paginado(
        self, token: str, canvas_group_category_id: int
    ) -> ResultadoPaginado[GrupoCrudo]:
        if canvas_group_category_id != self._CONJUNTO_GRUPOS_ID:
            return ResultadoPaginado(items=[], per_page_medido=0, truncado=False)
        grupos = [
            GrupoCrudo(
                canvas_group_id=gid,
                canvas_group_category_id=canvas_group_category_id,
                nombre=nombre,
                is_full=False,
            )
            for gid, nombre, _miembros in self._GRUPOS_PADRON
        ]
        return ResultadoPaginado(items=grupos, per_page_medido=len(grupos), truncado=False)

    def obtener_pertenencias_de_grupo_paginado(
        self, token: str, canvas_group_id: int
    ) -> ResultadoPaginado[PertenenciaCruda]:
        for gid, _nombre, miembros in self._GRUPOS_PADRON:
            if gid == canvas_group_id:
                pertenencias = [
                    PertenenciaCruda(canvas_user_id=uid, workflow_state="accepted")
                    for uid in miembros
                ]
                return ResultadoPaginado(
                    items=pertenencias, per_page_medido=len(pertenencias), truncado=False
                )
        return ResultadoPaginado(items=[], per_page_medido=0, truncado=False)

    # --- Etapa P6: tarea de registro de GitHub (S7.4) ---
    _ASSIGNMENT_ID_REGISTRO = 9001
    # 2001 declara un candidato valido (url de perfil), 2002 declara otro
    # valido distinto (arroba), 2003 declara una cuenta inexistente, 2004
    # entrega texto ambiguo (ningun patron casa) y 2005 no entrega nada --
    # cubre las cinco salidas de RECIBIDO de un solo fixture (S7.6.1).
    _ENTREGAS_REGISTRO = (
        (2001, "Mi perfil es https://github.com/estudiante-valido"),
        (2002, "mi usuario es @estudiante-valido-2"),
        (2003, "no-existe-esta-cuenta-en-github"),
        (2004, "no se cual es mi usuario de github, como lo averiguo"),
    )

    def crear_tarea_registro(
        self, token: str, canvas_course_id: int, config: ConfiguracionTareaRegistro
    ) -> TareaRegistroCreada:
        # "Canvas" recuerda exactamente lo que se le escribio, para que
        # `verificar_configuracion` no detecte una desviacion inventada por el
        # doble mismo en el siguiente ciclo (S7.2.3: la huella se compara
        # contra lo que Canvas devuelve, no contra un valor fijo del fixture).
        _escribir_config_registro_doble(self._ASSIGNMENT_ID_REGISTRO, config)
        return TareaRegistroCreada(
            canvas_assignment_id=self._ASSIGNMENT_ID_REGISTRO, configuracion=config
        )

    def actualizar_tarea_registro(
        self,
        token: str,
        canvas_course_id: int,
        canvas_assignment_id: int,
        config: ConfiguracionTareaRegistro,
    ) -> None:
        _escribir_config_registro_doble(canvas_assignment_id, config)

    def obtener_configuracion_tarea(
        self, token: str, canvas_course_id: int, canvas_assignment_id: int
    ) -> ConfiguracionTareaRegistro | None:
        if canvas_assignment_id != self._ASSIGNMENT_ID_REGISTRO:
            return None
        return _leer_config_registro_doble(canvas_assignment_id)

    def obtener_entregas_tarea_paginado(
        self, token: str, canvas_course_id: int, canvas_assignment_id: int
    ) -> ResultadoPaginado[EntregaRegistro]:
        if (
            token != "valido"
            or canvas_course_id != self._CURSOS[0].canvas_course_id
            or canvas_assignment_id != self._ASSIGNMENT_ID_REGISTRO
        ):
            return ResultadoPaginado(items=[], per_page_medido=0, truncado=False)
        entregas = [
            EntregaRegistro(canvas_user_id=uid, body_html=texto, submitted_at=None)
            for uid, texto in self._ENTREGAS_REGISTRO
        ]
        return ResultadoPaginado(items=entregas, per_page_medido=len(entregas), truncado=False)

    def comentar_entrega(
        self,
        token: str,
        canvas_course_id: int,
        canvas_assignment_id: int,
        canvas_user_id: int,
        comentario: str,
    ) -> bool:
        return token == "valido"

    def enviar_conversacion(
        self, token: str, *, destinatarios_canvas_user_ids: list[int], asunto: str, cuerpo: str
    ) -> bool:
        for destinatario in destinatarios_canvas_user_ids:
            conversaciones_doble.append(
                {
                    "recipients": [str(destinatario)],
                    "subject": asunto,
                    "body": cuerpo,
                    "group_conversation": False,
                }
            )
        return token == "valido"

    def crear_anuncio(
        self,
        token: str,
        canvas_course_id: int,
        *,
        titulo: str,
        mensaje_html: str,
        secciones: list[int] | None,
    ) -> AnuncioCreado | None:
        if token != "valido":
            return None
        if secciones and rechazar_secciones_doble:
            return None
        topic_id = 70_000 + len(anuncios_doble)
        anuncios_doble.append(
            {
                "id": topic_id,
                "title": titulo,
                "message": mensaje_html,
                "specific_sections": secciones,
                "locked": True,
            }
        )
        return AnuncioCreado(
            topic_id=topic_id,
            html_url=f"https://canvas.doble/courses/{canvas_course_id}/discussion_topics/{topic_id}",
        )

    def borrar_anuncio(self, token: str, canvas_course_id: int, topic_id: int) -> bool:
        anuncios_borrados_doble.append(topic_id)
        return token == "valido"

    def publicar_nota(
        self,
        token: str,
        canvas_course_id: int,
        canvas_assignment_id: int,
        canvas_user_id: int,
        payload: dict[str, Any],
    ) -> RespuestaCanvas:
        publicaciones_doble.append(
            {"assignment_id": canvas_assignment_id, "user_id": canvas_user_id, **payload}
        )
        if token != "valido":
            return RespuestaCanvas(
                codigo_http=401, cuerpo={"errors": [{"message": "Invalid access token."}]}
            )
        nota = str((payload.get("submission") or {}).get("posted_grade", ""))
        try:
            score: float | None = float(nota.rstrip("%"))
        except ValueError:
            score = 1.0 if nota == "pass" else 0.0 if nota == "fail" else None
        destinatarios = [canvas_user_id]
        if (payload.get("comment") or {}).get("group_comment"):
            destinatarios = next(
                (list(m) for _, _, m in self._GRUPOS_PADRON if canvas_user_id in m),
                [canvas_user_id],
            )
        ahora = datetime.now(UTC)
        for uid in destinatarios:
            calificaciones_doble[(canvas_assignment_id, uid)] = {
                "user_id": uid,
                "score": None if score is None else score - descuento_doble,
                "entered_score": score,
                "grade": nota,
                "graded_at": ahora.isoformat(),
                "grader_id": self._CANVAS_USER_ID,
                "points_deducted": descuento_doble or None,
                "workflow_state": "graded",
            }
        return RespuestaCanvas(
            codigo_http=200, cuerpo=calificaciones_doble[(canvas_assignment_id, canvas_user_id)]
        )

    def leer_calificaciones(
        self, token: str, canvas_course_id: int, canvas_assignment_id: int
    ) -> list[CalificacionCanvas]:
        return [
            _calificacion_desde_json(d)
            for (aid, _), d in calificaciones_doble.items()
            if aid == canvas_assignment_id
        ]

    def estudiantes_calificables(
        self, token: str, canvas_course_id: int, canvas_assignment_id: int
    ) -> set[int]:
        return {2001, 2002, 2003, 2004, 2005} - no_calificables_doble

    def ejecutar_prueba_anuncio(
        self, token: str, canvas_course_id: int, *, section_id: int | None
    ) -> bool:
        return token == "valido" and canvas_course_id == self._CURSOS[0].canvas_course_id

    def ejecutar_prueba_comentario_entrega(self, token: str, canvas_course_id: int) -> bool | None:
        if token != "valido" or canvas_course_id != self._CURSOS[0].canvas_course_id:
            return None
        return True

    # --- Etapa P7: tareas de Canvas (endpoints 12, 13, 14) ---
    # 9101 individual y visible para todos (el camino feliz de la parcial),
    # 9102 grupal (capa 3 hasta el 23-sep), 9103 visible solo por un override
    # de la seccion 101 y 9104 visible solo para 2005 por
    # `assignment_visibility`: cubre las cuatro filas de A-164 paso 1.
    # Relativa al arranque, no fija: una fecha fija termina quedando en el
    # pasado y entonces todas las entregas del doble aparecen ya cerradas
    # (paso el 01-10-2026 y rompio las pruebas que esperan una entrega abierta).
    # Anclada al dia 1 de dentro de dos meses (31-62 dias por delante): asi no
    # cambia en cada arranque del proceso, que sincronizaria fechas nuevas y
    # dejaria una FechaEfectiva SUPERSEDIDA por reinicio.
    _HOY_DOBLE = datetime.now(UTC)
    _FECHA_CIERRE_DOBLE = datetime(
        _HOY_DOBLE.year + (_HOY_DOBLE.month + 1) // 12,
        (_HOY_DOBLE.month + 1) % 12 + 1,
        1,
        23,
        59,
        tzinfo=UTC,
    )

    def _assignments_doble(self) -> list[AssignmentCanvasCrudo]:
        def assignment(
            canvas_assignment_id: int,
            nombre: str,
            *,
            group_category_id: int | None = None,
            only_visible_to_overrides: bool = False,
            assignment_visibility: list[int] | None = None,
        ) -> AssignmentCanvasCrudo:
            payload: dict[str, Any] = {
                "id": canvas_assignment_id,
                "name": nombre,
                "published": True,
                "grade_group_students_individually": False,
            }
            if canvas_assignment_id == 9101:
                # F11: rubrica de ejemplo, embebida en el assignment como en Canvas.
                payload["rubric"] = RUBRICA_DOBLE
                payload["rubric_settings"] = {
                    "points_possible": 100,
                    "free_form_criterion_comments": False,
                    "hide_points": False,
                    "hide_score_total": False,
                }
                payload["use_rubric_for_grading"] = False
            return AssignmentCanvasCrudo(
                canvas_assignment_id=canvas_assignment_id,
                nombre=nombre,
                puntos_posibles=100.0,
                grading_type="points",
                publicada=True,
                moderated_grading=False,
                anonymous_grading=False,
                group_category_id=group_category_id,
                only_visible_to_overrides=only_visible_to_overrides,
                due_at=self._FECHA_CIERRE_DOBLE,
                all_day=False,
                canvas_updated_at=self._FECHA_CIERRE_DOBLE - timedelta(days=30),
                assignment_visibility=assignment_visibility,
                payload=payload,
            )

        tareas = [
            assignment(9101, "Tarea 1: Ordenamiento"),
            assignment(9102, "Tarea 2: Compilador", group_category_id=self._CONJUNTO_GRUPOS_ID),
            assignment(9103, "Tarea 3: Seccion 101", only_visible_to_overrides=True),
            assignment(
                9104,
                "Tarea 4: Recuperativa",
                only_visible_to_overrides=True,
                assignment_visibility=[2005],
            ),
        ]
        # La tarea de registro solo existe en "Canvas" si ya se creo (P6).
        config_registro = _leer_config_registro_doble(self._ASSIGNMENT_ID_REGISTRO)
        if config_registro is not None:
            tareas.append(assignment(self._ASSIGNMENT_ID_REGISTRO, config_registro.nombre))
        return tareas

    def obtener_assignments_paginado(
        self, token: str, canvas_course_id: int
    ) -> ResultadoPaginado[AssignmentCanvasCrudo]:
        if token != "valido" or canvas_course_id != self._CURSOS[0].canvas_course_id:
            return ResultadoPaginado(items=[], per_page_medido=0, truncado=False)
        tareas = self._assignments_doble()
        return ResultadoPaginado(items=tareas, per_page_medido=len(tareas), truncado=False)

    def obtener_assignment(
        self, token: str, canvas_course_id: int, canvas_assignment_id: int
    ) -> AssignmentCanvasCrudo | None:
        if token != "valido" or canvas_course_id != self._CURSOS[0].canvas_course_id:
            return None
        for tarea in self._assignments_doble():
            if tarea.canvas_assignment_id == canvas_assignment_id:
                return tarea
        return None

    def obtener_overrides_assignment(
        self, token: str, canvas_course_id: int, canvas_assignment_id: int
    ) -> list[OverrideCanvasCrudo]:
        if canvas_assignment_id != 9103:
            return []
        return [
            OverrideCanvasCrudo(
                canvas_override_id=77001,
                student_ids=None,
                course_section_id=101,
                group_id=None,
                due_at=self._FECHA_CIERRE_DOBLE,
                titulo="Seccion 1",
            )
        ]


def crear_cliente_canvas(*, modo: str, canvas_base_url: str) -> ClienteCanvas:
    if modo == "real":
        return ClienteCanvasReal(canvas_base_url)
    return ClienteCanvasDoble()
