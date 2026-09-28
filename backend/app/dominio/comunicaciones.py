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
from datetime import datetime, timedelta
from html import escape

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


# --- Etapa F10: catalogo, guardas completas, franja y tope (S11.2.3, S11.6) ---


@dataclass(frozen=True)
class Evento:
    clave: str
    alcance: str  # CURSO | TAREA
    activo_por_defecto: bool
    prioridad: int  # menor = sale antes cuando manda el tope diario
    es_recordatorio: bool  # lo alcanza la supresion SOLO_RECORDATORIOS
    para_invitados: bool  # lo recibe un estudiante con matricula `invited`


# S11.6.1: catalogo cerrado. Prioridad fija de S11.6.5: lo que caduca hoy,
# lo que desbloquea, lo que puede esperar.
EVENTOS: dict[str, Evento] = {
    e.clave: e
    for e in (
        Evento("proximidad_cierre", "TAREA", True, 0, True, False),
        Evento("repositorio_disponible", "TAREA", True, 1, False, True),
        Evento("invitacion_aceptada", "TAREA", True, 2, False, True),
        Evento("recordatorio_invitacion", "TAREA", True, 3, True, False),
        Evento("cambio_de_fecha", "TAREA", True, 3, False, False),
        Evento("correccion_publicada", "TAREA", False, 4, False, False),
        Evento("recordatorio_mapeo", "CURSO", True, 5, True, False),
    )
}
TOPE_DIARIO_AUTOMATICOS = 3
HORA_APERTURA = 8
HORA_CIERRE = 21
DIAS_SUSPENSION_MAXIMA = 7
_EVENTOS_INVITADOS = frozenset(e.clave for e in EVENTOS.values() if e.para_invitados)
_EVENTOS_RECORDATORIO = frozenset(e.clave for e in EVENTOS.values() if e.es_recordatorio)

# S11.2.4: cada motivo pertenece a un solo estado.
MOTIVOS_POR_ESTADO: dict[str, tuple[str, ...]] = {
    "CADUCADO": ("CADUCIDAD_ALCANZADA", "SUSPENSION_PROLONGADA"),
    "SUPRIMIDO": (
        "MATRICULA_NO_ACTIVA",
        "SUPRESION_POR_ESTUDIANTE",
        "REGLA_DESACTIVADA",
        "YA_ACEPTADO",
        "MAPEO_YA_VIGENTE",
        "ENTREGA_EXCLUIDA",
        "NO_ES_DESTINATARIO_VALIDO",
        "FUERA_DEL_GRUPO",
        "TAREA_REGISTRO_AUSENTE",
    ),
    "DIFERIDO": (
        "MODO_SOLO_LECTURA",
        "SUSPENSION_DE_CURSO",
        "VENTANA_TRAS_RESTAURACION",
        "PUBLICACION_PENDIENTE",
        "CUOTA_AGOTADA",
    ),
    "CANCELADO": ("CURSO_ARCHIVADO", "TAREA_ARCHIVADA", "ENTREGA_ELIMINADA", "ACCION_DOCENTE"),
}


def guardas_outbox(
    *,
    ahora: datetime,
    caduca_en: datetime | None,
    estado_estudiante: str | None,
    evento: str | None = None,
    automatico: bool = False,
    supresion_alcance: str | None = None,
    regla_activa: bool = True,
    modo_escritura: str = "COMPLETO",
    comunicaciones_salientes: str = "ACTIVAS",
    canal: str | None = None,
    en_ventana_supresion: bool = False,
) -> tuple[EstadoMensaje, str] | None:
    """S11.2.3 (RG-039): las siete guardas en su orden fijo; gana la primera.
    Corren dentro del despacho, justo antes de cada intento. La pantalla
    «por que no salio» llama a esta misma funcion."""
    # 1. Caducidad.
    if caduca_en is not None and caduca_en <= ahora:
        return EstadoMensaje.CADUCADO, "CADUCIDAD_ALCANZADA"
    # 2. Matricula del destinatario (S11.7.5: `invited` recibe solo lo que
    #    le permite entrar al repositorio).
    if estado_estudiante is not None:
        if estado_estudiante not in (
            EstadoEstudiante.ACTIVO.value,
            EstadoEstudiante.INVITADO.value,
        ):
            return EstadoMensaje.SUPRIMIDO, "MATRICULA_NO_ACTIVA"
        if (
            estado_estudiante == EstadoEstudiante.INVITADO.value
            and automatico
            and evento not in _EVENTOS_INVITADOS
        ):
            return EstadoMensaje.SUPRIMIDO, "MATRICULA_NO_ACTIVA"
    # 3. Supresion pedida por el estudiante (solo automaticos).
    if automatico and supresion_alcance is not None:
        if supresion_alcance == "TODAS_AUTOMATICAS" or evento in _EVENTOS_RECORDATORIO:
            return EstadoMensaje.SUPRIMIDO, "SUPRESION_POR_ESTUDIANTE"
    # 4. Interruptor del evento.
    if not regla_activa:
        return EstadoMensaje.SUPRIMIDO, "REGLA_DESACTIVADA"
    # 5. Curso en solo lectura.
    if modo_escritura == "SOLO_LECTURA":
        return EstadoMensaje.DIFERIDO, "MODO_SOLO_LECTURA"
    # 6. Comunicaciones del curso suspendidas: nunca detiene el CORREO.
    if comunicaciones_salientes == "SUSPENDIDAS" and (canal or "").startswith("CANVAS_"):
        return EstadoMensaje.DIFERIDO, "SUSPENSION_DE_CURSO"
    # 7. Ventana tras una restauracion.
    if en_ventana_supresion:
        return EstadoMensaje.DIFERIDO, "VENTANA_TRAS_RESTAURACION"
    return None


