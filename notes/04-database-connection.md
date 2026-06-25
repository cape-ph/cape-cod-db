# Database Connection

## Overview

Database connection setup is handled in `cape_cod_db/database.py`.

## Connection Configuration

**Location:** `database.py:5-38`

### URL Resolution Logic

Attempts to find database URL in this order:

1. **Alembic Config (primary):**
   - Imports from `migrations.env` config object
   - Gets URL from `config.get_main_option("sqlalchemy.url")`
   - Used when running migration commands

2. **Environment Variable (fallback):**
   - If Alembic config not available (AttributeError)
   - Checks `DB_URL` environment variable
   - Used when using ORM directly (e.g., in API lambdas)

3. **Error on Failure:**
   - If no URL found, logs error and exits with code 1
   - Message: "DB_URL is not configured..."

### Engine Creation

**Location:** `database.py:38`

```python
engine = create_engine(db_url)
```

- Uses SQLModel's `create_engine()` wrapper around SQLAlchemy
- Engine instance exported for use in other modules
- Logging shows configured database URL (sanitize in production)

## Usage Patterns

### In Migration Context

```python
# database.py automatically gets URL from alembic config
from cape_cod_db import database as db

# Engine already configured
with Session(db.engine) as session:
    # ... ORM operations
```

### In Application Context

```bash
# Set environment variable
export DB_URL="postgresql://user:pass@localhost/cape_env_db"

# Or use .env file (not in repo)
DB_URL=postgresql://user:pass@localhost/cape_env_db
```

```python
# database.py falls back to DB_URL env var
from cape_cod_db import database as db
from sqlmodel import Session

with Session(db.engine) as session:
    # ... ORM operations
```

## Direct Table Creation

**Location:** `database.py:41-46`

```python
def create_tables():
    """Create tables on the DB pointed to by engine.
    
    Expects empty database to exist.
    """
    SQLModel.metadata.create_all(engine)
```

- Used by `capedb-app` CLI tool
- Bypasses migrations (creates current schema only)
- Does NOT create alembic_version table

## Security Considerations

- **Never log full DB URLs in production** (contains credentials)
- Current implementation logs URL at INFO level (line 36) - needs sanitization for production
- No credentials stored in code
- Use environment variables or secure config management

## PostgreSQL Setup

See README.md for development PostgreSQL setup with proper permissions.
