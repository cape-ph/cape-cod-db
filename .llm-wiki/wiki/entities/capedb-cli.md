---
type: entity
title: capedb and capedb-app CLI
slug: capedb-cli
created: 2026-07-13
updated: 2026-07-13
tags: ["cli", "alembic", "capedb", "scripts", "poetry"]
---

# capedb and capedb-app CLI

The package registers two console scripts in `pyproject.toml`
(`[tool.poetry.scripts]`), available after `poetry install`:

```toml
capedb = "cape_cod_db.cli.capedb:main"
capedb-app = "cape_cod_db.cli.app:main"
```

## capedb (primary, migration-based)

`cape_cod_db/cli/capedb.py` is a thin wrapper over Alembic's `CommandLine`. Its
`main()` registers three commands and delegates to `alembic.command`:

- `current(config, verbose=False)` - show the current DB revision.
- `upgrade(config, revision)` - upgrade to a revision (`head` for latest).
- `downgrade(config, revision)` - downgrade to a revision.

Because it wraps Alembic's `CommandLine`, it accepts the standard Alembic flags:
`-c/--config` for the ini file (or the `ALEMBIC_CONFIG` env var, or
auto-discovery in the CWD) and `-x db_url=...` for the database URL. See
[[concepts/alembic-migrations]] for URL precedence and usage examples.

## capedb-app (direct create, no migrations)

`cape_cod_db/cli/app.py` calls `database.create_tables()`, which runs
`SQLModel.metadata.create_all(engine)`. This creates the current schema directly
with no migration history and no `alembic_version` table. It is incompatible
with the migration workflow and is intended only for throwaway/prototype
databases. It requires `DB_URL` to be set (it does not use the Alembic config).
See [[concepts/database-connection]].

Prefer `capedb` (migrations) for any database that must track schema state.

## Related pages

- [[concepts/alembic-migrations]]
- [[concepts/database-connection]]
- [[entities/cape-cod-db]]
