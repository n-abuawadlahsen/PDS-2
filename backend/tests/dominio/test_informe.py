"""Etapa F9 (SPEC 11 S11.3-S11.5): el informe docente diario, en funciones puras."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from app.dominio.informe import (
    CUOTA_DIARIA,
    HechosTarea,
    Item,
    armar_secciones,
    asunto_informe,
    reserva_a_consumir,
    tarea_activa,
    ventana_del_informe,
)
from app.infraestructura.enlaces_firmados import firmar, verificar

AHORA = datetime(2026, 10, 3, 11, 0, tzinfo=UTC)


def _hechos(**cambios) -> HechosTarea:
    base = {
        "estado_tarea": "ACTIVA",
        "estado_curso": "ACTIVO",
        "hay_cierre_futuro_publicado": False,
        "hay_repositorio_pendiente": False,
        "hay_incidencia_relevante": False,
    }
    base.update(cambios)
    return HechosTarea(**base)


def test_tarea_activa_exige_estado_y_algo_pendiente():
    assert not tarea_activa(_hechos())  # CA-11.3-02: todo operativo y cierre pasado
    assert tarea_activa(_hechos(hay_cierre_futuro_publicado=True))
    assert tarea_activa(_hechos(hay_repositorio_pendiente=True))
    assert tarea_activa(_hechos(hay_incidencia_relevante=True))
    assert not tarea_activa(_hechos(estado_tarea="ARCHIVADA", hay_cierre_futuro_publicado=True))
    assert not tarea_activa(_hechos(estado_curso="BORRADOR", hay_cierre_futuro_publicado=True))
    assert tarea_activa(_hechos(estado_tarea="INCONSISTENTE", hay_repositorio_pendiente=True))


def _item(clave: str, severidad: str = "ADVERTENCIA", dias: int = 1, texto: str | None = None):
    return Item(
        clave=clave,
        texto=texto or clave,
        enlace=f"/x/{clave}",
        severidad=severidad,
        desde=AHORA - timedelta(days=dias),
        tarea="Tarea 1",
    )


def test_cada_item_se_nombra_una_vez_en_su_seccion_mas_alta():
    # CA-11.3-08: un repositorio bloqueado va a la 1; en la 3 solo se cuenta.
    secciones = armar_secciones(
        {
            1: [("Repositorios bloqueados", _item("repo-a", "BLOQUEANTE"))],
            3: [
                ("Estudiantes sin participación", _item("repo-a")),
                ("Estudiantes sin participación", _item("repo-b")),
            ],
        }
    )
    assert [s.numero for s in secciones] == [1, 3]
    tercera = secciones[1].lineas[0]
    assert [i.clave for i in tercera.items] == ["repo-b"]
    assert tercera.contados_en_otra_seccion == 1


def test_secciones_vacias_se_omiten_y_orden_por_severidad_antiguedad_nombre():
    secciones = armar_secciones(
        {
            1: [
                ("Incidencias", _item("c", "ADVERTENCIA", dias=5)),
                ("Incidencias", _item("b", "BLOQUEANTE", dias=1)),
                ("Incidencias", _item("a", "ADVERTENCIA", dias=5)),
                ("Incidencias", _item("d", "ADVERTENCIA", dias=9)),
            ],
            2: [],
        }
    )
    assert len(secciones) == 1
    assert [i.clave for i in secciones[0].lineas[0].items] == ["b", "d", "a", "c"]


def test_mas_de_diez_nombrados_se_colapsan():
    # CA-11.3-07
    items = [("Sin cuenta de GitHub", _item(f"e{n:02d}")) for n in range(14)]
    linea = armar_secciones({2: items})[0].lineas[0]
    assert len(linea.items) == 10
    assert linea.mas == 4


def test_ventana_normal_ampliada_y_con_tope():
    desde, hasta = ventana_del_informe(
        ultimo_generado_hasta=AHORA - timedelta(hours=24), ahora=AHORA
    )
    assert hasta == AHORA and desde == AHORA - timedelta(hours=24)
    desde, _ = ventana_del_informe(ultimo_generado_hasta=AHORA - timedelta(days=12), ahora=AHORA)
    assert desde == AHORA - timedelta(days=7)
    creado = AHORA - timedelta(days=2)
    desde, _ = ventana_del_informe(ultimo_generado_hasta=None, ahora=AHORA, curso_creado_en=creado)
    assert desde == creado


def test_asunto_lleva_el_codigo_y_el_prefijo_si_hay_atencion():
    assert asunto_informe("ICC4201", date(2026, 10, 3), requiere_atencion=False) == (
        "ICC4201 · Informe docente del 03-10-2026"
    )
    assert asunto_informe("ICC4201", date(2026, 10, 3), requiere_atencion=True).startswith(
        "[Requiere atención] ICC4201"
    )


def test_reserva_de_cuota():
    assert CUOTA_DIARIA == {"INFORME": 60, "OPERATIVO": 20, "MARGEN": 20}
    assert reserva_a_consumir("INFORME", {"INFORME": 10}) == "INFORME"
    assert reserva_a_consumir("INFORME", {"INFORME": 60}) == "MARGEN"
    assert reserva_a_consumir("INFORME", {"INFORME": 60, "MARGEN": 20}) is None
    assert reserva_a_consumir("MARGEN", {"MARGEN": 20}) is None


def test_enlace_firmado_verifica_rechaza_alterado_y_vencido():
    token = firmar({"u": "1", "g": 3}, "clave", expira_en=AHORA + timedelta(days=90))
    assert verificar(token, ["clave"], ahora=AHORA) == {"u": "1", "g": 3}
    assert verificar(token, ["otra", "clave"], ahora=AHORA) is not None  # clave anterior
    assert verificar(token, ["otra"], ahora=AHORA) is None
    assert verificar(token[:-2] + "xx", ["clave"], ahora=AHORA) is None
    assert verificar(token, ["clave"], ahora=AHORA + timedelta(days=91)) is None
    assert verificar("basura", ["clave"], ahora=AHORA) is None


def test_estudiantes_de_un_repo_ya_nombrado_arriba_solo_se_cuentan():
    def participacion(clave: str, repo: str) -> Item:
        return Item(clave, clave, "/x", "ADVERTENCIA", AHORA, "Tarea 1", relacionado=repo)

    secciones = armar_secciones(
        {
            1: [("Repositorios bloqueados", _item("repo-a", "BLOQUEANTE"))],
            3: [
                ("Estudiantes sin participación", participacion("ana", "repo-a")),
                ("Estudiantes sin participación", participacion("bruno", "repo-a")),
                ("Estudiantes sin participación", participacion("carla", "repo-b")),
            ],
        }
    )
    linea = secciones[1].lineas[0]
    assert [i.clave for i in linea.items] == ["carla"]
    assert linea.contados_en_otra_seccion == 2
