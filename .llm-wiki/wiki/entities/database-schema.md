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
`cape_cod_db/migrations/versions/6919c61ea401_add_authorization_tables_tributary_user_.py`
and the ABAC rework migration
`cape_cod_db/migrations/versions/010c0bff0b83_abac_per_subject_resource_grants.py`.
When in doubt, `models.py` plus the migration DDL are the source of truth.

Tables are kept in a single module by intent. The header comment notes the split
will only happen "should this get painful."

Base timestamp behavior comes from [[concepts/capemodel-base-class]]. The models
now reproduce the cascade and unique constraints that the applied DDL declares;
see the "Model vs applied DDL: reconciled" section below.

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
`attributes`. `Resource` is a pure catalog: it records WHAT exists, never WHO
can access it. Access is expressed by `ResourceGrant` rows (below) plus
role-based tributary defaults evaluated in policy.

- `id: int | None` - primary key.
- `resource_type: str` - `index=True` (canonical value for S3 is `"s3"`; other
  observed values: `"ec2"`, `"application"`).
- `resource_identifier: str` - `unique=True`, `index=True`. For S3 this is the
  `s3://bucket/path` form, not the ARN.
- `display_name: str` - human-readable name.
- `tributary_id: int | None` - FK `tributary.id`, nullable for shared resources.
- `attributes: dict` - JSONB, `nullable=False`, server default `{}`; carries
  `bucket`, `path_prefix`/`arn`, `category`, etc.
- `created_at`, `last_edited` - inherited.
- Indexes: `ix_resource_resource_identifier` (unique),
  `ix_resource_resource_type`, and a GIN index `ix_resource_attributes` using
  `jsonb_path_ops`.

The old single `access_type` column was dropped in migration `010c0bff0b83`; a
resource no longer carries one access value for everyone. Per-subject,
per-action access now lives in `ResourceGrant`; see
[[concepts/abac-authorization-design]].

## ResourceGrant (`resourcegrant`)

The explicit assignment mechanism for ABAC: one row per (subject, resource,
action). Effective access for a (user, action, resource) is the UNION of
role-based tributary defaults and the grants recorded here, evaluated
default-deny in policy (OPA/Rego). Inherits `CapeModel`, so it has `created_at`
/ `last_edited`.

- `id: int | None` - primary key.
- `user_id: int | None` - FK `user.id`, `ON DELETE CASCADE`, nullable,
  `index=True` (`ix_resourcegrant_user_id`). Grants to a specific user.
- `tributary_id: int | None` - FK `tributary.id`, `ON DELETE CASCADE`, nullable,
  `index=True` (`ix_resourcegrant_tributary_id`). Grants to every member of a
  tributary (avoids per-user row explosion).
- `resource_id: int` - FK `resource.id`, `ON DELETE CASCADE`, `nullable=False`,
  `index=True` (`ix_resourcegrant_resource_id`).
- `access_type: str` - one action per row (e.g. `"read"`, `"write"`); use two
  rows for read+write.
- `granted_by: int | None` - FK `user.id`, nullable (no cascade; set NULL before
  deleting a grantor).
- `expires_at: datetime | None` - nullable expiry.
- `created_at`, `last_edited` - inherited.

Constraints:

- CHECK `ck_resourcegrant_exactly_one_subject`:
  `(user_id IS NOT NULL) <> (tributary_id IS NOT NULL)` - exactly one of
  `user_id` / `tributary_id` is set.
- UNIQUE `uq_resourcegrant_subject_resource_access` on
  `(user_id, tributary_id, resource_id, access_type)` with `NULLS NOT DISTINCT`,
  so a tributary grant (with `user_id` NULL) still cannot be duplicated.

Subject/action model rationale is confirmed in
[[concepts/abac-authorization-design]] (grant is per-action; subject is user OR
tributary; MVP is allow-only with default-deny).

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
- A subject (user OR tributary) has zero or more `ResourceGrant` rows against a
  resource; deleting the user, tributary, or resource cascades the grants.
- `UserTributary.granted_by` and `ResourceGrant.granted_by` reference the user
  who granted the membership / grant (no cascade).

## Model vs applied DDL: reconciled

The applied migration `6919c61ea401` declared foreign-key `ON DELETE CASCADE`
behavior and a composite unique constraint that earlier revisions of `models.py`
did NOT express. As of the ABAC rework, `models.py` now reproduces all of them,
so `alembic revision --autogenerate` reports no spurious changes:

- `usertributary`: `user_id` and `tributary_id` FKs are `ON DELETE CASCADE`,
  declared via
  `sa_column=Column(Integer, ForeignKey(..., ondelete="CASCADE"), primary_key=True, index=True)`.
- `userattribute`: `user_id` FK is `ON DELETE CASCADE` (and `nullable=False`),
  with `UNIQUE (user_id, attribute_key)`
  (`uq_userattribute_user_id_attribute_key`) in `__table_args__`.
- `resource`: GIN index `ix_resource_attributes` (`jsonb_path_ops`) declared in
  `__table_args__`.

Migration `010c0bff0b83` was autogenerated against these reconciled models and
hand-reviewed; a follow-up autogenerate produced an empty migration, confirming
models and DDL agree. Any future model change must keep these cascades, the
unique constraint, and the GIN index so autogenerate does not try to drop them.

## Related pages

- [[concepts/capemodel-base-class]]
- [[concepts/alembic-migrations]]
- [[entities/test-fixtures]]
- [[concepts/abac-authorization-design]]
- [[entities/cape-cod-db]]