def cuenta_para_tope(*, evento: str, origen: str, canal: str) -> bool:
    """S11.6.5: el tope cuenta los automaticos a un estudiante; los manuales y
    los anuncios no."""
    return origen == "AUTOMATICO" and evento in EVENTOS and canal != "CANVAS_ANUNCIO"


def exento_de_franja(*, evento: str, origen: str, ventana: str | None) -> bool:
    """La ventana H6 de `proximidad_cierre` y todo lo manual salen a su hora."""
    return origen != "AUTOMATICO" or (evento == "proximidad_cierre" and ventana == "H6")


def siguiente_apertura(local: datetime) -> datetime | None:
    """`None` si `local` esta dentro de 08:00-21:00; si no, la proxima 08:00
    del dia del curso (misma zona que `local`)."""
    if HORA_APERTURA <= local.hour < HORA_CIERRE:
        return None
    base = local if local.hour < HORA_APERTURA else local + timedelta(days=1)
    return base.replace(hour=HORA_APERTURA, minute=0, second=0, microsecond=0)


def orden_de_prioridad(evento: str) -> int:
    return EVENTOS[evento].prioridad if evento in EVENTOS else 9


# --- Validacion de plantillas editables (S11.2.5, A-126) ---

_EMOJI = re.compile("[\U0001f300-\U0001faff\u2600-\u27bf]")
_ETIQUETA = re.compile(r"</?\s*([a-zA-Z0-9]+)[^>]*>")
_ETIQUETAS_PERMITIDAS = frozenset({"p", "ul", "li", "a", "strong"})
# Nombres de variable que resolverian a otra persona (S11.7.3).
ESPACIOS_DE_TERCEROS = ("integrante", "companero", "otro", "miembros", "estudiantes")


def variables_de(texto: str) -> set[str]:
    return set(_VARIABLE.findall(texto))


def nombra_a_terceros(variable: str) -> bool:
    espacio = variable.split(".", 1)[0]
    return espacio in ESPACIOS_DE_TERCEROS or variable == "fecha_efectiva.origen"


def validar_plantilla(*, clave: str, canal: str, asunto: str, cuerpo: str) -> list[str]:
    """Errores que impiden guardar, cada uno nombrando lo que falla."""
    base = PLANTILLAS.get(clave)
    if base is None:
        return [f"no existe la plantilla {clave}"]
    errores = []
    if len(asunto) > 255:
        errores.append("el asunto supera los 255 caracteres")
    for texto in (asunto, cuerpo):
        if texto.count("{{") != texto.count("}}"):
            errores.append("hay una variable sin cerrar")
        for v in variables_de(texto):
            if v not in base.variables:
                errores.append(f"la variable {{{{{v}}}}} no existe para {clave}")
            elif nombra_a_terceros(v):
                errores.append(f"la variable {{{{{v}}}}} nombra a otra persona")
        if _EMOJI.search(texto):
            errores.append("los mensajes no llevan emojis")
    presentes = variables_de(asunto) | variables_de(cuerpo)
    for obligatoria in sorted(base.obligatorias - presentes):
        errores.append(f"falta la variable obligatoria {{{{{obligatoria}}}}}")
    etiquetas = {m.lower() for m in _ETIQUETA.findall(cuerpo)}
    if canal in ("CANVAS_CONVERSACION", "CANVAS_COMENTARIO") and etiquetas:
        errores.append("este canal es de texto plano: sin etiquetas HTML")
    elif etiquetas - _ETIQUETAS_PERMITIDAS:
        errores.append("solo se admiten las etiquetas p, ul, li, a y strong")
    return errores


