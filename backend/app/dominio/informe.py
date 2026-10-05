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


# Color de acento por seccion: rojo = actuar hoy, ambar = falta informacion,
# gris = silencio, azul = calendario, verde = resumen. Contraste AA sobre blanco.
_COLOR_SECCION = {1: "#b42318", 2: "#93370d", 3: "#475467", 4: "#175cd3", 5: "#216044"}
_FONDO_SECCION = {1: "#fef3f2", 2: "#fffaeb", 3: "#f2f4f7", 4: "#eff8ff", 5: "#ecfdf3"}
_FUENTE = "font-family:Lato,'Segoe UI',Arial,sans-serif"


def _total_nombrados(s: Seccion) -> int:
    return sum(len(li.items) + li.mas for li in s.lineas if li.cifra is None)


def _resumen_html(doc: DocumentoInforme) -> str:
    """Franja de cifras arriba del correo: cuanto hay en cada seccion de
    alerta, para decidir de un vistazo si hay que abrir el detalle."""
    celdas = []
    for s in doc.secciones:
        if s.numero == 5:
            continue
        color = _COLOR_SECCION[s.numero]
        celdas.append(
            f'<td style="padding:4px"><div style="background:{_FONDO_SECCION[s.numero]};'
            f'border-radius:6px;padding:10px 12px;text-align:left">'
            f'<div style="font-size:22px;font-weight:700;color:{color}">{_total_nombrados(s)}</div>'
            f'<div style="font-size:12px;color:#344054">{escape(s.titulo)}</div></div></td>'
        )
    if not celdas:
        return ""
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="margin:0 -4px 8px;table-layout:fixed"><tr>{"".join(celdas)}</tr></table>'
    )


def _pastilla(texto: str, numero: int) -> str:
    return (
        f'<span style="display:inline-block;min-width:18px;padding:1px 7px;border-radius:10px;'
        f"background:{_FONDO_SECCION.get(numero, '#f2f4f7')};"
        f"color:{_COLOR_SECCION.get(numero, '#475467')};font-size:12px;font-weight:700;"
        f'text-align:center;vertical-align:1px">{escape(texto)}</span>'
    )


def _fila_item(i: Item, url_app: str, color: str) -> str:
    """Un caso por fila: quien (destacado), que le pasa (en gris) y un enlace
    corto, en vez de una vineta con todo el texto subrayado."""
    e = escape
    url = e(url_app + i.enlace)
    nombre, sep, detalle = i.texto.partition(": ")
    detalle_html = (
        f'<div style="font-size:13px;color:#667085;margin-top:1px">{e(detalle)}</div>'
        if sep
        else ""
    )
    return (
        '<tr><td style="padding:9px 12px;border-top:1px solid #eaecf0">'
        f'<a href="{url}" style="color:#101828;font-size:14px;font-weight:600;'
        f'text-decoration:none">{e(nombre)}</a>{detalle_html}</td>'
        '<td width="56" style="padding:9px 12px;border-top:1px solid #eaecf0;'
        f'text-align:right;white-space:nowrap"><a href="{url}" style="color:{color};'
        f'font-size:13px;font-weight:600;text-decoration:none">Ver ›</a></td></tr>'
    )


def _linea_html(li: Linea, url_app: str, numero: int) -> str:
    e = escape
    if li.cifra is not None:
        return (
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            '<tr><td style="padding:7px 0;border-top:1px solid #eaecf0;font-size:14px">'
            f"{e(li.titulo)}</td>"
            '<td style="padding:7px 0;border-top:1px solid #eaecf0;font-size:16px;'
            f'text-align:right;font-weight:700;color:#101828">{e(li.cifra)}</td></tr></table>'
        )
    color = _COLOR_SECCION.get(numero, "#475467")
    filas = "".join(_fila_item(i, url_app, color) for i in li.items)
    extras = []
    if li.mas:
        extras.append(f"y {li.mas} más en la plataforma")
    if li.contados_en_otra_seccion:
        extras.append(f"{li.contados_en_otra_seccion} ya nombrados más arriba")
    if extras:
        filas += (
            '<tr><td colspan="2" style="padding:7px 12px;border-top:1px solid #eaecf0;'
            f'font-size:12px;color:#667085;background:#f9fafb">{e(" · ".join(extras))}</td></tr>'
        )
    return (
        '<div style="margin-top:10px">'
        f'<div style="font-size:14px;font-weight:700;color:#101828;margin-bottom:6px">'
        f"{e(li.titulo)} {_pastilla(str(len(li.items) + li.mas), numero)}</div>"
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="border:1px solid #eaecf0;border-top:0;border-radius:6px;'
        f'border-collapse:separate">{filas}</table></div>'
    )


