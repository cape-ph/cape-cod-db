# Project Overview

## Purpose

`cape-cod-db` is a Python library providing SQLModel definitions for the CAPE environment database. It serves as the canonical source of database schema definitions and migrations for the CAPE system.

## Technology Stack

- **Python**: 3.10+
- **ORM**: SQLModel (combines SQLAlchemy and Pydantic)
- **Database**: PostgreSQL 18.x (primary target)
- **Migrations**: Alembic
- **Build System**: Poetry
- **Formatting**: Black (line length 80)
- **Linting**: Ruff
- **Type Checking**: Pyright

## Package Structure

```
cape_cod_db/
├── __init__.py           # Empty module init
├── models.py             # All SQLModel table definitions
├── database.py           # Database engine and connection setup
├── alembic.ini           # Alembic configuration (can be overridden)
├── migrations/           # Alembic migration system
│   ├── env.py           # Alembic environment config
│   ├── script.py.mako   # Template for new migrations
│   └── versions/        # Individual migration files
└── cli/                  # Command-line tools
    ├── capedb.py        # Primary migration tool (wraps Alembic)
    └── app.py           # Direct table creation (non-migration)
```

## Key Characteristics

- **Library Package**: Installed as dependency in other CAPE projects
- **Single Models File**: All table definitions in `models.py` (may split if it becomes painful)
- **Base Class Pattern**: All tables inherit from `CapeModel`
- **Migration-First**: Alembic is the primary way to manage schema changes
- **Security Focus**: No PII/PHI in logs, no credentials in code

## Distribution

- Packaged via Poetry
- Version: 0.2.0
- Exports: `capedb` and `capedb-app` CLI scripts
