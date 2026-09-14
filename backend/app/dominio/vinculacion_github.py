"""Reglas puras de la vinculacion con GitHub (SPEC 04 S4.6-S4.7, SPEC 06 S6.2).

Los DTOs de instalacion/organizacion viven aqui (no en el adaptador) para que
la evaluacion del item 14 del checklist (seis sub-comprobaciones, S4.7.3) sea
una funcion pura sobre datos ya obtenidos, igual que el patron ya usado en
`dominio/vinculacion_canvas.py` para las cinco comprobaciones de Canvas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class MotivoRechazoInstalacion(StrEnum):
    CUENTA_PERSONAL = "CUENTA_PERSONAL"
    ORGANIZACION_YA_VINCULADA = "ORGANIZACION_YA_VINCULADA"
    STATE_INVALIDO = "STATE_INVALIDO"


class RechazoInstalacion(Exception):
    def __init__(self, motivo: MotivoRechazoInstalacion, detalle: str = "") -> None:
        self.motivo = motivo
        self.detalle = detalle
        super().__init__(motivo.value)


def es_cuenta_de_organizacion(*, existe_como_organizacion: bool) -> bool:
    """S6.2.4: se detecta por los endpoints, sin confiar en el campo `type`.

    En GitHub real `GET /users/{login}` responde 200 tambien para una
    organizacion, asi que no distingue nada; lo que distingue es
    `GET /orgs/{login}`: 200 solo para organizaciones, 404 para una cuenta
    personal. Una cuenta personal es la que existe en `/users` y no en `/orgs`.
    """
    return existe_como_organizacion


@dataclass(frozen=True)
class CuentaUsuarioInfo:
    """Respuesta de `GET /users/{login}` (SPEC 07 S7.4.2): se persiste
    siempre el identificador numerico y el login canonico devuelto por la
    API, nunca lo tecleado (S7.6.4 regla 3)."""

    github_user_id: int
    login: str


@dataclass(frozen=True)
class InstalacionInfo:
    """Respuesta de `GET /app/installations/{id}`."""

    installation_id: int
    account_login: str
    account_id: int
    repository_selection: str
    permisos: dict[str, str] = field(default_factory=dict)
    suspendida: bool = False


@dataclass(frozen=True)
class OrganizacionInfo:
    """Respuesta de `GET /orgs/{org}` con el token de instalacion.

    `None` en cualquier campo significa "no legible con este token" (S4.7.3:
    esas sub-comprobaciones solo se cierran entonces con `VERIFICADO_A_MANO`).
    """

    default_repository_permission: str | None
    members_can_create_repositories: bool | None
    two_factor_requirement_enabled: bool | None
    cantidad_owners: int | None


# S4.6.1 (guia previa al boton "Instalar"): los cuatro permisos que se
# conceden a la App, congelados. No hay un `docs/permisos.md` materializado
# todavia -- este es el catalogo citado por S4.7.3 sub-comprobacion (b),
# derivado literalmente del texto de la guia y coherente con los datos fijos
# de `ClienteGitHubDoble` (app/adaptadores/cliente_github.py).
PERMISOS_APP_CONGELADOS: dict[str, str] = {
    "administration": "write",
    "contents": "write",
    "metadata": "read",
    "members": "write",
}


@dataclass(frozen=True)
class ResultadoItem14:
    aprobado: bool
    requiere_verificacion_a_mano: bool
    detalle: dict[str, object]


def evaluar_item_14(
    *,
    instalacion: InstalacionInfo,
    org_login_esperado: str,
    organizacion: OrganizacionInfo,
    existe_repo_perfil: bool,
) -> ResultadoItem14:
    """Las seis sub-comprobaciones de S4.7.3.

    (a) y (b) siempre son legibles con el token de instalacion (vienen del
    mismo JWT de App que resolvio la instalacion). (c) nunca bloquea por si
    sola. (d), (e) y (f) pueden ser `None` (no legibles con el token de
    instalacion): en ese caso el item entero exige `VERIFICADO_A_MANO`.
    """
    sub_a = instalacion.account_login == org_login_esperado
    permisos_extra = {
        k: v for k, v in instalacion.permisos.items() if PERMISOS_APP_CONGELADOS.get(k) != v
    }
    permisos_faltantes = {
        k: v for k, v in PERMISOS_APP_CONGELADOS.items() if instalacion.permisos.get(k) != v
    }
    sub_b = not permisos_extra and not permisos_faltantes
    sub_c = existe_repo_perfil

    algun_campo_no_legible = (
        organizacion.default_repository_permission is None
        or organizacion.members_can_create_repositories is None
        or organizacion.two_factor_requirement_enabled is None
        or organizacion.cantidad_owners is None
    )

    detalle: dict[str, object] = {
        "a_instalacion_cubre_organizacion": sub_a,
        "b_permisos_coinciden": sub_b,
        "b_permisos_faltantes": permisos_faltantes,
        "b_permisos_extra": permisos_extra,
        "c_existe_repo_github": sub_c,
        "d_default_repository_permission": organizacion.default_repository_permission,
        "e_members_can_create_repositories": organizacion.members_can_create_repositories,
        "f_two_factor_requirement_enabled": organizacion.two_factor_requirement_enabled,
        "f_cantidad_owners": organizacion.cantidad_owners,
    }

    if algun_campo_no_legible:
        return ResultadoItem14(aprobado=False, requiere_verificacion_a_mano=True, detalle=detalle)

    sub_d = organizacion.default_repository_permission == "none"
    sub_e = organizacion.members_can_create_repositories is False
    sub_f = (
        organizacion.two_factor_requirement_enabled is True
        and (organizacion.cantidad_owners or 0) >= 2
    )
    detalle["d_ok"] = sub_d
    detalle["e_ok"] = sub_e
    detalle["f_ok"] = sub_f

    aprobado = sub_a and sub_b and sub_d and sub_e and sub_f
    return ResultadoItem14(aprobado=aprobado, requiere_verificacion_a_mano=False, detalle=detalle)
