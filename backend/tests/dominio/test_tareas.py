"""SPEC 08 S8.2-S8.3 (A-080, A-097, A-164, A-208): reglas puras de Etapa P7."""

from __future__ import annotations

import pytest

from app.dominio.estados import (
    EstadoRepositorioBase,
    EstadoTarea,
    EstadoValidacionEntrega,
    ModalidadTarea,
    OrigenVisibilidadEntrega,
    TipoEntrega,
)
from app.dominio.repositorio_github import RepoGithubInfo
from app.dominio.tareas import (
    EntregaActivacion,
    EntregaOrden,
    EstudianteVisibilidad,
    MotivoRechazoTarea,
    RechazoTarea,
    condiciones_adopcion_fallidas,
    estado_base_segun_archivos,
    motivo_no_activable,
    ordenar_al_vincular,
    renumerar_al_desvincular,
    resolver_visibilidad,
    validar_modalidad_para_vincular,
    validar_ruta_archivo,
    validar_vincular_otra_entrega,
)
from app.dominio.tareas_canvas import OverrideCanvasCrudo

# --- Modalidad (R2.3.3, CA-8.2-01) ---


def test_ca_8_2_01_modalidad_incompatible_se_rechaza():
    with pytest.raises(RechazoTarea) as exc:
        validar_modalidad_para_vincular(
            modalidad_tarea=ModalidadTarea.INDIVIDUAL,
            es_grupal_canvas=True,
            perfil_alcance="completo",
        )
    assert exc.value.motivo == MotivoRechazoTarea.MODALIDAD_INCOMPATIBLE


def test_modalidad_grupal_es_capa_3_en_la_parcial():
    with pytest.raises(RechazoTarea) as exc:
        validar_modalidad_para_vincular(
            modalidad_tarea=None, es_grupal_canvas=True, perfil_alcance="parcial"
        )
    assert exc.value.motivo == MotivoRechazoTarea.MODALIDAD_GRUPAL_NO_DISPONIBLE
    assert "23 de septiembre" in exc.value.detalle
    assert "próximamente" not in exc.value.detalle.lower()


def test_modalidad_individual_se_deriva_de_canvas():
    assert (
        validar_modalidad_para_vincular(
            modalidad_tarea=None, es_grupal_canvas=False, perfil_alcance="parcial"
        )
        == ModalidadTarea.INDIVIDUAL
    )


def test_segunda_entrega_es_capa_3_en_la_parcial():
    validar_vincular_otra_entrega(cantidad_actual=0, perfil_alcance="parcial")
    with pytest.raises(RechazoTarea) as exc:
        validar_vincular_otra_entrega(cantidad_actual=1, perfil_alcance="parcial")
    assert exc.value.motivo == MotivoRechazoTarea.MULTIENTREGA_NO_DISPONIBLE
    validar_vincular_otra_entrega(cantidad_actual=1, perfil_alcance="completo")


# --- Orden y entrega FINAL (A-080) ---


def test_la_primera_entrega_nace_final_con_orden_1():
    assert ordenar_al_vincular([], nueva_id="a", final_id=None) == [
        EntregaOrden(id="a", orden=1, tipo=TipoEntrega.FINAL)
    ]


def test_ca_8_2_04_segunda_entrega_sin_elegir_final_no_se_completa():
    existentes = [EntregaOrden(id="a", orden=1, tipo=TipoEntrega.FINAL)]
    with pytest.raises(RechazoTarea) as exc:
        ordenar_al_vincular(existentes, nueva_id="b", final_id=None)
    assert exc.value.motivo == MotivoRechazoTarea.FINAL_NO_ELEGIDA


def test_segunda_entrega_elegida_como_final_reordena():
    existentes = [EntregaOrden(id="a", orden=1, tipo=TipoEntrega.FINAL)]
    resultado = ordenar_al_vincular(existentes, nueva_id="b", final_id="b")
    assert resultado == [
        EntregaOrden(id="a", orden=1, tipo=TipoEntrega.PARCIAL),
        EntregaOrden(id="b", orden=2, tipo=TipoEntrega.FINAL),
    ]


