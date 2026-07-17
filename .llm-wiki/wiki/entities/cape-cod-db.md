---
type: entity
title: cape-cod-db
slug: cape-cod-db
created: 2026-07-13
updated: 2026-07-13
tags: ["cape", "database", "sqlmodel", "alembic", "postgres", "overview"]
---

# cape-cod-db

`cape-cod-db` is a Python library that holds the SQLModel schema definitions and
Alembic migrations for the CAPE environment database. It is the canonical source
of truth for the authorization data (users, tributary membership, resources, and
user attributes) that downstream CAPE systems consume. Other CAPE projects
install it as a dependency and import its models.

This page is the hub for the project wiki. Every fact here is derived from the
code in this repository, which is the authoritative source when documentation
and code disagree.

## What this repo owns

- The database schema, defined as SQLModel classes in `cape_cod_db/models.py`.
  See [[entities/database-schema]].
- Alembic migrations under `cape_cod_db/migrations/versions/`. See
  [[concepts/alembic-migrations]].
- Two console scripts, `capedb` and `capedb-app`. See [[entities/capedb-cli]].
- Engine/connection setup in `cape_cod_db/database.py`. See
  [[concepts/database-connection]].
- Test data fixtures under `fixtures/test/`. See [[entities/test-fixtures]].

## What this repo does NOT own

- There is no data-access API. `cape_cod_db/__init__.py` is empty; the package
  exposes only the SQLModel classes plus `database.engine` and
  `database.create_tables()`.
- OPA policies, the Pulumi resource export, and the Ansible reconcile/sync
  script live in the sibling repos `cape-cod` (Pulumi infra) and `cape-cod-env`
  (Ansible). See [[concepts/abac-authorization-design]] for how they fit
  together.

## Technology stack

- Python 3.10+ (union type syntax `int | None`).
- SQLModel `^0.0.37` (SQLAlchemy + Pydantic) as the ORM layer.
- PostgreSQL 18.x as the target database (uses JSONB and GIN indexes).
- Alembic `^1.18.4` for migrations, with `psycopg2-binary` as the driver.
- Poetry for build and dependency management; distributed to PyPI as
  `cape_cod_db`.
- Ruff, Black, isort (all line length 80), and Pyright for quality checks. See
  [[concepts/development-workflow]].

## Current version

`0.3.0` (from `pyproject.toml` and `CHANGELOG.md`). The database currently has a
single `access_type` value per `Resource` row; an ABAC rework toward per-subject
grants is planned but not yet in the code. See
[[concepts/abac-authorization-design]].

## Related pages

- [[entities/database-schema]]
- [[concepts/capemodel-base-class]]
- [[concepts/alembic-migrations]]
- [[entities/capedb-cli]]
- [[concepts/database-connection]]
- [[entities/test-fixtures]]
- [[concepts/development-workflow]]
- [[concepts/release-and-ci]]
- [[concepts/abac-authorization-design]]
