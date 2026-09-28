"""Captura y versiones de entrega, reglas puras (SPEC 09 S9.6-S9.9; A-101 a
A-104, A-172, A-173, A-204, A-213; Etapa F4).

Recibe lo ya leido del espejo y de GitHub y decide. Las llamadas y las
escrituras viven en `app/adaptadores/versiones_repo.py`.

Decision documentada: S9.6.5 nombra `REPOSITORIO_VACIO`/`SOLO_COMMIT_INICIAL`
como «motivo» de `SIN_COMMITS`, pero el catalogo cerrado de
`version_entrega.motivo` (A-204, S9.11) tiene cinco valores y no los incluye.
Manda el catalogo cerrado: el subtipo viaja en `verificacion.motivo_sin_commits`.
"""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from app.dominio.estados import (
    AdvertenciaVersion,
    EstadoVersion,
    MotivoVersion,
    TagEstado,
    TagMotivo,
)

# --- S9.8.1 (A-204): la funcion unica de transicion ---

COLUMNAS_MUTABLES: frozenset[str] = frozenset(
    {
        "vigente",
        "motivo",
        "tag_estado",
        "tag_motivo",
        "tag_error",
        "tag_creado",
        "advertencias",
        "estado",
    }
)

# S9.6.3 (RG-026, RG-188): dos transiciones posteriores a la insercion, y solo dos.
TRANSICIONES_DE_ESTADO: frozenset[tuple[str, str]] = frozenset(
    {
        (EstadoVersion.CAPTURADA_SIN_TAG.value, EstadoVersion.CAPTURADA.value),
        (EstadoVersion.CAPTURADA.value, EstadoVersion.CAPTURADA_SIN_TAG.value),
    }
)


class VersionInmutable(Exception):
    """Un intento de escribir evidencia inmutable (CA-9.8-01)."""


def validar_cambios(actual: dict[str, Any], cambios: dict[str, Any]) -> None:
    """Rechaza cualquier escritura fuera de la lista cerrada, `vigente` que no
    sea `true -> false` y `estado` fuera de sus dos transiciones."""
    for columna, valor in cambios.items():
        if columna not in COLUMNAS_MUTABLES:
            raise VersionInmutable(f"«{columna}» es evidencia inmutable de la versión")
        anterior = actual.get(columna)
        if columna == "vigente" and valor != anterior and not (anterior is True and valor is False):
            raise VersionInmutable("una versión supersedida no vuelve a ser vigente")
        if (
            columna == "estado"
            and valor != anterior
            and (str(anterior), str(valor)) not in TRANSICIONES_DE_ESTADO
        ):
            raise VersionInmutable(f"transición de estado no permitida: {anterior} -> {valor}")


# --- S9.7.2 (A-104, A-172): el nombre del tag ---


def nombre_tag(*, orden: int, slug: str, intento: int) -> str:
    return f"entrega/{orden}-{slug}/v{intento}"


# --- S9.6.4 (A-102): seleccion del commit de cierre ---


@dataclass(frozen=True)
class CommitCierre:
    sha: str
    tree_sha: str | None
    fecha_committer: datetime
    fecha_autor: datetime | None
    mensaje: str | None


def seleccionar_commit_cierre(
    commits: list[CommitCierre], *, corte: datetime
) -> CommitCierre | None:
    """«Ultimo commit cuya fecha de committer es anterior o igual a la fecha
    efectiva de cierre, en UTC»: seleccion local, nunca el primero de la lista."""
    candidatos = [c for c in commits if c.fecha_committer <= corte]
    if not candidatos:
        return None
    return max(candidatos, key=lambda c: c.fecha_committer)


@dataclass(frozen=True)
class ResultadoCaptura:
    estado: EstadoVersion
    tag_estado: TagEstado
    tag_motivo: TagMotivo | None
    commit: CommitCierre | None
    verificacion: dict[str, Any]


