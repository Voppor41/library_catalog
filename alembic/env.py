import asyncio
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection

from alembic import context

# 1. Импортируем settings, Base и НАШ ГОТОВЫЙ ENGINE
from src.library_catalog.core.config import settings
from src.library_catalog.core.database import Base, engine

# Импортировать все модели (ОБЯЗАТЕЛЬНО!)
from src.library_catalog.data.models import book  # noqa
from src.library_catalog.data.models import user

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Установить target_metadata из Base
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Для оффлайн миграций используем URL с драйвером
    url = str(settings.database_url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    # Используем наш готовый engine из database.py, у которого уже правильный postgresql+asyncpg://
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()