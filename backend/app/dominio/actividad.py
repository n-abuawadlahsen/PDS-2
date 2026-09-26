"""Ingesta de actividad de GitHub y atribucion de commits, reglas puras (SPEC 10
S10.2-S10.3; SPEC 06 S6.8; A-070 a A-072, A-118, A-196, A-205, A-221; Etapa F5).

Recibe lo ya leido y decide. Las llamadas y escrituras viven en
`app/adaptadores/actividad_repo.py`.
"""

from __future__ import annotations

import hashlib
import hmac
import math
import re
from collections.abc import Hashable
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.dominio.estados import MotivoExclusionCommit, ReglaAtribucion

SHA_CEROS = "0" * 40


@dataclass(frozen=True)
class CommitGithub:
    """Un commit tal como lo entregan la API REST o el payload de `push`.
    `parent_shas = None` significa «no se sabe todavia» (el payload no trae
    padres): la ingesta lo enriquece despues, nunca inventa un cero."""

    sha: str
    parent_shas: tuple[str, ...] | None
    autor_nombre: str | None
    autor_email: str | None
    autor_github_user_id: int | None
    autor_es_bot: bool
    committer_github_user_id: int | None
    fecha_autor: datetime | None
    fecha_committer: datetime
    mensaje: str | None
    via_web: bool | None
    archivos_tocados: int | None = None


# --- S6.8.2: la firma, sobre el cuerpo crudo y en tiempo constante ---


def firma_valida(cuerpo: bytes, cabecera: str | None, *, secretos: list[str | None]) -> bool:
    """`X-Hub-Signature-256`. Se acepta tambien el secreto anterior mientras
    dure una rotacion (S14.6)."""
    if not cabecera or not cabecera.startswith("sha256="):
        return False
    recibida = cabecera.removeprefix("sha256=")
    for secreto in secretos:
        if not secreto:
            continue
        esperada = hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()
        if hmac.compare_digest(esperada, recibida):
            return True
    return False


# --- S10.3.1 y S10.3.6: correos ---

_NOREPLY = re.compile(r"^(\d+)\+[^@]+@users\.noreply\.github\.com$", re.IGNORECASE)


def normalizar_email(email: str | None) -> str | None:
    """Minusculas y recorte. No se quitan puntos ni `+etiqueta`: esa
    equivalencia es de un proveedor concreto, no universal."""
    if email is None:
        return None
    limpio = email.strip().lower()
    return limpio or None


def id_desde_noreply(email: str | None) -> int | None:
    normalizado = normalizar_email(email)
    if normalizado is None:
        return None
    coincide = _NOREPLY.match(normalizado)
    return int(coincide.group(1)) if coincide else None


def ofuscar_email(email: str | None) -> str | None:
    """`jp•••@g•••.com`: primera letra de la parte local y del dominio. El
    correo `noreply` de GitHub se muestra completo: es la evidencia del mapeo,
    no un dato de contacto."""
    if email is None:
        return None
    if id_desde_noreply(email) is not None:
        return email
    local, _, dominio = email.partition("@")
    if not dominio:
        return f"{local[:1]}•••"
    nombre, punto, tld = dominio.rpartition(".")
    if not punto:
        return f"{local[:1]}•••@{dominio[:1]}•••"
    return f"{local[:1]}•••@{nombre[:1]}•••.{tld}"


# --- S10.3.1: la cascada de atribucion ---

_ORDEN_REGLAS = {
    ReglaAtribucion.AUTOR_GITHUB: 0,
    ReglaAtribucion.EMAIL_NOREPLY: 1,
    ReglaAtribucion.EMAIL_DIRECTO: 2,
    ReglaAtribucion.IDENTIDAD_DOCENTE: 3,
    ReglaAtribucion.SIN_ATRIBUIR: 4,
}


@dataclass(frozen=True)
class ContextoAtribucion:
    """Lo que la cascada necesita saber del curso. La clave es siempre el
    `github_user_id` numerico: nunca el login ni el nombre.

    `identidad` es la identidad de Git vigente del correo en ese repositorio,
    como `(estado, estudiante_id)`, o `None` si no hay."""

    estudiante_por_github_id: dict[int, Hashable]
    estudiante_por_email: dict[str, Hashable]
    identidad: tuple[str, Hashable | None] | None


@dataclass(frozen=True)
class Atribucion:
    regla: ReglaAtribucion
    estudiante_id: Hashable | None
    confianza: str | None


