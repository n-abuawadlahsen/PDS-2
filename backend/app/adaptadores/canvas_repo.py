"""Orquesta el pegado de un token de Canvas: las cinco comprobaciones de S5.2.3
mas la persistencia de `identidad_canvas_usuario` y `credencial_canvas`
(SPEC 04 S4.5, SPEC 05 S5.2).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.adaptadores.base import ahora_utc
from app.adaptadores.cliente_canvas import ClienteCanvas
from app.adaptadores.modelos_canvas import CredencialCanvas, IdentidadCanvasUsuario
from app.adaptadores.modelos_curso import Curso
from app.adaptadores.modelos_identidad import Usuario
from app.dominio.estados import EstadoCredencialCanvas
from app.dominio.vinculacion_canvas import (
    IdentidadExistente,
    MotivoRechazoVinculacion,
    RechazoVinculacion,
    tiene_matricula_profesor_activa,
    todas_las_matriculas_profesor_limitadas_a_seccion,
    verificar_identidad,
)
from app.infraestructura.cifrado import Llavero, ValorCifrado, huella_token


def normalizar_canvas_base_url(url: str) -> str:
    """Esquema https, host en minusculas, sin barra final (S4.2.1, S5.2.8)."""
    normalizada = url.strip().lower()
    if not normalizada.startswith("https://"):
        normalizada = f"https://{normalizada.removeprefix('http://')}"
    return normalizada.rstrip("/")


def validar_instancia_permitida(*, canvas_base_url: str, instancias_permitidas: list[str]) -> None:
    if canvas_base_url not in instancias_permitidas:
        raise RechazoVinculacion(MotivoRechazoVinculacion.INSTANCIA_NO_RECONOCIDA)


def listar_cursos_disponibles(
    cliente: ClienteCanvas, bd: Session, *, token: str, canvas_base_url: str
) -> list[dict[str, object]]:
    """Lista de tarjetas del paso 2 (S4.5.3): un curso ya vinculado aparece
    deshabilitado, nombrando al curso ocupante -- nunca se oculta."""
    cursos_canvas = cliente.listar_cursos_profesor(token)
    resultado = []
    for c in cursos_canvas:
        ocupante = (
            bd.query(Curso)
            .filter(
                Curso.canvas_base_url == canvas_base_url,
                Curso.canvas_course_id == c.canvas_course_id,
            )
            .one_or_none()
        )
        resultado.append(
            {
                "canvas_course_id": c.canvas_course_id,
                "nombre": c.nombre,
                "codigo": c.codigo,
                "termino": c.termino,
                "total_estudiantes": c.total_estudiantes,
                "ya_vinculado_a": ocupante.nombre if ocupante is not None else None,
            }
        )
    return resultado


@dataclass(frozen=True)
class VinculacionCanvasCompletada:
    credencial: CredencialCanvas
    orden_respaldo: int


def vincular_canvas(
    bd: Session,
    cliente: ClienteCanvas,
    llavero: Llavero,
    *,
    curso: Curso,
    usuario: Usuario,
    token: str,
    canvas_base_url: str,
    canvas_course_id: int,
) -> VinculacionCanvasCompletada:
    """Ejecuta, en orden y siempre las cinco, las comprobaciones de S5.2.3, y
    persiste. Idempotente: un segundo pegado del mismo token es un upsert
    sobre `(curso_id, usuario_id)` (S4.5.5)."""
    # 2.a
    usuario_canvas = cliente.obtener_usuario_actual(token)

    # 2.b
    matriculas = cliente.obtener_matriculas_profesor(token, canvas_course_id)
    if not tiene_matricula_profesor_activa(matriculas):
        raise RechazoVinculacion(MotivoRechazoVinculacion.SIN_MATRICULA_PROFESOR)
    if todas_las_matriculas_profesor_limitadas_a_seccion(matriculas):
        raise RechazoVinculacion(MotivoRechazoVinculacion.LIMITADO_A_SECCION)

    # Curso de Canvas ya vinculado a OTRO curso de la aplicacion (A-027).
    ocupante = (
        bd.query(Curso)
        .filter(
            Curso.canvas_base_url == canvas_base_url,
            Curso.canvas_course_id == canvas_course_id,
            Curso.id != curso.id,
        )
        .one_or_none()
    )
    if ocupante is not None:
        raise RechazoVinculacion(
            MotivoRechazoVinculacion.CURSO_YA_VINCULADO, detalle=ocupante.nombre
        )

    # 2.c / 2.d / 2.e
    identidad_de_otro = (
        bd.query(IdentidadCanvasUsuario)
        .filter(
            IdentidadCanvasUsuario.canvas_base_url == canvas_base_url,
            IdentidadCanvasUsuario.canvas_user_id == usuario_canvas.canvas_user_id,
            IdentidadCanvasUsuario.usuario_id != usuario.id,
        )
        .one_or_none()
    )
    if identidad_de_otro is not None:
        raise RechazoVinculacion(MotivoRechazoVinculacion.IDENTIDAD_YA_VINCULADA_A_OTRO_USUARIO)

    identidad_propia = (
        bd.query(IdentidadCanvasUsuario)
        .filter(
            IdentidadCanvasUsuario.usuario_id == usuario.id,
            IdentidadCanvasUsuario.canvas_base_url == canvas_base_url,
        )
        .one_or_none()
    )
    verificar_identidad(
        canvas_user_id_devuelto=usuario_canvas.canvas_user_id,
        identidad_previa=IdentidadExistente(identidad_propia.canvas_user_id)
        if identidad_propia is not None
        else None,
    )

    ahora = ahora_utc()
    if identidad_propia is None:
        bd.add(
            IdentidadCanvasUsuario(
                usuario_id=usuario.id,
                canvas_base_url=canvas_base_url,
                canvas_user_id=usuario_canvas.canvas_user_id,
                verificada_en=ahora,
            )
        )
    else:
        identidad_propia.ultima_confirmacion_en = ahora

    # Persistencia de la credencial (upsert sobre curso_id+usuario_id).
    valor_cifrado = llavero.cifrar(token.encode(), curso_id=curso.id)
    existente = (
        bd.query(CredencialCanvas)
        .filter(CredencialCanvas.curso_id == curso.id, CredencialCanvas.usuario_id == usuario.id)
        .one_or_none()
    )
    hay_operativa_valida = (
        bd.query(CredencialCanvas)
        .filter(
            CredencialCanvas.curso_id == curso.id,
            CredencialCanvas.orden_respaldo == 0,
            CredencialCanvas.estado == EstadoCredencialCanvas.VALIDA.value,
        )
        .one_or_none()
        is not None
    )

    if existente is not None:
        orden_respaldo = existente.orden_respaldo
        existente.token_cifrado = valor_cifrado.texto_cifrado
        existente.nonce = valor_cifrado.nonce
        existente.version_clave = valor_cifrado.version_clave
        existente.huella = huella_token(token)
        existente.canvas_user_id = usuario_canvas.canvas_user_id
        existente.estado = EstadoCredencialCanvas.VALIDA.value
        existente.fallos_403_consecutivos = 0
        credencial = existente
    else:
        # S5.2.4: sin operativa valida, entra como operativa de inmediato;
        # con una operativa valida, entra como respaldo (max + 1).
        if hay_operativa_valida:
            maximo = (
                bd.query(CredencialCanvas.orden_respaldo)
                .filter(CredencialCanvas.curso_id == curso.id)
                .order_by(CredencialCanvas.orden_respaldo.desc())
                .limit(1)
                .scalar()
            )
            orden_respaldo = (maximo or 0) + 1
        else:
            orden_respaldo = 0
        credencial = CredencialCanvas(
            curso_id=curso.id,
            usuario_id=usuario.id,
            token_cifrado=valor_cifrado.texto_cifrado,
            nonce=valor_cifrado.nonce,
            version_clave=valor_cifrado.version_clave,
            huella=huella_token(token),
            canvas_user_id=usuario_canvas.canvas_user_id,
            estado=EstadoCredencialCanvas.VALIDA.value,
            orden_respaldo=orden_respaldo,
            consentimiento_en=ahora,
        )
        bd.add(credencial)

    curso.canvas_base_url = canvas_base_url
    curso.canvas_course_id = canvas_course_id
    if curso.estado == "BORRADOR":
        curso.estado = "VINCULANDO"
    curso.actualizado_en = ahora

    bd.flush()
    return VinculacionCanvasCompletada(credencial=credencial, orden_respaldo=orden_respaldo)


def descifrar_token(llavero: Llavero, credencial: CredencialCanvas) -> str:
    valor = ValorCifrado(
        version_clave=credencial.version_clave,
        nonce=credencial.nonce,
        texto_cifrado=credencial.token_cifrado,
    )
    return llavero.descifrar(valor, curso_id=credencial.curso_id).decode()


def obtener_credencial_operativa(bd: Session, curso_id: uuid.UUID) -> CredencialCanvas | None:
    return (
        bd.query(CredencialCanvas)
        .filter(CredencialCanvas.curso_id == curso_id, CredencialCanvas.orden_respaldo == 0)
        .one_or_none()
    )
