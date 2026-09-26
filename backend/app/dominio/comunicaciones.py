"""Mensajes al estudiante por Canvas: plantillas, clave de idempotencia y guardas
del outbox (SPEC 11 S11.2; SPEC 08 S8.10; A-125, A-126, A-127, A-224; Etapa P8).

Motor de sustitucion pura, sin logica: `{{variable}}` y nada mas (S11.2.5).
Texto plano para los canales de Canvas (A-126), español de Chile, «tú», sin
emojis (A-154).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime

from app.dominio.estados import EstadoEstudiante, EstadoMensaje


@dataclass(frozen=True)
class Plantilla:
    clave: str
    version: int
    asunto: str
    cuerpo: str
    variables: frozenset[str]
    obligatorias: frozenset[str]


# R2.3.12 (A-127): al invitar, el mensaje dice exactamente la organizacion, el
# repositorio y su URL, por donde llega la invitacion, que la URL mostrara «no
# encontrado» hasta aceptarla, la fecha de cierre con zona y que hacer si el
# correo no llega. No afirma quien firma el correo de GitHub (A-127 [MEDIR]).
REPOSITORIO_DISPONIBLE = Plantilla(
    clave="repositorio_disponible",
    version=1,
    asunto="Tu repositorio para «{{tarea.nombre}}» está listo",
    cuerpo=(
        "Hola {{estudiante.nombre}}:\n"
        "\n"
        "Ya creamos tu repositorio de GitHub para la tarea «{{tarea.nombre}}» del curso "
        "{{curso.nombre}}.\n"
        "\n"
        "Organización de GitHub: {{organizacion.nombre}}\n"
        "Repositorio: {{repositorio.nombre}}\n"
        "Dirección del repositorio:\n"
        "{{repositorio.url}}\n"
        "\n"
        "{{acceso.instrucciones}}\n"
        "\n"
        "Fecha de cierre de la primera entrega: {{entrega.fecha_cierre}}\n"
        "\n"
        "Si la invitación no te llega, revisa la carpeta de spam y confirma que tu cuenta de "
        "GitHub registrada en el curso es {{cuenta_github.login}}. Si el problema sigue, "
        "escríbele al equipo docente.\n"
    ),
    variables=frozenset(
        {
            "estudiante.nombre",
            "tarea.nombre",
            "curso.nombre",
            "organizacion.nombre",
            "repositorio.nombre",
            "repositorio.url",
            "acceso.instrucciones",
            "entrega.fecha_cierre",
            "cuenta_github.login",
        }
    ),
    obligatorias=frozenset({"repositorio.url", "repositorio.nombre", "organizacion.nombre"}),
)

INVITACION_ACEPTADA = Plantilla(
    clave="invitacion_aceptada",
    version=1,
    asunto="Ya tienes acceso a tu repositorio de «{{tarea.nombre}}»",
    cuerpo=(
        "Hola {{estudiante.nombre}}:\n"
        "\n"
        "Aceptaste la invitación y ya tienes acceso a tu repositorio {{repositorio.nombre}} "
        "de la tarea «{{tarea.nombre}}»:\n"
        "{{repositorio.url}}\n"
    ),
    variables=frozenset(
        {"estudiante.nombre", "tarea.nombre", "repositorio.nombre", "repositorio.url"}
    ),
    obligatorias=frozenset({"repositorio.url"}),
)

# Guarda 4 de A-197: aviso obligatorio y sin interruptor, catorce dias antes
# de archivar y de nuevo al ejecutar. Nadie descubre que su repositorio paso
# a solo lectura al intentar subir un cambio.
AVISO_ARCHIVADO_PREVIO = Plantilla(
    clave="aviso_archivado_previo",
    version=1,
    asunto="Tu repositorio de «{{tarea.nombre}}» se archivará en dos semanas",
    cuerpo=(
        "Hola {{estudiante.nombre}}:\n"
        "\n"
        "El equipo docente del curso {{curso.nombre}} archivará tu repositorio "
        "{{repositorio.nombre}} de la tarea «{{tarea.nombre}}» no antes de catorce días "
        "desde este aviso:\n"
        "{{repositorio.url}}\n"
        "\n"
        "Archivado, el repositorio queda en sólo lectura: podrás seguir viéndolo y "
        "descargándolo, pero no subir cambios. Las versiones que ya entregaste no cambian.\n"
        "\n"
        "Si todavía necesitas subir algo, hazlo antes de esa fecha o escríbele al equipo "
        "docente.\n"
    ),
    variables=frozenset(
        {
            "estudiante.nombre",
            "curso.nombre",
            "tarea.nombre",
            "repositorio.nombre",
            "repositorio.url",
        }
    ),
    obligatorias=frozenset({"repositorio.nombre"}),
)

AVISO_ARCHIVADO = Plantilla(
    clave="aviso_archivado",
    version=1,
    asunto="Tu repositorio de «{{tarea.nombre}}» quedó archivado",
    cuerpo=(
        "Hola {{estudiante.nombre}}:\n"
        "\n"
        "El equipo docente archivó hoy tu repositorio {{repositorio.nombre}} de la tarea "
        "«{{tarea.nombre}}». Desde ahora está en sólo lectura: puedes verlo y descargarlo, "
        "pero no subir cambios.\n"
        "{{repositorio.url}}\n"
    ),
    variables=frozenset(
        {"estudiante.nombre", "tarea.nombre", "repositorio.nombre", "repositorio.url"}
    ),
    obligatorias=frozenset({"repositorio.nombre"}),
)

PLANTILLAS: dict[str, Plantilla] = {
    REPOSITORIO_DISPONIBLE.clave: REPOSITORIO_DISPONIBLE,
    INVITACION_ACEPTADA.clave: INVITACION_ACEPTADA,
    AVISO_ARCHIVADO_PREVIO.clave: AVISO_ARCHIVADO_PREVIO,
    AVISO_ARCHIVADO.clave: AVISO_ARCHIVADO,
}


def instrucciones_de_acceso(*, via_invitacion: bool, invitacion_url: str | None) -> str:
    """El parrafo que cambia entre `INVITADO` y `ACCESO_DIRECTO`: el motor no
    tiene condicionales, asi que la variante la decide el codigo."""
    if not via_invitacion:
        return "Ya tienes acceso al repositorio: no necesitas aceptar ninguna invitación."
    enlace = invitacion_url or "https://github.com/notifications"
    return (
        "Te enviamos una invitación de GitHub para colaborar en ese repositorio. La encuentras "
        "en tu correo y también aquí:\n"
        f"{enlace}\n"
        "\n"
        'Hasta que aceptes la invitación, la dirección del repositorio te va a mostrar "no '
        'encontrado". Es normal: GitHub oculta los repositorios privados a quien todavía no '
        "tiene acceso."
    )


class PlantillaInvalida(Exception):
    """Variable desconocida u obligatoria vacia: el mensaje no se construye."""


_VARIABLE = re.compile(r"\{\{\s*([a-z_]+\.[a-z_]+)\s*\}\}")


def renderizar(texto: str, plantilla: Plantilla, valores: dict[str, str]) -> str:
    """Sustitucion pura. Sin la URL del repositorio, `repositorio_disponible`
    incumple R2.3.12 y no se construye (S11.2.5)."""
    for obligatoria in plantilla.obligatorias:
        if not valores.get(obligatoria):
            raise PlantillaInvalida(f"falta la variable obligatoria {obligatoria}")

    def sustituir(coincidencia: re.Match[str]) -> str:
        nombre = coincidencia.group(1)
        if nombre not in plantilla.variables:
            raise PlantillaInvalida(f"variable desconocida {nombre}")
        return valores.get(nombre, "")

    return _VARIABLE.sub(sustituir, texto)


def clave_idempotencia(
    *, canal: str, destinatario: str, plantilla: str, entidad: str, generacion: int = 1
) -> str:
    """A-224: `hash(canal, destinatario, plantilla, entidad, generacion)`. Incluye
    al destinatario, asi que es siempre por persona, nunca por grupo."""
    materia = "|".join((canal, destinatario, plantilla, entidad, str(generacion)))
    return hashlib.sha256(materia.encode()).hexdigest()


def guardas_outbox(
    *, ahora: datetime, caduca_en: datetime | None, estado_estudiante: str | None
) -> tuple[EstadoMensaje, str] | None:
    """S11.2.3, guardas 1 y 2 en su orden. Las guardas 3 a 7 dependen de
    `supresion_comunicacion`, `regla_comunicacion`, `curso.modo_escritura`,
    `curso.comunicaciones_salientes` y `ventana_supresion`, que todavia no
    existen (Bloques 2 y 3). TODO(etapa-F10): completarlas aqui mismo, en
    este orden, cuando existan esas columnas."""
    if caduca_en is not None and caduca_en <= ahora:
        return EstadoMensaje.CADUCADO, "CADUCIDAD_ALCANZADA"
    if estado_estudiante is not None and estado_estudiante not in (
        EstadoEstudiante.ACTIVO.value,
        EstadoEstudiante.INVITADO.value,
    ):
        return EstadoMensaje.SUPRIMIDO, "MATRICULA_NO_ACTIVA"
    return None
