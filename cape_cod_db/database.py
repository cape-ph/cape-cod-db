import logging

from dotenv import dotenv_values
from sqlmodel import SQLModel, create_engine

config = dotenv_values(".env")

logging.basicConfig()
logger = logging.getLogger("sqlalchemy.engine")
logger.setLevel(logging.getLevelName(config.get("LOG_LEVEL", logging.INFO)))


db_url = config.get("DB_URL", None)

if db_url is None:
    logger.error("DB_URL is not configured")
    exit(1)

engine = create_engine(db_url)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
