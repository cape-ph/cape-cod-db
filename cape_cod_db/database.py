import logging

from sqlmodel import SQLModel, create_engine

db_url = None

try:
    from .migrations.env import config

    logger = logging.getLogger("alembic.env")

    # this works for the case where we're doing alembic things. When we're
    # doing orm things (e.g. in an api lambda) we need another source to check
    # some other source for the DB  URL as the config object doesn't exit in
    # env.py. alembic doesn't play when we're just doing orm things.
    db_url = config.get_main_option("sqlalchemy.url")
except AttributeError as ae:
    logging.basicConfig()
    logger = logging.getLogger(__file__)
    logger.warning(
        "Not running with a valid alembic config. Checking for DB_URL "
        "environment variable"
    )

    import os

    db_url = os.getenv("DB_URL")

if db_url is None:
    logger.error(
        "DB_URL is not configured. This needs to be in the alembic config "
        "file or an environment variable named `DB_URL`"
    )
    exit(1)

logger.info(f"Configured for database: {db_url}")

engine = create_engine(db_url)


def create_tables():
    """Create the tables on the DB pointed to by `engine`.

    At this point we expect the empty database to exist when calling this.
    """
    SQLModel.metadata.create_all(engine)
