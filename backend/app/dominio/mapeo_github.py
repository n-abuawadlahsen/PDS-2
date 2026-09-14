"""Reglas puras del mapeo estudiante <-> GitHub (SPEC 07 S7.4-S7.6).

Extraccion del candidato desde el texto de la entrega, elegibilidad de una
cuenta de GitHub (una sola funcion, S7.5.1), y las decisiones de la maquina
de nueve estados que no requieren I/O. Las llamadas HTTP y las escrituras
viven en `app/adaptadores/mapeo_github_repo.py`.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from enum import StrEnum

from app.dominio.estados import EstadoMapeoGithub

# S7.4.2: cuatro patrones, aplicados en este orden. Un login de GitHub admite
# alfanumericos y guiones, no empieza ni termina en guion, hasta 39 caracteres
# (aproximado -- el guardian real es la validacion en vivo contra GitHub que
# sigue a esta extraccion, nunca esta regex por si sola).
_PATRON_LOGIN = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?"
_PATRON_URL_PERFIL = re.compile(rf"github\.com/({_PATRON_LOGIN})", re.IGNORECASE)
_PATRON_ARROBA = re.compile(rf"@({_PATRON_LOGIN})\b")
_PATRON_LOGIN_DESNUDO = re.compile(rf"^{_PATRON_LOGIN}$")
_PATRON_EMAIL_NOREPLY = re.compile(
    rf"(?:\d+\+)?({_PATRON_LOGIN})@users\.noreply\.github\.com", re.IGNORECASE
)


def limpiar_html(texto_html: str) -> str:
    """S7.4.2: el cuerpo de la entrega es HTML, no texto plano."""
    sin_etiquetas = re.sub(r"<[^>]+>", " ", texto_html)
    decodificado = html.unescape(sin_etiquetas)
    return re.sub(r"\s+", " ", decodificado).strip()


@dataclass(frozen=True)
class CandidatoExtraido:
    login: str | None
    texto_crudo: str


def extraer_candidato(texto_html: str) -> CandidatoExtraido:
    """S7.4.2: si ningun patron casa, o casan dos candidatos distintos con el
    mismo patron, el resultado es ambiguo (`login=None`) -> `NO_RESUELTO`.

    S7.4.2 enumera el orden "URL de perfil, arroba, login desnudo, correo
    `...@users.noreply.github.com`", pero un correo noreply *tambien* casa con
    el patron arroba (`@users` es lo que sigue al `@`, antes de
    `.noreply.github.com`): probarlo antes que el correo noreply extraeria
    siempre el candidato equivocado (`users`) de cualquier correo noreply real.
    Por eso el correo noreply, mas especifico, se prueba antes que arroba;
    URL de perfil y login desnudo no se superponen con ningun otro patron y
    conservan el orden literal del SPEC."""
    texto = limpiar_html(texto_html)

    for patron in (_PATRON_URL_PERFIL, _PATRON_EMAIL_NOREPLY, _PATRON_ARROBA):
        candidatos = {m.group(1) for m in patron.finditer(texto)}
        if len(candidatos) == 1:
            return CandidatoExtraido(login=next(iter(candidatos)), texto_crudo=texto)
        if len(candidatos) > 1:
            return CandidatoExtraido(login=None, texto_crudo=texto)

    if _PATRON_LOGIN_DESNUDO.match(texto):
        return CandidatoExtraido(login=texto, texto_crudo=texto)

    return CandidatoExtraido(login=None, texto_crudo=texto)


@dataclass(frozen=True)
class ContextoElegibilidad:
    """S7.5.1: los cuatro hechos que hacen no elegible a una cuenta, ya
    resueltos por el llamador (esta funcion no lee ni escribe nada)."""

    es_del_equipo_docente_activo: (
        bool  # perfil de cualquier profesor/ayudante ACTIVO de cualquier curso
    )
    es_miembro_equipo_lectura_github: (
        bool  # capitulo 6: equipo `docentes` de GitHub de cualquier curso
    )
    es_owner_de_la_organizacion: bool
    es_cuenta_bot_de_la_app: bool
    tiene_mapeo_vigente_en_otro_lado: bool  # VIGENTE para OTRO estudiante, en cualquier curso


def es_cuenta_elegible(ctx: ContextoElegibilidad) -> bool:
    """S7.5.1-S7.5.2: una sola funcion, alcance de toda la aplicacion."""
    return not (
        ctx.es_del_equipo_docente_activo
        or ctx.es_miembro_equipo_lectura_github
        or ctx.es_owner_de_la_organizacion
        or ctx.es_cuenta_bot_de_la_app
        or ctx.tiene_mapeo_vigente_en_otro_lado
    )


class MotivoRechazoMapeo(StrEnum):
    """S7.5.3 "puerta del docente": rechazo inmediato, sin persistir nada."""

    CUENTA_NO_EXISTE = "CUENTA_NO_EXISTE"
    ES_ORGANIZACION = "ES_ORGANIZACION"
    CUENTA_NO_ELEGIBLE = "CUENTA_NO_ELEGIBLE"
    CUENTA_YA_ASIGNADA = "CUENTA_YA_ASIGNADA"


class RechazoMapeo(Exception):
    def __init__(self, motivo: MotivoRechazoMapeo, detalle: str = "") -> None:
        self.motivo = motivo
        self.detalle = detalle
        super().__init__(motivo.value)


def texto_comentario_resultado(
    estado: EstadoMapeoGithub, *, login_canonico: str | None = None
) -> str:
    """S7.4.6: la aplicacion siempre responde por el mismo canal. Texto
    propio, no citado literalmente de ninguna seccion del SPEC leida (que no
    fija una redaccion exacta, solo el contenido minimo de cada caso)."""
    if estado == EstadoMapeoGithub.VIGENTE:
        return (
            f"Listo: quedo registrada tu cuenta de GitHub ({login_canonico}). "
            "Vas a recibir acceso a tu repositorio cuando corresponda."
        )
    if estado == EstadoMapeoGithub.NO_EXISTE:
        return (
            "La cuenta de GitHub que escribiste no existe. "
            "Revisa el nombre de usuario y vuelve a entregar."
        )
    if estado == EstadoMapeoGithub.ES_ORGANIZACION:
        return (
            "Lo que entregaste corresponde a una organizacion de GitHub, no a tu cuenta personal. "
            "Entrega el enlace a tu perfil personal."
        )
    if estado == EstadoMapeoGithub.EN_CONFLICTO:
        return (
            "Esa cuenta de GitHub ya fue declarada por otra persona de este curso. "
            "Si crees que es un error, contacta a tu profesor."
        )
    if estado == EstadoMapeoGithub.NO_RESUELTO:
        return (
            "No pudimos identificar un unico usuario de GitHub en tu entrega. "
            "Entrega solo el enlace a tu perfil (por ejemplo "
            "https://github.com/tu-usuario) o tu usuario, sin nada mas."
        )
    return "No pudimos procesar tu entrega. Vuelve a intentarlo."


def resultado_recibido(
    *,
    existe_como_usuario: bool,
    es_organizacion: bool,
    elegible: bool,
    hay_conflicto_en_el_curso: bool,
) -> EstadoMapeoGithub:
    """S7.6.1: a que estado transiciona un candidato `RECIBIDO` tras
    validarlo. El orden de las comprobaciones importa: existencia, luego
    tipo de cuenta, luego elegibilidad, luego conflicto con otro estudiante
    del mismo curso (S7.6.3).

    S7.5.3 "puerta de la ingesta": una cuenta no elegible no se rechaza como
    peticion (no hay a quien rechazarle nada) -- queda `NO_RESUELTO` con
    `motivo_invalidacion = CUENTA_NO_ELEGIBLE` (el llamador escribe ese
    motivo; esta funcion solo decide el estado)."""
    if not existe_como_usuario and not es_organizacion:
        return EstadoMapeoGithub.NO_EXISTE
    if es_organizacion:
        return EstadoMapeoGithub.ES_ORGANIZACION
    if not elegible:
        return EstadoMapeoGithub.NO_RESUELTO
    if hay_conflicto_en_el_curso:
        return EstadoMapeoGithub.EN_CONFLICTO
    return EstadoMapeoGithub.VIGENTE
