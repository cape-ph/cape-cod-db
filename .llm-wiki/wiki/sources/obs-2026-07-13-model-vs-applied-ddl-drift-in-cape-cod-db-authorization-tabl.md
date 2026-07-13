---
type: source
title: "Observation: Model vs applied-DDL drift in cape-cod-db authorization tables"
slug: obs-2026-07-13-model-vs-applied-ddl-drift-in-cape-cod-db-authorization-tabl
status: observation
created: 2026-07-13
updated: 2026-07-13
relevance: high
observed_at: 2026-07-13T19:38:00.596Z
tags: ["cape-cod-db", "schema", "alembic", "drift", "abac", "migrations"]
source_context: "Building the cape-cod-db project wiki from code as source of truth"
---
# ⭐ Observation: Model vs applied-DDL drift in cape-cod-db authorization tables
In cape-cod-db, migration 6919c61ea401 declares ON DELETE CASCADE on usertributary.user_id/tributary_id and userattribute.user_id, plus a UNIQUE(user_id, attribute_key) on userattribute (uq_userattribute_user_id_attribute_key). The current cape_cod_db/models.py does NOT express these cascades or that unique constraint. Consequence: `alembic revision --autogenerate` from the current models would try to DROP them. Before autogenerating any new migration (e.g. the planned ABAC ResourceGrant rework), restore these to models.py via sa_column/__table_args__ or hand-edit the generated migration. Also: CapeModel.created_at uses default=datetime.now(timezone.utc) (evaluated once at import) instead of default_factory, so ORM inserts share one import-time timestamp; last_edited is correct. Documented in .llm-wiki/wiki/entities/database-schema.md and concepts/capemodel-base-class.md.
*Relevance: high*

*Context: Building the cape-cod-db project wiki from code as source of truth*

*Tags: cape-cod-db schema alembic drift abac migrations*
---
*Observed: 2026-07-13T19:38:00.596Z*