def test_la_final_anterior_conservada_queda_con_mayor_orden():
    existentes = [EntregaOrden(id="a", orden=1, tipo=TipoEntrega.FINAL)]
    resultado = ordenar_al_vincular(existentes, nueva_id="b", final_id="a")
    assert resultado == [
        EntregaOrden(id="b", orden=1, tipo=TipoEntrega.PARCIAL),
        EntregaOrden(id="a", orden=2, tipo=TipoEntrega.FINAL),
    ]


def test_ca_8_2_02_desvincular_renumera_contiguo():
    existentes = [
        EntregaOrden(id="a", orden=1, tipo=TipoEntrega.PARCIAL),
        EntregaOrden(id="b", orden=2, tipo=TipoEntrega.PARCIAL),
        EntregaOrden(id="c", orden=3, tipo=TipoEntrega.FINAL),
    ]
    resultado = renumerar_al_desvincular(
        existentes, quitar_id="b", tiene_versiones_capturadas=False
    )
    assert resultado == [
        EntregaOrden(id="a", orden=1, tipo=TipoEntrega.PARCIAL),
        EntregaOrden(id="c", orden=2, tipo=TipoEntrega.FINAL),
    ]


def test_ca_8_2_03_desvincular_con_versiones_capturadas_se_rechaza():
    existentes = [EntregaOrden(id="a", orden=1, tipo=TipoEntrega.FINAL)]
    with pytest.raises(RechazoTarea) as exc:
        renumerar_al_desvincular(existentes, quitar_id="a", tiene_versiones_capturadas=True)
    assert exc.value.motivo == MotivoRechazoTarea.DESVINCULAR_NO_PERMITIDO


# --- Activacion (A-208, CA-8.3-01, CA-8.3-02) ---

_FINAL_VIGENTE = [EntregaActivacion(TipoEntrega.FINAL, EstadoValidacionEntrega.VIGENTE)]


def _motivo(**cambios: object) -> str | None:
    argumentos: dict[str, object] = {
        "estado_tarea": EstadoTarea.BORRADOR,
        "modalidad": ModalidadTarea.INDIVIDUAL,
        "entregas": _FINAL_VIGENTE,
        "estado_repositorio_base": None,
        "github_vinculado": True,
        "perfil_alcance": "parcial",
    }
    argumentos.update(cambios)
    return motivo_no_activable(**argumentos)  # type: ignore[arg-type]


def test_ca_8_3_01_sin_repositorio_base_se_activa_sin_comprobarlo():
    assert _motivo() is None


def test_ca_8_3_02_base_creado_vacio_bloquea_con_motivo_literal():
    assert _motivo(estado_repositorio_base=EstadoRepositorioBase.CREADO_VACIO) == (
        "El repositorio base no tiene contenido."
    )


def test_base_listo_permite_activar():
    assert _motivo(estado_repositorio_base=EstadoRepositorioBase.LISTO) is None


def test_sin_entrega_final_no_se_activa():
    assert _motivo(entregas=[]) is not None


def test_sin_github_no_se_activa():
    assert _motivo(github_vinculado=False) == "El curso todavía no tiene GitHub vinculado."


def test_una_tarea_activa_no_se_vuelve_a_activar():
    assert _motivo(estado_tarea=EstadoTarea.ACTIVA) is not None


def test_entrega_eliminada_en_canvas_bloquea():
    entregas = [EntregaActivacion(TipoEntrega.FINAL, EstadoValidacionEntrega.ELIMINADA_EN_CANVAS)]
    assert _motivo(entregas=entregas) is not None


# --- Repositorio base: estado y rutas (A-067, A-208, S6.11.5) ---


def test_estado_base_segun_archivos():
    assert estado_base_segun_archivos({"README.md"}) == EstadoRepositorioBase.CREADO_VACIO
    assert estado_base_segun_archivos(set()) == EstadoRepositorioBase.CREADO_VACIO
    assert estado_base_segun_archivos({"README.md", "enunciado.pdf"}) == EstadoRepositorioBase.LISTO


