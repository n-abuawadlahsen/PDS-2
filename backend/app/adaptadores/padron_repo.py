"""Sincronizacion del espejo de Canvas: `sync_roster` y `sync_grupos`
(SPEC 07 S7.2-S7.3; Etapa P5).

`sync_roster` es la unica fuente de que personas existen en el curso
(S7.2.5): lee primero secciones y despues matriculas, en la misma ejecucion.
`sync_grupos` nunca crea estudiantes -- un `canvas_user_id` visto en un grupo
que no esta en `estudiante` se pone en cuarentena (S7.2.5).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.adaptadores import incidencia_repo, mapeo_github_repo, sincronizacion_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_canvas import ClienteCanvas
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_padron import (
    ConjuntoGrupos,
    Estudiante,
    Grupo,
    Matricula,
    PertenenciaGrupo,
    Seccion,
)
from app.adaptadores.trabajos_repo import encolar
from app.dominio.estados import (
    EstadoEstudiante,
    EstadoGrupo,
    EstadoSeccion,
    ResultadoSincronizacion,
)
from app.dominio.padron import (
    confirma_ausencia,
    detectar_traslado_o_doble_pertenencia,
    estado_estudiante_desde_matriculas,
    roster_sospechoso,
    slug_desde_nombre,
)

_RECURSO_ROSTER = "roster"
_RECURSO_GRUPOS = "grupos"


def sincronizar_roster(bd: Session, cliente: ClienteCanvas, *, curso: Curso, token: str) -> None:
    """S7.3.1: secciones primero, matriculas despues, misma ejecucion."""
    ahora = ahora_utc()
    assert curso.canvas_course_id is not None

    resultado_secciones = cliente.obtener_secciones_paginado(token, curso.canvas_course_id)
    vistas_ids: set[int] = set()
    seccion_por_canvas_id: dict[int, Seccion] = {}
    for cruda in resultado_secciones.items:
        fila = (
            bd.query(Seccion)
            .filter(
                Seccion.curso_id == curso.id, Seccion.canvas_section_id == cruda.canvas_section_id
            )
            .one_or_none()
        )
        if fila is None:
            fila = Seccion(
                curso_id=curso.id,
                canvas_section_id=cruda.canvas_section_id,
                nombre=cruda.nombre,
                sis_section_id=cruda.sis_section_id,
                nonxlist_course_id=cruda.nonxlist_course_id,
                estado=EstadoSeccion.ACTIVA.value,
                ciclos_ausente=0,
                sincronizado_en=ahora,
            )
            bd.add(fila)
            bd.flush()
        else:
            fila.nombre = cruda.nombre
            fila.sis_section_id = cruda.sis_section_id
            fila.nonxlist_course_id = cruda.nonxlist_course_id
            fila.estado = EstadoSeccion.ACTIVA.value
            fila.ciclos_ausente = 0
            fila.sincronizado_en = ahora
        vistas_ids.add(cruda.canvas_section_id)
        seccion_por_canvas_id[cruda.canvas_section_id] = fila

    for seccion_existente in (
        bd.query(Seccion)
        .filter(Seccion.curso_id == curso.id, Seccion.estado == EstadoSeccion.ACTIVA.value)
        .all()
    ):
        if seccion_existente.canvas_section_id not in vistas_ids:
            seccion_existente.ciclos_ausente += 1
            if confirma_ausencia(seccion_existente.ciclos_ausente):
                seccion_existente.estado = EstadoSeccion.ELIMINADA.value
    bd.flush()

    resultado_roster = cliente.obtener_roster_paginado(token, curso.canvas_course_id)
    matriculas_por_usuario: dict[int, list[Any]] = {}
    for m in resultado_roster.items:
        matriculas_por_usuario.setdefault(m.canvas_user_id, []).append(m)

    cantidad_anterior = (
        bd.query(Estudiante)
        .filter(
            Estudiante.curso_id == curso.id, Estudiante.estado != EstadoEstudiante.RETIRADO.value
        )
        .count()
    )
    cantidad_actual = len(matriculas_por_usuario)

    if roster_sospechoso(cantidad_anterior=cantidad_anterior, cantidad_actual=cantidad_actual):
        incidencia_repo.abrir_o_actualizar(
            bd,
            tipo="ROSTER_SOSPECHOSO",
            severidad="ADVERTENCIA",
            sujeto_tipo="CURSO",
            curso_id=curso.id,
            detalle={
                "recurso": _RECURSO_ROSTER,
                "anterior": cantidad_anterior,
                "actual": cantidad_actual,
            },
        )
        sincronizacion_repo.actualizar_cursor(
            bd,
            curso_id=curso.id,
            recurso=_RECURSO_ROSTER,
            referencia=str(curso.id),
            per_page_medido=resultado_roster.per_page_medido,
            estado=ResultadoSincronizacion.PARCIAL.value,
        )
        sincronizacion_repo.registrar_ciclo(
            bd,
            curso_id=curso.id,
            recurso=_RECURSO_ROSTER,
            resultado=ResultadoSincronizacion.PARCIAL.value,
            contadores={"anterior": cantidad_anterior, "actual": cantidad_actual},
        )
        return

    usuarios_vistos: set[int] = set()
    for canvas_user_id, matriculas_usuario in matriculas_por_usuario.items():
        usuarios_vistos.add(canvas_user_id)
        primera = matriculas_usuario[0]
        estado_nuevo = estado_estudiante_desde_matriculas(
            [m.workflow_state for m in matriculas_usuario]
        )
        estudiante = (
            bd.query(Estudiante)
            .filter(Estudiante.curso_id == curso.id, Estudiante.canvas_user_id == canvas_user_id)
            .one_or_none()
        )
        if estudiante is None:
            estudiante = Estudiante(
                curso_id=curso.id,
                canvas_user_id=canvas_user_id,
                nombre=primera.nombre,
                nombre_ordenable=primera.nombre_ordenable,
                login_id=primera.login_id,
                sis_user_id=primera.sis_user_id,
                email=primera.email,
                uuid=primera.uuid,
                past_uuid=primera.past_uuid,
                group_ids_canvas=[],
                estado=estado_nuevo.value,
                ciclos_ausente=0,
                primera_vista_en=ahora,
                ultima_vista_en=ahora,
            )
            bd.add(estudiante)
            bd.flush()
            # S7.2.6 criterio 3: la fila SIN_DATO nace en la misma transaccion
            # en que se espeja el estudiante.
            mapeo_github_repo.crear_mapeo_sin_dato(
                bd, curso_id=curso.id, estudiante_id=estudiante.id
            )
        else:
            estudiante.nombre = primera.nombre
            estudiante.nombre_ordenable = primera.nombre_ordenable
            estudiante.login_id = primera.login_id or estudiante.login_id
            estudiante.sis_user_id = primera.sis_user_id or estudiante.sis_user_id
            estudiante.email = primera.email or estudiante.email
            estudiante.uuid = primera.uuid or estudiante.uuid
            estudiante.past_uuid = primera.past_uuid or estudiante.past_uuid
            estudiante.estado = estado_nuevo.value
            estudiante.ciclos_ausente = 0
            estudiante.ultima_vista_en = ahora

        for m in matriculas_usuario:
            seccion = seccion_por_canvas_id.get(m.canvas_section_id)
            if seccion is None:
                seccion = (
                    bd.query(Seccion)
                    .filter(
                        Seccion.curso_id == curso.id,
                        Seccion.canvas_section_id == m.canvas_section_id,
                    )
                    .one_or_none()
                )
            if seccion is None:
                continue  # S7.2.5: sin seccion viva no se crea la matricula (huerfano de seccion)
            fila_m = (
                bd.query(Matricula)
                .filter(
                    Matricula.curso_id == curso.id,
                    Matricula.canvas_enrollment_id == m.canvas_enrollment_id,
                )
                .one_or_none()
            )
            if fila_m is None:
                bd.add(
                    Matricula(
                        curso_id=curso.id,
                        estudiante_id=estudiante.id,
                        seccion_id=seccion.id,
                        canvas_enrollment_id=m.canvas_enrollment_id,
                        tipo=m.tipo,
                        role_id=m.role_id,
                        estado=m.workflow_state,
                        limitada_a_seccion=m.limitada_a_seccion,
                        activa=m.workflow_state in ("active", "invited"),
                        sincronizado_en=ahora,
                    )
                )
            else:
                fila_m.seccion_id = seccion.id
                fila_m.estado = m.workflow_state
                fila_m.limitada_a_seccion = m.limitada_a_seccion
                fila_m.activa = m.workflow_state in ("active", "invited")
                fila_m.sincronizado_en = ahora
    bd.flush()

    for estudiante_existente in (
        bd.query(Estudiante)
        .filter(
            Estudiante.curso_id == curso.id, Estudiante.estado != EstadoEstudiante.RETIRADO.value
        )
        .all()
    ):
        if estudiante_existente.canvas_user_id not in usuarios_vistos:
            estudiante_existente.ciclos_ausente += 1
            if confirma_ausencia(estudiante_existente.ciclos_ausente):
                estudiante_existente.estado = EstadoEstudiante.RETIRADO.value
                estudiante_existente.retirado_en = ahora
                mapeo_github_repo.invalidar_por_retiro(
                    bd, curso_id=curso.id, estudiante_id=estudiante_existente.id
                )
    bd.flush()

    resultado_final = (
        ResultadoSincronizacion.TRUNCADA.value
        if resultado_roster.truncado
        else ResultadoSincronizacion.OK.value
    )
    if resultado_roster.truncado:
        incidencia_repo.abrir_o_actualizar(
            bd,
            tipo="ROSTER_TRUNCADO",
            severidad="ADVERTENCIA",
            sujeto_tipo="CURSO",
            curso_id=curso.id,
            detalle={"motivo": "tope_50_paginas", "recurso": _RECURSO_ROSTER},
        )
    sincronizacion_repo.actualizar_cursor(
        bd,
        curso_id=curso.id,
        recurso=_RECURSO_ROSTER,
        referencia=str(curso.id),
        per_page_medido=resultado_roster.per_page_medido,
        estado=resultado_final,
    )
    sincronizacion_repo.registrar_ciclo(
        bd,
        curso_id=curso.id,
        recurso=_RECURSO_ROSTER,
        resultado=resultado_final,
        contadores={"estudiantes_vistos": len(usuarios_vistos)},
    )


def sincronizar_grupos(bd: Session, cliente: ClienteCanvas, *, curso: Curso, token: str) -> None:
    """S7.3.3-S7.3.8. Nunca crea estudiantes (S7.2.5): un huerfano abre
    `ROSTER_TRUNCADO` y dispara un `sync_roster` inmediato, una vez por ciclo."""
    ahora = ahora_utc()
    assert curso.canvas_course_id is not None

    resultado_categorias = cliente.obtener_conjuntos_grupos_paginado(token, curso.canvas_course_id)
    conjunto_por_canvas_id: dict[int, ConjuntoGrupos] = {}
    for c in resultado_categorias.items:
        fila = (
            bd.query(ConjuntoGrupos)
            .filter(
                ConjuntoGrupos.curso_id == curso.id,
                ConjuntoGrupos.canvas_group_category_id == c.canvas_group_category_id,
            )
            .one_or_none()
        )
        if fila is None:
            fila = ConjuntoGrupos(
                curso_id=curso.id,
                canvas_group_category_id=c.canvas_group_category_id,
                nombre=c.nombre,
                no_colaborativo=c.no_colaborativo,
                self_signup=c.self_signup,
                group_limit=c.group_limit,
                auto_leader=c.auto_leader,
                sincronizado_en=ahora,
            )
            bd.add(fila)
            bd.flush()
        else:
            fila.nombre = c.nombre
            fila.no_colaborativo = c.no_colaborativo
            fila.self_signup = c.self_signup
            fila.group_limit = c.group_limit
            fila.auto_leader = c.auto_leader
            fila.sincronizado_en = ahora
        conjunto_por_canvas_id[c.canvas_group_category_id] = fila
    bd.flush()

    hubo_huerfanos = False
    huerfanos: list[dict[str, Any]] = []
    estudiante_por_canvas_id = {
        e.canvas_user_id: e
        for e in bd.query(Estudiante).filter(Estudiante.curso_id == curso.id).all()
    }

    for canvas_group_category_id, conjunto_fila in conjunto_por_canvas_id.items():
        if conjunto_fila.no_colaborativo:
            continue  # S7.3.3: differentiation tag, informativa, no genera grupo

        resultado_grupos = cliente.obtener_grupos_de_conjunto_paginado(
            token, canvas_group_category_id
        )
        grupos_vistos_ids: set[int] = set()
        grupo_por_canvas_id: dict[int, Grupo] = {}
        for g in resultado_grupos.items:
            fila_g = (
                bd.query(Grupo)
                .filter(Grupo.curso_id == curso.id, Grupo.canvas_group_id == g.canvas_group_id)
                .one_or_none()
            )
            if fila_g is None:
                fila_g = Grupo(
                    curso_id=curso.id,
                    conjunto_grupos_id=conjunto_fila.id,
                    canvas_group_id=g.canvas_group_id,
                    nombre=g.nombre,
                    slug=slug_desde_nombre(g.nombre, canvas_group_id=g.canvas_group_id),
                    estado=EstadoGrupo.ACTIVO.value,
                    is_full=g.is_full,
                    ciclos_ausente=0,
                    sincronizado_en=ahora,
                )
                bd.add(fila_g)
                bd.flush()
            else:
                fila_g.nombre = g.nombre
                fila_g.estado = EstadoGrupo.ACTIVO.value
                fila_g.is_full = g.is_full
                fila_g.ciclos_ausente = 0
                fila_g.sincronizado_en = ahora
            grupos_vistos_ids.add(g.canvas_group_id)
            grupo_por_canvas_id[g.canvas_group_id] = fila_g

        for grupo_existente in (
            bd.query(Grupo)
            .filter(
                Grupo.conjunto_grupos_id == conjunto_fila.id,
                Grupo.estado == EstadoGrupo.ACTIVO.value,
            )
            .all()
        ):
            if grupo_existente.canvas_group_id not in grupos_vistos_ids:
                grupo_existente.ciclos_ausente += 1
                if confirma_ausencia(grupo_existente.ciclos_ausente):
                    grupo_existente.estado = EstadoGrupo.ELIMINADO.value
        bd.flush()

        cantidad_anterior_conjunto = (
            bd.query(PertenenciaGrupo)
            .join(Grupo, Grupo.id == PertenenciaGrupo.grupo_id)
            .filter(Grupo.conjunto_grupos_id == conjunto_fila.id, PertenenciaGrupo.activa.is_(True))
            .count()
        )

        anterior_por_estudiante: dict[uuid.UUID, set[uuid.UUID]] = {}
        filas_pertenencia_previas = (
            bd.query(PertenenciaGrupo)
            .join(Grupo, Grupo.id == PertenenciaGrupo.grupo_id)
            .filter(
                Grupo.conjunto_grupos_id == conjunto_fila.id,
                PertenenciaGrupo.workflow_state == "accepted",
                PertenenciaGrupo.activa.is_(True),
            )
            .all()
        )
        for pg in filas_pertenencia_previas:
            anterior_por_estudiante.setdefault(pg.estudiante_id, set()).add(pg.grupo_id)

        crudas_por_grupo: dict[uuid.UUID, list[Any]] = {}
        cantidad_actual_conjunto = 0
        for canvas_group_id, grupo_fila in grupo_por_canvas_id.items():
            resultado_p = cliente.obtener_pertenencias_de_grupo_paginado(token, canvas_group_id)
            crudas_por_grupo[grupo_fila.id] = resultado_p.items
            cantidad_actual_conjunto += sum(
                1 for p in resultado_p.items if p.workflow_state == "accepted"
            )

        if roster_sospechoso(
            cantidad_anterior=cantidad_anterior_conjunto, cantidad_actual=cantidad_actual_conjunto
        ):
            incidencia_repo.abrir_o_actualizar(
                bd,
                tipo="ROSTER_SOSPECHOSO",
                severidad="ADVERTENCIA",
                sujeto_tipo="CONJUNTO_GRUPOS",
                sujeto_id=conjunto_fila.id,
                curso_id=curso.id,
                detalle={
                    "recurso": _RECURSO_GRUPOS,
                    "conjunto": conjunto_fila.nombre,
                    "anterior": cantidad_anterior_conjunto,
                    "actual": cantidad_actual_conjunto,
                },
            )
            continue  # S7.3.8: no se aplica ninguna baja en este conjunto

        vistos_pares: set[tuple[uuid.UUID, uuid.UUID]] = set()
        nuevo_por_estudiante: dict[uuid.UUID, set[uuid.UUID]] = {}

        for grupo_id, crudas in crudas_por_grupo.items():
            for p in crudas:
                estudiante = estudiante_por_canvas_id.get(p.canvas_user_id)
                if estudiante is None:
                    hubo_huerfanos = True
                    huerfanos.append(
                        {
                            "canvas_user_id": p.canvas_user_id,
                            "fuente": "grupos",
                            "grupo_id": str(grupo_id),
                        }
                    )
                    continue
                vistos_pares.add((grupo_id, estudiante.id))
                fila_pg = (
                    bd.query(PertenenciaGrupo)
                    .filter(
                        PertenenciaGrupo.grupo_id == grupo_id,
                        PertenenciaGrupo.estudiante_id == estudiante.id,
                    )
                    .one_or_none()
                )
                if fila_pg is None:
                    fila_pg = PertenenciaGrupo(
                        grupo_id=grupo_id,
                        estudiante_id=estudiante.id,
                        workflow_state=p.workflow_state,
                        activa=(p.workflow_state == "accepted"),
                        activa_desde=ahora,
                        ciclos_ausente=0,
                        sincronizado_en=ahora,
                    )
                    bd.add(fila_pg)
                else:
                    fila_pg.workflow_state = p.workflow_state
                    fila_pg.sincronizado_en = ahora
                    if p.workflow_state == "accepted":
                        if not fila_pg.activa:
                            fila_pg.activa = True
                            fila_pg.activa_desde = ahora
                            fila_pg.activa_hasta = None
                        fila_pg.ciclos_ausente = 0
                if p.workflow_state == "accepted":
                    nuevo_por_estudiante.setdefault(estudiante.id, set()).add(grupo_id)
        bd.flush()

        for pg in filas_pertenencia_previas:
            if (pg.grupo_id, pg.estudiante_id) in vistos_pares:
                continue
            pg.ciclos_ausente += 1
            if confirma_ausencia(pg.ciclos_ausente) and pg.activa:
                pg.activa = False
                pg.activa_hasta = ahora
                deteccion = detectar_traslado_o_doble_pertenencia(
                    grupos_aceptados_anteriores=frozenset(
                        anterior_por_estudiante.get(pg.estudiante_id, set())
                    ),
                    grupos_aceptados_actuales=frozenset(
                        nuevo_por_estudiante.get(pg.estudiante_id, set())
                    ),
                )
                subtipo = (
                    "TRASLADO_DE_GRUPO" if deteccion.es_traslado else "INTEGRANTE_SALIO_DEL_GRUPO"
                )
                incidencia_repo.abrir_o_actualizar(
                    bd,
                    tipo="GRUPO_INCOMPLETO",
                    severidad="ADVERTENCIA",
                    sujeto_tipo="ESTUDIANTE",
                    sujeto_id=pg.estudiante_id,
                    curso_id=curso.id,
                    detalle={"subtipo": subtipo, "grupo_id": str(pg.grupo_id)},
                )
        bd.flush()

        for estudiante_id, grupos_ids in nuevo_por_estudiante.items():
            if len(grupos_ids) > 1:
                incidencia_repo.abrir_o_actualizar(
                    bd,
                    tipo="ESTUDIANTE_EN_DOS_GRUPOS",
                    severidad="BLOQUEANTE",
                    sujeto_tipo="ESTUDIANTE",
                    sujeto_id=estudiante_id,
                    curso_id=curso.id,
                    detalle={
                        "conjunto": conjunto_fila.nombre,
                        "grupos": [str(g) for g in grupos_ids],
                    },
                )

    if hubo_huerfanos:
        incidencia_repo.abrir_o_actualizar(
            bd,
            tipo="ROSTER_TRUNCADO",
            severidad="ADVERTENCIA",
            sujeto_tipo="CURSO",
            curso_id=curso.id,
            detalle={"huerfanos": huerfanos},
        )
        # S7.2.5 punto 4: un sync_roster inmediato, una sola vez por ciclo.
        encolar(
            bd,
            tipo="sync_roster",
            clave_idempotencia=f"roster_por_huerfano:{curso.id}:{ahora.date().isoformat()}",
            max_intentos=4,
            curso_id=curso.id,
        )

    resultado_final = ResultadoSincronizacion.OK.value
    sincronizacion_repo.actualizar_cursor(
        bd,
        curso_id=curso.id,
        recurso=_RECURSO_GRUPOS,
        referencia=str(curso.id),
        estado=resultado_final,
    )
    sincronizacion_repo.registrar_ciclo(
        bd,
        curso_id=curso.id,
        recurso=_RECURSO_GRUPOS,
        resultado=resultado_final,
        contadores={"conjuntos": len(conjunto_por_canvas_id), "huerfanos": len(huerfanos)},
    )
