"""`/personas`: espejo de estudiantes, secciones y grupos, mapeo de GitHub
(SPEC 07 S7.2, S7.4, S7.8.2).

Ninguna pantalla consulta a Canvas para renderizarse (Ley 1, A-119): esta
ruta solo lee el espejo ya sincronizado y su propio sello de antigüedad
(A-231). "Sincronizar ahora" solo encola -- nunca llama a Canvas en linea.
Correo y `sis_user_id` van enmascarados salvo `mapeo.editar`; revelarlos
queda en bitacora (criterio resumido de Etapa P6).
"""

from __future__ import annotations

import csv
import io
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adaptadores import mapeo_github_repo, registro_github_repo, tareas_repo, trabajos_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.bitacora_repo import registrar as registrar_bitacora
from app.adaptadores.canvas_repo import descifrar_token, obtener_credencial_operativa
from app.adaptadores.cliente_canvas import FalloProveedorCanvas, crear_cliente_canvas
from app.adaptadores.cliente_github import FalloProveedorGithub, crear_cliente_github_desde_config
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_infraestructura import CursorSincronizacion
from app.adaptadores.modelos_mapeo import CuentaGithub, MapeoGithub
from app.adaptadores.modelos_padron import (
    ConjuntoGrupos,
    Estudiante,
    Grupo,
    Matricula,
    PertenenciaGrupo,
    Seccion,
)
from app.api.dependencias import exigir_csrf, obtener_sesion_bd, requiere
from app.dominio.estados import EstadoEstudiante, EstadoMapeoGithub
from app.dominio.mapeo_github import RechazoMapeo
from app.dominio.permisos import Permiso, permisos_efectivos
from app.infraestructura.cifrado import Llavero
from app.infraestructura.config import Settings, obtener_configuracion

router = APIRouter(tags=["personas"])


def _llavero(settings: Settings) -> Llavero:
    return Llavero(settings.llavero_cifrado(), settings.app_encryption_key_activa)


def _puede_ver_sensible(membresia: MembresiaCurso) -> bool:
    efectivos = permisos_efectivos(
        rol=membresia.rol, permisos_configurados=frozenset(Permiso(p) for p in membresia.permisos)
    )
    return Permiso.MAPEO_EDITAR in efectivos


def _enmascarar_email(email: str | None) -> str | None:
    if not email:
        return None
    usuario, separador, dominio = email.partition("@")
    if not separador:
        return "*" * len(email)
    visible = usuario[0]
    return f"{visible}{'*' * max(len(usuario) - 1, 1)}@{dominio}"


def _enmascarar_texto(valor: str | None) -> str | None:
    if not valor:
        return None
    if len(valor) <= 2:
        return "*" * len(valor)
    return f"{valor[0]}{'*' * (len(valor) - 2)}{valor[-1]}"


class SeccionSalida(BaseModel):
    id: uuid.UUID
    nombre: str
    estado: str
    cantidad_estudiantes: int


class GrupoSalida(BaseModel):
    id: uuid.UUID
    nombre: str
    conjunto: str
    estado: str
    integrantes: list[str]


class MapeoSalida(BaseModel):
    estado: str
    cuenta_login: str | None
    motivo_invalidacion: str | None


class EstudianteSalida(BaseModel):
    id: uuid.UUID
    canvas_user_id: int
    nombre: str
    estado: str
    email: str | None
    sis_user_id: str | None
    secciones: list[str]
    grupos: list[str]
    mapeo: MapeoSalida


class PersonasSalida(BaseModel):
    estudiantes: list[EstudianteSalida]
    secciones: list[SeccionSalida]
    grupos: list[GrupoSalida]
    roster_sincronizado_en: str | None
    grupos_sincronizado_en: str | None
    registro_estado: str


def _mapeos_vivos_por_estudiante(bd: Session, curso_id: uuid.UUID) -> dict[uuid.UUID, MapeoGithub]:
    mapeos = (
        bd.query(MapeoGithub)
        .filter(
            MapeoGithub.curso_id == curso_id,
            MapeoGithub.estado != EstadoMapeoGithub.SUPERSEDIDO.value,
        )
        .all()
    )
    return {m.estudiante_id: m for m in mapeos}


