"""Fecha efectiva por `(entrega, sujeto)` y huella de reglas (SPEC 09 S9.3-S9.4;
A-054, A-055, A-056, A-082). Etapa P8 la usa en modo lectura; F1 anade el sujeto
grupal (S9.3.3): la cadena de cada integrante `accepted` y el maximo.
"""

from __future__ import annotations

import hashlib
from collections.abc import Hashable
from dataclasses import dataclass
from datetime import UTC, datetime
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


def formatear_fecha(instante: datetime | None, zona_horaria: str) -> str:
    """S9.5: `dd-MM-yyyy HH:mm (Zona)`, reloj de 24 h, zona del curso escrita."""
    if instante is None:
        return "sin fecha de cierre"
    local = instante.astimezone(ZoneInfo(zona_horaria))
    return f"{local.strftime('%d-%m-%Y %H:%M')} ({zona_horaria})"
