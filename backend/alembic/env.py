from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Importar todos los modulos de modelos para que Base.metadata los conozca.
from app.adaptadores import (  # noqa: F401
    modelos_aprovisionamiento,
    modelos_canvas,
    modelos_curso,
    modelos_github,
    modelos_identidad,
    modelos_infraestructura,
    modelos_mapeo,
    modelos_padron,
    modelos_tarea,
)
from app.adaptadores.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# La URL real viene de DATABASE_URL (S14.6.1.1: toda la configuracion viaja por
# variables de entorno), nunca cableada en alembic.ini. Orden: la variable de
# entorno; la que ya puso quien invoca (el trabajador, `aplicar_migraciones`); y
# por ultimo la configuracion completa, que lee el `.env` en desarrollo local.
url = os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
if not url:
    from app.infraestructura.config import obtener_configuracion

    url = obtener_configuracion().database_url
# configparser interpreta `%`: una contraseña codificada en la URL lo trae.
config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
