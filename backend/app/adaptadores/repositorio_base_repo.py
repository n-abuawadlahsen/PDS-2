"""Repositorio base y sus archivos iniciales (SPEC 08 S8.3; A-066, A-067, A-068,
A-069, A-097, A-169 escrituras 2 y 3, A-208; Etapa P7).

Contrato de A-169, punto por punto, como lo aplica este modulo:

1. Lectura antes del efecto: `GET /repos/{o}/{r}` antes de crear (adopcion
   segura de A-097) y `GET contents` antes de `PUT`/`DELETE` (el `sha` vigente).
2. Intencion persistida antes de la llamada: `registrar_intencion_*` escribe la
   fila `CREANDO` o la bitacora de solicitud, y el llamador (la ruta) hace
   `commit` antes de invocar `completar_*`/`ejecutar_*`.
3. Tope de 20 s: lo aplica `ClienteGitHubReal`. Si se agota, la fila queda
   `CREANDO` con el error y la pantalla lo dice; reintentar es idempotente por
   el punto 1. TODO(etapa-P8): `aprovisionar_repositorios` completara en su
   barrido un base que siga `CREANDO`, que es la degradacion a cola que pide
   A-169 sin abrir un trabajo fuera del catalogo cerrado de 31.
4. Resultado en pantalla con el error literal (`RechazoProveedorGithub`).
5. Bitacora de cada escritura externa.
6. Ninguna envia comunicacion a un estudiante.
"""

from __future__ import annotations

import base64
import binascii
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.adaptadores import incidencia_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.bitacora_repo import registrar as registrar_bitacora
from app.adaptadores.cliente_github import (
    ClienteGitHub,
    FalloProveedorGithub,
    RechazoProveedorGithub,
)
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_tarea import ArchivoRepositorioBase, RepositorioBase, Tarea
from app.dominio.estados import EstadoRepositorioBase, EstadoTarea, FamiliaError
from app.dominio.nombres_repositorio import (
    marcador_descripcion,
    nombre_repositorio,
    topics_repositorio,
)
from app.dominio.repositorio_github import RepoGithubInfo
from app.dominio.tareas import (
    ARCHIVO_AUTO_INIT,
    MotivoRechazoTarea,
    RechazoTarea,
    condiciones_adopcion_fallidas,
    estado_base_segun_archivos,
    validar_ruta_archivo,
    validar_tamano_archivo,
)

# Tope de previsualizacion de texto: suficiente para un enunciado o un archivo
# de codigo de partida, sin volcar un binario en pantalla.
_TOPE_PREVISUALIZACION_BYTES = 200_000

_ESTADOS_OPERABLES = frozenset(
    {EstadoRepositorioBase.CREADO_VACIO.value, EstadoRepositorioBase.LISTO.value}
)


def _exigir_github(curso: Curso) -> str:
    if curso.github_org_login is None or curso.github_installation_id is None:
        raise RechazoTarea(
            MotivoRechazoTarea.GITHUB_NO_VINCULADO, "El curso todavía no tiene GitHub vinculado."
        )
    return curso.github_org_login


def _descripcion_base(curso: Curso, tarea: Tarea) -> str:
    marcador = marcador_descripcion(curso_slug=curso.slug, tarea_slug=tarea.slug, sujeto="base")
    return f"Repositorio base de «{tarea.nombre}» — {curso.nombre} {marcador}"


# --- Escritura sincrona 2: crear el repositorio base ---