@router.get("/api/cursos/{curso_id}/personas", response_model=PersonasSalida)
def obtener_personas(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> PersonasSalida:
    curso = bd.query(Curso).filter(Curso.id == curso_id).one_or_none()
    if curso is None:
        raise HTTPException(status_code=404)

    estudiantes = (
        bd.query(Estudiante)
        .filter(Estudiante.curso_id == curso_id)
        .order_by(Estudiante.nombre)
        .all()
    )
    secciones = (
        bd.query(Seccion).filter(Seccion.curso_id == curso_id).order_by(Seccion.nombre).all()
    )
    grupos = (
        bd.query(Grupo)
        .join(ConjuntoGrupos, ConjuntoGrupos.id == Grupo.conjunto_grupos_id)
        .filter(Grupo.curso_id == curso_id)
        .order_by(Grupo.nombre)
        .all()
    )
    conjunto_por_id = {
        c.id: c for c in bd.query(ConjuntoGrupos).filter(ConjuntoGrupos.curso_id == curso_id).all()
    }

    matriculas = (
        bd.query(Matricula).filter(Matricula.curso_id == curso_id, Matricula.activa.is_(True)).all()
    )
    seccion_por_id = {s.id: s for s in secciones}
    secciones_por_estudiante: dict[uuid.UUID, list[str]] = {}
    for m in matriculas:
        seccion = seccion_por_id.get(m.seccion_id)
        if seccion is not None:
            secciones_por_estudiante.setdefault(m.estudiante_id, []).append(seccion.nombre)

    pertenencias = (
        bd.query(PertenenciaGrupo)
        .join(Grupo, Grupo.id == PertenenciaGrupo.grupo_id)
        .filter(Grupo.curso_id == curso_id, PertenenciaGrupo.activa.is_(True))
        .all()
    )
    grupo_por_id = {g.id: g for g in grupos}
    grupos_por_estudiante: dict[uuid.UUID, list[str]] = {}
    integrantes_por_grupo: dict[uuid.UUID, list[str]] = {}
    nombre_por_estudiante_id = {e.id: e.nombre for e in estudiantes}
    for p in pertenencias:
        grupo = grupo_por_id.get(p.grupo_id)
        if grupo is not None:
            grupos_por_estudiante.setdefault(p.estudiante_id, []).append(grupo.nombre)
        nombre = nombre_por_estudiante_id.get(p.estudiante_id)
        if nombre:
            integrantes_por_grupo.setdefault(p.grupo_id, []).append(nombre)

    mapeo_por_estudiante = _mapeos_vivos_por_estudiante(bd, curso_id)
    cuentas_por_id = {
        c.id: c
        for c in bd.query(CuentaGithub)
        .filter(
            CuentaGithub.id.in_(
                [m.cuenta_github_id for m in mapeo_por_estudiante.values() if m.cuenta_github_id]
            )
        )
        .all()
    }

    cursor_roster = (
        bd.query(CursorSincronizacion)
        .filter(CursorSincronizacion.curso_id == curso_id, CursorSincronizacion.recurso == "roster")
        .one_or_none()
    )
    cursor_grupos = (
        bd.query(CursorSincronizacion)
        .filter(CursorSincronizacion.curso_id == curso_id, CursorSincronizacion.recurso == "grupos")
        .one_or_none()
    )

    puede_ver = _puede_ver_sensible(membresia)
    if puede_ver:
        registrar_bitacora(
            bd,
            accion="DATOS_SENSIBLES_PERSONAS_REVELADOS",
            entidad="curso",
            entidad_id=str(curso_id),
            actor_usuario_id=membresia.usuario_id,
            curso_id=curso_id,
        )

    estudiantes_salida = []
    for e in estudiantes:
        mapeo = mapeo_por_estudiante.get(e.id)
        cuenta = (
            cuentas_por_id.get(mapeo.cuenta_github_id) if mapeo and mapeo.cuenta_github_id else None
        )
        estudiantes_salida.append(
            EstudianteSalida(
                id=e.id,
                canvas_user_id=e.canvas_user_id,
                nombre=e.nombre,
                estado=e.estado,
                email=e.email if puede_ver else _enmascarar_email(e.email),
                sis_user_id=e.sis_user_id if puede_ver else _enmascarar_texto(e.sis_user_id),
                secciones=secciones_por_estudiante.get(e.id, []),
                grupos=grupos_por_estudiante.get(e.id, []),
                mapeo=MapeoSalida(
                    estado=mapeo.estado if mapeo else EstadoMapeoGithub.SIN_DATO.value,
                    cuenta_login=cuenta.login if cuenta else None,
                    motivo_invalidacion=mapeo.motivo_invalidacion if mapeo else None,
                ),
            )
        )

    return PersonasSalida(
        estudiantes=estudiantes_salida,
        secciones=[
            SeccionSalida(
                id=s.id,
                nombre=s.nombre,
                estado=s.estado,
                cantidad_estudiantes=sum(
                    1 for lista in secciones_por_estudiante.values() if s.nombre in lista
                ),
            )
            for s in secciones
        ],
        grupos=[
            GrupoSalida(
                id=g.id,
                nombre=g.nombre,
                conjunto=conjunto_por_id[g.conjunto_grupos_id].nombre,
                estado=g.estado,
                integrantes=integrantes_por_grupo.get(g.id, []),
            )
            for g in grupos
        ],
        roster_sincronizado_en=(
            cursor_roster.ultimo_exito_en.isoformat()
            if cursor_roster and cursor_roster.ultimo_exito_en
            else None
        ),
        grupos_sincronizado_en=(
            cursor_grupos.ultimo_exito_en.isoformat()
            if cursor_grupos and cursor_grupos.ultimo_exito_en
            else None
        ),
        registro_estado=curso.registro_estado,
    )


class CabeceraCursoSalida(BaseModel):
    con_cuenta_verificada: int
    total: int


@router.get("/api/cursos/{curso_id}/personas/cabecera", response_model=CabeceraCursoSalida)
def obtener_cabecera_personas(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_VER)),
) -> CabeceraCursoSalida:
    """S7.8.2: "N de M estudiantes con cuenta verificada". El denominador
    excluye RETIRADO/INACTIVO/CONCLUIDO (S7.8.2)."""
    total = (
        bd.query(Estudiante)
        .filter(
            Estudiante.curso_id == curso_id,
            Estudiante.estado.in_([EstadoEstudiante.ACTIVO.value, EstadoEstudiante.INVITADO.value]),
        )
        .count()
    )
    con_cuenta = (
        bd.query(MapeoGithub)
        .join(Estudiante, Estudiante.id == MapeoGithub.estudiante_id)
        .filter(
            MapeoGithub.curso_id == curso_id,
            MapeoGithub.estado == EstadoMapeoGithub.VIGENTE.value,
            Estudiante.estado.in_([EstadoEstudiante.ACTIVO.value, EstadoEstudiante.INVITADO.value]),
        )
        .count()
    )
    return CabeceraCursoSalida(con_cuenta_verificada=con_cuenta, total=total)


