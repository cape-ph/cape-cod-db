---
type: entity
title: Test fixtures
slug: test-fixtures
created: 2026-07-13
updated: 2026-07-13
tags: ["fixtures", "test-data", "sql", "psql", "postgres"]
---

# Test fixtures

Realistic development/test data lives in `fixtures/test/` as raw SQL, loaded
with `psql`. There is no automated test framework in the repo yet; these
fixtures are the current way to populate a dev database.

- `fixtures/test/test_data.sql` - loads the data inside a `BEGIN; ... COMMIT;`
  transaction, then prints verification queries.
- `fixtures/test/cleanup_test_data.sql` - removes the test data in FK-safe
  order, also transactional and idempotent.

```bash
source .env && psql "$DB_URL" -f fixtures/test/test_data.sql
source .env && psql "$DB_URL" -f fixtures/test/cleanup_test_data.sql
```

## What test_data.sql creates

- 6 users, all with `@example.com` emails (used as the cleanup match pattern):
  Alice (ENG admin), Bob (DS admin), Charlie (OPS member, `suspended`), Diana
  (multi-role: ENG member, PLAT-ENG admin, DS viewer), Admin (org admin via
  attributes, no membership), Quinn (`quarantine`, no membership).
- 4 tributaries: `ENG`, `DS`, `OPS`, and `PLAT-ENG` (child of `ENG`, showing the
  `parent_id` hierarchy). PLAT-ENG is inserted with a subquery to resolve the
  parent id.
- Resources: ENG gets the full four-bucket S3 pattern (raw/clean uploads,
  raw/clean results); PLAT-ENG, DS, and OPS get varied S3 resources; plus a
  shared S3 resource (`tributary_id NULL`), an EC2 instance, and an application
  resource - demonstrating `resource_type` values `s3`, `ec2`, `application` and
  `access_type` values `write`, `read`, `both`, `ssh`, `admin`.
- Memberships in `usertributary` with roles `member`, `admin`, `viewer`.
- `userattribute` rows: `user_status` (active/quarantine/suspended), `is_admin`,
  `system_role`, `clearance_level`, with `source` values `system`, `manual`,
  `ad`.

Timestamps are set explicitly with `NOW()` in the SQL because raw inserts do not
trigger the ORM timestamp defaults; see [[concepts/capemodel-base-class]].

## Fixture representation caveat

The S3 fixtures model buckets as a single `cape-datalake` bucket with per-team
path prefixes (e.g. `s3://cape-datalake/eng/raw-uploads/`). The real Pulumi
infra provisions a separate bucket per role, so production `resource_identifier`
values are whole-bucket paths. The fixtures are accurate for the current schema
and dev use; treat the single-bucket-with-prefix shape as a fixture convenience,
not a production contract. See [[concepts/abac-authorization-design]].

## Keeping fixtures in sync

Per the project completion checklist, any schema change must be reflected in
both `test_data.sql` and `cleanup_test_data.sql`, including the `\echo`
verification queries. Cleanup relies on `@example.com` emails and known
tributary codes plus FK cascades to remove dependent rows.

## Related pages

- [[entities/database-schema]]
- [[concepts/capemodel-base-class]]
- [[concepts/abac-authorization-design]]
- [[entities/cape-cod-db]]
