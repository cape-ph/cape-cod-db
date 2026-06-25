# CLI Tools

## Overview

The package provides two command-line scripts, defined in `pyproject.toml` [tool.poetry.scripts].

## capedb - Primary Migration Tool

**Location:** `cape_cod_db/cli/capedb.py`

**Purpose:** Simplified Alembic wrapper for database migrations.

**Entry Point:** `main()` function registers custom commands with Alembic's CommandLine

**Commands:**
- `current(config, verbose=False)` - Display current DB version
- `upgrade(config, revision)` - Upgrade to specified revision
- `downgrade(config, revision)` - Downgrade to specified revision

**Usage:**
```bash
# Show current version
capedb current
capedb current --verbose

# Upgrade to latest
capedb upgrade head

# Downgrade to specific revision
capedb downgrade eecb735a6c3b
```

**Configuration:**
- Requires Alembic config (see 02-migrations.md for configuration options)
- Database URL via CLI arg, env var, or config file

**Implementation:** Uses `alembic.config.CommandLine` and registers custom command functions

## capedb-app - Direct Table Creation

**Location:** `cape_cod_db/cli/app.py`

**Purpose:** Create tables directly from SQLModel metadata WITHOUT migrations.

**WARNING:** This tool:
- Applies only the current schema (no migration history)
- Does NOT create alembic_version table
- Incompatible with migration-based workflows
- Only useful for fresh databases without migration requirements

**Usage:**
```bash
# Requires DB_URL environment variable
DB_URL=postgresql://user@localhost/dbname capedb-app
```

**Implementation:** Simply calls `database.create_tables()`

**When to Use:**
- Quick testing/prototyping with throwaway databases
- Projects that don't need migration history

**When NOT to Use:**
- Production environments
- Any database that needs migration tracking
- Projects using `capedb` for migrations (incompatible)

## Script Registration

Both scripts registered in `pyproject.toml`:
```toml
[tool.poetry.scripts]
capedb = "cape_cod_db.cli.capedb:main"
capedb-app = "cape_cod_db.cli.app:main"
```

Available after `poetry install` or when package is installed as dependency.