def registrar_intencion_repositorio_base(
    bd: Session, *, curso: Curso, tarea: Tarea, actor_usuario_id: uuid.UUID
) -> RepositorioBase:
    """Crea (o reabre desde `ERROR`/`CREANDO`) la fila del base. `ERROR ->
    CREANDO` es la salida "por accion explicita con `tarea.administrar`" de A-208."""
    _exigir_github(curso)
    if tarea.estado != EstadoTarea.BORRADOR.value:
        raise RechazoTarea(
            MotivoRechazoTarea.TAREA_NO_EDITABLE,
            "El repositorio base solo se declara mientras la tarea está en borrador: los "
            "repositorios de los estudiantes copian el base una sola vez al crearse.",
        )
    existente = bd.query(RepositorioBase).filter(RepositorioBase.tarea_id == tarea.id).one_or_none()
    if existente is not None and existente.estado in _ESTADOS_OPERABLES:
        raise RechazoTarea(
            MotivoRechazoTarea.REPOSITORIO_BASE_YA_EXISTE, "Esta tarea ya tiene repositorio base."
        )
    if existente is not None and existente.estado == EstadoRepositorioBase.INACCESIBLE.value:
        raise RechazoTarea(
            MotivoRechazoTarea.REPOSITORIO_BASE_NO_OPERABLE,
            "El repositorio base de esta tarea dejó de ser accesible en GitHub.",
        )

    ahora = ahora_utc()
    nombre = nombre_repositorio(curso_slug=curso.slug, tarea_slug=tarea.slug, sujeto="base")
    if existente is None:
        existente = RepositorioBase(
            tarea_id=tarea.id,
            nombre=nombre,
            es_plantilla=False,
            creado_por=actor_usuario_id,
            creado_en=ahora,
        )
        bd.add(existente)
    existente.estado = EstadoRepositorioBase.CREANDO.value
    existente.clase_error = None
    existente.error_mensaje_literal = None
    existente.actualizado_en = ahora
    bd.flush()
    tarea.repositorio_base_id = existente.id
    tarea.actualizada_en = ahora
    bd.flush()
    registrar_bitacora(
        bd,
        accion="REPOSITORIO_BASE_CREACION_SOLICITADA",
        entidad="repositorio_base",
        entidad_id=str(existente.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=curso.id,
        despues={"nombre": nombre},
    )
    return existente


def completar_creacion_repositorio_base(
    bd: Session,
    cliente: ClienteGitHub,
    token_instalacion: str,
    *,
    curso: Curso,
    tarea: Tarea,
    base: RepositorioBase,
    actor_usuario_id: uuid.UUID,
) -> RepositorioBase:
    org = _exigir_github(curso)
    try:
        info = _crear_o_adoptar(
            bd, cliente, token_instalacion, org=org, curso=curso, tarea=tarea, base=base
        )
        if info is None:
            return base  # ERROR permanente ya registrado
        if not info.es_plantilla:
            info = cliente.marcar_como_plantilla(org, info.nombre, token_instalacion)
        cliente.reemplazar_topics(
            org,
            info.nombre,
            topics_repositorio(curso_slug=curso.slug, tarea_slug=tarea.slug),
            token_instalacion,
        )
        readme = cliente.obtener_archivo(org, info.nombre, ARCHIVO_AUTO_INIT, token_instalacion)
    except RechazoProveedorGithub as exc:
        _marcar_error(
            bd, base, FamiliaError.PERMANENTE, exc.mensaje_literal, actor_usuario_id, curso
        )
        return base
    except FalloProveedorGithub as exc:
        # Transitorio: la intencion ya esta persistida; queda CREANDO con el motivo.
        base.clase_error = FamiliaError.TRANSITORIO.value
        base.error_mensaje_literal = str(exc)
        base.actualizado_en = ahora_utc()
        bd.flush()
        raise

    ahora = ahora_utc()
    base.github_repo_id = info.github_repo_id
    base.full_name = info.full_name
    base.url_html = info.url_html
    base.rama_por_defecto = info.rama_por_defecto  # A-068: leida, nunca supuesta
    base.es_plantilla = True
    if readme is not None:
        _registrar_archivo(
            bd, base, ruta=readme.ruta, sha=readme.sha, tamano=readme.tamano_bytes, actor=None
        )
    base.estado = estado_base_segun_archivos(_rutas(bd, base)).value
    base.clase_error = None
    base.error_mensaje_literal = None
    base.actualizado_en = ahora
    bd.flush()
    registrar_bitacora(
        bd,
        accion="REPOSITORIO_BASE_CREADO",
        entidad="repositorio_base",
        entidad_id=str(base.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=curso.id,
        despues={
            "full_name": base.full_name,
            "github_repo_id": base.github_repo_id,
            "rama_por_defecto": base.rama_por_defecto,
            "estado": base.estado,
        },
    )
    return base


def _crear_o_adoptar(
    bd: Session,
    cliente: ClienteGitHub,
    token_instalacion: str,
    *,
    org: str,
    curso: Curso,
    tarea: Tarea,
    base: RepositorioBase,
) -> RepoGithubInfo | None:
    """A-097: si el nombre ya existe, se adopta solo con las condiciones
    cumplidas; si no, `ERROR` con el detalle de que condicion fallo. Nunca se
    añade un sufijo (A-111)."""
    existente = cliente.obtener_repo(org, base.nombre, token_instalacion)
    if existente is None:
        return cliente.crear_repo_organizacion(
            org,
            nombre=base.nombre,
            descripcion=_descripcion_base(curso, tarea),
            token_instalacion=token_instalacion,
        )
    fallidas = condiciones_adopcion_fallidas(
        existente, org_login=org, curso_slug=curso.slug, tarea_slug=tarea.slug
    )
    if fallidas:
        mensaje = (
            f"Ya existe en GitHub un repositorio llamado {base.nombre} que no es el base de esta "
            f"tarea ({'; '.join(fallidas)}). Renómbralo o bórralo en GitHub y vuelve a intentarlo."
        )
        _marcar_error(bd, base, FamiliaError.PERMANENTE, mensaje, None, curso)
        incidencia_repo.abrir_o_actualizar(
            bd,
            tipo="REPO_NOMBRE_OCUPADO",
            severidad="BLOQUEANTE",
            sujeto_tipo="REPOSITORIO_BASE",
            curso_id=curso.id,
            sujeto_id=base.id,
            detalle={"nombre": base.nombre, "condiciones_fallidas": fallidas},
        )
        return None
    return existente


def _marcar_error(
    bd: Session,
    base: RepositorioBase,
    familia: FamiliaError,
    mensaje: str,
    actor_usuario_id: uuid.UUID | None,
    curso: Curso,
) -> None:
    base.estado = EstadoRepositorioBase.ERROR.value
    base.clase_error = familia.value
    base.error_mensaje_literal = mensaje
    base.actualizado_en = ahora_utc()
    bd.flush()
    registrar_bitacora(
        bd,
        accion="REPOSITORIO_BASE_ERROR",
        entidad="repositorio_base",
        entidad_id=str(base.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=curso.id,
        despues={"clase_error": familia.value, "mensaje": mensaje},
    )


# --- Escritura sincrona 3: archivos iniciales ---


def _rutas(bd: Session, base: RepositorioBase) -> set[str]:
    return {
        ruta
        for (ruta,) in bd.query(ArchivoRepositorioBase.ruta).filter(
            ArchivoRepositorioBase.repositorio_base_id == base.id
        )
    }


def _registrar_archivo(
    bd: Session,
    base: RepositorioBase,
    *,
    ruta: str,
    sha: str,
    tamano: int,
    actor: uuid.UUID | None,
) -> None:
    fila = (
        bd.query(ArchivoRepositorioBase)
        .filter(
            ArchivoRepositorioBase.repositorio_base_id == base.id,
            ArchivoRepositorioBase.ruta == ruta,
        )
        .one_or_none()
    )
    if fila is None:
        fila = ArchivoRepositorioBase(repositorio_base_id=base.id, ruta=ruta)
        bd.add(fila)
    fila.sha = sha
    fila.tamano_bytes = tamano
    fila.actualizado_por = actor
    fila.actualizado_en = ahora_utc()
    bd.flush()


def _quitar_archivo(bd: Session, base: RepositorioBase, ruta: str) -> None:
    bd.query(ArchivoRepositorioBase).filter(
        ArchivoRepositorioBase.repositorio_base_id == base.id, ArchivoRepositorioBase.ruta == ruta
    ).delete()
    bd.flush()


def _recalcular_estado(bd: Session, base: RepositorioBase) -> None:
    base.estado = estado_base_segun_archivos(_rutas(bd, base)).value
    base.actualizado_en = ahora_utc()
    bd.flush()


def exigir_base_operable(bd: Session, tarea: Tarea) -> RepositorioBase:
    base = bd.query(RepositorioBase).filter(RepositorioBase.tarea_id == tarea.id).one_or_none()
    if base is None:
        raise RechazoTarea(
            MotivoRechazoTarea.REPOSITORIO_BASE_NO_EXISTE, "Esta tarea no tiene repositorio base."
        )
    if base.estado not in _ESTADOS_OPERABLES:
        raise RechazoTarea(
            MotivoRechazoTarea.REPOSITORIO_BASE_NO_OPERABLE,
            "El repositorio base todavía no está disponible para administrar archivos.",
        )
    return base


def validar_contenido_base64(contenido_base64: str) -> int:
    """Devuelve el tamano en bytes, o rechaza si el contenido no es base64."""
    try:
        tamano = len(base64.b64decode(contenido_base64, validate=True))
    except (binascii.Error, ValueError):
        raise RechazoTarea(
            MotivoRechazoTarea.RUTA_INVALIDA, "El contenido del archivo no llegó bien codificado."
        ) from None
    validar_tamano_archivo(tamano)
    return tamano


def registrar_intencion_archivo(
    bd: Session,
    *,
    curso: Curso,
    base: RepositorioBase,
    accion: str,
    rutas: dict[str, str],
    actor_usuario_id: uuid.UUID,
) -> None:
    registrar_bitacora(
        bd,
        accion=accion,
        entidad="repositorio_base",
        entidad_id=str(base.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=curso.id,
        despues=rutas,
    )


def escribir_archivo(
    bd: Session,
    cliente: ClienteGitHub,
    token_instalacion: str,
    *,
    curso: Curso,
    base: RepositorioBase,
    ruta: str,
    contenido_base64: str,
    actor_usuario_id: uuid.UUID,
) -> ArchivoRepositorioBase:
    """Subir o reemplazar (A-067). La ruta ya viene validada por el llamador."""
    org = _exigir_github(curso)
    tamano = validar_contenido_base64(contenido_base64)
    anterior = cliente.obtener_archivo(org, base.nombre, ruta, token_instalacion)
    verbo = "Reemplaza" if anterior is not None else "Agrega"
    escrito = cliente.escribir_archivo(
        org,
        base.nombre,
        ruta,
        contenido_base64=contenido_base64,
        mensaje=f"{verbo} {ruta} desde la aplicación del curso",
        sha_anterior=anterior.sha if anterior is not None else None,
        token_instalacion=token_instalacion,
    )
    _registrar_archivo(bd, base, ruta=ruta, sha=escrito.sha, tamano=tamano, actor=actor_usuario_id)
    _recalcular_estado(bd, base)
    registrar_bitacora(
        bd,
        accion="ARCHIVO_BASE_REEMPLAZADO" if anterior is not None else "ARCHIVO_BASE_SUBIDO",
        entidad="repositorio_base",
        entidad_id=str(base.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=curso.id,
        antes={"ruta": ruta, "sha": anterior.sha} if anterior is not None else None,
        despues={"ruta": ruta, "sha": escrito.sha, "tamano_bytes": tamano},
    )
    return (
        bd.query(ArchivoRepositorioBase)
        .filter(
            ArchivoRepositorioBase.repositorio_base_id == base.id,
            ArchivoRepositorioBase.ruta == ruta,
        )
        .one()
    )


def borrar_archivo(
    bd: Session,
    cliente: ClienteGitHub,
    token_instalacion: str,
    *,
    curso: Curso,
    base: RepositorioBase,
    ruta: str,
    actor_usuario_id: uuid.UUID,
) -> None:
    org = _exigir_github(curso)
    anterior = cliente.obtener_archivo(org, base.nombre, ruta, token_instalacion)
    if anterior is not None:
        cliente.borrar_archivo(
            org,
            base.nombre,
            ruta,
            sha=anterior.sha,
            mensaje=f"Retira {ruta} desde la aplicación del curso",
            token_instalacion=token_instalacion,
        )
    _quitar_archivo(bd, base, ruta)
    _recalcular_estado(bd, base)
    registrar_bitacora(
        bd,
        accion="ARCHIVO_BASE_BORRADO",
        entidad="repositorio_base",
        entidad_id=str(base.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=curso.id,
        antes={"ruta": ruta, "sha": anterior.sha if anterior is not None else None},
    )


def renombrar_archivo(
    bd: Session,
    cliente: ClienteGitHub,
    token_instalacion: str,
    *,
    curso: Curso,
    base: RepositorioBase,
    desde: str,
    hacia: str,
    actor_usuario_id: uuid.UUID,
) -> None:
    """La API de contenidos no renombra: se escribe `hacia` con el mismo
    contenido y se borra `desde`, cada paso con su lectura previa."""
    org = _exigir_github(curso)
    if desde == hacia:
        return
    origen = cliente.obtener_archivo(org, base.nombre, desde, token_instalacion)
    if origen is None or origen.contenido_base64 is None:
        raise RechazoTarea(
            MotivoRechazoTarea.RUTA_INVALIDA, f"El archivo {desde} ya no existe en el repositorio."
        )
    if cliente.obtener_archivo(org, base.nombre, hacia, token_instalacion) is not None:
        raise RechazoTarea(
            MotivoRechazoTarea.RUTA_INVALIDA,
            f"Ya existe un archivo en {hacia}: bórralo o elige otra ruta.",
        )
    escrito = cliente.escribir_archivo(
        org,
        base.nombre,
        hacia,
        contenido_base64=origen.contenido_base64,
        mensaje=f"Renombra {desde} a {hacia} desde la aplicación del curso",
        sha_anterior=None,
        token_instalacion=token_instalacion,
    )
    cliente.borrar_archivo(
        org,
        base.nombre,
        desde,
        sha=origen.sha,
        mensaje=f"Renombra {desde} a {hacia} desde la aplicación del curso",
        token_instalacion=token_instalacion,
    )
    _quitar_archivo(bd, base, desde)
    _registrar_archivo(
        bd, base, ruta=hacia, sha=escrito.sha, tamano=origen.tamano_bytes, actor=actor_usuario_id
    )
    _recalcular_estado(bd, base)
    registrar_bitacora(
        bd,
        accion="ARCHIVO_BASE_RENOMBRADO",
        entidad="repositorio_base",
        entidad_id=str(base.id),
        actor_usuario_id=actor_usuario_id,
        curso_id=curso.id,
        antes={"ruta": desde, "sha": origen.sha},
        despues={"ruta": hacia, "sha": escrito.sha},
    )


@dataclass(frozen=True)
class Previsualizacion:
    ruta: str
    tamano_bytes: int
    texto: str | None
    motivo_sin_texto: str | None


def previsualizar_archivo(
    cliente: ClienteGitHub,
    token_instalacion: str,
    *,
    curso: Curso,
    base: RepositorioBase,
    ruta: str,
) -> Previsualizacion:
    """A-067 "previsualizar texto": el contenido se lee y se muestra, nunca se persiste."""
    org = _exigir_github(curso)
    archivo = cliente.obtener_archivo(org, base.nombre, ruta, token_instalacion)
    if archivo is None or archivo.contenido_base64 is None:
        raise RechazoTarea(
            MotivoRechazoTarea.RUTA_INVALIDA, f"El archivo {ruta} no existe en el repositorio base."
        )
    if archivo.tamano_bytes > _TOPE_PREVISUALIZACION_BYTES:
        return Previsualizacion(
            ruta, archivo.tamano_bytes, None, "El archivo es demasiado grande para previsualizarlo."
        )
    try:
        texto = base64.b64decode(archivo.contenido_base64).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return Previsualizacion(ruta, archivo.tamano_bytes, None, "El archivo no es texto.")
    return Previsualizacion(ruta, archivo.tamano_bytes, texto, None)


def listar_archivos(bd: Session, base: RepositorioBase) -> list[ArchivoRepositorioBase]:
    return (
        bd.query(ArchivoRepositorioBase)
        .filter(ArchivoRepositorioBase.repositorio_base_id == base.id)
        .order_by(ArchivoRepositorioBase.ruta)
        .all()
    )


def exigir_ruta(ruta: str) -> str:
    return validar_ruta_archivo(ruta)