@router.post(
    "/api/cursos/{curso_id}/sincronizaciones", status_code=202, dependencies=[Depends(exigir_csrf)]
)
def sincronizar_ahora(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    _membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_ADMINISTRAR)),
) -> dict[str, bool]:
    """S7.3.1, S9.9: encola los mismos trabajos que el ciclo automatico, nunca
    llama a Canvas dentro de la peticion (Ley 1). Roster antes que grupos, y
    ambos antes que tareas: un grupo referencia estudiantes que deben existir
    primero (S7.2.5), y la visibilidad de una entrega se calcula sobre ese
    padron (A-164)."""
    ahora = ahora_utc()
    for tipo, prefijo in (
        ("sync_roster", "manual_roster"),
        ("sync_grupos", "manual_grupos"),
        ("sync_tareas_y_fechas", "manual_tareas"),
    ):
        trabajos_repo.encolar(
            bd,
            tipo=tipo,
            clave_idempotencia=f"{prefijo}:{curso_id}:{ahora.isoformat()}",
            max_intentos=4,
            curso_id=curso_id,
        )
    return {"ok": True}


def _detalle_rechazo(exc: RechazoMapeo) -> dict[str, str]:
    return {"motivo": exc.motivo.value, "detalle": exc.detalle}


class DeclararMapeoEntrada(BaseModel):
    login: str


@router.post(
    "/api/cursos/{curso_id}/personas/{estudiante_id}/mapeo",
    response_model=MapeoSalida,
    dependencies=[Depends(exigir_csrf)],
)
def declarar_mapeo_manual(
    curso_id: uuid.UUID,
    estudiante_id: uuid.UUID,
    datos: DeclararMapeoEntrada,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    membresia: MembresiaCurso = Depends(requiere(Permiso.MAPEO_EDITAR)),
) -> MapeoSalida:
    """Via 2 (S7.4.3): validacion en vivo contra GitHub, puerta del docente
    (S7.5.3): rechazo inmediato, sin persistir nada, si la cuenta no sirve."""
    estudiante = (
        bd.query(Estudiante)
        .filter(Estudiante.id == estudiante_id, Estudiante.curso_id == curso_id)
        .one_or_none()
    )
    if estudiante is None:
        raise HTTPException(status_code=404)

    cliente_github = crear_cliente_github_desde_config(settings)
    try:
        mapeo = mapeo_github_repo.declarar_manual(
            bd,
            cliente_github,
            curso_id=curso_id,
            estudiante=estudiante,
            login=datos.login,
            actor_usuario_id=membresia.usuario_id,
        )
    except RechazoMapeo as exc:
        registrar_bitacora(
            bd,
            accion="MAPEO_RECHAZADO",
            entidad="estudiante",
            entidad_id=str(estudiante_id),
            actor_usuario_id=membresia.usuario_id,
            curso_id=curso_id,
            despues=_detalle_rechazo(exc),
        )
        codigo = 422
        raise HTTPException(status_code=codigo, detail=_detalle_rechazo(exc)) from None
    except FalloProveedorGithub as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None

    # S8.7.1: un mapeo recien VIGENTE dispara su repositorio sin esperar el barrido.
    tareas_repo.encolar_materializacion(bd, curso_id=curso_id)
    cuenta = (
        bd.query(CuentaGithub).filter(CuentaGithub.id == mapeo.cuenta_github_id).one_or_none()
        if mapeo.cuenta_github_id
        else None
    )
    return MapeoSalida(
        estado=mapeo.estado,
        cuenta_login=cuenta.login if cuenta else None,
        motivo_invalidacion=mapeo.motivo_invalidacion,
    )


