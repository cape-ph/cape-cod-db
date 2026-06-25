# Alembic Migrations

## Overview

Database schema changes are managed via Alembic. This is the **mandatory** approach for schema changes in production environments.

## Migration System Components

### env.py Configuration

**Location:** `cape_cod_db/migrations/env.py`

**Key Features:**
- Custom naming conventions for constraints (ix_, uq_, ck_, fk_, pk_)
- Type change detection enabled (`compare_type=True`)
- Batch mode for SQLite compatibility (`render_as_batch=True`)
- Target metadata from `SQLModel.metadata`

**Model Registration:** New models MUST be imported in `env.py:10` for autogenerate to work:
```python
from cape_cod_db.models import User  # Add new models here
```

### Existing Migrations

**Location:** `cape_cod_db/migrations/versions/`

1. `eecb735a6c3b_create_user_table.py` - Initial User table creation
2. `6001985fea71_add_email_to_user_table.py` - Added email field to User

## capedb CLI Tool

**Location:** `cape_cod_db/cli/capedb.py`

**Purpose:** Wrapper around Alembic providing simplified migration commands.

**Available Commands:**
- `capedb upgrade <revision>` - Upgrade to specified revision (use `head` for latest)
- `capedb downgrade <revision>` - Downgrade to specified revision
- `capedb current [--verbose]` - Show current database version

**Configuration Options (in priority order):**
1. Command-line: `capedb -c <config_path>` or via `ALEMBIC_CONFIG` env var
2. Auto-discovery: Looks for `alembic.ini` in current directory
3. Database URL: `capedb -x db_url=<url>` or `DB_URL` env var or `alembic.ini`

**Script Entry Point:** Defined in `pyproject.toml` [tool.poetry.scripts]

## Database URL Configuration

Three ways to specify DB URL (higher precedence first):
1. CLI argument: `capedb -x db_url=postgresql://...`
2. Environment variable: `DB_URL=postgresql://...`
3. alembic.ini: `sqlalchemy.url = postgresql://...`

## Migration Workflow

### Creating New Migrations

1. **Modify models:** Edit `models.py` with schema changes
2. **Import new models:** Add imports to `migrations/env.py` if new tables
3. **Generate migration:** 
   ```bash
   alembic revision --autogenerate -m "descriptive message"
   ```
4. **Review migration:** Check generated file in `versions/` directory
5. **Test upgrade:** `capedb upgrade head` on test database
6. **Test downgrade:** `capedb downgrade <previous_revision>` to verify rollback
7. **Commit:** Migration file + model changes together

### Applying Migrations

```bash
# Upgrade to latest
capedb upgrade head

# Check current version
capedb current --verbose

# Downgrade one revision
capedb downgrade -1
```

## Important Notes

- **Empty DB Required:** Migrations expect empty database to exist before first run
- **Never Bypass:** Always use migrations; never modify schema directly in production
- **Black Excluded:** Migrations directory excluded from Black formatting
- **Migration Files:** Never modify applied migrations; create new ones for changes
