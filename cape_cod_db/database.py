import logging

from sqlmodel import SQLModel, create_engine

from .migrations.env import config

logging.basicConfig()
logger = logging.getLogger("sqlalchemy.engine")

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
