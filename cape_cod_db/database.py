import logging

from sqlmodel import SQLModel, create_engine

from .migrations.env import config

logger = logging.getLogger("alembic.env")

# TODO: this works for the case where we're doing alembic things. When
#       we start doing orm things (e.g. in an api lambda) we will need
#       to check some other source first (like an env var, which we
#       check for in the alembic env.py already). the alembic env.py
#       shouldn't come into play in the case where we're just attaching to the
#       DB via ORM
db_url = config.get_main_option("sqlalchemy.url")

if db_url is None:
    logger.error(
        "DB_URL is not configured. This needs to be in the alembic config "
        "file or an environment variable named `DB_URL`"
    )
    exit(1)

logger.info(f"Configured for database: {db_url}")

engine = create_engine(db_url)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