# --- Plantillas de los eventos de F10 (texto plano, «tu», sin emojis) ---

_PIE_RESPUESTA = (
    "\n"
    "Si tienes dudas, responde a este mensaje en Canvas: llegará a {{curso.titular}}, "
    "del equipo docente del curso.\n"
)


def _plantilla(
    clave: str, asunto: str, cuerpo: str, obligatorias: frozenset[str] = frozenset()
) -> Plantilla:
    variables = frozenset(_VARIABLE.findall(asunto + cuerpo))
    return Plantilla(clave, 1, asunto, cuerpo, variables, obligatorias)


RECORDATORIO_MAPEO = _plantilla(
    "recordatorio_mapeo",
    "[{{curso.codigo}}] Registra tu cuenta de GitHub",
    "[{{curso.codigo}}] Registra tu cuenta de GitHub\n"
    "\n"
    "Hola {{estudiante.nombre}}:\n"
    "\n"
    "Todavía no tenemos registrada tu cuenta de GitHub en el curso {{curso.nombre}}. Sin ella "
    "no podemos crear tu repositorio. Entra a la tarea de registro en Canvas y escribe tu "
    "usuario de GitHub.\n" + _PIE_RESPUESTA,
)

RECORDATORIO_INVITACION = _plantilla(
    "recordatorio_invitacion",
    "[{{curso.codigo}}] Tu invitación a {{repositorio.nombre}} sigue pendiente",
    "[{{curso.codigo}}] Tu invitación a {{repositorio.nombre}} sigue pendiente\n"
    "\n"
    "Hola {{estudiante.nombre}}:\n"
    "\n"
    "Todavía no aceptas la invitación de GitHub a tu repositorio de «{{tarea.nombre}}».\n"
    "\n"
    "{{acceso.instrucciones}}\n"
    "\n"
    "Dirección del repositorio:\n"
    "{{repositorio.url}}\n" + _PIE_RESPUESTA,
    frozenset({"repositorio.url"}),
)

PROXIMIDAD_CIERRE = _plantilla(
    "proximidad_cierre",
    "[{{curso.codigo}}] Se acerca tu fecha de cierre de «{{entrega.nombre}}»",
    "[{{curso.codigo}}] Se acerca tu fecha de cierre de «{{entrega.nombre}}»\n"
    "\n"
    "Hola {{estudiante.nombre}}:\n"
    "\n"
    "Tu fecha de cierre de «{{entrega.nombre}}» ({{tarea.nombre}}) es {{entrega.fecha_cierre}}. "
    "Se registrará el último commit de tu repositorio anterior a esa hora.\n" + _PIE_RESPUESTA,
    frozenset({"entrega.fecha_cierre"}),
)

PROXIMIDAD_CIERRE_FECHA_CAMBIO = _plantilla(
    "proximidad_cierre_fecha_cambio",
    "[{{curso.codigo}}] Tu fecha de cierre de «{{entrega.nombre}}» cambió",
    "[{{curso.codigo}}] Tu fecha de cierre de «{{entrega.nombre}}» cambió\n"
    "\n"
    "Hola {{estudiante.nombre}}:\n"
    "\n"
    "La fecha cambió: tu fecha de cierre de «{{entrega.nombre}}» ({{tarea.nombre}}) ahora es "
    "{{entrega.fecha_cierre}}.\n" + _PIE_RESPUESTA,
    frozenset({"entrega.fecha_cierre"}),
)

# S11.6.5: fusion antes que diferir.
REPOSITORIO_Y_CIERRE = _plantilla(
    "repositorio_y_cierre",
    "Tu repositorio para «{{tarea.nombre}}» está listo",
    REPOSITORIO_DISPONIBLE.cuerpo + "\n"
    "Recuerda: tu fecha de cierre de «{{entrega.nombre}}» es {{entrega.fecha_cierre}}.\n",
    frozenset({"repositorio.url", "repositorio.nombre", "organizacion.nombre"}),
)

