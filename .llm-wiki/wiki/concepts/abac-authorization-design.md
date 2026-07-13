---
type: concept
title: ABAC authorization design
slug: abac-authorization-design
created: 2026-07-13
updated: 2026-07-13
tags: ["abac", "authorization", "opa", "rego", "design", "roadmap"]
---

# ABAC authorization design

CAPE authorizes access with ABAC (Attribute-Based Access Control), using OPA
(Open Policy Agent) as the decision engine. This database is the source of truth
for the authorization facts OPA evaluates. This page separates what the code
does today from the confirmed design decisions and the planned rework.

## The three-repo loop

- `cape-cod` (Pulumi infra): provisions the RDS instance and S3 buckets and
  emits a JSON export of deployed resources.
- `cape-cod-db` (this repo): owns the schema and migrations for the
  authorization data. See [[entities/database-schema]].
- `cape-cod-env` (Ansible): runs migrations against RDS and (planned) ingests
  the Pulumi export, reconciling it into this schema. That sync/reconcile logic
  is out of scope for this repo.

The near-term demo use case: a user asks "which S3 locations can I write to /
read from?", and upload/download requests are gated by an OPA decision. Internal
users first; SAML-federated external users later.

## Current state (as coded)

- Authorization facts are the tables in [[entities/database-schema]]:
  membership/role in `UserTributary`, resource catalog in `Resource`, and
  per-user flags in `UserAttribute`.
- `Resource` carries a single `access_type` and `resource_identifier` is
  globally unique. That means a resource has ONE access value for everyone;
  there is no per-(user, resource, action) grant in the schema today.
- There is no OPA integration code, no bundle generator, and no sync script in
  this repo.

## Confirmed design decisions (still in force)

- ABAC + OPA, not RBAC or pure tributary-based access. Tributary membership is
  modeled as a user attribute.
- Generic `Resource` table with JSONB `attributes`, not per-platform tables (no
  separate S3Resource/EC2Instance). Platform-agnostic, extend by inserting rows.
- Resource records are the single source of resource access; tributaries do NOT
  carry `s3_read_paths` / `s3_write_paths` arrays.
- Every tributary conceptually gets four standard S3 buckets (raw uploads, clean
  uploads, raw results, clean results), represented as `Resource` rows.
- Data sync to OPA uses the bundle pull model (Postgres -> JSON -> OPA bundle;
  OPA polls and hot-reloads). Local file for demo, S3 for production.
- `attributes.category` (`raw_uploads`, `clean_uploads`, `raw_results`,
  `clean_results`, ...) is the stable descriptor from the Pulumi export; policy
  maps category to a default action (raw -> write, clean -> read).
- Canonical `resource_type` for S3 is `"s3"` (matches fixtures), not
  `"s3_bucket"`.

## The problem the rework solves

Authorization is fundamentally per-(user, resource, action), but a single
`access_type` on a globally-unique `Resource` row cannot express "Alice can
write bucket X while Bob can only read it." Access must move off the `Resource`
row and become a relationship between a subject (user or tributary) and a
resource, per action. `Resource` becomes a pure catalog; WHO can do WHAT lives
in memberships (broad role-based defaults) plus an explicit grant table.

## Planned rework (not yet in code)

Direction under consideration (names/constraints to be confirmed before
implementing):

- Keep `User`, `Tributary`, `UserTributary`, `UserAttribute` as-is.
- Adjust `Resource` into a pure catalog: either drop `access_type` and derive
  the default from `attributes.category` in policy, or repurpose it as a
  nullable `default_access`.
- Add a grant table (working name `ResourceGrant`) with a subject that is
  exactly one of `user_id` / `tributary_id` (CHECK constraint), a `resource_id`
  (FK `ON DELETE CASCADE`), an `access_type` (one action per row), plus
  `granted_by` and `expires_at`; UNIQUE on
  `(user_id, tributary_id, resource_id, access_type)`.
- Effective access (evaluated in Rego, not stored) is default-deny, allow if
  guards pass and any grant path matches: explicit user grant, explicit
  tributary grant, or role-based default from membership + `category`.
  User-status guards (`quarantine`/`suspended`/`deactivated`) block; a global
  `is_admin` may short-circuit to allow. Deny-grants are out of scope for MVP.

Open decisions to confirm at implementation time include grant action
cardinality (one row per action vs a combined value), whether to support both
user- and tributary-level grants initially, whether to drop or keep
`Resource.access_type`, the grant table name, the role-to-action and
category-to-action mappings, and the canonical `resource_type` string.

## Rework checklist (when it happens)

1. Edit `models.py`; register any new model in `migrations/env.py`.
2. Autogenerate a migration and hand-review it (verify the CHECK, composite
   UNIQUE, CASCADE, and any `access_type` drop/rename; autogenerate will not
   infer a rename). Also preserve the existing cascades/unique constraint that
   the models currently under-declare - see the drift note in
   [[entities/database-schema]].
3. Provide a working `downgrade()`.
4. Update `fixtures/test/test_data.sql` and `cleanup_test_data.sql` to express
   grants instead of a per-resource `access_type`; keep verification queries in
   sync. See [[entities/test-fixtures]].
5. Run `ruff` and `pyright`; update `CHANGELOG.md`; a schema change is a minor
   version bump that `cape-cod-env` must pin. See [[concepts/release-and-ci]].

## Related pages

- [[entities/database-schema]]
- [[entities/test-fixtures]]
- [[concepts/alembic-migrations]]
- [[concepts/release-and-ci]]
- [[entities/cape-cod-db]]
