"""A-184: ningun modelo SQLAlchemy fuera del censo cerrado de entidades."""

from __future__ import annotations

from app.adaptadores import modelos_curso, modelos_identidad, modelos_infraestructura  # noqa: F401
from app.adaptadores.base import Base
from app.dominio.censo import CENSO


def test_todas_las_tablas_orm_estan_en_el_censo():
    tablas = set(Base.metadata.tables.keys())
    fuera_del_censo = tablas - CENSO
    assert not fuera_del_censo, f"tablas ORM fuera de app/dominio/censo.py: {fuera_del_censo}"


def test_el_censo_no_tiene_entradas_huerfanas():
    tablas = set(Base.metadata.tables.keys())
    en_censo_sin_modelo = CENSO - tablas
    assert not en_censo_sin_modelo, f"en censo.py pero sin modelo ORM: {en_censo_sin_modelo}"
