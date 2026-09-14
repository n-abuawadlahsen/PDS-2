"""SPEC 07 S7.4-S7.6: reglas puras del mapeo estudiante <-> GitHub."""

from __future__ import annotations

from app.dominio.estados import EstadoMapeoGithub
from app.dominio.mapeo_github import (
    ContextoElegibilidad,
    es_cuenta_elegible,
    extraer_candidato,
    resultado_recibido,
    texto_comentario_resultado,
)

_CTX_ELEGIBLE = ContextoElegibilidad(
    es_del_equipo_docente_activo=False,
    es_miembro_equipo_lectura_github=False,
    es_owner_de_la_organizacion=False,
    es_cuenta_bot_de_la_app=False,
    tiene_mapeo_vigente_en_otro_lado=False,
)


def test_extraer_candidato_desde_url_de_perfil():
    resultado = extraer_candidato("<p>Mi perfil: https://github.com/mi-usuario</p>")
    assert resultado.login == "mi-usuario"


def test_extraer_candidato_desde_arroba():
    resultado = extraer_candidato("Mi usuario es @mi-usuario, saludos")
    assert resultado.login == "mi-usuario"


def test_extraer_candidato_desde_email_noreply():
    resultado = extraer_candidato("12345+mi-usuario@users.noreply.github.com")
    assert resultado.login == "mi-usuario"


def test_extraer_candidato_login_desnudo():
    resultado = extraer_candidato("mi-usuario")
    assert resultado.login == "mi-usuario"


def test_extraer_candidato_ambiguo_dos_urls_distintas():
    resultado = extraer_candidato("https://github.com/primero y tambien https://github.com/segundo")
    assert resultado.login is None


def test_extraer_candidato_sin_nada_reconocible():
    resultado = extraer_candidato("no tengo cuenta de github todavia")
    assert resultado.login is None


def test_extraer_candidato_limpia_html():
    resultado = extraer_candidato("<p>Mira mi perfil: <a href='x'>@mi-usuario</a></p>")
    assert resultado.login == "mi-usuario"


def test_cuenta_elegible_cuando_no_hay_ningun_impedimento():
    assert es_cuenta_elegible(_CTX_ELEGIBLE)


def test_cuenta_no_elegible_si_es_del_equipo_docente():
    ctx = ContextoElegibilidad(
        es_del_equipo_docente_activo=True,
        es_miembro_equipo_lectura_github=False,
        es_owner_de_la_organizacion=False,
        es_cuenta_bot_de_la_app=False,
        tiene_mapeo_vigente_en_otro_lado=False,
    )
    assert not es_cuenta_elegible(ctx)


def test_cuenta_no_elegible_si_ya_tiene_mapeo_vigente_en_otro_curso():
    ctx = ContextoElegibilidad(
        es_del_equipo_docente_activo=False,
        es_miembro_equipo_lectura_github=False,
        es_owner_de_la_organizacion=False,
        es_cuenta_bot_de_la_app=False,
        tiene_mapeo_vigente_en_otro_lado=True,
    )
    assert not es_cuenta_elegible(ctx)


def test_resultado_recibido_no_existe():
    estado = resultado_recibido(
        existe_como_usuario=False,
        es_organizacion=False,
        elegible=False,
        hay_conflicto_en_el_curso=False,
    )
    assert estado == EstadoMapeoGithub.NO_EXISTE


def test_resultado_recibido_es_organizacion():
    estado = resultado_recibido(
        existe_como_usuario=True,
        es_organizacion=True,
        elegible=False,
        hay_conflicto_en_el_curso=False,
    )
    assert estado == EstadoMapeoGithub.ES_ORGANIZACION


def test_resultado_recibido_no_elegible_es_no_resuelto_no_no_existe():
    """S7.5.3 "puerta de la ingesta": una cuenta no elegible nunca se
    confunde con una cuenta inexistente (bug que este proyecto tuvo y
    corrigio antes de escribir esta prueba)."""
    estado = resultado_recibido(
        existe_como_usuario=True,
        es_organizacion=False,
        elegible=False,
        hay_conflicto_en_el_curso=False,
    )
    assert estado == EstadoMapeoGithub.NO_RESUELTO


def test_resultado_recibido_en_conflicto():
    estado = resultado_recibido(
        existe_como_usuario=True,
        es_organizacion=False,
        elegible=True,
        hay_conflicto_en_el_curso=True,
    )
    assert estado == EstadoMapeoGithub.EN_CONFLICTO


def test_resultado_recibido_vigente_camino_feliz():
    estado = resultado_recibido(
        existe_como_usuario=True,
        es_organizacion=False,
        elegible=True,
        hay_conflicto_en_el_curso=False,
    )
    assert estado == EstadoMapeoGithub.VIGENTE


def test_texto_comentario_resultado_incluye_login_en_vigente():
    texto = texto_comentario_resultado(EstadoMapeoGithub.VIGENTE, login_canonico="Mi-Usuario")
    assert "Mi-Usuario" in texto


def test_texto_comentario_resultado_tiene_texto_para_cada_estado_no_terminal():
    for estado in (
        EstadoMapeoGithub.NO_EXISTE,
        EstadoMapeoGithub.ES_ORGANIZACION,
        EstadoMapeoGithub.EN_CONFLICTO,
        EstadoMapeoGithub.NO_RESUELTO,
    ):
        assert texto_comentario_resultado(estado)
