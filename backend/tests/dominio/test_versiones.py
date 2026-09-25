"""Etapa F4 (SPEC 09 S9.6-S9.9; A-101 a A-104, A-172, A-204, A-213): captura y
versiones de entrega, reglas puras."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.dominio.estados import (
    AdvertenciaVersion,
    EstadoVersion,
    MotivoVersion,
    TagEstado,
    TagMotivo,
)
from app.dominio.versiones import (
    COLUMNAS_MUTABLES,
    CommitCierre,
    EntregaDelSujeto,
    VersionInmutable,
    advertencias_de_captura,
    entrega_anterior,
    estado_tras_etiqueta,
    motivo_de_supersede,
    motivo_por_alcance,
    nombre_tag,
    resolver_captura,
    seleccionar_commit_cierre,
    tag_tras_rechazo,
    validar_cambios,
)

_CORTE = datetime(2026, 10, 1, 23, 59, tzinfo=UTC)


def _commit(sha: str, minutos: int) -> CommitCierre:
    return CommitCierre(
        sha=sha,
        tree_sha=f"t{sha}",
        fecha_committer=_CORTE + timedelta(minutes=minutos),
        fecha_autor=_CORTE + timedelta(minutes=minutos),
        mensaje=f"commit {sha}",
    )


def test_nombre_del_tag_hace_visible_la_independencia():
    # S9.7.2 / A-172: v<n> es exactamente el intento, por (entrega, sujeto).
    assert nombre_tag(orden=1, slug="avance-parcial", intento=1) == "entrega/1-avance-parcial/v1"
    assert nombre_tag(orden=2, slug="entrega-final", intento=2) == "entrega/2-entrega-final/v2"


def test_seleccion_local_del_mayor_commit_anterior_o_igual_al_corte():
    """S9.6.4: nunca «el primero» de la lista; inclusiva en el segundo exacto."""
    lista = [_commit("c3", 1), _commit("c1", -30), _commit("c2", 0), _commit("c0", -90)]
    elegido = seleccionar_commit_cierre(lista, corte=_CORTE)
    assert elegido is not None and elegido.sha == "c2"
    assert seleccionar_commit_cierre([_commit("x", 5)], corte=_CORTE) is None


def test_resolver_captura_coincidente_y_discrepante():
    github = _commit("abc", -5)
    ok = resolver_captura(espejo=github, github=github, commit_inicial_sha="ini")
    assert (ok.estado, ok.tag_estado, ok.commit) == (
        EstadoVersion.CAPTURADA_SIN_TAG,
        TagEstado.PENDIENTE,
        github,
    )
    # CA-9.6-03: discrepancia -> REVISAR con ambos SHA; manda el espejo.
    espejo = _commit("def", -10)
    revisar = resolver_captura(espejo=espejo, github=github, commit_inicial_sha="ini")
    assert revisar.estado == EstadoVersion.REVISAR
    assert revisar.commit == espejo
    assert revisar.verificacion["espejo_sha"] == "def"
    assert revisar.verificacion["github_sha"] == "abc"
    # Sin espejo de actividad todavia (llega con la ingesta): GitHub sola,
    # declarado en la verificacion.
    sin_espejo = resolver_captura(espejo=None, github=github, commit_inicial_sha="ini")
    assert sin_espejo.estado == EstadoVersion.CAPTURADA_SIN_TAG
    assert sin_espejo.verificacion["espejo_sha"] is None


def test_sin_commits_es_informacion_y_no_error():
    """S9.6.5 / CA-9.6-04: nunca error; sin etiqueta."""
    vacio = resolver_captura(espejo=None, github=None, commit_inicial_sha=None)
    assert (vacio.estado, vacio.tag_estado, vacio.tag_motivo) == (
        EstadoVersion.SIN_COMMITS,
        TagEstado.NO_APLICA,
        TagMotivo.SIN_COMMITS,
    )
    assert vacio.verificacion["motivo_sin_commits"] == "REPOSITORIO_VACIO"
    inicial = resolver_captura(espejo=None, github=_commit("ini", -500), commit_inicial_sha="ini")
    assert inicial.estado == EstadoVersion.SIN_COMMITS
    assert inicial.verificacion["motivo_sin_commits"] == "SOLO_COMMIT_INICIAL"
    assert inicial.commit is None


def test_la_etiqueta_mueve_solo_las_dos_transiciones_permitidas():
    assert estado_tras_etiqueta(EstadoVersion.CAPTURADA_SIN_TAG, TagEstado.CREADO) == (
        EstadoVersion.CAPTURADA
    )
    # REVISAR describe una discrepancia de SHA, ortogonal a la etiqueta.
    assert estado_tras_etiqueta(EstadoVersion.REVISAR, TagEstado.CREADO) == EstadoVersion.REVISAR
    assert estado_tras_etiqueta(EstadoVersion.CAPTURADA, TagEstado.PENDIENTE) == (
        EstadoVersion.CAPTURADA_SIN_TAG
    )
    assert estado_tras_etiqueta(EstadoVersion.CAPTURADA, TagEstado.CONFLICTO) == (
        EstadoVersion.CAPTURADA_SIN_TAG
    )


def test_rechazos_al_crear_la_etiqueta():
    # CA-9.6-06: un 403 de limite deja la etiqueta pendiente y se reintenta.
    assert tag_tras_rechazo(403, "API rate limit exceeded") == (
        TagEstado.PENDIENTE,
        TagMotivo.LIMITE_API,
        True,
    )
    assert tag_tras_rechazo(403, "Repository was archived so is read-only.") == (
        TagEstado.FALLIDO,
        TagMotivo.REPOSITORIO_ARCHIVADO,
        False,
    )
    assert tag_tras_rechazo(403, "Resource not accessible by integration") == (
        TagEstado.FALLIDO,
        TagMotivo.PERMISO_INSUFICIENTE,
        False,
    )
    assert tag_tras_rechazo(404, "Not Found") == (
        TagEstado.FALLIDO,
        TagMotivo.REPOSITORIO_INACCESIBLE,
        False,
    )
    assert tag_tras_rechazo(502, "Bad Gateway") == (
        TagEstado.PENDIENTE,
        TagMotivo.DESCONOCIDO,
        True,
    )


def test_solo_las_columnas_de_la_lista_cerrada_son_mutables():
    """S9.8.1 / CA-9.8-01: la funcion unica de transicion."""
    assert "commit_sha" not in COLUMNAS_MUTABLES
    actual = {"vigente": True, "estado": "CAPTURADA_SIN_TAG", "commit_sha": "a" * 40}
    validar_cambios(actual, {"vigente": False, "motivo": "FECHA_ADELANTADA"})
    validar_cambios(actual, {"estado": "CAPTURADA", "tag_estado": "CREADO"})
    for prohibido in ({"commit_sha": "b" * 40}, {"fecha_corte_utc": _CORTE}, {"intento": 2}):
        with pytest.raises(VersionInmutable):
            validar_cambios(actual, prohibido)
    with pytest.raises(VersionInmutable):
        validar_cambios({"vigente": False}, {"vigente": True})
    with pytest.raises(VersionInmutable):
        validar_cambios({"estado": "SIN_COMMITS"}, {"estado": "CAPTURADA"})


def test_recaptura_ante_cambio_de_fecha():
    """S9.8.2 (A-103): automatica, simetrica, nada se descarta."""
    assert motivo_de_supersede(corte_version=_CORTE, nueva_fecha=_CORTE - timedelta(hours=3)) == (
        MotivoVersion.FECHA_ADELANTADA
    )
    assert motivo_de_supersede(corte_version=_CORTE, nueva_fecha=_CORTE + timedelta(days=1)) == (
        MotivoVersion.FECHA_EXTENDIDA
    )
    assert motivo_de_supersede(corte_version=_CORTE, nueva_fecha=None) == (
        MotivoVersion.FECHA_EXTENDIDA
    )
    assert motivo_de_supersede(corte_version=_CORTE, nueva_fecha=_CORTE) is None


def test_captura_tardia_por_alcance():
    servicio = _CORTE + timedelta(days=1)
    assert motivo_por_alcance(corte=_CORTE, entrada_en_servicio=servicio) == (
        MotivoVersion.CAPTURA_TARDIA_POR_ALCANCE
    )
    assert (
        motivo_por_alcance(corte=servicio + timedelta(hours=1), entrada_en_servicio=servicio)
        is None
    )


def test_entrega_anterior_por_sujeto_con_fechas_cruzadas():
    """S9.7.3 (A-173): mayor orden estrictamente menor, con fecha no nula y
    anterior a la actual para ese sujeto; si no, se sigue bajando."""
    e1 = EntregaDelSujeto(entrega_id="e1", orden=1, due_at=_CORTE - timedelta(days=10))
    e2 = EntregaDelSujeto(entrega_id="e2", orden=2, due_at=_CORTE + timedelta(days=1))  # cruzada
    e3 = EntregaDelSujeto(entrega_id="e3", orden=3, due_at=_CORTE)
    assert entrega_anterior([e1, e2, e3], actual="e3") == "e1"
    assert entrega_anterior([e1, e2, e3], actual="e2") == "e1"
    assert entrega_anterior([e1, e2, e3], actual="e1") is None
    sin_fecha = EntregaDelSujeto(entrega_id="e0", orden=1, due_at=None)
    assert entrega_anterior([sin_fecha, e3], actual="e3") is None


def test_advertencias_de_captura():
    ahora = _CORTE + timedelta(minutes=2)
    advertencias, abrir_incidencia = advertencias_de_captura(
        sha="abc",
        sha_entrega_anterior="abc",
        estado_sujeto_al_cierre="RETIRADO",
        fecha_calculada_en=ahora - timedelta(hours=7),
        ahora=ahora,
        captura_diferida_por_github=False,
        usa_lfs=True,
        tiene_submodulos=False,
    )
    assert advertencias == [
        AdvertenciaVersion.SIN_CAMBIOS_RESPECTO_A_LA_ANTERIOR,
        AdvertenciaVersion.SUJETO_RETIRADO,
        AdvertenciaVersion.FECHAS_POSIBLEMENTE_DESACTUALIZADAS,
        AdvertenciaVersion.USA_GIT_LFS,
    ]
    assert abrir_incidencia is False
    # Mas de 48 horas sin refrescar la fecha: advertencia e incidencia.
    _, abrir = advertencias_de_captura(
        sha="abc",
        sha_entrega_anterior=None,
        estado_sujeto_al_cierre="ACTIVO",
        fecha_calculada_en=ahora - timedelta(hours=49),
        ahora=ahora,
        captura_diferida_por_github=True,
        usa_lfs=False,
        tiene_submodulos=True,
    )
    assert abrir is True
