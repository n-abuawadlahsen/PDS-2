"""Censo cerrado de entidades del dominio (ARQUITECTURA.md, A-184).

"La lista es cerrada: anadir una entidad es una decision que se registra en esta
carta [ARQUITECTURA.md]". Una prueba de arquitectura falla la construccion si
existe un modelo SQLAlchemy que no esta en este censo.

El censo completo del proyecto tiene 70 entidades (SPEC 14 S14.8.1). Esta lista
solo declara las que Etapa 0 (infraestructura) y Etapa P1 (identidad y acceso)
crean; el resto se añade tabla por tabla a medida que se implementa cada etapa
siguiente del plan (docs/PLAN-IMPLEMENTACION.md), nunca de una vez adivinando
columnas que otro capitulo del SPEC todavia no fijo.
"""

from __future__ import annotations

# Etapa 0 - infraestructura propia (SPEC 14 S14.1, tabla de S14 del plan).
ENTIDADES_ETAPA_0: frozenset[str] = frozenset(
    {
        "trabajo",
        "trabajo_periodico",
        "presupuesto_api",
        "cubo_tasa",
        "bitacora",
        "incidencia",
        "sincronizacion",
        "cursor_sincronizacion",
        "salud_proveedor_curso",
        "estado_sistema",
        "resultado_invariante",
        "respaldo",
    }
)

# Etapa P1 - identidad y acceso (SPEC 02 S2.2, S2.10).
ENTIDADES_ETAPA_P1: frozenset[str] = frozenset({"usuario", "sesion", "sesion_membresia"})

# Etapa P2 - curso, equipo docente y permisos (SPEC 02 S2.4, S2.5).
ENTIDADES_ETAPA_P2: frozenset[str] = frozenset({"curso", "membresia_curso", "invitacion_equipo"})

# Etapa P3 - vinculacion con Canvas (SPEC 04 S4.2.2, SPEC 05 S5.2.2).
ENTIDADES_ETAPA_P3: frozenset[str] = frozenset({"credencial_canvas", "identidad_canvas_usuario"})

# Etapa P4 - vinculacion con GitHub y checklist de verificacion (SPEC 04 S4.6,
# S4.7; SPEC 06 S6.2, S6.10).
ENTIDADES_ETAPA_P4: frozenset[str] = frozenset(
    {
        "instalacion_github",
        "equipo_github_curso",
        "verificacion_vinculacion",
        "intento_instalacion_github",
        "verificacion_canal",
        "acceso_docente_repositorio",
    }
)

# Etapa P5 - espejo de Canvas: estudiantes, secciones y grupos (SPEC 07 S7.2).
ENTIDADES_ETAPA_P5: frozenset[str] = frozenset(
    {
        "seccion",
        "estudiante",
        "matricula",
        "conjunto_grupos",
        "grupo",
        "pertenencia_grupo",
    }
)

# Etapa P6 - mapeo estudiante <-> GitHub y Pendientes (SPEC 07 S7.2.2, S7.4-S7.8).
ENTIDADES_ETAPA_P6: frozenset[str] = frozenset({"cuenta_github", "mapeo_github"})

# Etapa P7 - tarea individual, entrega unica y repositorio base (SPEC 08 S8.2-S8.3).
ENTIDADES_ETAPA_P7: frozenset[str] = frozenset(
    {
        "assignment_canvas",
        "tarea",
        "entrega",
        "visibilidad_entrega",
        "repositorio_base",
        "archivo_repositorio_base",
    }
)

# Etapa P8 - aprovisionamiento, estado, aviso al estudiante y lectura de fechas
# (SPEC 08 S8.5-S8.10, SPEC 09 S9.3, SPEC 11 S11.2).
ENTIDADES_ETAPA_P8: frozenset[str] = frozenset(
    {
        "sujeto",
        "repositorio",
        "acceso_repositorio",
        "regla_fecha",
        "fecha_efectiva",
        "mensaje_saliente",
    }
)

CENSO: frozenset[str] = (
    ENTIDADES_ETAPA_0
    | ENTIDADES_ETAPA_P1
    | ENTIDADES_ETAPA_P2
    | ENTIDADES_ETAPA_P3
    | ENTIDADES_ETAPA_P4
    | ENTIDADES_ETAPA_P5
    | ENTIDADES_ETAPA_P6
    | ENTIDADES_ETAPA_P7
    | ENTIDADES_ETAPA_P8
)

# Valor especial admitido en bitacora.entidad ademas del censo (A-184).
ENTIDAD_SISTEMA = "sistema"
