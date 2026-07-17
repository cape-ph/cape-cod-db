---
type: concept
title: Database connection and engine
slug: database-connection
created: 2026-07-13
updated: 2026-07-13
tags: ["engine", "connection", "db-url", "sqlmodel", "import-side-effect"]
---

# Database connection and engine

`cape_cod_db/database.py` builds the SQLAlchemy/SQLModel `engine` and exposes it
as a module-level global, plus a `create_tables()` helper.

## URL resolution and import-time side effect

At import time, `database.py` resolves the database URL:

1. It tries to import the Alembic `config` object from `migrations.env` and read
   `sqlalchemy.url`. This path works when Alembic is driving (the config
   exists).
2. If that raises `AttributeError` (ORM-only usage, e.g. inside an API Lambda),
   it falls back to the `DB_URL` environment variable.
3. If no URL is found, it logs an error and calls `exit(1)`.

The `exit(1)` is a module-level side effect: importing `cape_cod_db.database`
with no `DB_URL` set will terminate the process. Anything that only needs the
`models` classes should import `cape_cod_db.models` directly and avoid importing
`database`. Making the engine creation lazy (so importing the module does not
kill the process) is a noted optional improvement, driven by the sibling
`cape-cod-env` sync script that wants to import models without a live DB.

## Engine and create_tables

```python
engine = create_engine(db_url)

def create_tables():
    SQLModel.metadata.create_all(engine)
```

- `engine` is created once at import and reused.
- `create_tables()` backs the `capedb-app` script (see [[entities/capedb-cli]]);
  it creates the current schema with no migration history.

## Security note

`database.py` logs the configured database URL at INFO level. In production this
would leak credentials embedded in the URL and must be sanitized. Broader
project security rules: no credentials in code, no PII/PHI in logs. See
[[concepts/development-workflow]].

## Related pages

- [[entities/capedb-cli]]
- [[concepts/alembic-migrations]]
- [[concepts/development-workflow]]
- [[entities/cape-cod-db]]
