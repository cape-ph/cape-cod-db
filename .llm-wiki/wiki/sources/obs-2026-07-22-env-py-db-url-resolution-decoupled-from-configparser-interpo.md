---
type: source
title: "Observation: env.py DB URL resolution decoupled from ConfigParser interpolation"
slug: obs-2026-07-22-env-py-db-url-resolution-decoupled-from-configparser-interpo
status: observation
created: 2026-07-22
updated: 2026-07-22
relevance: high
observed_at: 2026-07-22T17:24:16.863Z
tags: ["alembic", "database", "migrations", "bugfix", "url-encoding"]
source_context: "Fixing GitHub issue #18 (env.py ConfigParser interpolation on % in DB URLs)"
---
# ⭐ Observation: env.py DB URL resolution decoupled from ConfigParser interpolation
Fixed issue #18 in cape-cod-db. cape_cod_db/migrations/env.py used to store the DB URL via config.set_main_option and re-read it through Alembic's ConfigParser (BasicInterpolation), so any '%' in a percent-encoded password raised configparser.InterpolationSyntaxError. Fix: added a pure resolve_db_url(cli_args, environ, ini_url) helper (precedence: CLI -x db_url -> DB_URL env -> ini sqlalchemy.url, SystemExit if None), removed set_main_option, and now pass the resolved db_url straight to context.configure(url=db_url) offline and create_engine(db_url, poolclass=pool.NullPool) online (imported create_engine from sqlmodel, dropped engine_from_config). cape_cod_db/database.py now does `from .migrations.env import db_url` instead of config.get_main_option; its existing `except AttributeError` DB_URL fallback still works because importing env.py outside Alembic raises AttributeError at `config = context.config`. Confirmed BasicInterpolation only treats '%' as special -- '$' passes through fine, so it was never part of this bug. Added tests/test_db_url.py (pytest) covering % @ : / space # ? plus a combined password, asserting make_url(url).password == raw. Verified: ruff clean, pyright 0 errors, pytest passes.
*Relevance: high*

*Context: Fixing GitHub issue #18 (env.py ConfigParser interpolation on % in DB URLs)*

*Tags: alembic database migrations bugfix url-encoding*
---
*Observed: 2026-07-22T17:24:16.863Z*