def atribuir(
    *, autor_github_user_id: int | None, autor_email: str | None, contexto: ContextoAtribucion
) -> Atribucion:
    """Gana la primera regla que casa. La regla 3 (correo directo) es senal
    debil y se marca en pantalla."""
    if (
        autor_github_user_id is not None
        and autor_github_user_id in contexto.estudiante_por_github_id
    ):
        return Atribucion(
            ReglaAtribucion.AUTOR_GITHUB,
            contexto.estudiante_por_github_id[autor_github_user_id],
            "ALTA",
        )
    noreply = id_desde_noreply(autor_email)
    if noreply is not None and noreply in contexto.estudiante_por_github_id:
        return Atribucion(
            ReglaAtribucion.EMAIL_NOREPLY, contexto.estudiante_por_github_id[noreply], "ALTA"
        )
    email = normalizar_email(autor_email)
    if email is not None and email in contexto.estudiante_por_email:
        return Atribucion(
            ReglaAtribucion.EMAIL_DIRECTO, contexto.estudiante_por_email[email], "MEDIA"
        )
    if contexto.identidad is not None and contexto.identidad[0] == "RESUELTA":
        return Atribucion(ReglaAtribucion.IDENTIDAD_DOCENTE, contexto.identidad[1], "ALTA")
    return Atribucion(ReglaAtribucion.SIN_ATRIBUIR, None, None)


def es_mejora(actual: ReglaAtribucion, nueva: ReglaAtribucion) -> bool:
    """La reatribucion solo mejora: sustituye una regla por otra anterior en la
    cascada. Asi la correccion docente nunca pisa a `AUTOR_GITHUB` ni a
    `EMAIL_NOREPLY` (S10.3.4 regla 3)."""
    return _ORDEN_REGLAS[nueva] < _ORDEN_REGLAS[actual]


# --- S10.5.1: el commit contable ---


def motivo_exclusion(
    *, n_padres: int | None, sha: str, commit_inicial_sha: str | None, huerfano: bool
) -> MotivoExclusionCommit:
    """Exactamente tres motivos. Bots y docentes SI son contables. Con padres
    aun desconocidos no se inventa un merge."""
    if huerfano:
        return MotivoExclusionCommit.HUERFANO
    if n_padres is not None and n_padres > 1:
        return MotivoExclusionCommit.MERGE
    if commit_inicial_sha is not None and sha == commit_inicial_sha:
        return MotivoExclusionCommit.COMMIT_INICIAL
    return MotivoExclusionCommit.NINGUNO


# --- S10.2.3: del push al commit ---


def decidir_relleno(*, before: str, after: str) -> str:
    """`RAMA_BORRADA`: no hay commits que ingerir. `RECORRIDO`: rama nueva, se
    recorre hasta un SHA conocido. `COMPARE`: todo lo demas, paginado.

    Decision documentada: el payload de `push` no trae los padres ni el
    `author.id` numerico de cada commit, sin los cuales no se detecta un merge
    ni se aplica `AUTOR_GITHUB`. Por eso todo push con `before` conocido pasa
    por `compare`, no solo el truncado; el payload se ingiere antes como dato
    provisional y la respuesta de `compare` lo completa."""
    if after == SHA_CEROS:
        return "RAMA_BORRADA"
    if before == SHA_CEROS:
        return "RECORRIDO"
    return "COMPARE"


# --- S10.2.8: hasta cuando se ingiere ---

_ESTADOS_REPOSITORIO_EN_INGESTA = frozenset({"OPERATIVO", "DEGRADADO"})
_ESTADOS_TAREA_EN_INGESTA = frozenset({"ACTIVA", "INCONSISTENTE"})
COLA_DE_GRACIA = timedelta(days=14)


def repositorio_en_ingesta(
    *,
    estado_repositorio: str,
    estado_tarea: str,
    ultima_fecha: datetime | None,
    ahora: datetime,
) -> bool:
    """La unica funcion que deciden los tres trabajos de sondeo. Fuera de ella
    el repositorio sigue recibiendo webhooks, que no cuestan peticiones."""
    if estado_repositorio not in _ESTADOS_REPOSITORIO_EN_INGESTA:
        return False
    if estado_tarea not in _ESTADOS_TAREA_EN_INGESTA:
        return False
    return ultima_fecha is None or ahora <= ultima_fecha + COLA_DE_GRACIA


# --- S10.2.1: el techo de frescura sin webhook ---

REPOSITORIOS_POR_CICLO = 200
CADENCIA_RECONCILIACION = timedelta(minutes=15)


def techo_frescura(repositorios_en_ingesta: int) -> timedelta:
    ciclos = max(1, math.ceil(repositorios_en_ingesta / REPOSITORIOS_POR_CICLO))
    return ciclos * CADENCIA_RECONCILIACION
