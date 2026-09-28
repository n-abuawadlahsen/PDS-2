"""Etapa F2 (SPEC 08 S8.2.1-S8.2.2; SPEC 09 S9.11; A-080): multiples entregas
por tarea, reglas puras."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.dominio.estados import AdvertenciaEntrega, TipoEntrega
from app.dominio.tareas import (
    EntregaFechas,
    EntregaOrden,
    MotivoRechazoTarea,
    RechazoTarea,
    advertencias_de_entregas,
    ordenar_al_vincular,
    validar_conjunto_para_vincular,
    validar_excluir,
    validar_vincular_otra_entrega,
)

_CIERRE = datetime(2026, 10, 1, 23, 59, tzinfo=UTC)


def test_la_segunda_entrega_ya_no_esta_limitada_en_la_parcial():
    # Bandera `tarea_multientrega` retirada: una tercera tambien se admite.
    validar_vincular_otra_entrega(cantidad_actual=1, perfil_alcance="parcial")
    validar_vincular_otra_entrega(cantidad_actual=2, perfil_alcance="parcial")


def test_nunca_hay_cero_ni_dos_finales_al_vincular():
    existentes = [EntregaOrden(id="a", orden=1, tipo=TipoEntrega.FINAL)]
    # La nueva como final: la anterior pasa a parcial.
    orden = ordenar_al_vincular(existentes, nueva_id="b", final_id="b")
    assert [(e.id, e.orden, e.tipo) for e in orden] == [
        ("a", 1, TipoEntrega.PARCIAL),
        ("b", 2, TipoEntrega.FINAL),
    ]
    # La anterior sigue siendo la final: la nueva queda antes, como parcial.
    orden = ordenar_al_vincular(existentes, nueva_id="b", final_id="a")
    assert [(e.id, e.orden, e.tipo) for e in orden] == [
        ("b", 1, TipoEntrega.PARCIAL),
        ("a", 2, TipoEntrega.FINAL),
    ]
    with pytest.raises(RechazoTarea) as exc:
        ordenar_al_vincular(existentes, nueva_id="b", final_id=None)
    assert exc.value.motivo == MotivoRechazoTarea.FINAL_NO_ELEGIDA


def test_una_tarea_grupal_no_mezcla_conjuntos_de_grupos():
    """R2.3.3: todas las entregas con la misma configuracion. En una tarea
    grupal eso incluye el conjunto de grupos (A-047)."""
    validar_conjunto_para_vincular(categorias_existentes={77}, categoria_nueva=77)
    validar_conjunto_para_vincular(categorias_existentes=set(), categoria_nueva=None)
    with pytest.raises(RechazoTarea) as exc:
        validar_conjunto_para_vincular(categorias_existentes={77}, categoria_nueva=78)
    assert exc.value.motivo == MotivoRechazoTarea.MODALIDAD_INCOMPATIBLE


def test_excluir_la_final_de_una_tarea_activa_se_rechaza():
    validar_excluir(tipo=TipoEntrega.PARCIAL, ya_excluida=False)
    with pytest.raises(RechazoTarea) as exc:
        validar_excluir(tipo=TipoEntrega.FINAL, ya_excluida=False)
    assert exc.value.motivo == MotivoRechazoTarea.EXCLUIR_NO_PERMITIDO
    with pytest.raises(RechazoTarea):
        validar_excluir(tipo=TipoEntrega.PARCIAL, ya_excluida=True)


def test_advertencias_de_orden_y_de_fechas():
    """S9.11 `entrega.advertencias`: la interfaz ordena por `orden`, nunca por
    fecha; lo cruzado se advierte, no se bloquea."""
    entregas = [
        EntregaFechas(
            id="p", orden=1, tipo=TipoEntrega.PARCIAL, due_at=_CIERRE, lock_at=None, unlock_at=None
        ),
        EntregaFechas(
            id="f",
            orden=2,
            tipo=TipoEntrega.FINAL,
            due_at=_CIERRE - timedelta(days=2),
            lock_at=_CIERRE - timedelta(days=3),
            unlock_at=None,
        ),
    ]
    advertencias = advertencias_de_entregas(entregas)
    assert advertencias["f"] == [
        AdvertenciaEntrega.LOCK_ANTES_DE_DUE,
        AdvertenciaEntrega.FINAL_ANTES_QUE_PARCIAL,
    ]
    assert advertencias["p"] == []

    misma_fecha = [
        EntregaFechas(
            id="p", orden=1, tipo=TipoEntrega.PARCIAL, due_at=_CIERRE, lock_at=None, unlock_at=None
        ),
        EntregaFechas(
            id="f",
            orden=2,
            tipo=TipoEntrega.FINAL,
            due_at=_CIERRE,
            lock_at=None,
            unlock_at=_CIERRE + timedelta(hours=1),
        ),
    ]
    advertencias = advertencias_de_entregas(misma_fecha)
    assert advertencias["p"] == [AdvertenciaEntrega.DOS_ENTREGAS_MISMA_FECHA]
    assert advertencias["f"] == [
        AdvertenciaEntrega.UNLOCK_DESPUES_DE_DUE,
        AdvertenciaEntrega.DOS_ENTREGAS_MISMA_FECHA,
    ]