class FilaCsvSalida(BaseModel):
    fila: int
    canvas_user_id: int | None
    login_id: str | None
    github_login: str
    resultado: str
    detalle: str | None


class ImportarCsvSalida(BaseModel):
    filas: list[FilaCsvSalida]


def _parsear_csv(contenido: str) -> list[dict[str, str]]:
    lector = csv.DictReader(io.StringIO(contenido))
    return list(lector)


@router.post(
    "/api/cursos/{curso_id}/mapeo/importar-csv",
    response_model=ImportarCsvSalida,
    dependencies=[Depends(exigir_csrf)],
)
def importar_mapeo_csv(
    curso_id: uuid.UUID,
    contenido: dict[str, str],
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    membresia: MembresiaCurso = Depends(requiere(Permiso.MAPEO_EDITAR)),
) -> ImportarCsvSalida:
    """Via 3 (S7.4.4): columnas `canvas_user_id` (o `login_id`) y
    `github_login`. `{"aplicar": false}` (o ausente) solo previsualiza, sin
    escribir nada; `{"aplicar": true}` aplica unicamente las filas validas
    (S7.7.3: "nunca rechaza el archivo entero")."""
    filas_crudas = _parsear_csv(contenido.get("csv", ""))
    aplicar = contenido.get("aplicar") == "true"
    cliente_github = crear_cliente_github_desde_config(settings)

    estudiantes_por_canvas_id = {
        e.canvas_user_id: e
        for e in bd.query(Estudiante).filter(Estudiante.curso_id == curso_id).all()
    }
    estudiantes_por_login_id = {
        e.login_id: e
        for e in bd.query(Estudiante).filter(Estudiante.curso_id == curso_id).all()
        if e.login_id
    }

    resultado: list[FilaCsvSalida] = []
    for numero, fila in enumerate(filas_crudas, start=1):
        github_login = (fila.get("github_login") or "").strip()
        canvas_user_id_texto = (fila.get("canvas_user_id") or "").strip()
        login_id = (fila.get("login_id") or "").strip() or None
        canvas_user_id = int(canvas_user_id_texto) if canvas_user_id_texto.isdigit() else None

        estudiante = None
        if canvas_user_id is not None:
            estudiante = estudiantes_por_canvas_id.get(canvas_user_id)
        elif login_id:
            estudiante = estudiantes_por_login_id.get(login_id)

        if estudiante is None:
            resultado.append(
                FilaCsvSalida(
                    fila=numero,
                    canvas_user_id=canvas_user_id,
                    login_id=login_id,
                    github_login=github_login,
                    resultado="INVALIDA",
                    detalle="no se encontro un estudiante con ese canvas_user_id/login_id",
                )
            )
            continue
        if not github_login:
            resultado.append(
                FilaCsvSalida(
                    fila=numero,
                    canvas_user_id=canvas_user_id,
                    login_id=login_id,
                    github_login=github_login,
                    resultado="INVALIDA",
                    detalle="github_login vacio",
                )
            )
            continue

        if not aplicar:
            resultado.append(
                FilaCsvSalida(
                    fila=numero,
                    canvas_user_id=estudiante.canvas_user_id,
                    login_id=login_id,
                    github_login=github_login,
                    resultado="SE_APLICARIA",
                    detalle=None,
                )
            )
            continue

        try:
            mapeo_github_repo.procesar_candidato(
                bd,
                cliente_github,
                curso_id=curso_id,
                estudiante=estudiante,
                login=github_login,
                texto_crudo=None,
                origen="IMPORTACION_CSV",
                es_puerta_docente=False,
                creado_por=membresia.usuario_id,
            )
            resultado.append(
                FilaCsvSalida(
                    fila=numero,
                    canvas_user_id=estudiante.canvas_user_id,
                    login_id=login_id,
                    github_login=github_login,
                    resultado="APLICADA",
                    detalle=None,
                )
            )
        except FalloProveedorGithub as exc:
            resultado.append(
                FilaCsvSalida(
                    fila=numero,
                    canvas_user_id=estudiante.canvas_user_id,
                    login_id=login_id,
                    github_login=github_login,
                    resultado="FALLIDA",
                    detalle=str(exc),
                )
            )

    tareas_repo.encolar_materializacion(bd, curso_id=curso_id)
    return ImportarCsvSalida(filas=resultado)


