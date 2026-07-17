---
type: concept
title: Alembic migrations
slug: alembic-migrations
created: 2026-07-13
updated: 2026-07-13
tags: ["alembic", "migrations", "schema", "postgres", "workflow"]
---

# Alembic migrations

Schema changes are managed with Alembic. Migrations are the mandatory mechanism
for changing the schema; the direct-create path (`capedb-app`) bypasses
migration history and is only for throwaway databases (see
[[entities/capedb-cli]]).

## Layout

- Migration environment: `cape_cod_db/migrations/env.py`.
- Migration scripts: `cape_cod_db/migrations/versions/`.
- Config: `cape_cod_db/alembic.ini` (its `script_location` points at
  `%(here)s/migrations`).
- Template for new scripts: `cape_cod_db/migrations/script.py.mako`.

Note: a top-level `alembic/` directory exists but contains only stale
`__pycache__` bytecode, no source. The real migrations live under
`cape_cod_db/migrations/`. Do not treat the root `alembic/` as active.

## Migration chain (current head)

Three revisions, applied in order:

1. `eecb735a6c3b` - create_user_table (initial `user` table, no `email`).
2. `6001985fea71` - add_email_to_user_table (adds unique-indexed `email`).
3. `6919c61ea401` - add authorization tables: `tributary`, `resource`,
   `userattribute`, `usertributary` (current head).

Revision `6919c61ea401` is the authoritative DDL for the authorization tables.
It includes constraints not currently expressed in `models.py` (cascade deletes
and a unique constraint on `userattribute`); see the drift note in
[[entities/database-schema]].

## env.py behavior

- `target_metadata = SQLModel.metadata`.
- All table models are imported at the top of `env.py`
  (`Resource, Tributary, User, UserAttribute, UserTributary`). Any NEW model
  must be added to that import for autogenerate to see it.
- Database URL resolution order (highest precedence first): the `-x db_url=...`
  CLI argument, then the `DB_URL` environment variable, then `sqlalchemy.url` in
  the ini file.
- A constraint naming convention is applied (`ix_`, `uq_`, `ck_`, `fk_`, `pk_`)
  so names are stable across database backends.
- `compare_type=True` detects column type changes; `render_as_batch=True` is set
  for SQLite compatibility (SQLite is not used in practice).

## Creating a migration

1. Edit `cape_cod_db/models.py`.
2. Add any new model to the imports in `cape_cod_db/migrations/env.py`.
3. Generate:
   `alembic -c cape_cod_db/alembic.ini revision --autogenerate -m "message"`.
4. Hand-review the generated script. Autogenerate will not infer column renames
   and, given the current model/DDL drift, may try to drop cascades or the
   `userattribute` unique constraint - preserve them explicitly.
5. Provide a working `downgrade()`.
6. Apply and test up/down; keep the fixtures in sync (see
   [[entities/test-fixtures]]).
7. Commit the migration together with the model change.

## Applying migrations

The `.env` file holds `DB_URL`. Typical commands:

```bash
source .env && capedb -c cape_cod_db/alembic.ini -x db_url="$DB_URL" current --verbose
source .env && capedb -c cape_cod_db/alembic.ini -x db_url="$DB_URL" upgrade head
source .env && capedb -c cape_cod_db/alembic.ini -x db_url="$DB_URL" downgrade -1
```

An empty database must already exist before the first migration is applied.

## Related pages

- [[entities/capedb-cli]]
- [[entities/database-schema]]
- [[concepts/database-connection]]
- [[entities/test-fixtures]]
- [[entities/cape-cod-db]]
