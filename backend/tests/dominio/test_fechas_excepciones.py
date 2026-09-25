"""Etapa F3 (SPEC 09 S9.3-S9.5; A-054, A-055, A-056, A-114): excepciones de
fecha completas, reglas puras."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.dominio.estados import AlcanceReglaFecha, OrigenFechaEfectiva
from app.dominio.fechas import (
    IntegranteFecha,
    ReglaFechaDatos,
    cadencia_sync_fechas,
    candidatas_fecha,
    discrepancias_aceleracion,
    fecha_efectiva_grupal,
    fecha_efectiva_individual,
    incidencia_de_fecha,
    overrides_no_interpretables,
)

_BASE_DUE = datetime(2026, 10, 1, 23, 59, tzinfo=UTC)


def _regla(
    ref: str,
    alcance: AlcanceReglaFecha,
    due_at: datetime | None,
    *,
    override: int | None = None,
    seccion: int | None = None,
    grupo: int | None = None,
    estudiantes: tuple[int, ...] = (),
) -> ReglaFechaDatos:
    return ReglaFechaDatos(
        ref=ref,
        alcance=alcance,
        canvas_override_id=override,
        seccion_canvas_id=seccion,
        grupo_canvas_id=grupo,
        estudiante_canvas_ids=estudiantes,
        due_at=due_at,
        unlock_at=None,
        lock_at=None,
        titulo=None,
    )


_BASE = _regla("base", AlcanceReglaFecha.BASE, _BASE_DUE)
_SEC_101 = _regla(
    "s101", AlcanceReglaFecha.SECCION, _BASE_DUE + timedelta(days=1), override=1, seccion=101
)
_SEC_102 = _regla(
    "s102", AlcanceReglaFecha.SECCION, _BASE_DUE + timedelta(days=2), override=2, seccion=102
)
_ADHOC = _regla(
    "adhoc",
    AlcanceReglaFecha.ESTUDIANTES,
    _BASE_DUE - timedelta(days=1),
    override=3,
    estudiantes=(2001,),
)


def test_ca_9_3_01_adhoc_mas_restrictivo_gana_igual():
    r = fecha_efectiva_individual(
        reglas=[_BASE, _SEC_101, _ADHOC], canvas_user_id=2001, canvas_section_ids=frozenset({101})
    )
    assert (r.due_at_utc, r.origen, r.ambigua) == (_ADHOC.due_at, OrigenFechaEfectiva.ADHOC, False)


def test_ca_9_3_02_dos_secciones_abren_estudiante_en_dos_secciones():
    r = fecha_efectiva_individual(
        reglas=[_BASE, _SEC_101, _SEC_102],
        canvas_user_id=2001,
        canvas_section_ids=frozenset({101, 102}),
    )
    assert r.ambigua and r.due_at_utc == _SEC_102.due_at
    tipo, detalle = incidencia_de_fecha(r) or ("", {})
    assert tipo == "ESTUDIANTE_EN_DOS_SECCIONES"
    assert detalle["origen"] == "SECCION"


def test_ca_9_3_03_grupo_heterogeneo_abre_discrepancia_con_integrantes():
    r = fecha_efectiva_grupal(
        reglas=[_BASE, _SEC_101, _SEC_102],
        canvas_group_id=601,
        integrantes=[
            IntegranteFecha(canvas_user_id=2001, canvas_section_ids=frozenset({101})),
            IntegranteFecha(canvas_user_id=2004, canvas_section_ids=frozenset({102})),
        ],
    )
    assert r is not None
    tipo, detalle = incidencia_de_fecha(r) or ("", {})
    assert tipo == "DISCREPANCIA_FECHAS"
    assert detalle["motivo"] == "GRUPO_HETEROGENEO"
    assert {i["canvas_user_id"] for i in detalle["integrantes"]} == {2001, 2004}


def test_empate_de_dos_adhoc_es_discrepancia_de_fechas():
    otro = _regla(
        "adhoc2",
        AlcanceReglaFecha.ESTUDIANTES,
        _BASE_DUE + timedelta(hours=5),
        override=4,
        estudiantes=(2001,),
    )
    r = fecha_efectiva_individual(
        reglas=[_BASE, _ADHOC, otro], canvas_user_id=2001, canvas_section_ids=frozenset()
    )
    assert r.ambigua and r.due_at_utc == otro.due_at
    tipo, detalle = incidencia_de_fecha(r) or ("", {})
    assert (tipo, detalle["motivo"]) == ("DISCREPANCIA_FECHAS", "EMPATE_EN_NIVEL")


def test_sin_ambiguedad_no_hay_incidencia():
    r = fecha_efectiva_individual(
        reglas=[_BASE], canvas_user_id=2001, canvas_section_ids=frozenset()
    )
    assert incidencia_de_fecha(r) is None


def test_ca_9_5_03_candidatas_listan_todas_las_reglas_que_alcanzan_al_sujeto():
    candidatas = candidatas_fecha(
        reglas=[_BASE, _SEC_101, _SEC_102, _ADHOC],
        integrantes=[IntegranteFecha(canvas_user_id=2001, canvas_section_ids=frozenset({101}))],
        canvas_group_id=None,
    )
    assert [(c.origen, c.canvas_override_id) for c in candidatas] == [
        (OrigenFechaEfectiva.ADHOC, 3),
        (OrigenFechaEfectiva.SECCION, 1),
        (OrigenFechaEfectiva.BASE, None),
    ]


def test_overrides_no_interpretables():
    grupo_ajeno = _regla("g", AlcanceReglaFecha.GRUPO, _BASE_DUE, override=5, grupo=999)
    seccion_desconocida = _regla("s", AlcanceReglaFecha.SECCION, _BASE_DUE, override=6, seccion=555)
    nadie_inscrito = _regla(
        "e", AlcanceReglaFecha.ESTUDIANTES, _BASE_DUE, override=7, estudiantes=(8888, 9999)
    )
    alguno_inscrito = _regla(
        "e2", AlcanceReglaFecha.ESTUDIANTES, _BASE_DUE, override=8, estudiantes=(8888, 2001)
    )
    hallazgos = overrides_no_interpretables(
        [_BASE, _SEC_101, grupo_ajeno, seccion_desconocida, nadie_inscrito, alguno_inscrito],
        secciones_conocidas={101, 102},
        estudiantes_conocidos={2001, 2002},
        grupos_de_la_tarea={601, 602},
    )
    assert {(h.canvas_override_id, h.motivo) for h in hallazgos} == {
        (5, "GRUPO_FUERA_DEL_CONJUNTO"),
        (6, "SECCION_DESCONOCIDA"),
        (7, "ESTUDIANTES_NO_INSCRITOS"),
    }
    # En una tarea individual el nivel de grupo no se evalua: no es un hallazgo.
    individual = overrides_no_interpretables(
        [grupo_ajeno],
        secciones_conocidas=set(),
        estudiantes_conocidos=set(),
        grupos_de_la_tarea=None,
    )
    assert individual == []


def test_discrepancia_entre_aceleracion_y_autoridad():
    autoridad = {1: _BASE_DUE, 2: _BASE_DUE + timedelta(days=1)}
    assert discrepancias_aceleracion(aceleracion=None, autoridad=autoridad) == []
    assert discrepancias_aceleracion(aceleracion=dict(autoridad), autoridad=autoridad) == []
    # La aceleracion no trae un override y trae otro con otra fecha: manda la autoridad.
    distintas = discrepancias_aceleracion(
        aceleracion={2: _BASE_DUE, 3: _BASE_DUE}, autoridad=autoridad
    )
    assert distintas == [1, 2, 3]


def test_cadencia_de_un_minuto_en_las_dos_horas_previas_a_un_cierre():
    ahora = _BASE_DUE - timedelta(hours=3)
    assert cadencia_sync_fechas(ahora=ahora, proximos_cierres=[_BASE_DUE]) == 300
    ahora = _BASE_DUE - timedelta(minutes=90)
    assert cadencia_sync_fechas(ahora=ahora, proximos_cierres=[_BASE_DUE]) == 60
    # Un cierre ya pasado no mantiene la cadencia alta.
    ahora = _BASE_DUE + timedelta(minutes=1)
    assert cadencia_sync_fechas(ahora=ahora, proximos_cierres=[_BASE_DUE]) == 300
