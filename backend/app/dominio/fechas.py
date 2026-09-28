"""Fecha efectiva por `(entrega, sujeto)` y huella de reglas (SPEC 09 S9.3-S9.4;
A-054, A-055, A-056, A-082). Etapa P8 la usa en modo lectura; F1 anade el sujeto
grupal (S9.3.3): la cadena de cada integrante `accepted` y el maximo.
"""

from __future__ import annotations

import hashlib
from collections.abc import Hashable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.dominio.estados import AlcanceReglaFecha, OrigenFechaEfectiva


@dataclass(frozen=True)
class ReglaFechaDatos:
    """Copia cruda de una regla de Canvas: la fila `BASE` o un override."""

    ref: Hashable
    alcance: AlcanceReglaFecha
    canvas_override_id: int | None
    seccion_canvas_id: int | None
    grupo_canvas_id: int | None
    estudiante_canvas_ids: tuple[int, ...]
    due_at: datetime | None
    unlock_at: datetime | None
    lock_at: datetime | None
    titulo: str | None


@dataclass(frozen=True)
class ResultadoFecha:
    """`due_at_utc = None` es «sin fecha de cierre» (S9.3.2): no se inventa una.

    `fechas_integrantes` solo se llena para un sujeto grupal: la fecha que la
    cadena dio a cada integrante, que es el detalle de `GRUPO_HETEROGENEO`."""

    due_at_utc: datetime | None
    origen: OrigenFechaEfectiva
    regla_ref: Hashable | None
    ambigua: bool
    fechas_integrantes: tuple[tuple[int, datetime | None], ...] = ()


@dataclass(frozen=True)
class IntegranteFecha:
    canvas_user_id: int
    canvas_section_ids: frozenset[int]


def _elegir_mas_tardia(candidatas: list[ReglaFechaDatos]) -> tuple[ReglaFechaDatos, bool]:
    """Empate dentro de un nivel: gana la mas tardia y la fila queda ambigua
    si habia fechas distintas (A-055). Una regla sin `due_at` no gana a una con fecha."""
    con_fecha = [c for c in candidatas if c.due_at is not None]
    if not con_fecha:
        return candidatas[0], len(candidatas) > 1
    ganadora = max(con_fecha, key=lambda c: c.due_at)  # type: ignore[arg-type,return-value]
    distintas = {c.due_at for c in candidatas}
    return ganadora, len(distintas) > 1


def fecha_efectiva_individual(
    *,
    reglas: list[ReglaFechaDatos],
    canvas_user_id: int,
    canvas_section_ids: frozenset[int],
    canvas_group_id: int | None = None,
) -> ResultadoFecha:
    """S9.3.2, cadena estricta entre niveles: extension individual, grupo,
    seccion, base. El nivel de grupo solo se evalua en tareas grupales, es
    decir, cuando el llamador pasa `canvas_group_id`.

    Un override aplicable con `due_at` nulo produce «sin fecha», no hereda la
    base (CA-9.3-04)."""
    niveles: tuple[tuple[OrigenFechaEfectiva, list[ReglaFechaDatos]], ...] = (
        (
            OrigenFechaEfectiva.ADHOC,
            [
                r
                for r in reglas
                if r.alcance == AlcanceReglaFecha.ESTUDIANTES
                and canvas_user_id in r.estudiante_canvas_ids
            ],
        ),
        (
            OrigenFechaEfectiva.GRUPO,
            [
                r
                for r in reglas
                if canvas_group_id is not None
                and r.alcance == AlcanceReglaFecha.GRUPO
                and r.grupo_canvas_id == canvas_group_id
            ],
        ),
        (
            OrigenFechaEfectiva.SECCION,
            [
                r
                for r in reglas
                if r.alcance == AlcanceReglaFecha.SECCION
                and r.seccion_canvas_id in canvas_section_ids
            ],
        ),
        (
            OrigenFechaEfectiva.BASE,
            [r for r in reglas if r.alcance == AlcanceReglaFecha.BASE],
        ),
    )
    for origen, candidatas in niveles:
        if candidatas:
            ganadora, ambigua = _elegir_mas_tardia(candidatas)
            return ResultadoFecha(
                due_at_utc=ganadora.due_at, origen=origen, regla_ref=ganadora.ref, ambigua=ambigua
            )
    return ResultadoFecha(
        due_at_utc=None, origen=OrigenFechaEfectiva.BASE, regla_ref=None, ambigua=False
    )


