---
type: source
title: "Reproduce drifted DDL in models before Alembic autogenerate"
slug: alembic-preserve-drifted-ddl-before-autogenerate
status: insight
created: 2026-07-13
updated: 2026-07-13
category: database
---
# Reproduce drifted DDL in models before Alembic autogenerate
When an applied Alembic migration declares constraints that the SQLModel/SQLAlchemy models do not express (FK `ON DELETE CASCADE`, named `UNIQUE`, GIN indexes), `alembic revision --autogenerate` will emit DROP statements for them because it diffs the DB against model metadata. Before generating a new migration, encode those constraints back into the models via `sa_column=Column(..., ForeignKey(..., ondelete="CASCADE"))` and `__table_args__` (`UniqueConstraint`, `Index(..., postgresql_using="gin", postgresql_ops=...)`). Verify by running a second autogenerate against a throwaway DB already at head and confirming it produces an empty migration (0 `op.*` calls).

Also watch for silent nullability drift: switching a required FK from `Field(foreign_key=...)` to `Field(sa_column=Column(Integer, ForeignKey(...)))` without `nullable=False` flips the column to nullable, and autogenerate will try to `alter_column ... nullable=True`. Always set `nullable=False` explicitly on non-optional `sa_column` fields.

For Postgres partial-null uniqueness (e.g. a grant table where one subject FK is NULL), use `UniqueConstraint(..., postgresql_nulls_not_distinct=True)` so NULLs are treated as equal and duplicates are still blocked.

Validate migrations on a disposable database (`createdb`/`dropdb`) rather than the dev DB, especially when the dev DB has data that blocks earlier migrations (e.g. a NOT NULL backfill failing on legacy rows). Test both `upgrade head` and `downgrade -1`, and exercise the CHECK/UNIQUE/CASCADE behavior with real inserts.

See [[entities/database-schema]] and [[concepts/alembic-migrations]] in the cape-cod-db wiki.
*Category: database*
---
*Captured: 2026-07-13*
## Related
_Add links to related pages._