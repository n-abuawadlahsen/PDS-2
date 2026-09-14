"""Catalogo cerrado de las doce banderas de alcance (SPEC 01 S1.11, S13.3.3).

`PERFIL_ALCANCE` no es estado del dominio y no vive en base de datos: el
llamador pasa el perfil leido de la configuracion. Cada bandera lleva la fecha
comprometida que la capa 3 ("deshabilitado con motivo") escribe en pantalla --
nunca la palabra "proximamente" (S1.11).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BanderaAlcance:
    nombre: str
    capa: int
    fecha_comprometida: str


BANDERAS: tuple[BanderaAlcance, ...] = (
    BanderaAlcance("tarea_multientrega", 3, "23 de septiembre"),
    BanderaAlcance("tarea_modalidad_grupal", 3, "23 de septiembre"),
    BanderaAlcance("fechas_excepciones", 3, "23 de septiembre"),
    BanderaAlcance("versiones_entrega", 3, "23 de septiembre"),
    BanderaAlcance("tarea_archivado", 2, "30 de septiembre"),
    BanderaAlcance("tablero_actividad", 2, "30 de septiembre"),
    BanderaAlcance("repositorio_timeline", 2, "30 de septiembre"),
    BanderaAlcance("ingesta_actividad", 2, "30 de septiembre"),
    BanderaAlcance("mis_notificaciones", 2, "3 de octubre"),
    BanderaAlcance("informe_diario", 2, "3 de octubre"),
    BanderaAlcance("comunicaciones_automaticas", 3, "5 de octubre"),
    BanderaAlcance("correccion", 2, "5 de octubre"),
)

assert len(BANDERAS) == 12, "el catalogo de banderas de alcance tiene exactamente 12 (S1.11)"

NOMBRES_BANDERAS: tuple[str, ...] = tuple(b.nombre for b in BANDERAS)
_POR_NOMBRE = {b.nombre: b for b in BANDERAS}


def bandera_activa(perfil_alcance: str, nombre: str) -> bool:
    """Bajo `parcial` ninguna de las doce esta retirada todavia; bajo
    `completo`, todas. El calendario fino de retiro llega con cada etapa F."""
    if nombre not in _POR_NOMBRE:
        raise KeyError(f"bandera fuera del catalogo cerrado: {nombre}")
    return perfil_alcance == "completo"


def motivo_capa_3(nombre: str, que_falta: str) -> str:
    """Texto de un control deshabilitado con motivo (S1.11 capa 3): dice que
    falta y la fecha comprometida escrita."""
    return f"{que_falta} llega el {_POR_NOMBRE[nombre].fecha_comprometida}."
