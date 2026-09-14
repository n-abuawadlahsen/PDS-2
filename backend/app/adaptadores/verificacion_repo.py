"""Ejecucion del checklist de 19 items (SPEC 04 S4.7). Adaptador: hace la
I/O real contra Canvas y GitHub y persiste en `verificacion_vinculacion`,
usando las reglas puras de `dominio/verificacion.py`,
`dominio/vinculacion_canvas.py` y `dominio/vinculacion_github.py` para decidir
el resultado de cada item.

Los dos carriles (S4.7.1) se ejecutan uno tras otro, nunca los dos cerrojos a
la vez (RG-062, orden fijado en `infraestructura/cerrojos.py`): el trabajador
de `app/trabajos/ejecutor.py` procesa un trabajo a la vez de todos modos (sin
hilos), asi que la ejecucion "en paralelo" de S4.7.1 se refiere a que ningun
carril espera al otro para *empezar*, no a paralelismo real de hilos -- una
simplificacion documentada, no una desviacion silenciosa del SPEC.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturoAgotado
from typing import Any, TypeVar

from sqlalchemy.orm import Session

from app.adaptadores import canvas_repo
from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_canvas import ClienteCanvas, FalloProveedorCanvas
from app.adaptadores.cliente_github import ClienteGitHub, FalloProveedorGithub
from app.adaptadores.modelos_curso import Curso, MembresiaCurso
from app.adaptadores.modelos_github import VerificacionVinculacion
from app.dominio.estados import (
    EstadoCurso,
    EstadoMembresia,
    EstadoOrgGithubMembresia,
    OrigenVerificacion,
    ResultadoVerificacion,
    ViaAnuncioSeccion,
)
from app.dominio.verificacion import (
    CATALOGO_VERIFICACION,
    ITEMS_CARRIL_GITHUB,
    ORDEN_CARRIL_CANVAS,
    MotivoNoVerificado,
    Severidad,
    curso_puede_pasar_a_activo,
    resultado_binario,
    resultado_item_17,
)
from app.dominio.vinculacion_canvas import DetalleCursoCanvas, RechazoVinculacion, item_3_aprobado
from app.dominio.vinculacion_github import evaluar_item_14
from app.infraestructura.cerrojos import cerrojo_canvas, cerrojo_github
from app.infraestructura.cifrado import Llavero
from app.infraestructura.identificadores import uuid7

_TOPE_ITEM_SEGUNDOS = 10.0
_TOPE_GLOBAL_SEGUNDOS = 180.0

_SEVERIDAD_POR_ITEM: dict[str, Severidad] = {i.id: i.severidad for i in CATALOGO_VERIFICACION}

_PERMISOS_CANVAS: list[str] = [
    "manage_grades",
    "post_to_forum",
    "create_announcement",
    "send_messages",
    "send_messages_all",
    "read_email_addresses",
    "manage_assignments",
    "manage_assignments_add",
    "comment_on_submissions",
    "moderate_forum",
]

_T = TypeVar("_T")


class _ItemAgotado(Exception):
    pass


def _tope(funcion: Callable[[], _T]) -> _T:
    """Impone el tope de 10s por item (S4.7.1) sin tocar el timeout propio
    (20s) de los clientes HTTP, pensado para conexiones colgadas."""
    with ThreadPoolExecutor(max_workers=1) as ejecutor:
        futuro = ejecutor.submit(funcion)
        try:
            return futuro.result(timeout=_TOPE_ITEM_SEGUNDOS)
        except FuturoAgotado as exc:
            raise _ItemAgotado from exc


def _restante(inicio: float) -> float:
    return _TOPE_GLOBAL_SEGUNDOS - (time.monotonic() - inicio)


def _persistir(
    bd: Session,
    *,
    curso_id: uuid.UUID,
    ejecucion_id: uuid.UUID,
    item: str,
    resultado: ResultadoVerificacion,
    detalle: dict[str, Any],
) -> None:
    bd.add(
        VerificacionVinculacion(
            curso_id=curso_id,
            ejecucion_id=ejecucion_id,
            item=item,
            origen=OrigenVerificacion.CHECKLIST.value,
            capacidad=None,
            resultado=resultado.value,
            detalle=detalle,
            ejecutada_en=ahora_utc(),
        )
    )
    bd.flush()


def _persistir_no_verificado(
    bd: Session, *, curso_id: uuid.UUID, ejecucion_id: uuid.UUID, item: str, motivo: str
) -> ResultadoVerificacion:
    _persistir(
        bd,
        curso_id=curso_id,
        ejecucion_id=ejecucion_id,
        item=item,
        resultado=ResultadoVerificacion.NO_VERIFICADO,
        detalle={"motivo": motivo},
    )
    return ResultadoVerificacion.NO_VERIFICADO


def _evaluar_item_1(
    cliente: ClienteCanvas, token: str, canvas_user_id_esperado: int
) -> tuple[ResultadoVerificacion, dict[str, Any]]:
    try:
        usuario_canvas = cliente.obtener_usuario_actual(token)
    except RechazoVinculacion:
        return resultado_binario(aprobado=False, severidad=_SEVERIDAD_POR_ITEM["1"]), {
            "token_valido": False
        }
    aprobado = usuario_canvas.canvas_user_id == canvas_user_id_esperado
    return resultado_binario(aprobado=aprobado, severidad=_SEVERIDAD_POR_ITEM["1"]), {
        "token_valido": True,
        "identidad_coincide": aprobado,
    }


def _evaluar_permiso(
    item: str, detalle_curso: DetalleCursoCanvas
) -> tuple[ResultadoVerificacion, dict[str, Any]]:
    p = detalle_curso.permisos
    if item == "4":
        aprobado = bool(p.get("manage_grades"))
    elif item == "5":
        aprobado = bool(p.get("post_to_forum")) or bool(p.get("create_announcement"))
    elif item == "6":
        aprobado = bool(p.get("send_messages")) or bool(p.get("send_messages_all"))
    elif item == "7":
        aprobado = bool(p.get("read_email_addresses"))
    elif item == "16":
        aprobado = bool(p.get("manage_assignments")) and bool(p.get("manage_assignments_add"))
    elif item == "19":
        aprobado = bool(p.get("moderate_forum"))
    else:  # pragma: no cover - catalogo cerrado, ver ORDEN_CARRIL_CANVAS
        raise AssertionError(item)
    return resultado_binario(aprobado=aprobado, severidad=_SEVERIDAD_POR_ITEM[item]), {
        "aprobado": aprobado
    }


def _ejecutar_carril_canvas(
    bd: Session,
    cliente: ClienteCanvas,
    llavero: Llavero,
    *,
    curso: Curso,
    ejecucion_id: uuid.UUID,
    items: list[str],
    inicio: float,
    es_corrida_completa: bool,
) -> dict[str, ResultadoVerificacion]:
    resultados: dict[str, ResultadoVerificacion] = {}
    credencial = canvas_repo.obtener_credencial_operativa(bd, curso.id)
    if credencial is None or curso.canvas_course_id is None:
        for item in items:
            resultados[item] = _persistir_no_verificado(
                bd,
                curso_id=curso.id,
                ejecucion_id=ejecucion_id,
                item=item,
                motivo="SIN_CREDENCIAL_CANVAS",
            )
        return resultados

    token = canvas_repo.descifrar_token(llavero, credencial)
    canvas_course_id: int = curso.canvas_course_id
    detalle_curso: DetalleCursoCanvas | None = None
    bloqueado_por: str | None = None

    for item in items:
        if _restante(inicio) <= 0:
            resultados[item] = _persistir_no_verificado(
                bd,
                curso_id=curso.id,
                ejecucion_id=ejecucion_id,
                item=item,
                motivo=MotivoNoVerificado.TIEMPO_AGOTADO.value,
            )
            continue
        if es_corrida_completa and bloqueado_por is not None and item != "1":
            motivo = (
                MotivoNoVerificado.DEPENDE_DE_ITEM_1.value
                if bloqueado_por == "1"
                else MotivoNoVerificado.DEPENDE_DE_ITEM_2.value
            )
            resultados[item] = _persistir_no_verificado(
                bd, curso_id=curso.id, ejecucion_id=ejecucion_id, item=item, motivo=motivo
            )
            continue

        try:
            if item in {"2", "4", "5", "6", "7", "13", "16", "17", "19"} and detalle_curso is None:
                detalle_curso = _tope(
                    lambda: cliente.obtener_detalle_curso(token, canvas_course_id, _PERMISOS_CANVAS)
                )

            if item == "1":
                resultado, detalle = _tope(
                    lambda: _evaluar_item_1(cliente, token, credencial.canvas_user_id)
                )
            elif item == "2":
                assert detalle_curso is not None
                aprobado = detalle_curso.existe and detalle_curso.publicado
                resultado = resultado_binario(aprobado=aprobado, severidad=_SEVERIDAD_POR_ITEM["2"])
                detalle = {"existe": detalle_curso.existe, "publicado": detalle_curso.publicado}
            elif item == "13":
                assert detalle_curso is not None
                resultado = resultado_binario(
                    aprobado=detalle_curso.time_zone is not None,
                    severidad=_SEVERIDAD_POR_ITEM["13"],
                )
                detalle = {"time_zone": detalle_curso.time_zone}
            elif item == "17":
                assert detalle_curso is not None
                item_6_fallo = resultados.get("6") != ResultadoVerificacion.CORRECTO
                aprobado = bool(detalle_curso.permisos.get("comment_on_submissions"))
                resultado = resultado_item_17(aprobado=aprobado, item_6_fallo=item_6_fallo)
                detalle = {"aprobado": aprobado, "item_6_fallo": item_6_fallo}
            elif item in {"4", "5", "6", "7", "16", "19"}:
                assert detalle_curso is not None
                resultado, detalle = _evaluar_permiso(item, detalle_curso)
            elif item == "3":
                matriculas = _tope(
                    lambda: cliente.obtener_matriculas_profesor(token, canvas_course_id)
                )
                aprobado = item_3_aprobado(matriculas)
                resultado = resultado_binario(aprobado=aprobado, severidad=_SEVERIDAD_POR_ITEM["3"])
                detalle = {"cantidad_matriculas": len(matriculas)}
            elif item == "8":
                secciones = _tope(lambda: cliente.obtener_secciones(token, canvas_course_id))
                aprobado = not any(s.es_cross_listed for s in secciones)
                resultado = resultado_binario(aprobado=aprobado, severidad=_SEVERIDAD_POR_ITEM["8"])
                detalle = {
                    "cantidad_secciones": len(secciones),
                    "cross_listed": [s.section_id for s in secciones if s.es_cross_listed],
                }
            elif item == "9":
                cantidad = _tope(lambda: cliente.contar_grupos(token, canvas_course_id))
                resultado = resultado_binario(aprobado=True, severidad=_SEVERIDAD_POR_ITEM["9"])
                detalle = {"cantidad_conjuntos_grupos": cantidad}
            elif item == "10":
                configurada = _tope(
                    lambda: cliente.existe_politica_entrega_tardia(token, canvas_course_id)
                )
                resultado = resultado_binario(
                    aprobado=configurada, severidad=_SEVERIDAD_POR_ITEM["10"]
                )
                detalle = {"configurada": configurada}
            elif item == "11":
                periodos = _tope(
                    lambda: cliente.obtener_periodos_calificacion(token, canvas_course_id)
                )
                aprobado = not any(p.is_closed for p in periodos)
                resultado = resultado_binario(
                    aprobado=aprobado, severidad=_SEVERIDAD_POR_ITEM["11"]
                )
                detalle = {
                    "cantidad_periodos": len(periodos),
                    "cerrados": sum(p.is_closed for p in periodos),
                }
            elif item in ("12", "15"):
                roster = _tope(lambda: cliente.obtener_roster(token, canvas_course_id))
                if item == "12":
                    resultado = resultado_binario(
                        aprobado=True, severidad=_SEVERIDAD_POR_ITEM["12"]
                    )
                    detalle = {
                        "tamano_pagina": roster.cantidad_primera_pagina,
                        "hay_siguiente_pagina": roster.hay_siguiente_pagina,
                    }
                else:
                    aprobado = roster.cantidad_primera_pagina > 0 or roster.hay_siguiente_pagina
                    resultado = resultado_binario(
                        aprobado=aprobado, severidad=_SEVERIDAD_POR_ITEM["15"]
                    )
                    detalle = {"estudiantes_en_primera_pagina": roster.cantidad_primera_pagina}
            else:  # pragma: no cover - catalogo cerrado
                continue
        except _ItemAgotado:
            resultado = ResultadoVerificacion.NO_VERIFICADO
            detalle = {"motivo": MotivoNoVerificado.TIEMPO_AGOTADO.value}
        except FalloProveedorCanvas as exc:
            resultado = ResultadoVerificacion.NO_VERIFICADO
            detalle = {"motivo": "FALLO_PROVEEDOR", "error": str(exc)}

        _persistir(
            bd,
            curso_id=curso.id,
            ejecucion_id=ejecucion_id,
            item=item,
            resultado=resultado,
            detalle=detalle,
        )
        resultados[item] = resultado
        if (
            es_corrida_completa
            and item in ("1", "2")
            and resultado == ResultadoVerificacion.BLOQUEANTE
        ):
            bloqueado_por = item

    return resultados


def _evaluar_item_18(bd: Session, curso: Curso) -> tuple[ResultadoVerificacion, dict[str, Any]]:
    if curso.github_org_login is None:
        return resultado_binario(aprobado=False, severidad=_SEVERIDAD_POR_ITEM["18"]), {
            "motivo": "GITHUB_NO_VINCULADO"
        }
    miembros_activos = (
        bd.query(MembresiaCurso)
        .filter(
            MembresiaCurso.curso_id == curso.id,
            MembresiaCurso.estado == EstadoMembresia.ACTIVA.value,
        )
        .all()
    )
    total = len(miembros_activos)
    activos_org = sum(
        1 for m in miembros_activos if m.org_github_estado == EstadoOrgGithubMembresia.ACTIVA.value
    )
    aprobado = total > 0 and activos_org == total
    return resultado_binario(aprobado=aprobado, severidad=_SEVERIDAD_POR_ITEM["18"]), {
        "total_docentes": total,
        "activos_en_organizacion": activos_org,
    }


def _evaluar_item_14(
    cliente: ClienteGitHub, curso: Curso
) -> tuple[ResultadoVerificacion, dict[str, Any]]:
    if curso.github_installation_id is None or curso.github_org_login is None:
        return ResultadoVerificacion.BLOQUEANTE, {"motivo": "GITHUB_NO_VINCULADO"}
    token = cliente.obtener_token_instalacion(curso.github_installation_id)
    instalacion = cliente.obtener_instalacion(curso.github_installation_id)
    organizacion = cliente.obtener_organizacion(curso.github_org_login, token)
    existe_repo_perfil = cliente.existe_repo(curso.github_org_login, ".github", token)
    evaluacion = evaluar_item_14(
        instalacion=instalacion,
        org_login_esperado=curso.github_org_login,
        organizacion=organizacion,
        existe_repo_perfil=existe_repo_perfil,
    )
    if evaluacion.requiere_verificacion_a_mano:
        # S4.7.4: VERIFICADO_A_MANO nunca se escribe solo; queda NO_VERIFICADO
        # hasta que un profesor lo firme (ver `firmar_item_14_a_mano`).
        return ResultadoVerificacion.NO_VERIFICADO, {
            **evaluacion.detalle,
            "requiere_firma_manual": True,
        }
    return resultado_binario(
        aprobado=evaluacion.aprobado, severidad=_SEVERIDAD_POR_ITEM["14"]
    ), evaluacion.detalle


def _ejecutar_carril_github(
    bd: Session,
    cliente: ClienteGitHub,
    *,
    curso: Curso,
    ejecucion_id: uuid.UUID,
    items: list[str],
    inicio: float,
) -> dict[str, ResultadoVerificacion]:
    resultados: dict[str, ResultadoVerificacion] = {}
    for item in items:
        if _restante(inicio) <= 0:
            resultados[item] = _persistir_no_verificado(
                bd,
                curso_id=curso.id,
                ejecucion_id=ejecucion_id,
                item=item,
                motivo=MotivoNoVerificado.TIEMPO_AGOTADO.value,
            )
            continue
        try:
            if item == "18":
                resultado, detalle = _evaluar_item_18(bd, curso)
            elif item == "14":
                resultado, detalle = _tope(lambda: _evaluar_item_14(cliente, curso))
            else:  # pragma: no cover - catalogo cerrado
                continue
        except _ItemAgotado:
            resultado = ResultadoVerificacion.NO_VERIFICADO
            detalle = {"motivo": MotivoNoVerificado.TIEMPO_AGOTADO.value}
        except FalloProveedorGithub as exc:
            resultado = ResultadoVerificacion.NO_VERIFICADO
            detalle = {"motivo": "FALLO_PROVEEDOR", "error": str(exc)}

        _persistir(
            bd,
            curso_id=curso.id,
            ejecucion_id=ejecucion_id,
            item=item,
            resultado=resultado,
            detalle=detalle,
        )
        resultados[item] = resultado
    return resultados


def ultimos_resultados(bd: Session, curso_id: uuid.UUID) -> dict[str, ResultadoVerificacion]:
    """El resultado mas reciente de cada item (no necesariamente de la misma
    `ejecucion_id`): una reejecucion de un solo item actualiza solo ese item."""
    filas = (
        bd.query(VerificacionVinculacion)
        .filter(
            VerificacionVinculacion.curso_id == curso_id,
            VerificacionVinculacion.origen == OrigenVerificacion.CHECKLIST.value,
        )
        .order_by(VerificacionVinculacion.ejecutada_en.asc())
        .all()
    )
    ultimos: dict[str, ResultadoVerificacion] = {}
    for fila in filas:
        if fila.item is not None:
            ultimos[fila.item] = ResultadoVerificacion(fila.resultado)
    return ultimos


def _quizas_activar_curso(
    bd: Session, curso: Curso, ultimos: dict[str, ResultadoVerificacion]
) -> None:
    """S4.3.2, S4.7 regla 5: ACTIVO solo con los dos vinculos hechos y cero
    items BLOQUEANTE en rojo."""
    if curso.estado != EstadoCurso.VINCULANDO.value:
        return
    if curso.canvas_course_id is None or curso.github_org_id is None:
        return
    numerados = {
        k: v for k, v in ultimos.items() if k in ORDEN_CARRIL_CANVAS or k in ITEMS_CARRIL_GITHUB
    }
    if curso_puede_pasar_a_activo(numerados):
        curso.estado = EstadoCurso.ACTIVO.value
        curso.actualizado_en = ahora_utc()
        bd.flush()


def ejecutar_checklist(
    bd: Session,
    cliente_canvas: ClienteCanvas,
    cliente_github: ClienteGitHub,
    llavero: Llavero,
    *,
    curso: Curso,
    ejecucion_id: uuid.UUID,
    solo_items: tuple[str, ...] | None = None,
) -> uuid.UUID:
    """`ejecucion_id` lo genera quien encola el trabajo (S4.7.1: `POST
    .../verificacion` responde `202` con el `ejecucion_id` de inmediato, antes
    de que el trabajo corra), no esta funcion -- asi el sondeo puede empezar
    en cuanto se encola. `solo_items=None` corre los 19 items en orden; con un
    subconjunto, reejecuta solo esos, sin la cascada de dependencia de los
    items 1/2 (esa cascada es exclusiva de la corrida completa, CA-4.7-02)."""
    inicio = time.monotonic()
    es_corrida_completa = solo_items is None

    items_canvas = [i for i in ORDEN_CARRIL_CANVAS if solo_items is None or i in solo_items]
    items_github = [i for i in ITEMS_CARRIL_GITHUB if solo_items is None or i in solo_items]

    resultados: dict[str, ResultadoVerificacion] = {}
    if items_canvas:
        with cerrojo_canvas(bd, curso.id):
            resultados.update(
                _ejecutar_carril_canvas(
                    bd,
                    cliente_canvas,
                    llavero,
                    curso=curso,
                    ejecucion_id=ejecucion_id,
                    items=items_canvas,
                    inicio=inicio,
                    es_corrida_completa=es_corrida_completa,
                )
            )
    if items_github:
        with cerrojo_github(bd, curso.id):
            resultados.update(
                _ejecutar_carril_github(
                    bd,
                    cliente_github,
                    curso=curso,
                    ejecucion_id=ejecucion_id,
                    items=items_github,
                    inicio=inicio,
                )
            )

    ultimos = ultimos_resultados(bd, curso.id)
    ultimos.update(resultados)
    _quizas_activar_curso(bd, curso, ultimos)
    return ejecucion_id


def firmar_item_14_a_mano(bd: Session, *, curso: Curso, actor_usuario_id: uuid.UUID) -> None:
    """S4.7.3: la unica forma de escribir `VERIFICADO_A_MANO`. El llamador
    (ruta API) es responsable de exigir `curso.administrar` y de escribir la
    fila de `bitacora` con `VERIFICACION_FIRMADA_A_MANO` (S14.8.1: la
    escritura de auditoria vive junto al resto de las escrituras de la ruta,
    no aqui)."""
    _persistir(
        bd,
        curso_id=curso.id,
        ejecucion_id=uuid7(),
        item="14",
        resultado=ResultadoVerificacion.VERIFICADO_A_MANO,
        detalle={"firmado_por_declaracion": True},
    )
    ultimos = ultimos_resultados(bd, curso.id)
    _quizas_activar_curso(bd, curso, ultimos)


def ejecutar_prueba_5bis(
    bd: Session, cliente: ClienteCanvas, llavero: Llavero, *, curso: Curso, consiento: bool
) -> ResultadoVerificacion:
    """Prueba de escritura sincrona, fuera del trabajo encolado (S4.7.2):
    pasada 1 sin `specific_sections`, pasada 2 con la primera seccion."""
    ejecucion_id = uuid7()
    if not consiento:
        curso.via_anuncio_seccion = ViaAnuncioSeccion.NO_VERIFICADO.value
        return _persistir_no_verificado(
            bd,
            curso_id=curso.id,
            ejecucion_id=ejecucion_id,
            item="5-bis",
            motivo=MotivoNoVerificado.CASILLA_NO_MARCADA.value,
        )
    credencial = canvas_repo.obtener_credencial_operativa(bd, curso.id)
    if credencial is None or curso.canvas_course_id is None:
        curso.via_anuncio_seccion = ViaAnuncioSeccion.NO_VERIFICADO.value
        return _persistir_no_verificado(
            bd,
            curso_id=curso.id,
            ejecucion_id=ejecucion_id,
            item="5-bis",
            motivo="SIN_CREDENCIAL_CANVAS",
        )
    token = canvas_repo.descifrar_token(llavero, credencial)

    secciones = cliente.obtener_secciones(token, curso.canvas_course_id)
    pasada_1 = cliente.ejecutar_prueba_anuncio(token, curso.canvas_course_id, section_id=None)
    pasada_2 = (
        cliente.ejecutar_prueba_anuncio(
            token, curso.canvas_course_id, section_id=secciones[0].section_id
        )
        if secciones
        else False
    )

    if pasada_1 and pasada_2:
        via = ViaAnuncioSeccion.SECCION.value
    elif pasada_1:
        via = ViaAnuncioSeccion.CURSO.value
    else:
        via = ViaAnuncioSeccion.NINGUNA.value
    curso.via_anuncio_seccion = via

    resultado = resultado_binario(aprobado=pasada_1 and pasada_2, severidad=Severidad.INFORMATIVO)
    _persistir(
        bd,
        curso_id=curso.id,
        ejecucion_id=ejecucion_id,
        item="5-bis",
        resultado=resultado,
        detalle={"pasada_1": pasada_1, "pasada_2": pasada_2, "via_anuncio_seccion": via},
    )
    bd.flush()
    return resultado


def ejecutar_prueba_17bis(
    bd: Session, cliente: ClienteCanvas, llavero: Llavero, *, curso: Curso, consiento: bool
) -> ResultadoVerificacion:
    ejecucion_id = uuid7()
    if not consiento:
        return _persistir_no_verificado(
            bd,
            curso_id=curso.id,
            ejecucion_id=ejecucion_id,
            item="17-bis",
            motivo=MotivoNoVerificado.CASILLA_NO_MARCADA.value,
        )
    credencial = canvas_repo.obtener_credencial_operativa(bd, curso.id)
    if credencial is None or curso.canvas_course_id is None:
        return _persistir_no_verificado(
            bd,
            curso_id=curso.id,
            ejecucion_id=ejecucion_id,
            item="17-bis",
            motivo="SIN_CREDENCIAL_CANVAS",
        )
    token = canvas_repo.descifrar_token(llavero, credencial)
    exito = cliente.ejecutar_prueba_comentario_entrega(token, curso.canvas_course_id)
    if exito is None:
        return _persistir_no_verificado(
            bd,
            curso_id=curso.id,
            ejecucion_id=ejecucion_id,
            item="17-bis",
            motivo="SIN_ENTREGAS_QUE_PROBAR",
        )
    resultado = resultado_binario(aprobado=exito, severidad=Severidad.INFORMATIVO)
    _persistir(
        bd,
        curso_id=curso.id,
        ejecucion_id=ejecucion_id,
        item="17-bis",
        resultado=resultado,
        detalle={"exito": exito},
    )
    return resultado
