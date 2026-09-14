"""DTOs de repositorios y archivos de GitHub (SPEC 06 S6.5.2). Sin I/O."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepoGithubInfo:
    """Lo que la aplicacion lee de `GET /repos/{o}/{r}` o del `201` de creacion.
    `rama_por_defecto` se lee siempre de la respuesta, nunca se supone (A-068)."""

    github_repo_id: int
    nombre: str
    full_name: str
    owner_login: str
    descripcion: str | None
    topics: tuple[str, ...]
    rama_por_defecto: str | None
    es_plantilla: bool
    url_html: str


@dataclass(frozen=True)
class ResultadoInvitacion:
    """`PUT /repos/{o}/{r}/collaborators/{login}`: `201` con invitacion, o `204`
    si el acceso quedo concedido de inmediato (S8.8.2 `ACCESO_DIRECTO`)."""

    status_code: int
    invitation_id: int | None
    html_url: str | None


@dataclass(frozen=True)
class InvitacionGithub:
    """Una fila de `GET /repos/{o}/{r}/invitations` (reconciliacion, S6.5.6)."""

    invitation_id: int
    login: str
    expirada: bool
    html_url: str | None


@dataclass(frozen=True)
class ArchivoGithub:
    """Un archivo del repositorio base. `sha` es el blob sha que devuelve la
    API de contenidos; el contenido nunca se persiste (A-090), solo viaja para
    previsualizar o para renombrar."""

    ruta: str
    sha: str
    tamano_bytes: int
    contenido_base64: str | None = None
