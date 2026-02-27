# CAPE Environment Database Repo

***TBD***
blah blah repo for the main cape environment database

## Setup

### Local postgresql

#### Installation
We are using version 18.x. Installation instructions are 
[provided by the community for various platforms](https://www.postgresql.org/download/)

#### perms to allow database operations
Just so it's said, these are dev only operations. Don't do this in anything but your test system.

```bash
# connect to postgres as default user
sudo -iu postgres psql

# create a group for granting some types of access
postgres=# create role lp76_group nologin;

# grant the group total select on the public schema 
postgres=# grant select on all tables in schema public to lp76_group;

# and all future tables in the group
postgres=# alter default privileges in schema public grant select on tables to lp76_group;

# and usage on the public schema in general
postgres=# grant usage on schema public to lp76_group;

# now your user (replace <username> with your username)
postgres=# create role <username> with login;

# let your user create databases (replace <username> with your username)
postgres=# alter user <username> createdb;

# create the cape db so we can grant some perms there
postgres=# create database cape_env_db;

# allow create of this database - not strictly necessary since this user has 
# been granted createdb (replace <username> with your username)
postgres=# grant create on database cape_env_db to <username>;

# allow connect to this database (replace <username> with your username)
postgres=# grant connect on database cape_env_db to <username>;

# make your user owner of the db (replace <username> with your username)
postgres=# alter database cape_env_db owner to <username>;

postgres=# exit

# at this point you should be able to connect to the cape_env_db as yourself with no password.
14:43 $ psql cape_env_db
```

### repo
Users of `mise en place` or `asdf` can use the `.tool-versions` and `mise.toml`
provided. For those managing software in other manners, the software requirements 
are as follows: 
- python 3.10
- items in `requirements.txt`


### Setup DB
Make sure the env file contains a valid DB_URL for your setup. If you're 
folling this setup exactly, the value is already correct 
(`DB_URL="postgresql:///cape_env_db"`).

Run the alembic migrations on the empty (or previously alembic updated) db to get up to date
`alembic upgrade head`

### play with it
From repo root in the python repl of your fancy (that has all the dependencies from 
`requirements.txt`).

```python
import cape_cod_db
from sqlmodel import select, Session
from cape_cod_db import database as db
from cape_cod_db import models

# add a user
with Session(db.engine) as session:
    usr = models.User(first_name="First", last_name="Last", email="fl@fakeemail.test")
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
