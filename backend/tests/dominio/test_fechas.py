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


# --- Etapa F1: sujeto grupal (S9.3.3, Q-2.4-05) ---


def _integrante(uid: int, *secciones: int):
    from app.dominio.fechas import IntegranteFecha

    return IntegranteFecha(canvas_user_id=uid, canvas_section_ids=frozenset(secciones))


def test_f1_grupo_toma_el_maximo_de_sus_integrantes_y_queda_ambiguo():
    from app.dominio.fechas import fecha_efectiva_grupal

    # CA-9.3-03: integrantes en secciones con fechas distintas, sin ADHOC propio.
    r = fecha_efectiva_grupal(
        reglas=[_BASE, _SECCION],
        canvas_group_id=601,
        integrantes=[_integrante(1, 101), _integrante(2, 102)],
    )
    assert r is not None
    assert r.due_at_utc == _SECCION.due_at
    assert r.origen == OrigenFechaEfectiva.SECCION
    assert r.ambigua is True
    assert dict(r.fechas_integrantes) == {1: _SECCION.due_at, 2: _BASE_DUE}


def test_f1_override_de_grupo_gana_a_la_seccion_y_pierde_con_adhoc():
    from app.dominio.fechas import fecha_efectiva_grupal

    grupo = ReglaFechaDatos(
        ref="grp",
        alcance=AlcanceReglaFecha.GRUPO,
        canvas_override_id=2,
        seccion_canvas_id=None,
        grupo_canvas_id=601,
        estudiante_canvas_ids=(),
        due_at=datetime(2026, 10, 5, 23, 59, tzinfo=UTC),
        unlock_at=None,
        lock_at=None,
        titulo=None,
    )
    r = fecha_efectiva_grupal(
        reglas=[_BASE, _SECCION, grupo], canvas_group_id=601, integrantes=[_integrante(1, 101)]
    )
    assert r is not None
    assert (r.due_at_utc, r.origen, r.ambigua) == (grupo.due_at, OrigenFechaEfectiva.GRUPO, False)
    # Otro grupo: el override no le alcanza.
    otro = fecha_efectiva_grupal(
        reglas=[_BASE, grupo], canvas_group_id=602, integrantes=[_integrante(1, 101)]
    )
    assert otro is not None and otro.origen == OrigenFechaEfectiva.BASE
    adhoc = _regla(
        "adhoc",
        AlcanceReglaFecha.ESTUDIANTES,
        datetime(2026, 10, 2, 12, 0, tzinfo=UTC),
        override=3,
        estudiantes=(1,),
    )
    r2 = fecha_efectiva_grupal(
        reglas=[_BASE, grupo, adhoc], canvas_group_id=601, integrantes=[_integrante(1, 101)]
    )
    assert r2 is not None and r2.origen == OrigenFechaEfectiva.ADHOC


def test_f1_integrante_sin_fecha_no_anula_al_resto_y_grupo_vacio_no_tiene_fecha():
    from app.dominio.fechas import fecha_efectiva_grupal

    sin_fecha = _regla("nulo", AlcanceReglaFecha.ESTUDIANTES, None, override=9, estudiantes=(2,))
    r = fecha_efectiva_grupal(
        reglas=[_BASE, sin_fecha],
        canvas_group_id=601,
        integrantes=[_integrante(1, 101), _integrante(2, 101)],
    )
    assert r is not None and r.due_at_utc == _BASE_DUE
    assert fecha_efectiva_grupal(reglas=[_BASE], canvas_group_id=601, integrantes=[]) is None
