---
type: entity
title: Database Schema
slug: database-schema
created: 2026-07-13
updated: 2026-07-13
tags: ["schema", "sqlmodel", "models", "postgres", "abac", "tables"]
---

# Database Schema

All tables are defined as SQLModel classes in `cape_cod_db/models.py`. This page
records the schema exactly as the code defines it, cross-checked against the
applied Alembic DDL in
`cape_cod_db/migrations/versions/6919c61ea401_add_authorization_tables_tributary_user_.py`.
When in doubt, `models.py` plus the migration DDL are the source of truth.

Tables are kept in a single module by intent. The header comment notes the split
will only happen "should this get painful."

Base timestamp behavior comes from [[concepts/capemodel-base-class]]. There is
an important drift between the models and the applied DDL (cascades and a unique
constraint) documented in the "Model vs applied DDL drift" section below.

## User (`user`)

Core user identity, sourced from Cognito.

- `id: int | None` - primary key, autoincrement.
- `first_name: str` - required.
- `last_name: str` - required.
- `email: str` - required, `index=True`, `unique=True` (index `ix_user_email`).
- `created_at`, `last_edited` - inherited from `CapeModel`.

`__repr__` currently includes `first_name` and `last_name` (PII). A TODO in the
code flags that repr output must exclude PII/PHI before it is used for log
tracing. Do not rely on the repr for safe logging yet.

## Tributary (`tributary`)

An organizational unit (team, department, project) that owns resources and has
user members. Membership grants base permissions. Tributaries can form a
hierarchy via `parent_id`.

- `id: int | None` - primary key.
- `name: str` - `unique=True`, `index=True`.
- `code: str` - `unique=True`, `index=True` (short code, e.g. `ENG`, `DS`).
- `description: str | None` - nullable, stored as a `Text` column.
- `parent_id: int | None` - self-referential FK to `tributary.id`, nullable.
- `attributes: dict` - JSONB, `nullable=False`, server default `{}`.
- `created_at`, `last_edited` - inherited.

Every tributary is expected to have four standard S3 bucket Resource records
(raw uploads, clean uploads, raw results, clean results), but these are
`Resource` rows, not columns on this table.

## UserTributary (`usertributary`)

Many-to-many membership join between users and tributaries, carrying a role.
This is the core attribute for ABAC decisions. It inherits `SQLModel` directly,
NOT `CapeModel`, so it has no `created_at` / `last_edited` columns.

- `user_id: int` - FK `user.id`, part of composite primary key.
- `tributary_id: int` - FK `tributary.id`, part of composite primary key.
- `role: str` - default `"member"`; documented values are `member`, `admin`,
  `viewer`.
- `granted_at: datetime` - `default_factory` UTC now, `nullable=False`.
- `granted_by: int | None` - FK `user.id`, nullable.
- `expires_at: datetime | None` - nullable.
- Primary key is composite `(user_id, tributary_id)`.
- Indexes: `ix_usertributary_user_id`, `ix_usertributary_tributary_id`.

## Resource (`resource`)

Platform-agnostic catalog of things that can be authorized (S3 paths, EC2
instances, applications, etc.). Resource-specific detail lives in JSONB
`attributes`.

- `id: int | None` - primary key.
- `resource_type: str` - `index=True` (canonical value for S3 is `"s3"`; other
  observed values: `"ec2"`, `"application"`).
- `resource_identifier: str` - `unique=True`, `index=True`. For S3 this is the
  `s3://bucket/path` form, not the ARN.
- `display_name: str` - human-readable name.
- `tributary_id: int | None` - FK `tributary.id`, nullable for shared resources.
- `access_type: str` - single access value for the resource (observed values in
  fixtures: `read`, `write`, `both`, `ssh`, `admin`).
- `attributes: dict` - JSONB, `nullable=False`, server default `{}`; carries
  `bucket`, `path_prefix`/`arn`, `category`, etc.
- `created_at`, `last_edited` - inherited.
- Indexes: `ix_resource_resource_identifier` (unique),
  `ix_resource_resource_type`, and a GIN index `ix_resource_attributes` using
  `jsonb_path_ops`.

The single `access_type` per row means a resource has one access value for
everyone. Removing that limitation is the subject of the planned ABAC rework;
see [[concepts/abac-authorization-design]].

## UserAttribute (`userattribute`)

Flexible key-value attributes on a user for non-tributary authorization
decisions (lifecycle status, admin flags, clearance, synced AD/SAML attributes).

- `id: int | None` - primary key.
- `user_id: int` - FK `user.id`, `index=True` (`ix_userattribute_user_id`).
- `attribute_key: str` - e.g. `user_status`, `is_admin`, `system_role`,
  `clearance_level`.
- `attribute_value: str` - string value, e.g. `active`, `quarantine`,
  `suspended`, `deactivated`, `true`.
- `source: str | None` - nullable, e.g. `system`, `manual`, `ad`, `saml`.
- `created_at`, `last_edited` - inherited.

## Relationships summary

- A user belongs to zero or more tributaries via `UserTributary`.
- A tributary owns zero or more resources via `Resource.tributary_id`; shared
  resources have `tributary_id = NULL`.
- A tributary may have a parent tributary via `Tributary.parent_id`.
- A user has zero or more `UserAttribute` rows.
- `UserTributary.granted_by` references the user who granted the membership.

## Model vs applied DDL drift (important)

The applied migration DDL declares foreign-key `ON DELETE CASCADE` behavior and
a composite unique constraint that the current `models.py` does NOT express:

- `usertributary`: FKs `user_id` and `tributary_id` are `ON DELETE CASCADE` in
  the migration; `models.py` declares plain FKs with no `ondelete`.
- `userattribute`: FK `user_id` is `ON DELETE CASCADE` and there is a
  `UNIQUE (user_id, attribute_key)` constraint
  (`uq_userattribute_user_id_attribute_key`) in the migration; `models.py`
  declares neither.

Consequence: running `alembic revision --autogenerate` from the current models
would likely try to DROP these cascades and the unique constraint, because the
models do not reproduce them. Before autogenerating a new migration, restore
these to `models.py` (via `sa_column` / `__table_args__`) or hand-edit the
generated migration so the constraints are preserved. The cleanup fixture and
the planned ABAC rework both depend on the cascade behavior.

## Related pages

- [[concepts/capemodel-base-class]]
- [[concepts/alembic-migrations]]
- [[entities/test-fixtures]]
- [[concepts/abac-authorization-design]]
- [[entities/cape-cod-db]]