def renderizar_html(doc: DocumentoInforme, *, url_base: str, url_app: str, pie: str) -> str:
    """Correo de una columna con tablas y estilos en linea (los clientes de
    correo ignoran <style> y CSS moderno), sin imagenes ni recursos remotos."""
    e = escape
    partes = [
        f'<div style="background:#f6f7f8;padding:16px 8px;{_FUENTE};color:#24313a">',
        '<div style="max-width:600px;margin:0 auto;background:#ffffff;border:1px solid #d6dce1;'
        'border-radius:8px;overflow:hidden">',
        # Cabecera
        '<div style="border-top:4px solid #b42318;padding:20px 24px 12px">',
        f'<div style="font-size:12px;color:#596773;text-transform:uppercase;letter-spacing:.05em">'
        f"{e(doc.curso_codigo)} · Informe docente diario</div>",
        f'<h1 style="font-size:20px;line-height:1.3;margin:4px 0 2px;color:#101828">'
        f"{e(doc.curso_nombre)}</h1>",
        f'<div style="font-size:14px;color:#596773">{doc.fecha:%d-%m-%Y} · '
        f"{e(doc.ventana_texto)}</div>",
        "</div>",
        '<div style="padding:4px 24px 20px">',
    ]
    if doc.aviso_datos_viejos:
        partes.append(
            '<div style="background:#fffaeb;border:1px solid #fedf89;border-radius:6px;'
            f'padding:10px 12px;font-size:14px;color:#93370d;margin:8px 0">'
            f"<strong>Atención:</strong> {e(doc.aviso_datos_viejos)}</div>"
        )
    if doc.sin_alertas:
        partes.append(
            '<div style="background:#ecfdf3;border:1px solid #abefc6;border-radius:6px;'
            'padding:10px 12px;font-size:14px;color:#085d3a;margin:8px 0">'
            "<strong>✓ Nada requiere tu atención hoy.</strong></div>"
        )
    partes.append(_resumen_html(doc))
    partes.append(
        '<table role="presentation" cellpadding="0" cellspacing="0" style="margin:8px 0 4px">'
        f'<tr><td style="background:#b42318;border-radius:6px"><a href="{e(url_base)}" '
        'style="display:inline-block;padding:10px 18px;color:#ffffff;font-size:14px;'
        'font-weight:700;text-decoration:none">Abrir en la plataforma</a></td></tr></table>'
    )
    for s in doc.secciones:
        color = _COLOR_SECCION.get(s.numero, "#475467")
        partes.append(
            '<div style="margin-top:28px">'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="border-bottom:2px solid {color}"><tr>'
            f'<td style="padding-bottom:6px"><h2 style="font-size:17px;margin:0;color:{color}">'
            f"{e(s.titulo)}</h2></td>"
        )
        if s.numero != 5:
            partes.append(
                '<td style="padding-bottom:6px;text-align:right">'
                f"{_pastilla(str(_total_nombrados(s)), s.numero)}</td>"
            )
        partes.append("</tr></table>")
        if s.encabezado:
            partes.append(
                f'<p style="color:#667085;font-size:13px;margin:6px 0 0">{e(s.encabezado)}</p>'
            )
        # La tarea se muestra una vez, como subtitulo, no en cada linea.
        tarea_actual: str | None = None
        for li in s.lineas:
            if li.tarea and li.tarea != tarea_actual:
                partes.append(
                    '<div style="margin-top:14px;font-size:12px;font-weight:700;color:#596773;'
                    f'text-transform:uppercase;letter-spacing:.05em">{e(li.tarea)}</div>'
                )
            tarea_actual = li.tarea
            partes.append(_linea_html(li, url_app, s.numero))
        partes.append("</div>")
    partes.append("</div>")  # cuerpo
    # Pie
    partes.append(
        '<div style="background:#f6f7f8;border-top:1px solid #d6dce1;padding:14px 24px;'
        'font-size:12px;color:#596773;line-height:1.5">'
    )
    for f in doc.frescura_texto:
        partes.append(f"<div>{e(f)}</div>")
    partes.append(
        '<div style="margin-top:6px">Si los enlaces no funcionan, el informe completo está en '
        f'<a href="{e(url_base)}" style="color:#596773">{e(url_base)}</a>.</div>'
        f'<div style="margin-top:6px">{e(pie)}</div></div>'
    )
    partes.append("</div></div>")
    return "".join(partes)