def fecha_efectiva_grupal(
    *,
    reglas: list[ReglaFechaDatos],
    canvas_group_id: int,
    integrantes: list[IntegranteFecha],
) -> ResultadoFecha | None:
    """S9.3.3 (Q-2.4-05, Q-2.4-40): la cadena de S9.3.2 para cada integrante
    `accepted`, y el **maximo** de las fechas resultantes -- capturar antes de
    tiempo destruye trabajo legitimo. Un integrante sin fecha no aporta
    candidato ni anula al resto; si ninguno aporta, el grupo queda sin fecha.
    Fechas distintas entre integrantes dejan la fila `ambigua`.

    `None` = el grupo no tiene integrantes que cuenten: no hay fecha que
    calcular (el sujeto no deberia estar activo)."""
    if not integrantes:
        return None
    por_integrante = [
        (
            i.canvas_user_id,
            fecha_efectiva_individual(
                reglas=reglas,
                canvas_user_id=i.canvas_user_id,
                canvas_section_ids=i.canvas_section_ids,
                canvas_group_id=canvas_group_id,
            ),
        )
        for i in integrantes
    ]
    fechas = tuple((uid, r.due_at_utc) for uid, r in por_integrante)
    con_fecha = [(uid, r) for uid, r in por_integrante if r.due_at_utc is not None]
    if not con_fecha:
        primero = por_integrante[0][1]
        return ResultadoFecha(
            due_at_utc=None,
            origen=primero.origen,
            regla_ref=primero.regla_ref,
            ambigua=False,
            fechas_integrantes=fechas,
        )
    _, ganador = max(con_fecha, key=lambda par: par[1].due_at_utc)  # type: ignore[arg-type,return-value]
    distintas = {r.due_at_utc for _, r in con_fecha}
    return ResultadoFecha(
        due_at_utc=ganador.due_at_utc,
        origen=ganador.origen,
        regla_ref=ganador.regla_ref,
        ambigua=len(distintas) > 1 or any(r.ambigua for _, r in con_fecha),
        fechas_integrantes=fechas,
    )


def _instante(valor: datetime | None) -> str:
    if valor is None:
        return "-"
    return valor.astimezone(UTC).replace(microsecond=0).isoformat()


def huella_reglas(reglas: list[ReglaFechaDatos]) -> bytes:
    """S9.4.2 (A-056): SHA-256 del conjunto canonico. `BASE` primero, luego por
    `canvas_override_id`; ids de estudiante ordenados; instantes en UTC al
    segundo; `titulo` fuera, porque es cosmetico (CA-9.4-02)."""
    ordenadas = sorted(
        reglas,
        key=lambda r: (r.alcance != AlcanceReglaFecha.BASE, r.canvas_override_id or 0),
    )
    lineas = [
        "|".join(
            (
                r.alcance.value,
                str(r.canvas_override_id or ""),
                str(r.seccion_canvas_id or ""),
                str(r.grupo_canvas_id or ""),
                ",".join(str(i) for i in sorted(r.estudiante_canvas_ids)),
                _instante(r.due_at),
                _instante(r.unlock_at),
                _instante(r.lock_at),
            )
        )
        for r in ordenadas
    ]
    return hashlib.sha256("\n".join(lineas).encode()).digest()


# --- Etapa F3: excepciones completas (S9.3.1, S9.3.5, S9.4.4, S9.5) ---


@dataclass(frozen=True)
class CandidataFecha:
    """Una regla que alcanza al sujeto, con el nivel en que lo alcanza. Es lo
    que despliega la insignia «fecha ambigua» (CA-9.5-03)."""

    origen: OrigenFechaEfectiva
    regla_ref: Hashable
    canvas_override_id: int | None
    due_at: datetime | None
    canvas_user_id: int | None


_ORDEN_ORIGEN = {
    OrigenFechaEfectiva.ADHOC: 0,
    OrigenFechaEfectiva.GRUPO: 1,
    OrigenFechaEfectiva.SECCION: 2,
    OrigenFechaEfectiva.BASE: 3,
}


def candidatas_fecha(
    *,
    reglas: list[ReglaFechaDatos],
    integrantes: list[IntegranteFecha],
    canvas_group_id: int | None,
) -> list[CandidataFecha]:
    """Todas las reglas que alcanzan al sujeto, de mayor a menor precedencia.
    Un sujeto individual pasa un solo integrante; uno grupal, a los suyos."""
    vistas: dict[Hashable, CandidataFecha] = {}
    for integrante in integrantes:
        for r in reglas:
            origen: OrigenFechaEfectiva | None = None
            if (
                r.alcance == AlcanceReglaFecha.ESTUDIANTES
                and integrante.canvas_user_id in r.estudiante_canvas_ids
            ):
                origen = OrigenFechaEfectiva.ADHOC
            elif (
                r.alcance == AlcanceReglaFecha.GRUPO
                and canvas_group_id is not None
                and r.grupo_canvas_id == canvas_group_id
            ):
                origen = OrigenFechaEfectiva.GRUPO
            elif (
                r.alcance == AlcanceReglaFecha.SECCION
                and r.seccion_canvas_id in integrante.canvas_section_ids
            ):
                origen = OrigenFechaEfectiva.SECCION
            elif r.alcance == AlcanceReglaFecha.BASE:
                origen = OrigenFechaEfectiva.BASE
            if origen is None or r.ref in vistas:
                continue
            vistas[r.ref] = CandidataFecha(
                origen=origen,
                regla_ref=r.ref,
                canvas_override_id=r.canvas_override_id,
                due_at=r.due_at,
                canvas_user_id=(
                    integrante.canvas_user_id if origen == OrigenFechaEfectiva.ADHOC else None
                ),
            )
    return sorted(
        vistas.values(),
        key=lambda c: (_ORDEN_ORIGEN[c.origen], c.canvas_override_id or 0),
    )


