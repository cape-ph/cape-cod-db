import logging
import os

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from alembic import context

# NOTE: as new table models are added, they need to be imported here.
from cape_cod_db.models import User

logging.basicConfig()
logger = logging.getLogger("sqlalchemy.engine")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata


# we have 3 ways to specify the database url (higher in list is higher
# precedence):
# - command line parameter `db_url`
# - env var `DB_URL`
# - alembic config file value `sqlalchemy.url`

cli_args = context.get_x_argument(as_dictionary=True)

# first try a cli arg
db_url = cli_args.get("db_url", None)

# then an env var
if db_url is None:
    db_url = os.getenv("DB_URL")

# we've already got the file config, so if db_url is not None by here, overwrite
# the file config value
if db_url is not None:
    config.set_main_option("sqlalchemy.url", db_url)

logging.info(
    f"Configured for database: {config.get_main_option('sqlalchemy.url')}"
)

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
    # since different DB vendors use different default naming conventions for
    # things, and sqlalchemy can have issue with these sometimes, we're using
    # specified naming convention patterns. these will apply to whatever engine
    # we're using.
    # abbreviations:
    # - ix: index
    # - uq: uniqueness constraint
    # - ck: check constraint
    # - fk: foreign key
    # - pk: primary key
    naming_convention = {
        "ix": "ix_%(table_name)s_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        # look for column type changes
        compare_type=True,
        # apply our naming convention
        naming_convention=naming_convention,
        # this is really just for SQLite, which we can support but are not using
        # in practice. so if it causes issues, remove it and say we don't
        # support SQLite
        render_as_batch=True,
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

    # since different DB vendors use different default naming conventions for
    # things, and sqlalchemy can have issue with these sometimes, we're using
    # specified naming convention patterns. these will apply to whatever engine
    # we're using.
    # abbreviations:
    # - ix: index
    # - uq: uniqueness constraint
    # - ck: check constraint
    # - fk: foreign key
    # - pk: primary key
    naming_convention = {
        "ix": "ix_%(table_name)s_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # look for column type changes
            compare_type=True,
            # apply our naming convention
            naming_convention=naming_convention,
            # this is really just for SQLite, which we can support but are not using
            # in practice. so if it causes issues, remove it and say we don't
            # support SQLite
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
