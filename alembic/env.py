from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# ── Point sys.path at the plp_lms package ──────────────────────────────────
# alembic.ini lives one level above plp_lms/, so we add plp_lms/ explicitly.
_here = os.path.dirname(os.path.abspath(__file__))
_app_dir = os.path.join(os.path.dirname(_here), "plp_lms")
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

# ── Pull DATABASE_URL from the app config and inject it ────────────────────
from config import DATABASE_URL  # noqa: E402
from database import Base         # noqa: E402  (imports all models via init_db logic)

# Import every model so Base.metadata is fully populated for autogenerate
import models.user, models.course, models.cohort, models.assessment
import models.submission, models.certificate, models.training_record
import models.notification, models.audit, models.learning_path
import models.skill, models.document, models.message, models.rpl
import models.report_subscription, models.retention

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override the placeholder sqlalchemy.url with the real DATABASE_URL
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
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
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
