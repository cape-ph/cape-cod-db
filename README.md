# CAPE Environment Database Repo

**_TBD_** blah blah repo for the main cape environment database

## Setup

### Local postgresql

#### Installation

We are using version 18.x. Installation instructions are
[provided by the community for various platforms](https://www.postgresql.org/download/)

#### perms to allow database operations

Just so it's said, these are dev only operations. Don't do this in anything but
your test system.

```bash
# connect to postgres as default user
sudo -iu postgres psql

# replace <username> with your username in all of the below. you can do this
# however you want if you know what you're doing, username stuff just makes
# things quick for development.

# create a group for granting some types of access
postgres=# create role <username>_group nologin;

# grant the group total select on the public schema
postgres=# grant select on all tables in schema public to <username>_group;

# and all future tables in the group
postgres=# alter default privileges in schema public grant select on tables to <username>_group;

# and usage on the public schema in general
postgres=# grant usage on schema public to <username>_group;

# now your user
postgres=# create role <username> with login;

# let your user create databases
postgres=# alter user <username> createdb;

# create the cape db so we can grant some perms there
postgres=# create database cape_env_db;

# allow create of this database - not strictly necessary since this user has
# been granted createdb
postgres=# grant create on database cape_env_db to <username>;

# allow connect to this database
postgres=# grant connect on database cape_env_db to <username>;

# make your user owner of the db
postgres=# alter database cape_env_db owner to <username>;

postgres=# exit

# at this point you should be able to connect to the cape_env_db as yourself with no password.
14:43 $ psql cape_env_db
```

### repo

Users of `mise en place` or `asdf` can use the `.tool-versions` and `mise.toml`
provided. For those managing software in other manners, the software
requirements are as follows:

- python 3.10+
- poetry 2.3+
- items in `pyproject.toml` (installed via `poetry install`)

### Setup DB

Make sure the env file contains a valid DB_URL for your setup. If you're
following this setup exactly, the value is already correct
(`DB_URL="postgresql:///cape_env_db"`).

**_NOTE:_** You can also specify this in an environment variable name `DB_URL`.
This is intended more for automation use cases where the installation of the
package is less controllable.

This package provides the `capedb` script to handle DB upgrades, downgrades and
checking of current version. All other `alembic` commands (including upgrades,
downgrades and checking of current version) can be accomplished via normal
`alembic` means.

Run the alembic migrations on the empty (or previously upgraded) db to get up to
date `capedb upgrade head`. _NOTE:_ `head` can be replaced with another revision
identifier to go to a specific version.

Downgrades can be performed via `capedb upgrade <revision>`.

The current version can be determined with `capedb current [--verbose]`

### play with it

From repo root in the python repl of your fancy (that has all the dependencies
installed).

```python
import cape_cod_db
from sqlmodel import select, Session
from cape_cod_db import database as db
from cape_cod_db import models

# add a user
with Session(db.engine) as session:
    usr = models.User(
        first_name="First", last_name="Last", email="fl@fakeemail.test"
    )
    session.add(usr)
    session.commit()

# list the users in the db
with Session(db.engine) as session:
    stmnt = select(models.User)
    res = session.exec(stmnt)

    for u in res.all():
        print(u)

# update the user
with Session(db.engine) as session:
    usr_stmnt = select(models.User).where(
        models.User.first_name == "First", models.User.last_name == "Last"
    )
    usr = session.exec(usr_stmnt).first()
    usr.first_name = "Furst"
    session.add(usr)
    session.commit()

# list them again to show the first name and modified time have changed.
with Session(db.engine) as session:
    stmnt = select(models.User)
    res = session.exec(stmnt)

    for u in res.all():
        print(u)
```
