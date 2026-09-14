"""`ClienteGitHub`: interfaz con dos implementaciones (SPEC 06 S6.2-S6.5, S6.10).

Autenticacion en dos niveles (S6.3.1): un JWT de la App (10 minutos, firmado
con `GITHUB_APP_PRIVATE_KEY`) para llamadas de nivel App, y un token de
instalacion (1 hora, emitido con ese JWT) para todo lo demas. Ningun token de
GitHub se persiste jamas (A-038): el llamador es responsable de pedirlo cada
vez o cachearlo el mismo en memoria de proceso.

Catalogo cerrado de endpoints usados por Etapa P4 (subconjunto del catalogo
completo de S6.5, que cubre tambien aprovisionamiento de repositorios de
etapas posteriores).
"""

from __future__ import annotations

import base64
import hashlib
import threading
import time
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from urllib.parse import quote

import httpx
import jwt

from app.dominio.repositorio_github import (
    ArchivoGithub,
    InvitacionGithub,
    RepoGithubInfo,
    ResultadoInvitacion,
)
from app.dominio.vinculacion_github import CuentaUsuarioInfo, InstalacionInfo, OrganizacionInfo

_TIMEOUT_SEGUNDOS = 20.0
_GITHUB_API_VERSION = "2026-03-10"
_JWT_VIGENCIA_SEGUNDOS = 600
_JWT_MARGEN_RELOJ_SEGUNDOS = 60
_ALGORITMO_STATE = "HS256"
_EXPIRACION_STATE_INSTALACION = timedelta(minutes=15)


class FalloProveedorGithub(Exception):
    """5xx o timeout de GitHub: nunca se traduce a un diagnostico inventado (Ley 5)."""


class RechazoProveedorGithub(Exception):
    """4xx de una escritura sincrona (A-169 punto 4): el error literal del
    proveedor viaja tal cual a la pantalla, sin reinterpretarlo."""

    def __init__(self, status_code: int, mensaje_literal: str) -> None:
        self.status_code = status_code
        self.mensaje_literal = mensaje_literal
        super().__init__(f"GitHub respondio {status_code}: {mensaje_literal}")


def _mensaje_literal(respuesta: httpx.Response) -> str:
    try:
        cuerpo = respuesta.json()
    except ValueError:
        return respuesta.text[:500]
    if not isinstance(cuerpo, dict):
        return str(cuerpo)[:500]
    mensaje = str(cuerpo.get("message", ""))
    errores = cuerpo.get("errors")
    if errores:
        mensaje = f"{mensaje} {errores}"
    return mensaje[:500]


def _exigir_exito(respuesta: httpx.Response) -> None:
    if respuesta.status_code >= 500:
        raise FalloProveedorGithub(f"GitHub respondio {respuesta.status_code}")
    if respuesta.status_code >= 400:
        raise RechazoProveedorGithub(respuesta.status_code, _mensaje_literal(respuesta))


def _repo_desde_json(d: dict[str, Any]) -> RepoGithubInfo:
    return RepoGithubInfo(
        github_repo_id=int(d["id"]),
        nombre=str(d["name"]),
        full_name=str(d["full_name"]),
        owner_login=str((d.get("owner") or {}).get("login", "")),
        descripcion=d.get("description"),
        topics=tuple(d.get("topics") or ()),
        rama_por_defecto=d.get("default_branch"),
        es_plantilla=bool(d.get("is_template", False)),
        url_html=str(d.get("html_url", "")),
    )


def _cabeceras(token: str | None) -> dict[str, str]:
    cabeceras = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": _GITHUB_API_VERSION,
        "User-Agent": "proyecto2-icc4201",
    }
    if token is not None:
        cabeceras["Authorization"] = f"Bearer {token}"
    return cabeceras


# Token de instalacion para consultar cuentas publicas, por App: (token, vence).
_tokens_consulta: dict[str, tuple[str, datetime]] = {}
_cerrojo_tokens_consulta = threading.Lock()
_MARGEN_VENCIMIENTO_TOKEN = timedelta(minutes=5)


def emitir_jwt_de_app(*, app_id: str, private_key_pem_base64: str) -> str:
    """S6.3.1: 10 minutos, el maximo que GitHub admite. La clave viaja en
    base64 (S14.6.4: nunca como variable multilinea, nunca escrita a disco)."""
    clave_pem = base64.b64decode(private_key_pem_base64)
    ahora = int(time.time())
    payload = {
        "iat": ahora - _JWT_MARGEN_RELOJ_SEGUNDOS,
        "exp": ahora + _JWT_VIGENCIA_SEGUNDOS,
        "iss": app_id,
    }
    return jwt.encode(payload, clave_pem, algorithm="RS256")


class StateInstalacionInvalido(Exception):
    """S4.6.3: state ausente, invalido o caducado -- nunca se vincula por deduccion."""


@dataclass(frozen=True)
class ReclamacionesStateInstalacion:
    curso_id: str
    usuario_id: str
    jti: str


def emitir_state_instalacion(*, signing_key: str, curso_id: str, usuario_id: str, jti: str) -> str:
    """S4.6.1: JWT de 15 minutos con `curso_id`, `usuario_id` y un `jti` de un
    solo uso (A-058), firmado con `SIGNING_KEY` -- igual patron que el `state`
    de OIDC en `tokens_oidc.py`, pero para el flujo de instalacion de GitHub."""
    ahora = datetime.now(UTC)
    return jwt.encode(
        {
            "curso_id": curso_id,
            "usuario_id": usuario_id,
            "jti": jti,
            "iat": ahora,
            "exp": ahora + _EXPIRACION_STATE_INSTALACION,
        },
        signing_key,
        algorithm=_ALGORITMO_STATE,
    )


