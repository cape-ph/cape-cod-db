import os
import sys

# so that alembic has access to our models, we're adding the project root here
proj_root = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, proj_root)

print(sys.path)

from logging.config import fileConfig

from dotenv import dotenv_values
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from alembic import context

# NOTE: as new table models are added, they need to be imported here.
from cape_cod_db.models import User

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


# cape_cod_db has its own config file and which contains database url.
# Additionally for migrations we're running from an ephemeral virtualenv that
# may not have a good .env file available.
# we're going to ignore what's set in the alembic ini then check the following
# in decreasing order of precedence:
# - an environment variable named "DB_URL"
# - the project .env file for a key of "DB_URL"
# We'll consider one of those to be required and will error out if not found.

db_url = os.getenv("DB_URL")

if db_url is None:
    # TODO: we also specify a log level in that config. we *could* use that here,
    #       but for now we're going to respect what's in the alembic ini since the
    #       logging here is for a different purpose than the logging in the db app's
    #       setup
    proj_config = dotenv_values(os.path.join(proj_root, ".env"))
    db_url = proj_config.get("DB_URL")

if db_url is None:
    print(
        "No DB_URL configured in environment variable or project level .env "
        "file. Cannot continue."
    )
    # if we don't have this we have problems. so we are bailing
    sys.exit(1)


config.set_main_option("sqlalchemy.url", db_url)


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
