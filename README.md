# CAPE Environment Database Repo

Repo for the CAPE environment database. This is the main database used by
various resources in CAPE for tracking users, user attributes, and AWS resource
data.

## Schema Overview

### Authorization Model

The database implements an Attribute-Based Access Control (ABAC) system with the
following components:

- **User**: Core user identity (from Cognito)
- **Tributary**: Logical data compartments with associated AWS resources
- **UserTributary**: Many-to-many junction between users and tributaries
- **Resource**: Platform-agnostic resource definitions (S3 paths, EC2 instances,
  etc.) linked to tributaries
- **UserAttribute**: Key-value attributes for users (e.g., `user_status`,
  `role`, `department`)

#### Key Relationships

- Users belong to multiple tributaries (via `UserTributary`)
- Each tributary has multiple resources (via `Resource.tributary_id`)
- Resources define access patterns: `s3_read`, `s3_write`, `ec2_connect`, etc.
- User attributes handle non-tributary authorization (quarantine, admin roles,
  suspension)

#### Standard Resource Pattern

Each tributary typically has 4 S3 bucket resources:

- `raw_uploads` (write access)
- `clean_uploads` (read access)
- `raw_results` (write access)
- `clean_results` (read access)

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

This package provides the `capedb` script to handle DB upgrades, downgrades and
checking of current version. All other `alembic` commands (including upgrades,
downgrades and checking of current version) can be accomplished via normal
`alembic` means.

**_NOTE:_** At this point we expect an empty database to exist before we apply
migrations or create tables. This could change in the future, but for now it's a
requirement. If you followed the postgres setup above you have already done
this.

#### Alembic Config

Usage of the `capedb` script requires an `alembic` config file be available.
This can be accomplished in a number of ways:

- have it available in the current working directory when executing the `capedb`
  script (it will be found automatically)
- specification on the command line when calling `capedb`:
  `capedb [-c | --config <CONFIG_PATH>]`
- specifying the location in the `ALEMBIC_CONFIG` environment variable

**_NOTE:_** However the `alembic.ini` is specified, the value of
`script_location` needs to point to the migrations directory of this package.
This is most likely `<python_site_package_dir>/cape_cod_db/migrations` if you
are using an installed version of this package. The
`<python_site_package_dir>/cape_cod_db` directory also contains an `alembic.ini`
that can be used if defaults are fine, though you will want to specify the
database url as detailed below if you use the builtin config file.

#### Database URL

Though the database url is often defined in the `alembic` config, if you also
need to specify it separately you also have a few options:

- specification on the command line when calling `capedb`:
  `capedb [-x db_url=<DB_URL>]`
- specifying the location in the `DB_URL` environment variable

#### capedb Script Usage

Run the alembic migrations on the empty (or previously upgraded) db to get up to
date `capedb upgrade head`. _NOTE:_ `head` can be replaced with another revision
identifier to go to a specific version.

Downgrades can be performed via `capedb downgrade <revision>`.

The current version can be determined with `capedb current [--verbose]`.

#### capedb-app script

This is probably not anything you want to use. Probably.

This is the more traditional `app.py` like mechanism to create database tables.
This is not compatible with our provided migrations either. If you wish to
create an empty database using only the most schema in this version of this
package without any migration information, this is your boo. But you would have
to maintain your own migrations at that point. If you are maintaining migrations
ever.

This script requires the `DB_URL` environment variable be set and does not work
with alembic at all, so the alembic config is not needed.

### Running Tests

Unit tests live in `tests/` and run with `pytest` (installed via
`poetry install`). They are plain unit tests and do not require a running
database.

```bash
# run the full suite
poetry run pytest

# run a single file or test, verbosely
poetry run pytest tests/test_db_url.py -v
```

### Test Data

Test data fixtures are provided in `fixtures/test/`:

- `test_data.sql`: Loads 6 users, 4 tributaries, 12 resources, 9 user attributes
- `cleanup_test_data.sql`: Removes test data in proper dependency order

```bash
# Load test data (use transaction to allow rollback)
source .env && psql "$DB_URL" -f fixtures/test/test_data.sql

# Clean up test data
source .env && psql "$DB_URL" -f fixtures/test/cleanup_test_data.sql
```

**Important**: When modifying schema or test data, keep both SQL files
synchronized with changes.

### Play With The DB

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

# query authorization data
with Session(db.engine) as session:
    # get user's tributaries
    user = session.exec(select(models.User).where(models.User.email == "alice@example.com")).first()
    tributaries = session.exec(
        select(models.Tributary)
        .join(models.UserTributary)
        .where(models.UserTributary.user_id == user.id)
    ).all()

    # get resources for a tributary
    resources = session.exec(
        select(models.Resource).where(models.Resource.tributary_id == tributaries[0].id)
    ).all()

    # get user attributes
    attrs = session.exec(
        select(models.UserAttribute).where(models.UserAttribute.user_id == user.id)
    ).all()
```

If you prefer `psql` (**_NOTE:_** this assumes you have all the perms on the
db):

```bash
12:12 $ psql cape_env_db


psql (18.3)
Type "help" for help.

cape_env_db=> \d+
                                          List of relations
 Schema |      Name       |   Type   | Owner | Persistence | Access method |    Size    | Description
--------+-----------------+----------+-------+-------------+---------------+------------+-------------
 public | alembic_version | table    | xxxx  | permanent   | heap          | 8192 bytes |
 public | user            | table    | xxxx  | permanent   | heap          | 16 kB      |
 public | user_id_seq     | sequence | xxxx  | permanent   |               | 8192 bytes |

cape_env_db=> \d user
                                         Table "public.user"
   Column    |            Type             | Collation | Nullable |             Default
-------------+-----------------------------+-----------+----------+----------------------------------
 created_at  | timestamp without time zone |           | not null |
 last_edited | timestamp without time zone |           | not null |
 id          | integer                     |           | not null | nextval('user_id_seq'::regclass)
 first_name  | character varying           |           | not null |
 last_name   | character varying           |           | not null |
 email       | character varying           |           | not null |

cape_env_db=> select * from alembic_version;
 version_num
--------------
 6001985fea71
(1 row)

# NOTE that if you manipulate records via sql, the created_at and last_edited
# **ARE NOT HANDLED FOR YOU**

cape_env_db=> insert into public.user (created_at, last_edited, first_name, last_name, email) values (now(), now(), 'First', 'Last', 'fl@fakeemail.test');
INSERT 0 1
cape_env_db=> select * from public.user;
         created_at         |        last_edited         | id | first_name | last_name |       email
----------------------------+----------------------------+----+------------+-----------+-------------------
 2026-03-05 13:55:21.688756 | 2026-03-05 13:55:21.688756 |  2 | First      | Last      | fl@fakeemail.test
(1 row)
```
