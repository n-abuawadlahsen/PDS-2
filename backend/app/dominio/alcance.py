"""Catalogo cerrado de las doce banderas de alcance (SPEC 01 S1.11, S13.3.3).

`PERFIL_ALCANCE` no es estado del dominio y no vive en base de datos: el
llamador pasa el perfil leido de la configuracion. Cada bandera lleva la fecha
comprometida que la capa 3 ("deshabilitado con motivo") escribe en pantalla --
nunca la palabra "proximamente" (S1.11).

Retirar una bandera es escribir aqui su fecha de retirada, y solo cuando su
criterio de aceptacion esta en verde (S1.11): desde ese momento la bandera
queda activa en cualquier perfil. La retirada se registra tambien en
`docs/operacion.md` con fecha, titular y criterio (CA-1.11-06).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class BanderaAlcance:
    nombre: str
    capa: int
    fecha_comprometida: str
    retirada_el: str | None = None


BANDERAS: tuple[BanderaAlcance, ...] = (
    BanderaAlcance("tarea_multientrega", 3, "23 de septiembre", retirada_el="25-09-2026"),
    BanderaAlcance("tarea_modalidad_grupal", 3, "23 de septiembre", retirada_el="25-09-2026"),
    BanderaAlcance("fechas_excepciones", 3, "23 de septiembre", retirada_el="25-09-2026"),
    BanderaAlcance("versiones_entrega", 3, "23 de septiembre", retirada_el="25-09-2026"),
    BanderaAlcance("tarea_archivado", 2, "30 de septiembre", retirada_el="25-09-2026"),
    BanderaAlcance("tablero_actividad", 2, "30 de septiembre", retirada_el="25-09-2026"),
    BanderaAlcance("repositorio_timeline", 2, "30 de septiembre", retirada_el="25-09-2026"),
    BanderaAlcance("ingesta_actividad", 2, "30 de septiembre", retirada_el="25-09-2026"),
    BanderaAlcance("mis_notificaciones", 2, "3 de octubre", retirada_el="26-09-2026"),
    BanderaAlcance("informe_diario", 2, "3 de octubre", retirada_el="26-09-2026"),
    BanderaAlcance("comunicaciones_automaticas", 3, "5 de octubre"),
    BanderaAlcance("correccion", 2, "5 de octubre"),
)

assert len(BANDERAS) == 12, "el catalogo de banderas de alcance tiene exactamente 12 (S1.11)"

NOMBRES_BANDERAS: tuple[str, ...] = tuple(b.nombre for b in BANDERAS)
_POR_NOMBRE = {b.nombre: b for b in BANDERAS}


def bandera_activa(perfil_alcance: str, nombre: str) -> bool:
    """Bajo `completo` todas estan activas; bajo `parcial`, solo las que ya
    se retiraron porque su etapa F tiene el criterio en verde."""
    if nombre not in _POR_NOMBRE:
        raise KeyError(f"bandera fuera del catalogo cerrado: {nombre}")
    return perfil_alcance == "completo" or _POR_NOMBRE[nombre].retirada_el is not None


def motivo_capa_3(nombre: str, que_falta: str) -> str:
    """Texto de un control deshabilitado con motivo (S1.11 capa 3): dice que
    falta y la fecha comprometida escrita."""
    return f"{que_falta} llega el {_POR_NOMBRE[nombre].fecha_comprometida}."


def instante_retirada(nombre: str) -> datetime | None:
    """El comienzo del dia de retirada, en la zona por defecto de los cursos
    (A-152). Es el instante en que el codigo de esa bandera entra en servicio;
    `None` si aun no se retiro."""
    retirada = _POR_NOMBRE[nombre].retirada_el
    if retirada is None:
        return None
    dia, mes, anio = (int(p) for p in retirada.split("-"))
    return datetime(anio, mes, dia, tzinfo=ZoneInfo("America/Santiago"))