def resolver_captura(
    *, espejo: CommitCierre | None, github: CommitCierre | None, commit_inicial_sha: str | None
) -> ResultadoCaptura:
    """S9.6.4 pasos 3 y S9.6.5. `espejo = None` mientras no exista el espejo
    propio de actividad (Bloque 2): entonces GitHub es la unica fuente y la
    verificacion lo dice. Si ambas existen y difieren, `REVISAR` con los dos
    SHA y manda el espejo."""
    verificacion: dict[str, Any] = {
        "espejo_sha": espejo.sha if espejo is not None else None,
        "github_sha": github.sha if github is not None else None,
        "regla": "último commit cuya fecha de committer es anterior o igual a la fecha "
        "efectiva de cierre, en UTC",
    }
    elegido = espejo if espejo is not None else github
    if elegido is None:
        verificacion["motivo_sin_commits"] = "REPOSITORIO_VACIO"
        return ResultadoCaptura(
            EstadoVersion.SIN_COMMITS,
            TagEstado.NO_APLICA,
            TagMotivo.SIN_COMMITS,
            None,
            verificacion,
        )
    if commit_inicial_sha is not None and elegido.sha == commit_inicial_sha:
        verificacion["motivo_sin_commits"] = "SOLO_COMMIT_INICIAL"
        return ResultadoCaptura(
            EstadoVersion.SIN_COMMITS,
            TagEstado.NO_APLICA,
            TagMotivo.SIN_COMMITS,
            None,
            verificacion,
        )
    if espejo is not None and github is not None and espejo.sha != github.sha:
        return ResultadoCaptura(
            EstadoVersion.REVISAR, TagEstado.PENDIENTE, None, espejo, verificacion
        )
    return ResultadoCaptura(
        EstadoVersion.CAPTURADA_SIN_TAG, TagEstado.PENDIENTE, None, elegido, verificacion
    )


# --- S9.6.3: la etiqueta, eje aparte ---


def estado_tras_etiqueta(estado: EstadoVersion, tag_estado: TagEstado) -> EstadoVersion:
    """Invariante por implicaciones (RG-025): `CAPTURADA` exige `CREADO`.
    `REVISAR` es ortogonal a la etiqueta y no se mueve."""
    if estado == EstadoVersion.CAPTURADA_SIN_TAG and tag_estado == TagEstado.CREADO:
        return EstadoVersion.CAPTURADA
    if estado == EstadoVersion.CAPTURADA and tag_estado != TagEstado.CREADO:
        return EstadoVersion.CAPTURADA_SIN_TAG
    return estado


def tag_tras_rechazo(status_code: int, mensaje: str) -> tuple[TagEstado, TagMotivo, bool]:
    """`(tag_estado, tag_motivo, reintentar)`. Un limite de GitHub nunca es un
    fallo propio (Ley 5): la etiqueta sigue pendiente y se reintenta."""
    texto = mensaje.lower()
    if status_code == 429 or (
        status_code == 403 and ("rate limit" in texto or "secondary" in texto)
    ):
        return TagEstado.PENDIENTE, TagMotivo.LIMITE_API, True
    if status_code == 403 and "archived" in texto:
        return TagEstado.FALLIDO, TagMotivo.REPOSITORIO_ARCHIVADO, False
    if status_code in (401, 403):
        return TagEstado.FALLIDO, TagMotivo.PERMISO_INSUFICIENTE, False
    if status_code == 404:
        return TagEstado.FALLIDO, TagMotivo.REPOSITORIO_INACCESIBLE, False
    if status_code >= 500:
        return TagEstado.PENDIENTE, TagMotivo.DESCONOCIDO, True
    return TagEstado.FALLIDO, TagMotivo.DESCONOCIDO, False


# --- S9.8.2 (A-103): recaptura ante cambio de fecha ---


def motivo_de_supersede(
    *, corte_version: datetime, nueva_fecha: datetime | None
) -> MotivoVersion | None:
    """`None` = la fecha no cambio y la version sigue vigente. Una fecha que
    desaparece se trata como extendida: no hay nuevo corte que capturar."""
    if nueva_fecha is None or nueva_fecha > corte_version:
        return MotivoVersion.FECHA_EXTENDIDA
    if nueva_fecha < corte_version:
        return MotivoVersion.FECHA_ADELANTADA
    return None


