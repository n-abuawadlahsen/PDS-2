"""SPEC 09 S9.3-S9.5 (Etapa P8): fecha efectiva y huella de reglas."""

from __future__ import annotations

from datetime import UTC, datetime

from app.dominio.estados import AlcanceReglaFecha, OrigenFechaEfectiva
from app.dominio.fechas import (
    ReglaFechaDatos,
    fecha_efectiva_individual,
    formatear_fecha,
    huella_reglas,
)

_BASE_DUE = datetime(2026, 10, 1, 23, 59, tzinfo=UTC)


def _regla(
    ref: str,
    alcance: AlcanceReglaFecha,
    due_at: datetime | None,
    *,
    override: int | None = None,
    seccion: int | None = None,
    estudiantes: tuple[int, ...] = (),
    titulo: str | None = None,
) -> ReglaFechaDatos:
    return ReglaFechaDatos(
        ref=ref,
        alcance=alcance,
        canvas_override_id=override,
        seccion_canvas_id=seccion,
        grupo_canvas_id=None,
        estudiante_canvas_ids=estudiantes,
        due_at=due_at,
        unlock_at=None,
        lock_at=None,
        titulo=titulo,
    )


_BASE = _regla("base", AlcanceReglaFecha.BASE, _BASE_DUE)
_SECCION = _regla(
    "sec",
    AlcanceReglaFecha.SECCION,
    datetime(2026, 10, 3, 23, 59, tzinfo=UTC),
    override=1,
    seccion=101,
)


def test_sin_override_aplica_la_base():
    r = fecha_efectiva_individual(
        reglas=[_BASE], canvas_user_id=1, canvas_section_ids=frozenset({102})
    )
    assert (r.due_at_utc, r.origen, r.ambigua) == (_BASE_DUE, OrigenFechaEfectiva.BASE, False)


def test_override_de_seccion_gana_a_la_base():
    r = fecha_efectiva_individual(
        reglas=[_BASE, _SECCION], canvas_user_id=1, canvas_section_ids=frozenset({101})
    )
    assert r.origen == OrigenFechaEfectiva.SECCION
    assert r.regla_ref == "sec"


def test_ca_9_3_01_adhoc_gana_aunque_sea_anterior_a_la_seccion():
    adhoc = _regla(
        "adhoc",
        AlcanceReglaFecha.ESTUDIANTES,
        datetime(2026, 9, 28, tzinfo=UTC),
        override=2,
        estudiantes=(1,),
    )
    r = fecha_efectiva_individual(
        reglas=[_BASE, _SECCION, adhoc], canvas_user_id=1, canvas_section_ids=frozenset({101})
    )
    assert r.origen == OrigenFechaEfectiva.ADHOC
    assert r.due_at_utc == datetime(2026, 9, 28, tzinfo=UTC)


def test_ca_9_3_02_dos_secciones_gana_la_mas_tardia_y_queda_ambigua():
    otra = _regla(
        "sec2",
        AlcanceReglaFecha.SECCION,
        datetime(2026, 10, 5, tzinfo=UTC),
        override=3,
        seccion=102,
    )
    r = fecha_efectiva_individual(
        reglas=[_BASE, _SECCION, otra], canvas_user_id=1, canvas_section_ids=frozenset({101, 102})
    )
    assert r.due_at_utc == datetime(2026, 10, 5, tzinfo=UTC)
    assert r.ambigua is True


def test_ca_9_3_04_override_con_due_nulo_deja_sin_fecha_y_no_hereda_la_base():
    sin_fecha = _regla("sf", AlcanceReglaFecha.SECCION, None, override=4, seccion=101)
    r = fecha_efectiva_individual(
        reglas=[_BASE, sin_fecha], canvas_user_id=1, canvas_section_ids=frozenset({101})
    )
    assert r.due_at_utc is None
    assert r.origen == OrigenFechaEfectiva.SECCION


def test_ca_9_4_02_cambiar_solo_el_titulo_no_cambia_la_huella():
    con_titulo = _regla(
        "sec", AlcanceReglaFecha.SECCION, _SECCION.due_at, override=1, seccion=101, titulo="Otro"
    )
    assert huella_reglas([_BASE, _SECCION]) == huella_reglas([con_titulo, _BASE])


def test_la_huella_cambia_con_la_fecha():
    movida = _regla(
        "sec", AlcanceReglaFecha.SECCION, datetime(2026, 10, 4, tzinfo=UTC), override=1, seccion=101
    )
    assert huella_reglas([_BASE, _SECCION]) != huella_reglas([_BASE, movida])


def test_formato_de_fecha_con_zona_escrita():
    assert formatear_fecha(_BASE_DUE, "America/Santiago") == "01-10-2026 20:59 (America/Santiago)"
    assert formatear_fecha(None, "America/Santiago") == "sin fecha de cierre"