def verificar_state_instalacion(*, signing_key: str, state: str) -> ReclamacionesStateInstalacion:
    try:
        payload = jwt.decode(state, signing_key, algorithms=[_ALGORITMO_STATE])
    except jwt.PyJWTError as exc:
        raise StateInstalacionInvalido(str(exc)) from exc
    try:
        return ReclamacionesStateInstalacion(
            curso_id=payload["curso_id"], usuario_id=payload["usuario_id"], jti=payload["jti"]
        )
    except KeyError as exc:
        raise StateInstalacionInvalido(f"falta reclamacion {exc}") from exc


class ClienteGitHub(Protocol):
    def obtener_slug_app(self) -> str:
        """S4.6.1: el slug publico de la App, para construir
        `https://github.com/apps/<slug>/installations/new?state=...`. No hay
        variable de entorno para esto en el inventario cerrado de S14.6 -- se
        lee de `GET /app`, la misma fuente de verdad que todo lo demas."""
        ...

    def existe_como_usuario(self, login: str) -> bool: ...

    def existe_como_organizacion(self, login: str) -> bool: ...

    def obtener_cuenta_usuario(self, login: str) -> CuentaUsuarioInfo | None:
        """SPEC 07 S7.4.2: `None` si no existe. El llamador decide aparte si
        es una organizacion (`existe_como_organizacion`); esta llamada por si
        sola no distingue tipo (S6.2.4: nunca se confia en el campo `type`)."""
        ...

    def obtener_instalacion(self, installation_id: int) -> InstalacionInfo: ...

    def listar_instalaciones(self) -> list[InstalacionInfo]:
        """`GET /app/installations`: unica forma de descubrir, sin webhook,
        que una instalacion pendiente de aprobacion del owner ya se aprobo
        (S4.6.4), o que alguien instalo la App fuera del asistente (S4.6.5)."""
        ...

    def obtener_token_instalacion(self, installation_id: int) -> str: ...

    def obtener_organizacion(self, org_login: str, token_instalacion: str) -> OrganizacionInfo: ...

    def existe_repo(self, org_login: str, repo: str, token_instalacion: str) -> bool: ...

    def contar_owners_organizacion(self, org_login: str, token_instalacion: str) -> int | None:
        """S4.7.3 sub-comprobacion (f): `None` si el token no puede leer `role=admin`."""
        ...

    def crear_equipo(
        self, org_login: str, nombre: str, token_instalacion: str
    ) -> tuple[int, str]: ...

    def agregar_miembro_equipo(
        self, org_login: str, team_slug: str, login: str, token_instalacion: str
    ) -> None: ...

    def quitar_miembro_equipo(
        self, org_login: str, team_slug: str, login: str, token_instalacion: str
    ) -> None: ...

    def agregar_miembro_organizacion(
        self, org_login: str, login: str, token_instalacion: str
    ) -> None: ...

    def quitar_miembro_organizacion(
        self, org_login: str, login: str, token_instalacion: str
    ) -> None: ...

    def obtener_membresia_organizacion(
        self, org_login: str, login: str, token_instalacion: str
    ) -> str | None: ...

    def quitar_colaborador_repo(
        self, org_login: str, repo: str, login: str, token_instalacion: str
    ) -> None: ...

    # --- Etapa P7: repositorio base (S6.5.2, escrituras sincronas 2 y 3 de A-169) ---

    def obtener_repo(
        self, org_login: str, repo: str, token_instalacion: str
    ) -> RepoGithubInfo | None:
        """`GET /repos/{o}/{r}`: lectura previa por nombre antes de crear (A-097)."""
        ...

    def crear_repo_organizacion(
        self,
        org_login: str,
        *,
        nombre: str,
        descripcion: str,
        token_instalacion: str,
        gitignore_template: str | None = None,
    ) -> RepoGithubInfo:
        """`POST /orgs/{org}/repos`, privado y con `auto_init`: el `201` trae
        `default_branch`, que se persiste y nunca se supone (A-068)."""
        ...

    def generar_desde_plantilla(
        self,
        plantilla_owner: str,
        plantilla_repo: str,
        *,
        org_login: str,
        nombre: str,
        descripcion: str,
        token_instalacion: str,
    ) -> RepoGithubInfo:
        """`POST /repos/{template_owner}/{template_repo}/generate` (S6.5.2)."""
        ...

    def obtener_primer_commit(
        self, org_login: str, repo: str, token_instalacion: str
    ) -> str | None:
        """`GET /repos/{o}/{r}/commits?per_page=1`: el sondeo de contenido de
        A-096. `None` mientras el arbol no tiene commits (404/409 tolerados)."""
        ...

    def es_colaborador(self, org_login: str, repo: str, login: str, token_instalacion: str) -> bool:
        """`GET /repos/{o}/{r}/collaborators/{login}`: `204` si, `404` no (S6.5.6)."""
        ...

    def invitar_colaborador(
        self, org_login: str, repo: str, login: str, token_instalacion: str
    ) -> ResultadoInvitacion:
        """`PUT /repos/{o}/{r}/collaborators/{login}` con `push`, nunca `admin` (A-064)."""
        ...

    def listar_invitaciones(
        self, org_login: str, repo: str, token_instalacion: str
    ) -> list[InvitacionGithub]:
        """`GET /repos/{o}/{r}/invitations`: reconciliacion de invitaciones pendientes."""
        ...

    def conceder_lectura_equipo(
        self, org_login: str, team_slug: str, repo: str, token_instalacion: str
    ) -> None:
        """`PUT /orgs/{org}/teams/{team_slug}/repos/{org}/{repo}` con `pull`:
        una sola llamada por repositorio, no una por docente (A-163)."""
        ...

    def marcar_como_plantilla(
        self, org_login: str, repo: str, token_instalacion: str
    ) -> RepoGithubInfo:
        """`PATCH /repos/{o}/{r}` con `is_template: true` y nada mas (S6.11.2)."""
        ...

    def reemplazar_topics(
        self, org_login: str, repo: str, topics: list[str], token_instalacion: str
    ) -> None:
        """`PUT /repos/{o}/{r}/topics`: los tres topics de A-069."""
        ...

    def obtener_archivo(
        self, org_login: str, repo: str, ruta: str, token_instalacion: str
    ) -> ArchivoGithub | None:
        """`GET /repos/{o}/{r}/contents/{ruta}`. No figura en la tabla de
        S6.5.2, pero es la "lectura antes del efecto" que el contrato de A-169
        exige a las escrituras 3 (`PUT`/`DELETE contents` necesitan el `sha`
        vigente) y la previsualizacion de texto de A-067. Solo se usa sobre
        el repositorio base. Decision documentada."""
        ...

    def escribir_archivo(
        self,
        org_login: str,
        repo: str,
        ruta: str,
        *,
        contenido_base64: str,
        mensaje: str,
        sha_anterior: str | None,
        token_instalacion: str,
    ) -> ArchivoGithub:
        """`PUT /repos/{o}/{r}/contents/{ruta}` sin `author` ni `committer`: el
        commit queda a nombre de la cuenta `[bot]` de la instalacion (RG-090)."""
        ...

    def borrar_archivo(
        self,
        org_login: str,
        repo: str,
        ruta: str,
        *,
        sha: str,
        mensaje: str,
        token_instalacion: str,
    ) -> None:
        """`DELETE /repos/{o}/{r}/contents/{ruta}`: solo sobre el base (S6.5.2)."""
        ...