def motivo_por_alcance(*, corte: datetime, entrada_en_servicio: datetime) -> MotivoVersion | None:
    """S9.6.8: la fecha vencio mientras la captura aun no estaba en servicio.
    Se captura igual con el corte original, y nunca se presenta como una
    captura ocurrida al cierre."""
    if corte < entrada_en_servicio:
        return MotivoVersion.CAPTURA_TARDIA_POR_ALCANCE
    return None


# --- S9.7.3 (A-173): «la entrega anterior», por sujeto ---


@dataclass(frozen=True)
class EntregaDelSujeto:
    entrega_id: Hashable
    orden: int
    due_at: datetime | None


def entrega_anterior(entregas: list[EntregaDelSujeto], *, actual: Hashable) -> Hashable | None:
    """La de mayor `orden` estrictamente menor con fecha vigente no nula para
    el sujeto y anterior a la de la entrega actual; si no cumple, se sigue
    bajando. Una sola implementacion para comparar, detectar SHA repetido y
    las ventanas de actividad."""
    por_id = {e.entrega_id: e for e in entregas}
    esta = por_id.get(actual)
    if esta is None or esta.due_at is None:
        return None
    for e in sorted(entregas, key=lambda x: x.orden, reverse=True):
        if e.orden < esta.orden and e.due_at is not None and e.due_at < esta.due_at:
            return e.entrega_id
    return None


# --- S9.7.3, S9.8.9, S9.10.3-S9.10.5: advertencias al capturar ---

_UMBRAL_FECHA_DESACTUALIZADA = timedelta(hours=6)
_UMBRAL_INCIDENCIA_FECHA = timedelta(hours=48)
_ESTADOS_SUJETO_VIGENTES = frozenset({"ACTIVO", "INVITADO"})


def advertencias_de_captura(
    *,
    sha: str | None,
    sha_entrega_anterior: str | None,
    estado_sujeto_al_cierre: str | None,
    fecha_calculada_en: datetime | None,
    ahora: datetime,
    captura_diferida_por_github: bool,
    usa_lfs: bool,
    tiene_submodulos: bool,
) -> tuple[list[AdvertenciaVersion], bool]:
    """`(advertencias, abrir_version_revisar)`. Ninguna cambia el estado de la
    version: son banderas para el corrector. El umbral de antiguedad de la
    fecha no es configurable (S9.10.3)."""
    salida: list[AdvertenciaVersion] = []
    if sha is not None and sha == sha_entrega_anterior:
        salida.append(AdvertenciaVersion.SIN_CAMBIOS_RESPECTO_A_LA_ANTERIOR)
    if (
        estado_sujeto_al_cierre is not None
        and estado_sujeto_al_cierre not in _ESTADOS_SUJETO_VIGENTES
    ):
        salida.append(AdvertenciaVersion.SUJETO_RETIRADO)
    antiguedad = ahora - fecha_calculada_en if fecha_calculada_en is not None else timedelta(0)
    if antiguedad > _UMBRAL_FECHA_DESACTUALIZADA:
        salida.append(AdvertenciaVersion.FECHAS_POSIBLEMENTE_DESACTUALIZADAS)
    if captura_diferida_por_github:
        salida.append(AdvertenciaVersion.CAPTURA_DIFERIDA_POR_GITHUB)
    if usa_lfs:
        salida.append(AdvertenciaVersion.USA_GIT_LFS)
    if tiene_submodulos:
        salida.append(AdvertenciaVersion.TIENE_SUBMODULOS)
    return salida, antiguedad > _UMBRAL_INCIDENCIA_FECHA


# --- S9.9: el acceso directo, por SHA y nunca por etiqueta ---


def url_arbol(full_name: str, sha: str) -> str:
    return f"https://github.com/{full_name}/tree/{sha}"


def url_comparacion(full_name: str, base: str, sha: str) -> str:
    return f"https://github.com/{full_name}/compare/{base}...{sha}"


def url_zip(full_name: str, sha: str) -> str:
    return f"https://github.com/{full_name}/archive/{sha}.zip"