@pytest.mark.parametrize("ruta", ["", "/abs.py", "a/../b.py", "a//b.py", "a\\b.py", "./x.py"])
def test_rutas_invalidas(ruta: str):
    with pytest.raises(RechazoTarea):
        validar_ruta_archivo(ruta)


def test_no_se_suben_workflows():
    with pytest.raises(RechazoTarea):
        validar_ruta_archivo(".github/workflows/ci.yml")


def test_ruta_valida_se_limpia():
    assert validar_ruta_archivo("  src/main.py ") == "src/main.py"


# --- Adopcion segura del base (A-097) ---


def _repo(**cambios: object) -> RepoGithubInfo:
    datos: dict[str, object] = {
        "github_repo_id": 1,
        "nombre": "icc4201-202620-t1-base",
        "full_name": "org-valida/icc4201-202620-t1-base",
        "owner_login": "org-valida",
        "descripcion": "Base [gestor:icc4201-202620/t1/base]",
        "topics": ("gestor-tareas", "curso-icc4201-202620", "tarea-t1"),
        "rama_por_defecto": "main",
        "es_plantilla": True,
        "url_html": "https://github.com/org-valida/icc4201-202620-t1-base",
    }
    datos.update(cambios)
    return RepoGithubInfo(**datos)  # type: ignore[arg-type]


def test_adopcion_con_las_condiciones_cumplidas():
    assert (
        condiciones_adopcion_fallidas(
            _repo(), org_login="org-valida", curso_slug="icc4201-202620", tarea_slug="t1"
        )
        == []
    )


def test_adopcion_rechaza_repositorio_de_otro_curso_o_tarea():
    fallidas = condiciones_adopcion_fallidas(
        _repo(topics=("gestor-tareas", "curso-otro"), descripcion="[gestor:otro/t1/base]"),
        org_login="org-valida",
        curso_slug="icc4201-202620",
        tarea_slug="t1",
    )
    assert [f[0] for f in fallidas] == ["c", "d"]


# --- Visibilidad (A-164 paso 1) ---

_ESTUDIANTES = [
    EstudianteVisibilidad("ana", 1, "ACTIVO", frozenset({10}), frozenset({100})),
    EstudianteVisibilidad("beto", 2, "INVITADO", frozenset({20}), frozenset()),
    EstudianteVisibilidad("carla", 3, "INACTIVO", frozenset({10}), frozenset()),
]


def test_visibilidad_todos_excluye_inactivos():
    r = resolver_visibilidad(
        only_visible_to_overrides=False,
        assignment_visibility=None,
        overrides=None,
        estudiantes=_ESTUDIANTES,
    )
    assert r.origen == OrigenVisibilidadEntrega.TODOS
    assert r.visibles == {"ana", "beto"}


def test_visibilidad_por_assignment_visibility():
    r = resolver_visibilidad(
        only_visible_to_overrides=True,
        assignment_visibility=[2],
        overrides=None,
        estudiantes=_ESTUDIANTES,
    )
    assert r.origen == OrigenVisibilidadEntrega.ASSIGNMENT_VISIBILITY
    assert r.visibles == {"beto"}


def test_visibilidad_por_overrides_de_seccion_y_grupo():
    overrides = [
        OverrideCanvasCrudo(1, None, 20, None, None, None),
        OverrideCanvasCrudo(2, None, None, 100, None, None),
    ]
    r = resolver_visibilidad(
        only_visible_to_overrides=True,
        assignment_visibility=None,
        overrides=overrides,
        estudiantes=_ESTUDIANTES,
    )
    assert r.origen == OrigenVisibilidadEntrega.OVERRIDE
    assert r.visibles == {"ana", "beto"}


def test_visibilidad_no_resoluble_no_supone_universal():
    r = resolver_visibilidad(
        only_visible_to_overrides=True,
        assignment_visibility=None,
        overrides=None,
        estudiantes=_ESTUDIANTES,
    )
    assert r.no_resoluble
    assert r.visibles == frozenset()
