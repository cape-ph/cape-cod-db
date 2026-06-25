# Development Workflow

## Setup

### Prerequisites

- Python 3.10+
- Poetry 2.3+
- PostgreSQL 18.x (for local development)
- mise en place or asdf (optional, for version management)

### Installation

```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Local PostgreSQL Setup

See README.md for detailed PostgreSQL 18.x setup including:
- User and group creation
- Database permissions
- Development-only security settings

## Code Quality Tools

### Linting: Ruff

**Check formatting:**
```bash
ruff check cape_cod_db/
```

**Auto-format:**
```bash
ruff format cape_cod_db/
```

**Configuration:** `pyproject.toml` [tool.ruff]
- Line length: 80

### Formatting: Black

**Configuration:** `pyproject.toml` [tool.black]
- Line length: 80
- **Excludes:** `cape_cod_db/migrations` (generated code)

### Import Sorting: isort

**Configuration:** `pyproject.toml` [tool.isort]
- Profile: black
- Line length: 80
- **Excludes:** `cape_cod_db/migrations`

### Type Checking: Pyright

```bash
pyright
```

**Configuration:** `pyrightconfig.json` at repo root

## Testing

**Status:** TBD - no test framework currently configured

**Before assuming test commands:**
- Check README.md
- Search codebase for test configuration
- Never assume pytest/unittest without verification

## Code Conventions

### Python Style

1. **Type Hints:** Always use Python 3.10+ syntax
   - Use `int | None` (not `Optional[int]`)
   - Type all function parameters and returns

2. **Line Length:** 80 characters (Black/Ruff enforced)

3. **Imports:**
   - Standard library first
   - Third-party second
   - Local imports last
   - Sorted by isort (black profile)

### Database Patterns

1. **Model Inheritance:** All tables inherit from `CapeModel`

2. **Migration Required:** Never bypass Alembic for schema changes

3. **Model Registration:** Import all models in `migrations/env.py`

4. **No PII/PHI Logging:** 
   - Never log sensitive user data
   - Sanitize `__repr__` methods (see User model TODO)

5. **Security:**
   - Never commit database URLs, passwords, or credentials
   - Use environment variables for sensitive config
   - Dev-only PostgreSQL setup documented in README

## Development Database Operations

### Using Python REPL

```python
from sqlmodel import select, Session
from cape_cod_db import database as db
from cape_cod_db import models

# Create record
with Session(db.engine) as session:
    usr = models.User(
        first_name="First",
        last_name="Last", 
        email="fl@fakeemail.test"
    )
    session.add(usr)
    session.commit()

# Query records
with Session(db.engine) as session:
    stmnt = select(models.User)
    res = session.exec(stmnt)
    for u in res.all():
        print(u)

# Update record
with Session(db.engine) as session:
    usr_stmnt = select(models.User).where(
        models.User.first_name == "First"
    )
    usr = session.exec(usr_stmnt).first()
    usr.first_name = "Updated"
    session.add(usr)
    session.commit()
```

### Using psql

```bash
psql cape_env_db

# Show tables
\d+

# Describe table
\d user

# Query
SELECT * FROM public.user;

# Check migration version
SELECT * FROM alembic_version;
```

## Git Workflow

- Commit migrations with corresponding model changes
- Never modify applied migrations (create new ones)
- Keep AGENTS.md and notes/ synchronized with code changes

## Pre-commit Hooks

**Configuration:** `.pre-commit-config.yaml`

Check configuration file for enabled hooks.

## Configuration Files

- `.editorconfig` - Editor settings
- `.prettierrc.yaml` - Prettier formatting (for non-Python files)
- `.typos.toml` - Typo checking configuration
- `.mise.toml` - mise en place tool versions
- `poetry.toml` - Poetry configuration