CAMBIO_FECHA_DIRECTO = _plantilla(
    "cambio_fecha_directo",
    "[{{curso.codigo}}] Tu fecha de cierre de «{{entrega.nombre}}» ha cambiado",
    "[{{curso.codigo}}] Tu fecha de cierre de «{{entrega.nombre}}» ha cambiado\n"
    "\n"
    "Hola {{estudiante.nombre}}:\n"
    "\n"
    "Tu fecha de cierre de «{{entrega.nombre}}» ({{tarea.nombre}}) ha cambiado: ahora es "
    "{{entrega.fecha_cierre}}.\n" + _PIE_RESPUESTA,
    frozenset({"entrega.fecha_cierre"}),
)

CAMBIO_FECHA_GRUPO = _plantilla(
    "cambio_fecha_grupo",
    "[{{curso.codigo}}] La fecha de cierre del grupo {{grupo.nombre}} ha cambiado",
    "[{{curso.codigo}}] La fecha de cierre del grupo {{grupo.nombre}} ha cambiado\n"
    "\n"
    "Hola {{estudiante.nombre}}:\n"
    "\n"
    "La fecha de cierre del grupo {{grupo.nombre}} para «{{entrega.nombre}}» ({{tarea.nombre}}) "
    "ha cambiado: ahora es {{entrega.fecha_cierre}}.\n" + _PIE_RESPUESTA,
    frozenset({"entrega.fecha_cierre"}),
)

CORRECCION_PUBLICADA = _plantilla(
    "correccion_publicada",
    "[{{curso.codigo}}] Ya está tu nota de «{{entrega.nombre}}»",
    "[{{curso.codigo}}] Ya está tu nota de «{{entrega.nombre}}»\n"
    "\n"
    "Hola {{estudiante.nombre}}:\n"
    "\n"
    "Ya está publicada tu nota de «{{entrega.nombre}}» ({{tarea.nombre}}): {{correccion.nota}}. "
    "El comentario del equipo docente está en Canvas, en tu entrega.\n" + _PIE_RESPUESTA,
)

MANUAL = _plantilla(
    "manual",
    "[{{curso.codigo}}] {{mensaje.asunto}}",
    "[{{curso.codigo}}] {{mensaje.asunto}}\n"
    "\n"
    "{{mensaje.cuerpo}}\n"
    "\n"
    "Escrito por {{docente.nombre}}, equipo docente de {{curso.codigo}}.\n" + _PIE_RESPUESTA,
)

for _p in (
    RECORDATORIO_MAPEO,
    RECORDATORIO_INVITACION,
    PROXIMIDAD_CIERRE,
    PROXIMIDAD_CIERRE_FECHA_CAMBIO,
    REPOSITORIO_Y_CIERRE,
    CAMBIO_FECHA_DIRECTO,
    CAMBIO_FECHA_GRUPO,
    CORRECCION_PUBLICADA,
    MANUAL,
):
    PLANTILLAS[_p.clave] = _p


# --- Anuncio automatico de cambio de fecha (S11.8.4): contenido fijo ---


def anuncio_cambio_fecha(
    *,
    tarea: str,
    entrega: str,
    anterior: str,
    nueva: str,
    a_quien: str,
    seccion_afectada: str | None = None,
    salvaguarda: bool = False,
    linea_version: str | None = None,
    enlace_canvas: str | None = None,
    tabla_secciones: list[tuple[str, str]] | None = None,
) -> tuple[str, str]:
    """Titulo y HTML (cinco etiquetas). Nunca nombres de estudiantes, el
    origen de la regla ni el motivo del cambio."""
    titulo = f"Cambio de fecha — {tarea} · {entrega}"[:120]
    e = escape
    partes = []
    if seccion_afectada:
        partes.append(f"<p>Esto afecta a la sección {e(seccion_afectada)}.</p>")
    partes.append(f"<p>Cambió la fecha de cierre de «{e(entrega)}» de la tarea «{e(tarea)}».</p>")
    if tabla_secciones:
        partes.append(
            "<ul>" + "".join(f"<li>{e(s)}: {e(f)}</li>" for s, f in tabla_secciones) + "</ul>"
        )
    else:
        partes.append(f"<p>Antes: {e(anterior)}. Ahora: <strong>{e(nueva)}</strong>.</p>")
    partes.append(f"<p>Aplica a: {e(a_quien)}.</p>")
    if salvaguarda:
        partes.append(
            "<p>Si tienes una fecha distinta acordada con el equipo docente, "
            "se mantiene la tuya.</p>"
        )
    if linea_version:
        partes.append(f"<p>{e(linea_version)}</p>")
    if enlace_canvas:
        partes.append(f'<p><a href="{e(enlace_canvas)}">Ver la tarea en Canvas</a></p>')
    partes.append("<p>Aviso automático del sistema de gestión del curso.</p>")
    return titulo, "".join(partes)
