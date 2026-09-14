"""Carga y validacion de configuracion (SPEC 14 S14.6).

Toda la configuracion viaja por variables de entorno (S14.6.1.1). La carga falla el
arranque si falta un secreto obligatorio (S14.6.1.4), en vez de fallar en la primera
llamada. Ningun valor por defecto oculta un secreto ausente.
"""

from __future__ import annotations

import base64
import binascii
import json
from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfiguracionInvalida(RuntimeError):
    """El proceso no debe arrancar: falta o es invalida una variable obligatoria."""


class InstanciaCanvas(BaseModel):
    """Un elemento de la lista blanca de instancias (SPEC 05 S5.2.8)."""

    base_url: str
    nombre_visible: str
    oauth_client_id: str | None = None
    oauth_client_secret: str | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- No secretos (S14.6.3) ---
    entorno: Literal["produccion", "ensayo", "local"] = Field(alias="ENTORNO")
    perfil_alcance: Literal["parcial", "completo"] = Field(alias="PERFIL_ALCANCE")
    canvas_modo: Literal["doble", "real"] = Field(alias="CANVAS_MODO")
    # Analogo a CANVAS_MODO (S14.6.3), no nombrado literalmente por el SPEC:
    # selecciona la implementacion de ClienteGitHub (S6.2.1 patron A-133).
    github_modo: Literal["doble", "real"] = Field(alias="GITHUB_MODO")
    canvas_base_url: str = Field(alias="CANVAS_BASE_URL")
    # Mecanismo propio (no nombrado literalmente por el SPEC) para la guarda de S14.4
    # "el proceso no arranca si CANVAS_BASE_URL de ensayo coincide con la de produccion":
    # en ensayo se exige ademas la URL real de produccion, para poder contrastarla.
    canvas_base_url_produccion_referencia: str | None = Field(
        default=None, alias="CANVAS_BASE_URL_PRODUCCION_REFERENCIA"
    )
    comunicaciones_salientes: Literal["activadas", "pausadas"] = Field(
        alias="COMUNICACIONES_SALIENTES"
    )
    destinatarios_permitidos: str = Field(default="", alias="DESTINATARIOS_PERMITIDOS")
    email_from: str = Field(alias="EMAIL_FROM")
    email_from_nombre: str = Field(alias="EMAIL_FROM_NOMBRE")
    email_reply_to: str = Field(alias="EMAIL_REPLY_TO")
    email_dominio_verificado: str = Field(alias="EMAIL_DOMINIO_VERIFICADO")
    vite_api_base_url: str = Field(alias="VITE_API_BASE_URL")
    # Mecanismo propio para que la cookie csrf_token (no HttpOnly) sea legible
    # por JS en app.<dominio> aunque la emita api.<dominio> (S2.2.6): en
    # produccion vale ".<dominio>"; en local/ensayo con un solo host, None
    # (cookie host-only, suficiente cuando frontend y api comparten host).
    cookie_dominio: str | None = Field(default=None, alias="COOKIE_DOMINIO")
    # En Render, el SHA del despliegue llega como RENDER_GIT_COMMIT; tiene
    # prioridad sobre el APP_VERSION que la imagen trae por defecto.
    app_version: str = Field(
        default="dev", validation_alias=AliasChoices("RENDER_GIT_COMMIT", "APP_VERSION")
    )
    frontend_origen: str = Field(alias="FRONTEND_ORIGEN")
    # Lista blanca de instancias de Canvas seleccionables en el asistente de
    # vinculacion (S5.2.8): JSON, nunca un campo libre de URL en la interfaz.
    canvas_instancias: str = Field(alias="CANVAS_INSTANCIAS")

    # --- Secretos: inventario cerrado de 15 (S14.6.2) ---
    database_url: str = Field(alias="DATABASE_URL")
    app_encryption_keys: str = Field(alias="APP_ENCRYPTION_KEYS")
    app_encryption_key_activa: int = Field(alias="APP_ENCRYPTION_KEY_ACTIVA")
    google_client_id: str = Field(alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(alias="GOOGLE_CLIENT_SECRET")
    github_app_id: str = Field(alias="GITHUB_APP_ID")
    github_app_private_key: str = Field(alias="GITHUB_APP_PRIVATE_KEY")
    github_webhook_secret: str = Field(alias="GITHUB_WEBHOOK_SECRET")
    github_webhook_secret_anterior: str | None = Field(
        default=None, alias="GITHUB_WEBHOOK_SECRET_ANTERIOR"
    )
    email_provider_api_key: str = Field(alias="EMAIL_PROVIDER_API_KEY")
    signing_key: str = Field(alias="SIGNING_KEY")
    signing_key_anterior: str | None = Field(default=None, alias="SIGNING_KEY_ANTERIOR")
    github_ensayo_app_id: str | None = Field(default=None, alias="GITHUB_ENSAYO_APP_ID")
    github_ensayo_app_private_key: str | None = Field(
        default=None, alias="GITHUB_ENSAYO_APP_PRIVATE_KEY"
    )
    canvas_token_demo: str | None = Field(default=None, alias="CANVAS_TOKEN_DEMO")

    @field_validator("cookie_dominio")
    @classmethod
    def _cookie_dominio_vacio_es_host_only(cls, v: str | None) -> str | None:
        """`COOKIE_DOMINIO=` (vacio) es lo mismo que no declararla: cookie
        host-only. Un atributo `Domain=` vacio no es un valor valido."""
        return v.strip() or None if v is not None else None

    @field_validator("app_encryption_keys")
    @classmethod
    def _validar_formato_llavero(cls, v: str) -> str:
        try:
            _parsear_llavero(v)
        except (ValueError, binascii.Error) as exc:
            raise ConfiguracionInvalida(f"APP_ENCRYPTION_KEYS invalido: {exc}") from exc
        return v

    @model_validator(mode="after")
    def _validar_llave_activa_en_llavero(self) -> Settings:
        llavero = _parsear_llavero(self.app_encryption_keys)
        if self.app_encryption_key_activa not in llavero:
            raise ConfiguracionInvalida(
                "APP_ENCRYPTION_KEY_ACTIVA referencia una version ausente de " "APP_ENCRYPTION_KEYS"
            )
        return self

    @model_validator(mode="after")
    def _validar_ensayo_no_apunta_a_produccion(self) -> Settings:
        if self.entorno == "ensayo":
            if not self.canvas_base_url_produccion_referencia:
                raise ConfiguracionInvalida(
                    "ENTORNO=ensayo exige CANVAS_BASE_URL_PRODUCCION_REFERENCIA "
                    "para poder contrastarla (SPEC 14 S14.4)"
                )
            if self.canvas_base_url == self.canvas_base_url_produccion_referencia:
                raise ConfiguracionInvalida(
                    "CANVAS_BASE_URL de ensayo coincide con la de produccion: "
                    "el proceso no arranca (SPEC 14 S14.4)"
                )
        return self

    def llavero_cifrado(self) -> dict[int, bytes]:
        return _parsear_llavero(self.app_encryption_keys)

    def instancias_canvas(self) -> list[InstanciaCanvas]:
        datos = json.loads(self.canvas_instancias)
        return [InstanciaCanvas(**d) for d in datos]

    @field_validator("canvas_instancias")
    @classmethod
    def _validar_canvas_instancias(cls, v: str) -> str:
        try:
            datos = json.loads(v)
            for d in datos:
                InstanciaCanvas(**d)
        except Exception as exc:
            raise ConfiguracionInvalida(f"CANVAS_INSTANCIAS invalido: {exc}") from exc
        return v


def _parsear_llavero(valor: str) -> dict[int, bytes]:
    """Parsea `APP_ENCRYPTION_KEYS` como `version:clave_base64,version:clave_base64`.

    Cada clave decodificada debe tener exactamente 32 bytes (AES-256).
    """
    llavero: dict[int, bytes] = {}
    for entrada in valor.split(","):
        entrada = entrada.strip()
        if not entrada:
            continue
        version_str, _, clave_b64 = entrada.partition(":")
        if not _ or not version_str.strip().isdigit():
            raise ValueError(f"entrada de llavero mal formada: {entrada!r}")
        version = int(version_str.strip())
        clave = base64.b64decode(clave_b64.strip())
        if len(clave) != 32:
            raise ValueError(f"la clave de version {version} no tiene 32 bytes")
        llavero[version] = clave
    if not llavero:
        raise ValueError("APP_ENCRYPTION_KEYS esta vacio")
    return llavero


@lru_cache
def obtener_configuracion() -> Settings:
    try:
        return Settings()  # type: ignore[call-arg]
    except Exception as exc:  # pydantic ValidationError u otra
        raise ConfiguracionInvalida(str(exc)) from exc
