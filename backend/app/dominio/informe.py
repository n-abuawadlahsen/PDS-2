"""Informe docente diario (SPEC 11 S11.3-S11.5; A-131, A-132, A-228, A-229;
Etapa F9).

Funciones puras: quien decide si una tarea esta activa (la misma para el
trabajo y para la vista previa), como se arman las cinco secciones, la
ventana del periodo, el asunto, el texto y el HTML del correo, y que reserva
de la cuota diaria consume un envio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from html import escape

# S11.3.4: orden fijo; una seccion sin lineas se omite.
TITULOS_SECCION = {
    1: "Requiere tu atención hoy",
    2: "Información pendiente",
    3: "Sin actividad",
    4: "Próximos cierres",
    5: "Resumen del período",
}
MAX_NOMBRADOS = 10
# A-228: tope de suscriptores activos por curso y cuota diaria del despliegue.
TOPE_SUSCRIPTORES = 30
CUOTA_DIARIA = {"INFORME": 60, "OPERATIVO": 20, "MARGEN": 20}
# S11.5.4: «Enviarme el informe de hoy», dos veces por persona y dia.
TOPE_ENVIARME = 2
VENTANA_MAXIMA = timedelta(days=7)
# S11.3.5: con Canvas sin sincronizar mas de 24 h se avisa y se omite la 5.
FRESCURA_MAXIMA_CANVAS = timedelta(hours=24)
VALIDEZ_ENLACE_BAJA = timedelta(days=90)

_ESTADOS_TAREA = frozenset({"ACTIVA", "INCONSISTENTE"})
_ESTADOS_CURSO = frozenset({"ACTIVO", "CANVAS_DESVINCULADO", "GITHUB_DESVINCULADO"})
_RANGO_SEVERIDAD = {"BLOQUEANTE": 0, "ADVERTENCIA": 1, "INFORMATIVA": 2}


@dataclass(frozen=True)
class HechosTarea:
    estado_tarea: str
    estado_curso: str
    # (a) una fecha efectiva vigente de una entrega publicada aun sin cerrar
    hay_cierre_futuro_publicado: bool
    # (b) un repositorio sin terminar o un sujeto esperando informacion
    hay_repositorio_pendiente: bool
    # (c) una incidencia abierta bloqueante, VERSION_REVISAR o VERSION_ERROR
    hay_incidencia_relevante: bool


def tarea_activa(h: HechosTarea) -> bool:
    """S11.3.1: la unica definicion de «tarea activa» del requisito R2.6.1."""
    return (
        h.estado_tarea in _ESTADOS_TAREA
        and h.estado_curso in _ESTADOS_CURSO
        and (
            h.hay_cierre_futuro_publicado
            or h.hay_repositorio_pendiente
            or h.hay_incidencia_relevante
        )
    )


@dataclass(frozen=True)
class Item:
    """Algo nombrado en el informe. `clave` identifica el hecho (una
    incidencia, un repositorio) para nombrarlo una sola vez."""

    clave: str
    texto: str
    enlace: str
    severidad: str
    desde: datetime
    tarea: str | None = None
    # Otro hecho que, nombrado en una seccion mas alta, hace que este solo
    # se cuente (p. ej. el repositorio bloqueado de un estudiante sin
    # participacion, CA-11.3-08).
    relacionado: str | None = None


@dataclass
class Linea:
    titulo: str
    tarea: str | None
    items: list[Item] = field(default_factory=list)
    mas: int = 0
    contados_en_otra_seccion: int = 0
    cifra: str | None = None  # lineas de resumen: solo un numero


@dataclass
class Seccion:
    numero: int
    titulo: str
    lineas: list[Linea]
    encabezado: str | None = None


def _orden(i: Item) -> tuple[int, datetime, str]:
    return (_RANGO_SEVERIDAD.get(i.severidad, 3), i.desde, i.texto.lower())


def armar_secciones(
    candidatos: dict[int, list[tuple[str, Item]]],
    *,
    cifras: dict[int, list[tuple[str, str]]] | None = None,
    encabezados: dict[int, str] | None = None,
) -> list[Seccion]:
    """S11.3.4: cada hecho se nombra una vez, en su seccion de mayor severidad
    (la de menor numero); en las demas solo se cuenta. Dentro de una linea:
    severidad, antiguedad y nombre; mas de diez nombrados se colapsan."""
    nombrado_en: dict[str, int] = {}
    for numero in sorted(candidatos):
        for _, item in candidatos[numero]:
            nombrado_en.setdefault(item.clave, numero)
    secciones = []
    for numero in sorted(set(candidatos) | set(cifras or {})):
        lineas: dict[tuple[str | None, str], Linea] = {}
        for titulo, item in candidatos.get(numero, []):
            linea = lineas.setdefault((item.tarea, titulo), Linea(titulo, item.tarea))
            relacionado_antes = (
                item.relacionado is not None and nombrado_en.get(item.relacionado, numero) < numero
            )
            if nombrado_en[item.clave] == numero and not relacionado_antes:
                if all(i.clave != item.clave for i in linea.items):
                    linea.items.append(item)
            else:
                linea.contados_en_otra_seccion += 1
        for linea in lineas.values():
            linea.items.sort(key=_orden)
            if len(linea.items) > MAX_NOMBRADOS:
                linea.mas = len(linea.items) - MAX_NOMBRADOS
                linea.items = linea.items[:MAX_NOMBRADOS]
        ordenadas = sorted(lineas.values(), key=lambda li: ((li.tarea or ""), li.titulo))
        ordenadas += [Linea(t, None, cifra=c) for t, c in (cifras or {}).get(numero, [])]
        ordenadas = [li for li in ordenadas if li.items or li.contados_en_otra_seccion or li.cifra]
        if ordenadas:
            secciones.append(
                Seccion(
                    numero,
                    TITULOS_SECCION[numero],
                    ordenadas,
                    (encabezados or {}).get(numero),
                )
            )
    return secciones


def ventana_del_informe(
    *,
    ultimo_generado_hasta: datetime | None,
    ahora: datetime,
    curso_creado_en: datetime | None = None,
) -> tuple[datetime, datetime]:
    """S11.3.3: desde el fin de la ventana del ultimo informe GENERADO (o la
    creacion del curso), con tope de siete dias."""
    desde = ultimo_generado_hasta or curso_creado_en or (ahora - timedelta(days=1))
    return max(desde, ahora - VENTANA_MAXIMA), ahora


def asunto_informe(codigo_curso: str, fecha: date, *, requiere_atencion: bool) -> str:
    """S11.5.1: un correo por curso; el codigo va en el asunto (CA-11.5-01)."""
    asunto = f"{codigo_curso} · Informe docente del {fecha:%d-%m-%Y}"
    return f"[Requiere atención] {asunto}" if requiere_atencion else asunto


def reserva_a_consumir(solicitada: str, usados: dict[str, int]) -> str | None:
    """A-228: la reserva propia primero, luego el margen; `None` = cuota
    agotada, el envio queda DIFERIDO y no se pierde."""
    if usados.get(solicitada, 0) < CUOTA_DIARIA[solicitada]:
        return solicitada
    if solicitada != "MARGEN" and usados.get("MARGEN", 0) < CUOTA_DIARIA["MARGEN"]:
        return "MARGEN"
    return None


# --- Presentacion (texto plano y HTML de una columna, sin recursos remotos) ---


@dataclass
class DocumentoInforme:
    curso_nombre: str
    curso_codigo: str
    fecha: date
    ventana_texto: str
    frescura_texto: list[str]
    aviso_datos_viejos: str | None
    secciones: list[Seccion]
    sin_alertas: bool


def _linea_texto(li: Linea) -> str:
    prefijo = f"{li.tarea} · " if li.tarea else ""
    if li.cifra is not None:
        return f"- {li.titulo}: {li.cifra}"
    partes = [f"- {prefijo}{li.titulo} ({len(li.items) + li.mas})"]
    for i in li.items:
        partes.append(f"    · {i.texto}")
    if li.mas:
        partes.append(f"    · y {li.mas} más")
    if li.contados_en_otra_seccion:
        partes.append(f"    · {li.contados_en_otra_seccion} ya nombrados más arriba")
    return "\n".join(partes)


def renderizar_texto(doc: DocumentoInforme, *, url_base: str, pie: str) -> str:
    lineas = [
        f"Informe docente de {doc.curso_nombre} ({doc.curso_codigo}) · {doc.fecha:%d-%m-%Y}",
        doc.ventana_texto,
        *doc.frescura_texto,
    ]
    if doc.aviso_datos_viejos:
        lineas.append(doc.aviso_datos_viejos)
    lineas.append(
        f"Si no ves este correo en tu bandeja, el informe completo está siempre en {url_base}"
    )
    if doc.sin_alertas:
        lineas.append("Nada requiere tu atención hoy.")
    for s in doc.secciones:
        lineas += ["", s.titulo.upper()]
        if s.encabezado:
            lineas.append(s.encabezado)
        lineas += [_linea_texto(li) for li in s.lineas]
    lineas += ["", pie]
    return "\n".join(lineas)


def renderizar_html(doc: DocumentoInforme, *, url_base: str, url_app: str, pie: str) -> str:
    e = escape
    partes = [
        '<div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;color:#222">',
        f'<h1 style="font-size:18px">Informe docente de {e(doc.curso_nombre)} '
        f"({e(doc.curso_codigo)}) · {doc.fecha:%d-%m-%Y}</h1>",
        f'<p style="color:#555;font-size:13px">{e(doc.ventana_texto)}</p>',
    ]
    for f in doc.frescura_texto:
        partes.append(f'<p style="color:#555;font-size:13px">{e(f)}</p>')
    if doc.aviso_datos_viejos:
        partes.append(f'<p style="background:#fff3cd;padding:8px">{e(doc.aviso_datos_viejos)}</p>')
    partes.append(
        '<p style="font-size:13px">Si no ves este correo en tu bandeja, el informe completo '
        f'está siempre en <a href="{e(url_base)}">{e(url_base)}</a>.</p>'
    )
    if doc.sin_alertas:
        partes.append("<p>Nada requiere tu atención hoy.</p>")
    for s in doc.secciones:
        partes.append(f'<h2 style="font-size:16px;margin-top:20px">{e(s.titulo)}</h2>')
        if s.encabezado:
            partes.append(f'<p style="color:#555;font-size:13px">{e(s.encabezado)}</p>')
        partes.append("<ul>")
        for li in s.lineas:
            prefijo = f"{e(li.tarea)} · " if li.tarea else ""
            if li.cifra is not None:
                partes.append(f"<li>{e(li.titulo)}: <strong>{e(li.cifra)}</strong></li>")
                continue
            partes.append(f"<li>{prefijo}{e(li.titulo)} ({len(li.items) + li.mas})<ul>")
            for i in li.items:
                partes.append(f'<li><a href="{e(url_app + i.enlace)}">{e(i.texto)}</a></li>')
            if li.mas:
                partes.append(f"<li>y {li.mas} más</li>")
            if li.contados_en_otra_seccion:
                partes.append(f"<li>{li.contados_en_otra_seccion} ya nombrados más arriba</li>")
            partes.append("</ul></li>")
        partes.append("</ul>")
    partes.append(f'<p style="color:#777;font-size:12px;margin-top:24px">{e(pie)}</p></div>')
    return "".join(partes)
