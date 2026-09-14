"""Catalogo cerrado de los nueve permisos (SPEC 02 S2.3, R2.1.8, A-021, A-178).

La expresion "los siete permisos concedibles" esta prohibida (RG-121): son
"los cinco concedibles" o "los siete configurables", que son cosas distintas.
"""

from __future__ import annotations

from enum import StrEnum


class Permiso(StrEnum):
    """Los nueve permisos nombrados (S2.3.1). Dos implicitos, siete configurables."""

    CURSO_VER = "curso.ver"
    CORRECCION_CORREGIR = "correccion.corregir"
    CURSO_ADMINISTRAR = "curso.administrar"
    EQUIPO_ADMINISTRAR = "equipo.administrar"
    TAREA_ADMINISTRAR = "tarea.administrar"
    MAPEO_EDITAR = "mapeo.editar"
    CORRECCION_ASIGNAR = "correccion.asignar"
    NOTA_PUBLICAR = "nota.publicar"
    COMUNICACION_ENVIAR = "comunicacion.enviar"


# Implicitos e irrevocables mientras la membresia este activa (S2.3.1): nunca
# se persisten en `membresia_curso.permisos` / `invitacion_equipo.permisos`
# (S2.3.10 regla 1) -- se conceden por el solo hecho de tener membresia activa.
PERMISOS_IMPLICITOS: frozenset[Permiso] = frozenset(
    {Permiso.CURSO_VER, Permiso.CORRECCION_CORREGIR}
)

# Los siete unicos valores que admite el array `permisos` (S2.3.1, S2.3.10 #1).
PERMISOS_CONFIGURABLES: frozenset[Permiso] = frozenset(
    {
        Permiso.CURSO_ADMINISTRAR,
        Permiso.EQUIPO_ADMINISTRAR,
        Permiso.TAREA_ADMINISTRAR,
        Permiso.MAPEO_EDITAR,
        Permiso.CORRECCION_ASIGNAR,
        Permiso.NOTA_PUBLICAR,
        Permiso.COMUNICACION_ENVIAR,
    }
)

# De los siete configurables, los NO CONCEDIBLES a un ayudante (S2.3.1, S2.3.3).
# Cerrados por diseno, no por confianza: escalada de privilegios trivial.
PERMISOS_NO_CONCEDIBLES: frozenset[Permiso] = frozenset(
    {Permiso.CURSO_ADMINISTRAR, Permiso.EQUIPO_ADMINISTRAR}
)

# Los cinco concedibles a un ayudante (S2.3.1). NUNCA llamarlos "los siete
# permisos concedibles" (RG-121): esa frase esta prohibida.
PERMISOS_CONCEDIBLES: frozenset[Permiso] = PERMISOS_CONFIGURABLES - PERMISOS_NO_CONCEDIBLES

# Valor por defecto del formulario de invitacion para un ayudante (S2.3.4):
# mapeo.editar marcado, nota.publicar sin marcar -- la configuracion conservadora.
PERMISOS_AYUDANTE_POR_DEFECTO: frozenset[Permiso] = frozenset({Permiso.MAPEO_EDITAR})

# Conjuntos preparados del formulario (S2.3.5): azucar de interfaz, nunca se
# persiste el nombre, solo la lista de permisos que marcan.
CONJUNTO_SOLO_CORREGIR: frozenset[Permiso] = frozenset()
CONJUNTO_CORREGIR_Y_PUBLICAR: frozenset[Permiso] = frozenset({Permiso.NOTA_PUBLICAR})
CONJUNTO_GESTION_COMPLETA: frozenset[Permiso] = PERMISOS_CONCEDIBLES

# Las seis acciones cerradas por ROL (S2.3.9, A-179, RG-122): unico lugar del
# codigo donde `rol_minimo='PROFESOR'` puede aparecer.
ACCIONES_SOLO_PROFESOR: frozenset[str] = frozenset(
    {
        "confirmar_posible_fusion_canvas",
        "recapturar_version_manual_fecha",
        "fijar_version_manual_sha",
        "archivar_repositorios_tarea",
        "entrar_a_operacion",
        "salir_de_modo_recuperacion",
    }
)


class PermisoInvalido(Exception):
    """422 (S2.3.10): un array de permisos viola el catalogo cerrado."""


def validar_permisos_configurables(permisos: frozenset[Permiso]) -> None:
    """Los elementos deben ser exactamente del catalogo de siete configurables."""
    fuera_de_catalogo = permisos - PERMISOS_CONFIGURABLES
    if fuera_de_catalogo:
        raise PermisoInvalido(f"permiso fuera del catalogo: {sorted(fuera_de_catalogo)}")


def validar_permisos_ayudante(permisos: frozenset[Permiso]) -> None:
    """S2.3.10: se prohibe un permiso NO CONCEDIBLE en una fila de rol AYUDANTE."""
    validar_permisos_configurables(permisos)
    no_concedibles = permisos & PERMISOS_NO_CONCEDIBLES
    if no_concedibles:
        raise PermisoInvalido(f"permiso NO CONCEDIBLE a un ayudante: {sorted(no_concedibles)}")


def validar_permisos_profesor(permisos: frozenset[Permiso]) -> None:
    """S2.3.10 #3: se exige permisos = {} cuando rol = PROFESOR."""
    if permisos:
        raise PermisoInvalido(
            "un profesor tiene los nueve permisos implicitos; permisos debe ir vacio"
        )


def permisos_efectivos(
    *, rol: str, permisos_configurados: frozenset[Permiso]
) -> frozenset[Permiso]:
    """Los permisos que una membresia realmente ejerce (S2.3.1, S2.3.2).

    Un profesor tiene los nueve de forma implicita e irrevocable, sin importar
    lo que la columna `permisos` contenga (que siempre es vacia para el, por
    S2.3.10 #3): "no existe profesor con menos permisos".
    """
    if rol == "PROFESOR":
        return frozenset(Permiso)
    return PERMISOS_IMPLICITOS | permisos_configurados
