"""SPEC 08 S8.4 (A-107, A-108, A-172): CA-8.4-01, CA-8.4-02 y CA-8.4-05."""

from __future__ import annotations

from app.dominio.nombres_repositorio import (
    SujetoNombre,
    es_slug_valido,
    marcador_descripcion,
    nombre_repositorio,
    normalizar,
    slug_entrega,
    topics_repositorio,
)


def test_ca_8_4_01_nombre_exacto_de_ana_gomez():
    nombre = nombre_repositorio(
        curso_slug="icc4201-202620",
        tarea_slug="t1-ordenamiento",
        sujeto=SujetoNombre(tipo="e", canvas_id=5310, texto_legible="Gómez, Ana"),
    )
    assert nombre == "icc4201-202620-t1-ordenamiento-e5310-gomez-ana"
    assert len(nombre) == 46


def test_ejemplos_de_la_tabla_de_8_4_1():
    assert (
        nombre_repositorio(
            curso_slug="icc4201-202620",
            tarea_slug="t2-compilador",
            sujeto=SujetoNombre(tipo="g", canvas_id=8842, texto_legible="Equipo 04"),
        )
        == "icc4201-202620-t2-compilador-g8842-equipo-04"
    )
    assert (
        nombre_repositorio(curso_slug="icc4201-202620", tarea_slug="t1-ordenamiento", sujeto="base")
        == "icc4201-202620-t1-ordenamiento-base"
    )


def test_ca_8_4_02_escritura_no_latina_termina_en_el_identificador():
    nombre = nombre_repositorio(
        curso_slug="icc4201-202620",
        tarea_slug="t1-ordenamiento",
        sujeto=SujetoNombre(tipo="e", canvas_id=5310, texto_legible="李小龍"),
    )
    assert nombre == "icc4201-202620-t1-ordenamiento-e5310"
    assert not nombre.endswith("-")


def test_ca_8_4_05_tildes_y_enie():
    assert normalizar("Muñoz Ñandú, José") == "munoz-nandu-jose"


def test_ca_8_4_05_truncado_que_cae_sobre_un_guion():
    # 23 letras + guion: el truncado a 24 deja el guion al final y el paso 7 lo quita.
    texto = "a" * 23 + " b"
    assert normalizar(texto) == "a" * 23


def test_ca_8_4_05_componente_vacio_tras_normalizar():
    assert normalizar("★ ☆") == ""
    grupo = nombre_repositorio(
        curso_slug="c",
        tarea_slug="t",
        sujeto=SujetoNombre(tipo="g", canvas_id=1, texto_legible="★"),
    )
    assert grupo == "c-t-g1"


def test_ca_8_4_05_dos_cursos_distintos_no_producen_el_mismo_nombre():
    sujeto = SujetoNombre(tipo="e", canvas_id=5310, texto_legible="Gómez, Ana")
    a = nombre_repositorio(curso_slug="icc4201-202620", tarea_slug="t1", sujeto=sujeto)
    b = nombre_repositorio(curso_slug="icc4201-202620-s2", tarea_slug="t1", sujeto=sujeto)
    assert a != b


def test_el_identificador_numerico_nunca_se_trunca():
    nombre = nombre_repositorio(
        curso_slug="a" * 24,
        tarea_slug="b" * 24,
        sujeto=SujetoNombre(tipo="e", canvas_id=1234567890, texto_legible="x" * 40),
    )
    assert "e1234567890" in nombre
    assert len(nombre) <= 90


def test_slug_valido():
    assert es_slug_valido("t1-ordenamiento")
    assert es_slug_valido("t")
    assert not es_slug_valido("-t1")
    assert not es_slug_valido("T1")
    assert not es_slug_valido("a" * 25)


def test_marcador_y_topics_de_a_069():
    assert (
        marcador_descripcion(
            curso_slug="icc4201-202620", tarea_slug="t1-ordenamiento", sujeto="e5310"
        )
        == "[gestor:icc4201-202620/t1-ordenamiento/e5310]"
    )
    assert topics_repositorio(curso_slug="icc4201-202620", tarea_slug="t1") == [
        "gestor-tareas",
        "curso-icc4201-202620",
        "tarea-t1",
    ]


def test_a_172_slug_de_entrega():
    assert slug_entrega(nombre="Avance parcial", orden=1, slugs_ocupados=set()) == "avance-parcial"
    assert slug_entrega(nombre="★", orden=2, slugs_ocupados=set()) == "e2"
    assert slug_entrega(nombre="Entrega", orden=2, slugs_ocupados={"entrega"}) == "entrega-2"
    assert slug_entrega(nombre="Entrega", orden=2, slugs_ocupados={"entrega", "entrega-2"}) == "e2"


def test_a_172_la_colision_no_se_come_el_sufijo_con_nombre_largo():
    largo = "x" * 30
    slug = slug_entrega(nombre=largo, orden=3, slugs_ocupados={"x" * 24})
    assert slug == "x" * 22 + "-3"
