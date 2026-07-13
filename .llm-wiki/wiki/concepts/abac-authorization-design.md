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
  membership/role in `UserTributary`, resource catalog in `Resource`, per-user
  flags in `UserAttribute`, and explicit grants in `ResourceGrant`.
- `Resource` is now a pure catalog: the old `access_type` column was dropped
  (migration `010c0bff0b83`). WHO can do WHAT lives in `ResourceGrant` (one row
  per subject/resource/action) plus role-based tributary defaults.
- There is still no OPA integration code, bundle generator, or sync script in
  this repo; those live in `cape-cod` / `cape-cod-env`.

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

## Implemented rework

Delivered in migration `010c0bff0b83` ("abac per-subject resource grants") with
the confirmed decisions below:

- `User`, `Tributary`, `UserTributary`, `UserAttribute` kept as-is.
- `Resource.access_type` dropped; `Resource` is a pure catalog and the default
  action is derived from `attributes.category` in policy (D3).
- Added `ResourceGrant`:
  - Subject is exactly one of `user_id` / `tributary_id`, enforced by CHECK
      `ck_resourcegrant_exactly_one_subject` (D2). Both user- and
      tributary-level grants are supported.
  - `resource_id` FK `ON DELETE CASCADE`; `user_id` / `tributary_id` FKs also
      `ON DELETE CASCADE`.
  - One action per row via `access_type` (D1); plus `granted_by` and
      `expires_at`.
  - UNIQUE `uq_resourcegrant_subject_resource_access` on
      `(user_id, tributary_id, resource_id, access_type)` with
      `NULLS NOT DISTINCT` so tributary grants (user_id NULL) cannot duplicate.
  - Table name is `ResourceGrant` (D4).

Role/category mapping accepted as-is (D5): `raw_uploads` / `raw_results` ->
write, `clean_uploads` / `clean_results` -> read; on owned resources admin ->
read+write, member -> write raw / read clean, viewer -> read only. Canonical
`resource_type` for S3 is `"s3"` (D6). MVP is allow-only with default-deny;
deny-grants are out of scope (D7).

Effective access (evaluated in Rego, not stored) is default-deny, allow if
guards pass and any grant path matches: explicit user grant, explicit tributary
grant, or role-based default from membership + `category`. User-status guards
(`quarantine`/`suspended`/`deactivated`) block; a global `is_admin` may
short-circuit to allow. Policy, bundle generation, and sync remain in the other
repos.

## Related pages

- [[entities/database-schema]]
- [[entities/test-fixtures]]
- [[concepts/alembic-migrations]]
- [[concepts/release-and-ci]]
- [[entities/cape-cod-db]]
