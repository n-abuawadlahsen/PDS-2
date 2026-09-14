"""Aplicacion de migraciones (SPEC 14 S14.8.3).

Las aplica el trabajador al arrancar, tomando antes un `pg_advisory_lock`
dedicado, antes de tomar ningun trabajo. El servicio web nunca migra: solo
llama a `revision_actual()`/`revision_esperada()` para declarar el estado en
`GET /estado`. Esta funcion solo expone upgrade -- nunca downgrade contra
produccion (regla 4 de S14.8.3).
"""

from __future__ import annotations

from sqlalchemy.engine import Connection, Engine

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from app.infraestructura.cerrojos import cerrojo_global

_CLAVE_CERROJO_MIGRACIONES = "migraciones"


def _config_alembic(database_url: str) -> Config:
    cfg = Config("alembic.ini")
    # configparser interpreta `%`: una contraseña codificada en la URL lo trae.
    cfg.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return cfg


def aplicar_migraciones(engine: Engine, *, database_url: str) -> None:
    """`aplicar_migraciones()`: unico punto que invoca `alembic upgrade head`.

    Toma `pg_advisory_lock(hashtext('migraciones'))` antes de migrar, para que
    dos procesos desde la misma imagen no compitan (S14.8.3.1).
    """
    with engine.connect() as conexion, cerrojo_global(conexion, _CLAVE_CERROJO_MIGRACIONES):
        cfg = _config_alembic(database_url)
        command.upgrade(cfg, "head")


def revision_esperada() -> str | None:
    cfg = _config_alembic("")
    script = ScriptDirectory.from_config(cfg)
    return script.get_current_head()


def revision_actual(engine_o_conexion: Engine | Connection) -> str | None:
    if isinstance(engine_o_conexion, Connection):
        contexto = MigrationContext.configure(engine_o_conexion)
        return contexto.get_current_revision()
    with engine_o_conexion.connect() as conexion:
        contexto = MigrationContext.configure(conexion)
        return contexto.get_current_revision()
