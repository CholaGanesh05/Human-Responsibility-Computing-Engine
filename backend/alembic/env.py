"""
HRCE — Alembic Environment Configuration
Supports async SQLAlchemy engine for migrations.
"""
import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

# ─── Make 'app' importable ────────────────────────────────────
# Alembic runs from backend/alembic/, so we need to add backend/ to sys.path
# so that 'from app.core.config import settings' resolves correctly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# Import Base and settings from the app
from app.core.config import settings
from app.core.database import Base

# ─── Alembic Config ───────────────────────────────────────────
config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models here so Alembic can detect them for autogenerate
from app.models.user import User
from app.models.event import Event
from app.models.responsibility import Responsibility
from app.models.dependency import Dependency
from app.models.document import Document

target_metadata = Base.metadata


# ─── Offline Mode ─────────────────────────────────────────────
def run_migrations_offline() -> None:
    """Run migrations without a live DB connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ─── Online Mode (Async) ──────────────────────────────────────
def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations with an async DB connection."""
    connectable = create_async_engine(settings.database_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


# ─── Entry Point ──────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    # asyncio.run() would fail if there's already a running loop.
    # Using get_event_loop().run_until_complete() is the correct
    # pattern for Alembic's synchronous entry point.
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Fallback for environments with an existing event loop
        import nest_asyncio  # type: ignore[import]
        nest_asyncio.apply()
        loop.run_until_complete(run_migrations_online())
    else:
        asyncio.run(run_migrations_online())

