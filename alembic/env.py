from logging.config import fileConfig
import os
import asyncio

from dotenv import load_dotenv

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# ALEMBIC CONFIGURATION
# =========================================================

config = context.config


# =========================================================
# LOGGING CONFIGURATION
# =========================================================

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# =========================================================
# DATABASE URL
# =========================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env")


config.set_main_option(
    "sqlalchemy.url",
    DATABASE_URL.replace("%", "%%")
)


# =========================================================
# IMPORT BASE AND MODELS
# =========================================================

from src.configs.model import Base

from src.modules.admin.models import Admin
from src.modules.user.models import Student


# =========================================================
# TARGET METADATA
# =========================================================

target_metadata = Base.metadata


# =========================================================
# OFFLINE MIGRATION
# =========================================================

def run_migrations_offline() -> None:

    url = config.get_main_option(
        "sqlalchemy.url"
    )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
    )

    with context.begin_transaction():
        context.run_migrations()


# =========================================================
# ONLINE MIGRATION
# =========================================================

def do_run_migrations(connection):

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:

    connectable = async_engine_from_config(
        config.get_section(
            config.config_ini_section,
            {}
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:

        await connection.run_sync(
            do_run_migrations
        )

    await connectable.dispose()


# =========================================================
# START MIGRATION
# =========================================================

if context.is_offline_mode():

    run_migrations_offline()

else:

    asyncio.run(
        run_migrations_online()
    )