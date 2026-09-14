"""Reglas puras del equipo docente (SPEC 02 S2.4.2, S2.9). Sin I/O.

`cantidad_profesores_activos` la calcula la capa de adaptadores (cuenta filas
reales); estas funciones solo deciden con ese numero ya en mano.
"""

from __future__ import annotations


class UltimoProfesorActivo(Exception):
    """Invariante 2 de S2.4.2: todo curso ACTIVO conserva al menos un profesor ACTIVA."""

    MENSAJE = "promueve antes a otro profesor"

    def __init__(self) -> None:
        super().__init__(self.MENSAJE)


def puede_retirar_o_degradar(
    *, es_profesor_activo: bool, cantidad_profesores_activos: int, curso_activo: bool
) -> None:
    """Levanta `UltimoProfesorActivo` si la accion dejaria el curso sin profesor.

    Para un ayudante (`es_profesor_activo=False`) no hay invariante que lo
    impida (S2.9.2 "Guarda").
    """
    if not curso_activo:
        return
    if es_profesor_activo and cantidad_profesores_activos <= 1:
        raise UltimoProfesorActivo()
