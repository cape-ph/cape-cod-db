---
type: source
title: "Observation: DB password masked in env.py/database.py logs via render_as_string(hide_password=True)"
slug: obs-2026-07-22-db-password-masked-in-env-py-database-py-logs-via-render-as-
status: observation
created: 2026-07-22
updated: 2026-07-22
relevance: high
observed_at: 2026-07-22T17:34:35.200Z
tags: ["security", "logging", "database", "url-masking", "alembic"]
source_context: "Follow-up to issue #18 fix: masking DB password in env.py/database.py logs"
---
# ⭐ Observation: DB password masked in env.py/database.py logs via render_as_string(hide_password=True)
Fixed a cleartext password leak in cape-cod-db logging. cape_cod_db/migrations/env.py and cape_cod_db/database.py both logged the DB URL with f"Configured for database: {db_url}" where db_url is a plain string, exposing the (percent-encoded) password in logs -- a violation of the AGENTS.md "never log credentials" rule. Fix: log make_url(db_url).render_as_string(hide_password=True), which renders the password as ***, while the raw db_url string is still used unchanged for create_engine. Added `from sqlalchemy.engine import make_url` to both files. Note: SQLAlchemy's URL object masks the password on str()/repr() by default; the leak existed only because the code logged the raw string, not a URL object. Verified at runtime: log shows postgresql://user:***@host/db and the engine still receives the raw URL. Pre-existing issue, surfaced while cleaning up the issue #18 fix.
*Relevance: high*

*Context: Follow-up to issue #18 fix: masking DB password in env.py/database.py logs*

*Tags: security logging database url-masking alembic*
---
*Observed: 2026-07-22T17:34:35.200Z*