def incidencia_de_fecha(resultado: ResultadoFecha) -> tuple[str, dict[str, object]] | None:
    """S9.3.2-S9.3.3: una fecha ambigua siempre abre incidencia. Devuelve
    `(tipo, detalle)` o `None` si la fecha no es ambigua."""
    if not resultado.ambigua:
        return None
    distintas = {f for _, f in resultado.fechas_integrantes if f is not None}
    if len(distintas) > 1:
        return (
            "DISCREPANCIA_FECHAS",
            {
                "motivo": "GRUPO_HETEROGENEO",
                "integrantes": [
                    {"canvas_user_id": uid, "due_at": _instante(f)}
                    for uid, f in resultado.fechas_integrantes
                ],
            },
        )
    if resultado.origen == OrigenFechaEfectiva.SECCION:
        return ("ESTUDIANTE_EN_DOS_SECCIONES", {"origen": resultado.origen.value})
    return ("DISCREPANCIA_FECHAS", {"motivo": "EMPATE_EN_NIVEL", "origen": resultado.origen.value})


@dataclass(frozen=True)
class OverrideNoInterpretable:
    regla_ref: Hashable
    canvas_override_id: int | None
    motivo: str


def overrides_no_interpretables(
    reglas: list[ReglaFechaDatos],
    *,
    secciones_conocidas: set[int],
    estudiantes_conocidos: set[int],
    grupos_de_la_tarea: set[int] | None,
) -> list[OverrideNoInterpretable]:
    """S9.3.5: overrides con datos sucios. Ninguno contribuye a la fecha --el
    algoritmo ya no los empareja con nadie--; esto solo los nombra para la
    incidencia `OVERRIDE_NO_INTERPRETABLE`. `grupos_de_la_tarea = None` en una
    tarea individual, donde el nivel de grupo no se evalua (A-055)."""
    hallazgos = []
    for r in reglas:
        motivo = None
        if (
            r.alcance == AlcanceReglaFecha.SECCION
            and r.seccion_canvas_id not in secciones_conocidas
        ):
            motivo = "SECCION_DESCONOCIDA"
        elif (
            r.alcance == AlcanceReglaFecha.ESTUDIANTES
            and r.estudiante_canvas_ids
            and not set(r.estudiante_canvas_ids) & estudiantes_conocidos
        ):
            motivo = "ESTUDIANTES_NO_INSCRITOS"
        elif (
            r.alcance == AlcanceReglaFecha.GRUPO
            and grupos_de_la_tarea is not None
            and r.grupo_canvas_id not in grupos_de_la_tarea
        ):
            motivo = "GRUPO_FUERA_DEL_CONJUNTO"
        if motivo is not None:
            hallazgos.append(
                OverrideNoInterpretable(
                    regla_ref=r.ref, canvas_override_id=r.canvas_override_id, motivo=motivo
                )
            )
    return hallazgos


def discrepancias_aceleracion(
    *, aceleracion: dict[int, datetime | None] | None, autoridad: dict[int, datetime | None]
) -> list[int]:
    """S9.3.1 (A-054): ids de override en que la fuente de aceleracion y la de
    autoridad no coinciden. Manda siempre la autoridad; esto solo abre la
    incidencia. `aceleracion = None` = la instancia no la devolvio."""
    if aceleracion is None:
        return []
    ids = set(aceleracion) | set(autoridad)
    return sorted(
        i
        for i in ids
        if i not in aceleracion
        or i not in autoridad
        or _instante(aceleracion[i]) != _instante(autoridad[i])
    )


CADENCIA_NORMAL_SEGUNDOS = 300
CADENCIA_CRITICA_SEGUNDOS = 60
_VENTANA_CRITICA = timedelta(hours=2)


def cadencia_sync_fechas(*, ahora: datetime, proximos_cierres: list[datetime]) -> int:
    """S9.4.4 (A-114): 5 minutos; 1 minuto dentro de las 2 horas previas a una
    fecha efectiva de cierre."""
    if any(ahora <= cierre <= ahora + _VENTANA_CRITICA for cierre in proximos_cierres):
        return CADENCIA_CRITICA_SEGUNDOS
    return CADENCIA_NORMAL_SEGUNDOS


def formatear_fecha(instante: datetime | None, zona_horaria: str) -> str:
    """S9.5: `dd-MM-yyyy HH:mm (Zona)`, reloj de 24 h, zona del curso escrita."""
    if instante is None:
        return "sin fecha de cierre"
    local = instante.astimezone(ZoneInfo(zona_horaria))
    return f"{local.strftime('%d-%m-%Y %H:%M')} ({zona_horaria})"
