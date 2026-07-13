---
type: source
title: "Observation: ABAC ResourceGrant rework implemented in cape-cod-db"
slug: obs-2026-07-13-abac-resourcegrant-rework-implemented-in-cape-cod-db
status: observation
created: 2026-07-13
updated: 2026-07-13
relevance: high
observed_at: 2026-07-13T20:02:57.070Z
tags: ["cape-cod-db", "abac", "schema", "migration", "resourcegrant"]
source_context: "cape-cod-db ABAC ResourceGrant schema rework"
---
# ⭐ Observation: ABAC ResourceGrant rework implemented in cape-cod-db
cape-cod-db ABAC rework is implemented (migration 010c0bff0b83 "abac per-subject resource grants", revises 6919c61ea401). Dropped Resource.access_type; Resource is now a pure catalog. Added ResourceGrant (CapeModel) in cape_cod_db/models.py: subject is exactly one of user_id/tributary_id enforced by CHECK ck_resourcegrant_exactly_one_subject; resource_id/user_id/tributary_id FKs all ON DELETE CASCADE; one action per row via access_type; granted_by (no cascade) and expires_at; UNIQUE uq_resourcegrant_subject_resource_access on (user_id, tributary_id, resource_id, access_type) with postgresql_nulls_not_distinct=True. models.py now also reproduces the previously-drifted constraints (usertributary cascades, userattribute cascade + unique, resource GIN index ix_resource_attributes jsonb_path_ops), so autogenerate produces an empty diff. Registered ResourceGrant in migrations/env.py with a noqa:F401 because the pi-lens ruff auto-fixer strips the model imports otherwise. Validated on throwaway DBs (cape_env_db_migtest, cape_env_db_fixtest): upgrade/downgrade both work, CHECK and NULLS-NOT-DISTINCT constraints enforce correctly, resource-delete cascades grants, fixtures load (4 grants) and cleanup zeroes out. ruff + pyright pass.
*Relevance: high*

*Context: cape-cod-db ABAC ResourceGrant schema rework*

*Tags: cape-cod-db abac schema migration resourcegrant*
---
*Observed: 2026-07-13T20:02:57.070Z*