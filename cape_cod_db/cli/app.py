from cape_cod_db.database import create_db_and_tables
from cape_cod_db.models import User

# NOTE: if we need to create fixtures in code, do that here. add functions for
#       each fixture set and call them in main after creating the tables. if we
#       end up providing dumps of fixtures instead, we don't need to add code,
#       just import the dumps (probably)


def main():
    create_db_and_tables()


if __name__ == "__main__":
    main()
