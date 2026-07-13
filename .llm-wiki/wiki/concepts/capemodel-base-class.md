---
type: concept
title: CapeModel base class and timestamp semantics
slug: capemodel-base-class
created: 2026-07-13
updated: 2026-07-13
tags: ["sqlmodel", "timestamps", "base-class", "pitfall", "models"]
---

# CapeModel base class and timestamp semantics

`CapeModel` is the SQLModel base class that most CAPE tables inherit from. It is
defined in `cape_cod_db/models.py` and is NOT itself a table (`table=True` is
not set). It adds two timestamp columns:

```python
class CapeModel(SQLModel):
    created_at: datetime = Field(
        default=datetime.now(timezone.utc), nullable=False
    )
    last_edited: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
```

## Which tables inherit it

`User`, `Tributary`, `Resource`, and `UserAttribute` inherit `CapeModel`, so
they get `created_at` and `last_edited`. `UserTributary` inherits plain
`SQLModel` directly and therefore has neither timestamp column. See
[[entities/database-schema]].

## created_at pitfall (evaluated once at import)

`created_at` uses `default=datetime.now(timezone.utc)`. That expression is
evaluated a single time, when the module is imported, and the resulting fixed
timestamp becomes the column default. Every ORM insert that does not set
`created_at` explicitly will receive that same import-time value, not the time
of insertion.

`last_edited` avoids this by using `default_factory=lambda: ...`, which is
evaluated per instance. If a true per-row creation time is required from the
ORM, `created_at` should be changed to `default_factory` as well (or given a
server default). This is a latent correctness issue, not a syntax error, so it
does not surface in linting.

## Raw SQL does not get timestamps for free

`onupdate` for `last_edited` is an ORM-level hook. When rows are inserted or
updated with raw SQL (for example in `psql` or in the test fixtures),
`created_at` and `last_edited` are NOT populated automatically. The migration
DDL creates both columns as `DateTime NOT NULL` with no server default, so raw
inserts must supply the values. The fixtures do this with `NOW()`; see
[[entities/test-fixtures]].

## Related pages

- [[entities/database-schema]]
- [[entities/test-fixtures]]
- [[entities/cape-cod-db]]