class RegistroGithubSalida(BaseModel):
    registro_estado: str
    canvas_assignment_id: int | None


@router.post(
    "/api/cursos/{curso_id}/registro-github",
    response_model=RegistroGithubSalida,
    dependencies=[Depends(exigir_csrf)],
)
def crear_registro_github(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_ADMINISTRAR)),
) -> RegistroGithubSalida:
    """S7.4.1, S5.5.1 escritura sincrona #4: crea "Registro de tu cuenta de
    GitHub" en Canvas."""
    curso = bd.query(Curso).filter(Curso.id == curso_id).one_or_none()
    if curso is None:
        raise HTTPException(status_code=404)
    credencial = obtener_credencial_operativa(bd, curso_id)
    if credencial is None or curso.canvas_course_id is None:
        raise HTTPException(status_code=409, detail="el curso no tiene Canvas vinculado")

    token = descifrar_token(_llavero(settings), credencial)
    cliente = crear_cliente_canvas(
        modo=settings.canvas_modo, canvas_base_url=curso.canvas_base_url or settings.canvas_base_url
    )
    try:
        curso = registro_github_repo.crear_tarea_registro(
            bd, cliente, token, curso=curso, actor_usuario_id=membresia.usuario_id
        )
    except FalloProveedorCanvas as exc:
        trabajos_repo.encolar(
            bd,
            tipo="crear_registro_github",
            clave_idempotencia=f"crear_registro:{curso_id}:{ahora_utc().isoformat()}",
            max_intentos=4,
            curso_id=curso_id,
        )
        raise HTTPException(
            status_code=202,
            detail=f"Canvas no respondio a tiempo ({exc}); se reintenta en segundo plano",
        ) from None
    return RegistroGithubSalida(
        registro_estado=curso.registro_estado,
        canvas_assignment_id=curso.canvas_assignment_id_registro,
    )


@router.post(
    "/api/cursos/{curso_id}/registro-github/restaurar",
    response_model=RegistroGithubSalida,
    dependencies=[Depends(exigir_csrf)],
)
def restaurar_registro_github(
    curso_id: uuid.UUID,
    bd: Session = Depends(obtener_sesion_bd),
    settings: Settings = Depends(obtener_configuracion),
    membresia: MembresiaCurso = Depends(requiere(Permiso.CURSO_ADMINISTRAR)),
) -> RegistroGithubSalida:
    curso = bd.query(Curso).filter(Curso.id == curso_id).one_or_none()
    if curso is None:
        raise HTTPException(status_code=404)
    credencial = obtener_credencial_operativa(bd, curso_id)
    if credencial is None or curso.canvas_course_id is None:
        raise HTTPException(status_code=409, detail="el curso no tiene Canvas vinculado")

    token = descifrar_token(_llavero(settings), credencial)
    cliente = crear_cliente_canvas(
        modo=settings.canvas_modo, canvas_base_url=curso.canvas_base_url or settings.canvas_base_url
    )
    try:
        curso = registro_github_repo.restaurar_tarea_registro(
            bd, cliente, token, curso=curso, actor_usuario_id=membresia.usuario_id
        )
    except FalloProveedorCanvas as exc:
        trabajos_repo.encolar(
            bd,
            tipo="crear_registro_github",
            clave_idempotencia=f"restaurar_registro:{curso_id}:{ahora_utc().isoformat()}",
            max_intentos=4,
            curso_id=curso_id,
        )
        raise HTTPException(
            status_code=202,
            detail=f"Canvas no respondio a tiempo ({exc}); se reintenta en segundo plano",
        ) from None
    return RegistroGithubSalida(
        registro_estado=curso.registro_estado,
        canvas_assignment_id=curso.canvas_assignment_id_registro,
    )
