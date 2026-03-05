from cape_cod_db.database import create_tables
from cape_cod_db.models import User

# WARNING: Usage of this script only applies the most recent schema, with 0
#          respect to migrations and without including any migration tables or
#          history. If migrations are desired (probable) use `capedb.py`
#          instead.


def main():
    create_tables()


if __name__ == "__main__":
    main()
