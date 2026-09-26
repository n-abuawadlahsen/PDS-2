"""SPEC 11 S11.2 y SPEC 08 S8.10 (Etapa P8): plantillas, clave y guardas."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.dominio.comunicaciones import (
    INVITACION_ACEPTADA,
    REPOSITORIO_DISPONIBLE,
    PlantillaInvalida,
    clave_idempotencia,
    guardas_outbox,
    instrucciones_de_acceso,
    renderizar,
)
from app.dominio.estados import EstadoMensaje

_VALORES = {
    "estudiante.nombre": "Ana Pérez",
    "tarea.nombre": "Tarea 1",
    "curso.nombre": "Desarrollo de Software",
    "organizacion.nombre": "PDS-2",
    "repositorio.nombre": "pds-2-t1-e2001-perez-ana",
    "repositorio.url": "https://github.com/PDS-2/pds-2-t1-e2001-perez-ana",
    "acceso.instrucciones": instrucciones_de_acceso(via_invitacion=True, invitacion_url=None),
    "entrega.fecha_cierre": "01-10-2026 20:59 (America/Santiago)",
    "cuenta_github.login": "ana-perez",
}


def test_repositorio_disponible_dice_lo_que_exige_a_127():
    cuerpo = renderizar(REPOSITORIO_DISPONIBLE.cuerpo, REPOSITORIO_DISPONIBLE, _VALORES)
    assert "PDS-2" in cuerpo
    assert "pds-2-t1-e2001-perez-ana" in cuerpo
    assert "https://github.com/PDS-2/pds-2-t1-e2001-perez-ana" in cuerpo
    assert "no encontrado" in cuerpo
    assert "(America/Santiago)" in cuerpo
    assert "spam" in cuerpo
    assert "{{" not in cuerpo


def test_acceso_directo_no_habla_de_invitacion_pendiente():
    texto = instrucciones_de_acceso(via_invitacion=False, invitacion_url=None)
    assert "no necesitas aceptar" in texto


def test_sin_url_del_repositorio_el_mensaje_no_se_construye():
    valores = dict(_VALORES)
    valores["repositorio.url"] = ""
    with pytest.raises(PlantillaInvalida):
        renderizar(REPOSITORIO_DISPONIBLE.cuerpo, REPOSITORIO_DISPONIBLE, valores)


def test_variable_desconocida_se_rechaza():
    with pytest.raises(PlantillaInvalida):
        renderizar("{{version.sha_corto}}", INVITACION_ACEPTADA, _VALORES)


def test_la_clave_es_por_persona():
    comun = {
        "canal": "CANVAS_CONVERSACION",
        "plantilla": "repositorio_disponible",
        "entidad": "repo-1",
    }
    ana = clave_idempotencia(destinatario="2001", **comun)
    beto = clave_idempotencia(destinatario="2002", **comun)
    assert ana != beto
    assert ana == clave_idempotencia(destinatario="2001", **comun)
    assert ana != clave_idempotencia(destinatario="2001", generacion=2, **comun)


def test_guardas_en_orden():
    ahora = datetime(2026, 9, 15, tzinfo=UTC)
    assert guardas_outbox(ahora=ahora, caduca_en=None, estado_estudiante="ACTIVO") is None
    assert guardas_outbox(
        ahora=ahora, caduca_en=ahora - timedelta(minutes=1), estado_estudiante="RETIRADO"
    ) == (
        EstadoMensaje.CADUCADO,
        "CADUCIDAD_ALCANZADA",
    )
    assert guardas_outbox(ahora=ahora, caduca_en=None, estado_estudiante="RETIRADO") == (
        EstadoMensaje.SUPRIMIDO,
        "MATRICULA_NO_ACTIVA",
    )
    assert guardas_outbox(ahora=ahora, caduca_en=None, estado_estudiante="INVITADO") is None


# --- Etapa F10 ---

from zoneinfo import ZoneInfo  # noqa: E402

from app.dominio.comunicaciones import (  # noqa: E402
    EVENTOS,
    MOTIVOS_POR_ESTADO,
    PLANTILLAS,
    TOPE_DIARIO_AUTOMATICOS,
    anuncio_cambio_fecha,
    cuenta_para_tope,
    exento_de_franja,
    nombra_a_terceros,
    siguiente_apertura,
    validar_plantilla,
    variables_de,
)
from app.dominio.estados import MotivoEstadoMensaje  # noqa: E402


def _g(**kw):
    base = {
        "ahora": datetime(2026, 10, 3, 12, tzinfo=UTC),
        "caduca_en": None,
        "estado_estudiante": "ACTIVO",
    }
    base.update(kw)
    return guardas_outbox(**base)


def test_las_siete_guardas_en_su_orden():
    ahora = datetime(2026, 10, 3, 12, tzinfo=UTC)
    # CA-11.2-05: caducado con la regla apagada es CADUCADO, nunca SUPRIMIDO.
    assert _g(caduca_en=ahora, regla_activa=False)[1] == "CADUCIDAD_ALCANZADA"
    assert _g(estado_estudiante="CONCLUIDO")[1] == "MATRICULA_NO_ACTIVA"
    assert _g(
        automatico=True, supresion_alcance="TODAS_AUTOMATICAS", evento="repositorio_disponible"
    )[1] == ("SUPRESION_POR_ESTUDIANTE")
    # La supresion solo alcanza a los automaticos, y SOLO_RECORDATORIOS a los recordatorios.
    assert _g(automatico=False, supresion_alcance="TODAS_AUTOMATICAS") is None
    assert (
        _g(automatico=True, supresion_alcance="SOLO_RECORDATORIOS", evento="repositorio_disponible")
        is None
    )
    assert _g(automatico=True, supresion_alcance="SOLO_RECORDATORIOS", evento="proximidad_cierre")[
        1
    ] == ("SUPRESION_POR_ESTUDIANTE")
    assert _g(regla_activa=False)[1] == "REGLA_DESACTIVADA"
    assert _g(modo_escritura="SOLO_LECTURA")[1] == "MODO_SOLO_LECTURA"
    assert (
        _g(comunicaciones_salientes="SUSPENDIDAS", canal="CANVAS_CONVERSACION")[1]
        == "SUSPENSION_DE_CURSO"
    )
    # La suspension del curso nunca detiene el correo.
    assert _g(comunicaciones_salientes="SUSPENDIDAS", canal="CORREO") is None
    assert _g(en_ventana_supresion=True)[1] == "VENTANA_TRAS_RESTAURACION"


def test_invitado_recibe_el_repositorio_pero_no_recordatorios():
    # CA-11.7-05
    assert (
        _g(estado_estudiante="INVITADO", automatico=True, evento="repositorio_disponible") is None
    )
    assert _g(estado_estudiante="INVITADO", automatico=True, evento="proximidad_cierre")[1] == (
        "MATRICULA_NO_ACTIVA"
    )


def test_catalogo_cerrado_y_motivos_sin_repetir():
    # CA-11.6-01 y CA-11.2-04
    assert len(EVENTOS) == 7 and "salida_de_grupo" not in EVENTOS
    assert [e.clave for e in EVENTOS.values() if e.alcance == "CURSO"] == ["recordatorio_mapeo"]
    assert not EVENTOS["correccion_publicada"].activo_por_defecto
    todos = [m for ms in MOTIVOS_POR_ESTADO.values() for m in ms]
    assert len(todos) == len(set(todos)) == 20
    assert set(todos) == {m.value for m in MotivoEstadoMensaje}


def test_franja_horaria_y_exenciones():
    zona = ZoneInfo("America/Santiago")
    madrugada = datetime(2026, 10, 3, 3, 0, tzinfo=zona)
    assert siguiente_apertura(madrugada) == datetime(2026, 10, 3, 8, 0, tzinfo=zona)
    noche = datetime(2026, 10, 3, 22, 30, tzinfo=zona)
    assert siguiente_apertura(noche) == datetime(2026, 10, 4, 8, 0, tzinfo=zona)
    assert siguiente_apertura(datetime(2026, 10, 3, 15, 0, tzinfo=zona)) is None
    assert exento_de_franja(evento="proximidad_cierre", origen="AUTOMATICO", ventana="H6")
    assert not exento_de_franja(evento="proximidad_cierre", origen="AUTOMATICO", ventana="H48")
    assert exento_de_franja(evento="MANUAL", origen="MANUAL", ventana=None)


def test_tope_solo_para_automaticos_a_estudiantes():
    assert TOPE_DIARIO_AUTOMATICOS == 3
    assert cuenta_para_tope(
        evento="proximidad_cierre", origen="AUTOMATICO", canal="CANVAS_CONVERSACION"
    )
    assert not cuenta_para_tope(evento="MANUAL", origen="MANUAL", canal="CANVAS_CONVERSACION")
    assert not cuenta_para_tope(
        evento="cambio_de_fecha", origen="AUTOMATICO", canal="CANVAS_ANUNCIO"
    )


def test_validar_plantilla_nombra_lo_que_falta():
    # CA-11.2-07
    errores = validar_plantilla(
        clave="repositorio_disponible",
        canal="CANVAS_CONVERSACION",
        asunto="Tu repositorio",
        cuerpo="Hola {{estudiante.nombre}}: {{repositorio.nombre}} en {{organizacion.nombre}}",
    )
    assert errores == ["falta la variable obligatoria {{repositorio.url}}"]
    assert "sin etiquetas HTML" in " ".join(
        validar_plantilla(
            clave="invitacion_aceptada",
            canal="CANVAS_CONVERSACION",
            asunto="x",
            cuerpo="<p>{{repositorio.url}}</p>",
        )
    )
    assert any(
        "no existe" in e
        for e in validar_plantilla(
            clave="invitacion_aceptada",
            canal="CANVAS_CONVERSACION",
            asunto="x",
            cuerpo="{{repositorio.url}} {{nota.final}}",
        )
    )


def test_ninguna_plantilla_nombra_a_otro_estudiante():
    # CA-11.7-02: prueba de arquitectura sobre el catalogo de plantillas.
    for p in PLANTILLAS.values():
        for v in variables_de(p.asunto + p.cuerpo):
            assert not nombra_a_terceros(v), (p.clave, v)


def test_proximidad_nunca_menciona_el_origen_de_la_fecha():
    # CA-11.7-03
    for clave in ("proximidad_cierre", "proximidad_cierre_fecha_cambio", "cambio_fecha_directo"):
        cuerpo = PLANTILLAS[clave].cuerpo.lower()
        assert "extensión" not in cuerpo and "excepción" not in cuerpo and "prórroga" not in cuerpo


def test_anuncio_de_cambio_de_fecha_es_fijo_y_sin_nombres():
    titulo, html = anuncio_cambio_fecha(
        tarea="Tarea 1",
        entrega="Entrega final",
        anterior="01-10-2026 23:59 (America/Santiago)",
        nueva="03-10-2026 23:59 (America/Santiago)",
        a_quien="todo el curso",
    )
    assert titulo == "Cambio de fecha — Tarea 1 · Entrega final"
    assert "Antes: 01-10-2026" in html and "<strong>03-10-2026" in html
    _, plan_b = anuncio_cambio_fecha(
        tarea="T",
        entrega="E",
        anterior="a",
        nueva="b",
        a_quien="la sección 1",
        seccion_afectada="Sección 1",
        salvaguarda=True,
    )
    assert plan_b.startswith("<p>Esto afecta a la sección Sección 1.</p>")
    assert "se mantiene la tuya" in plan_b