class ClienteGitHubReal:
    def __init__(self, *, app_id: str, private_key_pem_base64: str) -> None:
        self._app_id = app_id
        self._clave = private_key_pem_base64

    def _jwt_app(self) -> str:
        return emitir_jwt_de_app(app_id=self._app_id, private_key_pem_base64=self._clave)

    def obtener_slug_app(self) -> str:
        respuesta = self._peticion("GET", "https://api.github.com/app", token=self._jwt_app())
        if respuesta.status_code >= 500:
            raise FalloProveedorGithub(f"GitHub respondio {respuesta.status_code}")
        respuesta.raise_for_status()
        return str(respuesta.json()["slug"])

    def _peticion(
        self,
        metodo: str,
        url: str,
        *,
        token: str | None,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        try:
            return httpx.request(
                metodo,
                url,
                headers=_cabeceras(token),
                json=json,
                params=params,
                timeout=_TIMEOUT_SEGUNDOS,
            )
        except httpx.TimeoutException as exc:
            raise FalloProveedorGithub("tiempo de espera agotado") from exc

    def _token_consultas_publicas(self) -> str | None:
        """Token para `GET /users/{login}` y `GET /orgs/{login}`.

        GitHub responde 401 al JWT de la App fuera de las rutas `/app/...`, asi
        que estas consultas usan un token de instalacion de cualquier
        instalacion activa de la App (limite de 5000 peticiones por hora),
        cacheado en memoria de proceso hasta poco antes de vencer (A-038: no se
        persiste). Sin ninguna instalacion todavia, `None`: la consulta viaja
        sin autenticar (60 por hora).
        """
        ahora = datetime.now(UTC)
        with _cerrojo_tokens_consulta:
            cacheado = _tokens_consulta.get(self._app_id)
        if cacheado is not None and cacheado[1] - _MARGEN_VENCIMIENTO_TOKEN > ahora:
            return cacheado[0]

        activas = [i for i in self.listar_instalaciones() if not i.suspendida]
        if not activas:
            return None
        respuesta = self._peticion(
            "POST",
            f"https://api.github.com/app/installations/{activas[0].installation_id}/access_tokens",
            token=self._jwt_app(),
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorGithub(f"GitHub respondio {respuesta.status_code}")
        respuesta.raise_for_status()
        datos = respuesta.json()
        token = str(datos["token"])
        vence = datetime.fromisoformat(str(datos["expires_at"]).replace("Z", "+00:00"))
        with _cerrojo_tokens_consulta:
            _tokens_consulta[self._app_id] = (token, vence)
        return token

    def _consultar_cuenta(self, ruta: str) -> httpx.Response | None:
        """`None` si la cuenta no existe (404). Cualquier otra respuesta que no
        sea 200 (401, limite de peticiones, 5xx) es un fallo del proveedor y
        nunca se traduce a "no existe" (Ley 5)."""
        respuesta = self._peticion(
            "GET", f"https://api.github.com{ruta}", token=self._token_consultas_publicas()
        )
        if respuesta.status_code == 404:
            return None
        if respuesta.status_code != 200:
            raise FalloProveedorGithub(f"GitHub respondio {respuesta.status_code} a GET {ruta}")
        return respuesta

    def existe_como_usuario(self, login: str) -> bool:
        return self._consultar_cuenta(f"/users/{quote(login, safe='')}") is not None

    def existe_como_organizacion(self, login: str) -> bool:
        return self._consultar_cuenta(f"/orgs/{quote(login, safe='')}") is not None

    def obtener_cuenta_usuario(self, login: str) -> CuentaUsuarioInfo | None:
        respuesta = self._consultar_cuenta(f"/users/{quote(login, safe='')}")
        if respuesta is None:
            return None
        datos = respuesta.json()
        return CuentaUsuarioInfo(github_user_id=datos["id"], login=datos["login"])

    def obtener_instalacion(self, installation_id: int) -> InstalacionInfo:
        respuesta = self._peticion(
            "GET",
            f"https://api.github.com/app/installations/{installation_id}",
            token=self._jwt_app(),
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorGithub(f"GitHub respondio {respuesta.status_code}")
        respuesta.raise_for_status()
        datos = respuesta.json()
        return InstalacionInfo(
            installation_id=installation_id,
            account_login=datos["account"]["login"],
            account_id=datos["account"]["id"],
            repository_selection=datos.get("repository_selection", "selected"),
            permisos=datos.get("permissions", {}),
            suspendida=datos.get("suspended_at") is not None,
        )

    def listar_instalaciones(self) -> list[InstalacionInfo]:
        respuesta = self._peticion(
            "GET", "https://api.github.com/app/installations?per_page=100", token=self._jwt_app()
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorGithub(f"GitHub respondio {respuesta.status_code}")
        respuesta.raise_for_status()
        return [
            InstalacionInfo(
                installation_id=d["id"],
                account_login=d["account"]["login"],
                account_id=d["account"]["id"],
                repository_selection=d.get("repository_selection", "selected"),
                permisos=d.get("permissions", {}),
                suspendida=d.get("suspended_at") is not None,
            )
            for d in respuesta.json()
        ]

    def obtener_token_instalacion(self, installation_id: int) -> str:
        respuesta = self._peticion(
            "POST",
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            token=self._jwt_app(),
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorGithub(f"GitHub respondio {respuesta.status_code}")
        respuesta.raise_for_status()
        return str(respuesta.json()["token"])

    def obtener_organizacion(self, org_login: str, token_instalacion: str) -> OrganizacionInfo:
        respuesta = self._peticion(
            "GET", f"https://api.github.com/orgs/{org_login}", token=token_instalacion
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorGithub(f"GitHub respondio {respuesta.status_code}")
        respuesta.raise_for_status()
        datos = respuesta.json()
        return OrganizacionInfo(
            default_repository_permission=datos.get("default_repository_permission"),
            members_can_create_repositories=datos.get("members_can_create_repositories"),
            two_factor_requirement_enabled=datos.get("two_factor_requirement_enabled"),
            cantidad_owners=self.contar_owners_organizacion(org_login, token_instalacion),
        )

    def existe_repo(self, org_login: str, repo: str, token_instalacion: str) -> bool:
        respuesta = self._peticion(
            "GET", f"https://api.github.com/repos/{org_login}/{repo}", token=token_instalacion
        )
        return respuesta.status_code == 200

    def contar_owners_organizacion(self, org_login: str, token_instalacion: str) -> int | None:
        respuesta = self._peticion(
            "GET",
            f"https://api.github.com/orgs/{org_login}/members",
            token=token_instalacion,
            params={"role": "admin", "per_page": 100},
        )
        if respuesta.status_code == 403 or respuesta.status_code == 404:
            return None
        if respuesta.status_code >= 500:
            raise FalloProveedorGithub(f"GitHub respondio {respuesta.status_code}")
        respuesta.raise_for_status()
        return len(respuesta.json())

    def crear_equipo(self, org_login: str, nombre: str, token_instalacion: str) -> tuple[int, str]:
        """Idempotente, como el doble: si la organizacion ya tiene un equipo con
        ese nombre (por ejemplo, de un curso anterior vinculado a la misma
        organizacion), GitHub responde 422 y se reutiliza ese equipo."""
        respuesta = self._peticion(
            "POST",
            f"https://api.github.com/orgs/{org_login}/teams",
            token=token_instalacion,
            json={"name": nombre, "privacy": "closed"},
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorGithub(f"GitHub respondio {respuesta.status_code}")
        if respuesta.status_code == 422:
            slug = nombre.strip().lower().replace(" ", "-")
            existente = self._peticion(
                "GET",
                f"https://api.github.com/orgs/{org_login}/teams/{quote(slug, safe='')}",
                token=token_instalacion,
            )
            if existente.status_code == 200:
                datos = existente.json()
                return datos["id"], datos["slug"]
        respuesta.raise_for_status()
        datos = respuesta.json()
        return datos["id"], datos["slug"]

    def agregar_miembro_equipo(
        self, org_login: str, team_slug: str, login: str, token_instalacion: str
    ) -> None:
        respuesta = self._peticion(
            "PUT",
            f"https://api.github.com/orgs/{org_login}/teams/{team_slug}/memberships/{login}",
            token=token_instalacion,
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorGithub(f"GitHub respondio {respuesta.status_code}")
        respuesta.raise_for_status()

    def quitar_miembro_equipo(
        self, org_login: str, team_slug: str, login: str, token_instalacion: str
    ) -> None:
        respuesta = self._peticion(
            "DELETE",
            f"https://api.github.com/orgs/{org_login}/teams/{team_slug}/memberships/{login}",
            token=token_instalacion,
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorGithub(f"GitHub respondio {respuesta.status_code}")
        if respuesta.status_code != 404:
            respuesta.raise_for_status()

    def agregar_miembro_organizacion(
        self, org_login: str, login: str, token_instalacion: str
    ) -> None:
        # A-060, S6.4: nunca se llama con el login de un estudiante -- lo
        # garantiza el llamador (github_repo.py), nunca este cliente.
        respuesta = self._peticion(
            "PUT",
            f"https://api.github.com/orgs/{org_login}/memberships/{login}",
            token=token_instalacion,
            json={"role": "member"},
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorGithub(f"GitHub respondio {respuesta.status_code}")
        respuesta.raise_for_status()

    def quitar_miembro_organizacion(
        self, org_login: str, login: str, token_instalacion: str
    ) -> None:
        respuesta = self._peticion(
            "DELETE",
            f"https://api.github.com/orgs/{org_login}/memberships/{login}",
            token=token_instalacion,
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorGithub(f"GitHub respondio {respuesta.status_code}")
        if respuesta.status_code != 404:
            respuesta.raise_for_status()

    def obtener_membresia_organizacion(
        self, org_login: str, login: str, token_instalacion: str
    ) -> str | None:
        respuesta = self._peticion(
            "GET",
            f"https://api.github.com/orgs/{org_login}/memberships/{login}",
            token=token_instalacion,
        )
        if respuesta.status_code == 404:
            return None
        if respuesta.status_code >= 500:
            raise FalloProveedorGithub(f"GitHub respondio {respuesta.status_code}")
        respuesta.raise_for_status()
        estado = respuesta.json().get("state")
        return str(estado) if estado is not None else None

    def quitar_colaborador_repo(
        self, org_login: str, repo: str, login: str, token_instalacion: str
    ) -> None:
        respuesta = self._peticion(
            "DELETE",
            f"https://api.github.com/repos/{org_login}/{repo}/collaborators/{login}",
            token=token_instalacion,
        )
        if respuesta.status_code >= 500:
            raise FalloProveedorGithub(f"GitHub respondio {respuesta.status_code}")
        if respuesta.status_code != 404:
            respuesta.raise_for_status()

    def obtener_repo(
        self, org_login: str, repo: str, token_instalacion: str
    ) -> RepoGithubInfo | None:
        respuesta = self._peticion(
            "GET", f"https://api.github.com/repos/{org_login}/{repo}", token=token_instalacion
        )
        if respuesta.status_code == 404:
            return None
        _exigir_exito(respuesta)
        return _repo_desde_json(respuesta.json())

    def crear_repo_organizacion(
        self,
        org_login: str,
        *,
        nombre: str,
        descripcion: str,
        token_instalacion: str,
        gitignore_template: str | None = None,
    ) -> RepoGithubInfo:
        cuerpo: dict[str, Any] = {
            "name": nombre,
            "description": descripcion,
            "private": True,
            "auto_init": True,
            "has_wiki": False,
            "has_projects": False,
        }
        if gitignore_template is not None:
            cuerpo["gitignore_template"] = gitignore_template
        respuesta = self._peticion(
            "POST",
            f"https://api.github.com/orgs/{org_login}/repos",
            token=token_instalacion,
            json=cuerpo,
        )
        _exigir_exito(respuesta)
        return _repo_desde_json(respuesta.json())

    def generar_desde_plantilla(
        self,
        plantilla_owner: str,
        plantilla_repo: str,
        *,
        org_login: str,
        nombre: str,
        descripcion: str,
        token_instalacion: str,
    ) -> RepoGithubInfo:
        respuesta = self._peticion(
            "POST",
            f"https://api.github.com/repos/{plantilla_owner}/{plantilla_repo}/generate",
            token=token_instalacion,
            json={
                "owner": org_login,
                "name": nombre,
                "description": descripcion,
                "private": True,
                "include_all_branches": False,
            },
        )
        _exigir_exito(respuesta)
        return _repo_desde_json(respuesta.json())

    def obtener_primer_commit(
        self, org_login: str, repo: str, token_instalacion: str
    ) -> str | None:
        respuesta = self._peticion(
            "GET",
            f"https://api.github.com/repos/{org_login}/{repo}/commits",
            token=token_instalacion,
            params={"per_page": 1},
        )
        # A-096: 404, 409 y 200 con lista vacia se toleran durante la ventana.
        if respuesta.status_code in (404, 409):
            return None
        _exigir_exito(respuesta)
        commits = respuesta.json()
        if not isinstance(commits, list) or not commits:
            return None
        return str(commits[0]["sha"])

    def es_colaborador(self, org_login: str, repo: str, login: str, token_instalacion: str) -> bool:
        respuesta = self._peticion(
            "GET",
            f"https://api.github.com/repos/{org_login}/{repo}/collaborators/{login}",
            token=token_instalacion,
        )
        if respuesta.status_code == 204:
            return True
        if respuesta.status_code == 404:
            return False
        _exigir_exito(respuesta)
        return False

    def invitar_colaborador(
        self, org_login: str, repo: str, login: str, token_instalacion: str
    ) -> ResultadoInvitacion:
        respuesta = self._peticion(
            "PUT",
            f"https://api.github.com/repos/{org_login}/{repo}/collaborators/{login}",
            token=token_instalacion,
            json={"permission": "push"},
        )
        _exigir_exito(respuesta)
        if respuesta.status_code == 204:
            return ResultadoInvitacion(status_code=204, invitation_id=None, html_url=None)
        datos = respuesta.json()
        return ResultadoInvitacion(
            status_code=respuesta.status_code,
            invitation_id=datos.get("id"),
            html_url=datos.get("html_url"),
        )

    def listar_invitaciones(
        self, org_login: str, repo: str, token_instalacion: str
    ) -> list[InvitacionGithub]:
        respuesta = self._peticion(
            "GET",
            f"https://api.github.com/repos/{org_login}/{repo}/invitations",
            token=token_instalacion,
            params={"per_page": 100},
        )
        _exigir_exito(respuesta)
        return [
            InvitacionGithub(
                invitation_id=int(d["id"]),
                login=str((d.get("invitee") or {}).get("login", "")),
                expirada=bool(d.get("expired", False)),
                html_url=d.get("html_url"),
            )
            for d in respuesta.json()
        ]

    def conceder_lectura_equipo(
        self, org_login: str, team_slug: str, repo: str, token_instalacion: str
    ) -> None:
        respuesta = self._peticion(
            "PUT",
            f"https://api.github.com/orgs/{org_login}/teams/{team_slug}/repos/{org_login}/{repo}",
            token=token_instalacion,
            json={"permission": "pull"},
        )
        _exigir_exito(respuesta)

    def marcar_como_plantilla(
        self, org_login: str, repo: str, token_instalacion: str
    ) -> RepoGithubInfo:
        respuesta = self._peticion(
            "PATCH",
            f"https://api.github.com/repos/{org_login}/{repo}",
            token=token_instalacion,
            json={"is_template": True},
        )
        _exigir_exito(respuesta)
        return _repo_desde_json(respuesta.json())

    def reemplazar_topics(
        self, org_login: str, repo: str, topics: list[str], token_instalacion: str
    ) -> None:
        respuesta = self._peticion(
            "PUT",
            f"https://api.github.com/repos/{org_login}/{repo}/topics",
            token=token_instalacion,
            json={"names": topics},
        )
        _exigir_exito(respuesta)

    def obtener_archivo(
        self, org_login: str, repo: str, ruta: str, token_instalacion: str
    ) -> ArchivoGithub | None:
        respuesta = self._peticion(
            "GET",
            f"https://api.github.com/repos/{org_login}/{repo}/contents/{quote(ruta, safe='/')}",
            token=token_instalacion,
        )
        if respuesta.status_code == 404:
            return None
        _exigir_exito(respuesta)
        datos = respuesta.json()
        if not isinstance(datos, dict) or datos.get("type") != "file":
            return None  # la ruta es un directorio: no hay archivo que reemplazar
        return ArchivoGithub(
            ruta=str(datos["path"]),
            sha=str(datos["sha"]),
            tamano_bytes=int(datos.get("size", 0)),
            contenido_base64=str(datos.get("content", "")).replace("\n", ""),
        )

    def escribir_archivo(
        self,
        org_login: str,
        repo: str,
        ruta: str,
        *,
        contenido_base64: str,
        mensaje: str,
        sha_anterior: str | None,
        token_instalacion: str,
    ) -> ArchivoGithub:
        cuerpo: dict[str, Any] = {"message": mensaje, "content": contenido_base64}
        if sha_anterior is not None:
            cuerpo["sha"] = sha_anterior
        respuesta = self._peticion(
            "PUT",
            f"https://api.github.com/repos/{org_login}/{repo}/contents/{quote(ruta, safe='/')}",
            token=token_instalacion,
            json=cuerpo,
        )
        _exigir_exito(respuesta)
        contenido = respuesta.json()["content"]
        return ArchivoGithub(
            ruta=str(contenido["path"]),
            sha=str(contenido["sha"]),
            tamano_bytes=int(contenido.get("size", 0)),
        )

    def borrar_archivo(
        self,
        org_login: str,
        repo: str,
        ruta: str,
        *,
        sha: str,
        mensaje: str,
        token_instalacion: str,
    ) -> None:
        respuesta = self._peticion(
            "DELETE",
            f"https://api.github.com/repos/{org_login}/{repo}/contents/{quote(ruta, safe='/')}",
            token=token_instalacion,
            json={"message": mensaje, "sha": sha},
        )
        if respuesta.status_code == 404:
            return  # ya no estaba: el efecto buscado ya existe
        _exigir_exito(respuesta)


def _sha_blob(contenido: bytes) -> str:
    """El `sha` que GitHub devuelve en la API de contenidos es el blob sha de git."""
    return hashlib.sha1(b"blob %d\0" % len(contenido) + contenido).hexdigest()


# Estado compartido por toda instancia de ClienteGitHubDoble en el proceso:
# `crear_cliente_github()` crea una instancia nueva en cada llamada (igual que
# el cliente de Canvas), pero a diferencia de Canvas, el doble de GitHub
# necesita recordar equipos y membresias entre una llamada y la siguiente
# (crear el equipo, luego añadir miembros, luego consultarlos) para que el
# checklist y `sincronizar_acceso_docente` se puedan probar de punta a punta.
_equipos: dict[str, tuple[int, str]] = {}
_miembros_equipo: dict[tuple[str, str], set[str]] = {}
_miembros_org: dict[str, set[str]] = {}
# Etapa P7: repositorios y archivos del doble. Las escrituras del base son
# sincronas y viven solo en el servicio web (A-169), asi que un dict de
# proceso alcanza -- a diferencia del registro de Canvas, no hay salto al
# trabajador.
_repos: dict[tuple[str, str], RepoGithubInfo] = {}
_archivos: dict[tuple[str, str], dict[str, bytes]] = {}
# Etapa P8: colaboradores, invitaciones pendientes y lectura del equipo. A
# diferencia del base, esto lo tocan el trabajador (invita) y el servicio web
# (nada); en las pruebas corre todo en un solo proceso. Para probar a mano sin
# GitHub real, `aceptar_invitacion_doble` simula que el estudiante acepta.
_colaboradores: dict[tuple[str, str], set[str]] = {}
_invitaciones: dict[tuple[str, str], dict[str, InvitacionGithub]] = {}
_repos_con_lectura_equipo: set[tuple[str, str, str]] = set()


def aceptar_invitacion_doble(org_login: str, repo: str, login: str) -> None:
    """Solo para el doble: el estudiante acepta su invitacion en GitHub."""
    pendientes = _invitaciones.get((org_login, repo), {})
    if pendientes.pop(login.lower(), None) is not None:
        _colaboradores.setdefault((org_login, repo), set()).add(login.lower())


class ClienteGitHubDoble:
    """Datos fijos y deterministas para desarrollo local sin GitHub real.

    `installation_id=8001` esta instalada en la organizacion `org-valida`,
    con la configuracion base correcta (item 14 en verde). El login
    `cuenta-personal` existe como usuario, no como organizacion.
    `installation_id=8002` esta instalada en `cuenta-personal` (para probar
    el rechazo de S4.6.3 sin depender de GitHub real).
    """

    _INSTALLATION_ID = 8001
    _ORG_LOGIN = "org-valida"
    _ORG_ID = 90001
    _INSTALLATION_ID_PERSONAL = 8002
    _CUENTA_PERSONAL = "cuenta-personal"
    _CUENTA_PERSONAL_ID = 90002
    # SPEC 07 S7.4: cuentas fijas para probar las cuatro vias sin GitHub real.
    # La API devuelve las mayusculas canonicas (S7.2.4): el login declarado en
    # minusculas por el estudiante nunca coincide letra a letra con el
    # guardado, a proposito, para ejercitar esa regla en las pruebas.
    _CUENTAS_ESTUDIANTE = {
        "estudiante-valido": (70001, "Estudiante-Valido"),
        "estudiante-valido-2": (70002, "Estudiante-Valido-2"),
    }

    def obtener_slug_app(self) -> str:
        return "proyecto2-icc4201-doble"

    def existe_como_usuario(self, login: str) -> bool:
        # Como GitHub real: `GET /users/{login}` tambien responde 200 para una
        # organizacion. Un doble que lo negara esconderia errores de deteccion.
        return (
            login == self._CUENTA_PERSONAL
            or login == self._ORG_LOGIN
            or login.lower() in self._CUENTAS_ESTUDIANTE
        )

    def existe_como_organizacion(self, login: str) -> bool:
        return login == self._ORG_LOGIN

    def obtener_cuenta_usuario(self, login: str) -> CuentaUsuarioInfo | None:
        if login == self._CUENTA_PERSONAL:
            return CuentaUsuarioInfo(
                github_user_id=self._CUENTA_PERSONAL_ID, login=self._CUENTA_PERSONAL
            )
        datos = self._CUENTAS_ESTUDIANTE.get(login.lower())
        if datos is None:
            return None
        return CuentaUsuarioInfo(github_user_id=datos[0], login=datos[1])

    def obtener_instalacion(self, installation_id: int) -> InstalacionInfo:
        if installation_id == self._INSTALLATION_ID:
            return InstalacionInfo(
                installation_id=installation_id,
                account_login=self._ORG_LOGIN,
                account_id=self._ORG_ID,
                repository_selection="selected",
                permisos={
                    "administration": "write",
                    "contents": "write",
                    "metadata": "read",
                    "members": "write",
                },
                suspendida=False,
            )
        if installation_id == self._INSTALLATION_ID_PERSONAL:
            return InstalacionInfo(
                installation_id=installation_id,
                account_login=self._CUENTA_PERSONAL,
                account_id=self._CUENTA_PERSONAL_ID,
                repository_selection="all",
                permisos={
                    "administration": "write",
                    "contents": "write",
                    "metadata": "read",
                    "members": "write",
                },
                suspendida=False,
            )
        raise FalloProveedorGithub("instalacion inexistente en modo doble")

    def listar_instalaciones(self) -> list[InstalacionInfo]:
        return [self.obtener_instalacion(self._INSTALLATION_ID)]

    def obtener_token_instalacion(self, installation_id: int) -> str:
        return f"doble-token-{installation_id}"

    def obtener_organizacion(self, org_login: str, token_instalacion: str) -> OrganizacionInfo:
        return OrganizacionInfo(
            default_repository_permission="none",
            members_can_create_repositories=False,
            two_factor_requirement_enabled=True,
            cantidad_owners=2,
        )

    def existe_repo(self, org_login: str, repo: str, token_instalacion: str) -> bool:
        return repo == ".github"

    def contar_owners_organizacion(self, org_login: str, token_instalacion: str) -> int | None:
        return 2

    def crear_equipo(self, org_login: str, nombre: str, token_instalacion: str) -> tuple[int, str]:
        return _equipos.setdefault(org_login, (7001, "docentes"))

    def agregar_miembro_equipo(
        self, org_login: str, team_slug: str, login: str, token_instalacion: str
    ) -> None:
        _miembros_equipo.setdefault((org_login, team_slug), set()).add(login)

    def quitar_miembro_equipo(
        self, org_login: str, team_slug: str, login: str, token_instalacion: str
    ) -> None:
        _miembros_equipo.get((org_login, team_slug), set()).discard(login)

    def agregar_miembro_organizacion(
        self, org_login: str, login: str, token_instalacion: str
    ) -> None:
        _miembros_org.setdefault(org_login, set()).add(login)

    def quitar_miembro_organizacion(
        self, org_login: str, login: str, token_instalacion: str
    ) -> None:
        _miembros_org.get(org_login, set()).discard(login)

    def obtener_membresia_organizacion(
        self, org_login: str, login: str, token_instalacion: str
    ) -> str | None:
        return "active" if login in _miembros_org.get(org_login, set()) else None

    def quitar_colaborador_repo(
        self, org_login: str, repo: str, login: str, token_instalacion: str
    ) -> None:
        return None

    def obtener_repo(
        self, org_login: str, repo: str, token_instalacion: str
    ) -> RepoGithubInfo | None:
        return _repos.get((org_login, repo))

    def crear_repo_organizacion(
        self,
        org_login: str,
        *,
        nombre: str,
        descripcion: str,
        token_instalacion: str,
        gitignore_template: str | None = None,
    ) -> RepoGithubInfo:
        if (org_login, nombre) in _repos:
            raise RechazoProveedorGithub(422, "name already exists on this account")
        info = self._nuevo_repo(org_login, nombre, descripcion)
        archivos = {"README.md": f"# {nombre}\n".encode()}
        if gitignore_template is not None:
            archivos[".gitignore"] = f"# {gitignore_template}\n".encode()
        _archivos[(org_login, nombre)] = archivos
        return info

    def _nuevo_repo(self, org_login: str, nombre: str, descripcion: str) -> RepoGithubInfo:
        info = RepoGithubInfo(
            github_repo_id=600_000 + len(_repos) + 1,
            nombre=nombre,
            full_name=f"{org_login}/{nombre}",
            owner_login=org_login,
            descripcion=descripcion,
            topics=(),
            rama_por_defecto="main",
            es_plantilla=False,
            url_html=f"https://github.com/{org_login}/{nombre}",
        )
        _repos[(org_login, nombre)] = info
        return info

    def generar_desde_plantilla(
        self,
        plantilla_owner: str,
        plantilla_repo: str,
        *,
        org_login: str,
        nombre: str,
        descripcion: str,
        token_instalacion: str,
    ) -> RepoGithubInfo:
        if (org_login, nombre) in _repos:
            raise RechazoProveedorGithub(422, "name already exists on this account")
        if (plantilla_owner, plantilla_repo) not in _repos:
            raise RechazoProveedorGithub(404, "Not Found")
        info = self._nuevo_repo(org_login, nombre, descripcion)
        _archivos[(org_login, nombre)] = dict(_archivos.get((plantilla_owner, plantilla_repo), {}))
        return info

    def obtener_primer_commit(
        self, org_login: str, repo: str, token_instalacion: str
    ) -> str | None:
        archivos = _archivos.get((org_login, repo))
        if not archivos:
            return None
        return hashlib.sha1(repr(sorted(archivos)).encode()).hexdigest()

    def es_colaborador(self, org_login: str, repo: str, login: str, token_instalacion: str) -> bool:
        return login.lower() in _colaboradores.get((org_login, repo), set())

    def invitar_colaborador(
        self, org_login: str, repo: str, login: str, token_instalacion: str
    ) -> ResultadoInvitacion:
        if (org_login, repo) not in _repos:
            raise RechazoProveedorGithub(404, "Not Found")
        if self.es_colaborador(org_login, repo, login, token_instalacion):
            return ResultadoInvitacion(status_code=204, invitation_id=None, html_url=None)
        pendientes = _invitaciones.setdefault((org_login, repo), {})
        existente = pendientes.get(login.lower())
        if existente is None:
            existente = InvitacionGithub(
                invitation_id=900_000 + sum(len(p) for p in _invitaciones.values()) + 1,
                login=login,
                expirada=False,
                html_url=f"https://github.com/{org_login}/{repo}/invitations",
            )
            pendientes[login.lower()] = existente
        return ResultadoInvitacion(
            status_code=201, invitation_id=existente.invitation_id, html_url=existente.html_url
        )

    def listar_invitaciones(
        self, org_login: str, repo: str, token_instalacion: str
    ) -> list[InvitacionGithub]:
        return list(_invitaciones.get((org_login, repo), {}).values())

    def conceder_lectura_equipo(
        self, org_login: str, team_slug: str, repo: str, token_instalacion: str
    ) -> None:
        if (org_login, repo) not in _repos:
            raise RechazoProveedorGithub(404, "Not Found")
        _repos_con_lectura_equipo.add((org_login, team_slug, repo))

    def marcar_como_plantilla(
        self, org_login: str, repo: str, token_instalacion: str
    ) -> RepoGithubInfo:
        info = replace(_repos[(org_login, repo)], es_plantilla=True)
        _repos[(org_login, repo)] = info
        return info

    def reemplazar_topics(
        self, org_login: str, repo: str, topics: list[str], token_instalacion: str
    ) -> None:
        _repos[(org_login, repo)] = replace(_repos[(org_login, repo)], topics=tuple(topics))

    def obtener_archivo(
        self, org_login: str, repo: str, ruta: str, token_instalacion: str
    ) -> ArchivoGithub | None:
        contenido = _archivos.get((org_login, repo), {}).get(ruta)
        if contenido is None:
            return None
        return ArchivoGithub(
            ruta=ruta,
            sha=_sha_blob(contenido),
            tamano_bytes=len(contenido),
            contenido_base64=base64.b64encode(contenido).decode(),
        )

    def escribir_archivo(
        self,
        org_login: str,
        repo: str,
        ruta: str,
        *,
        contenido_base64: str,
        mensaje: str,
        sha_anterior: str | None,
        token_instalacion: str,
    ) -> ArchivoGithub:
        archivos = _archivos.setdefault((org_login, repo), {})
        existente = archivos.get(ruta)
        # Mismo contrato que la API real: reemplazar exige el sha vigente.
        if existente is not None and sha_anterior != _sha_blob(existente):
            raise RechazoProveedorGithub(409, f"{ruta} does not match {sha_anterior}")
        contenido = base64.b64decode(contenido_base64)
        archivos[ruta] = contenido
        return ArchivoGithub(ruta=ruta, sha=_sha_blob(contenido), tamano_bytes=len(contenido))

    def borrar_archivo(
        self,
        org_login: str,
        repo: str,
        ruta: str,
        *,
        sha: str,
        mensaje: str,
        token_instalacion: str,
    ) -> None:
        _archivos.get((org_login, repo), {}).pop(ruta, None)


def crear_cliente_github(*, modo: str, app_id: str, private_key_pem_base64: str) -> ClienteGitHub:
    if modo == "real":
        return ClienteGitHubReal(app_id=app_id, private_key_pem_base64=private_key_pem_base64)
    return ClienteGitHubDoble()


def crear_cliente_github_desde_config(settings: Any) -> ClienteGitHub:
    """Atajo para las rutas y trabajos: lee `github_modo`/credenciales de `Settings`."""
    return crear_cliente_github(
        modo=settings.github_modo,
        app_id=settings.github_app_id,
        private_key_pem_base64=settings.github_app_private_key,
    )
