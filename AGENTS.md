# Agent Instructions for cape-cod-db

## MANDATORY: Project Context Protocol

**Context is NOT optional. All work on this project MUST include context maintenance.**

### Loading Protocol (REQUIRED)

At the start of EVERY session, you MUST:
1. Read ALL files in `notes/*.md` to load current project context
2. Verify you understand the project structure, architecture, and current state
3. If notes/ doesn't exist or is incomplete, update it before proceeding with work

### Maintenance Protocol (CRITICAL)

When making ANY changes to code:
- Update relevant context notes IN THE SAME SESSION as code changes
- Add new notes files if new subsystems/concepts are introduced
- Keep notes synchronized with code - outdated context is worse than no context

### Completion Checklist

Before marking work as complete, verify:
- [ ] All relevant notes/*.md files have been read
- [ ] Context notes reflect current code state
- [ ] New functionality is documented in appropriate notes
- [ ] Changes to architecture/patterns are reflected in notes
- [ ] Test fixtures (fixtures/test/test_data.sql and cleanup_test_data.sql) are synchronized with schema changes
- [ ] Linting and type checking pass: `poetry run ruff check cape_cod_db/ && poetry run pyright`

**Work is incomplete without synchronized context. No exceptions.**

## Project-Specific Guidelines

### Development Commands

- **Linting**: `poetry run ruff check cape_cod_db/` (check linting) or `poetry run ruff format cape_cod_db/` (auto-format)
- **Type checking**: `poetry run pyright` (configured via pyrightconfig.json)
- **Code formatting**: `poetry run black cape_cod_db/` (Black) or `poetry run isort cape_cod_db/` (import sorting)
- **Testing**: TBD (check if test framework exists before assuming)
- **Database Connection**: Requires `DB_URL` environment variable (set in `.env` file)
- **Test Data**: Load/cleanup test fixtures:
  ```bash
  source .env && psql "$DB_URL" -f fixtures/test/test_data.sql
  source .env && psql "$DB_URL" -f fixtures/test/cleanup_test_data.sql
  ```
- **Migration Commands**:
  ```bash
  # Load DB_URL from .env and run capedb commands
  source .env && capedb -c cape_cod_db/alembic.ini -x db_url="$DB_URL" current --verbose
  source .env && capedb -c cape_cod_db/alembic.ini -x db_url="$DB_URL" upgrade head
  source .env && capedb -c cape_cod_db/alembic.ini -x db_url="$DB_URL" downgrade -1
  
  # Or use alembic directly
  alembic -c cape_cod_db/alembic.ini revision --autogenerate -m "description"
  ```

### Code Conventions

- Python 3.10+ with SQLModel ORM
- Black formatting (line length 80) - migrations excluded
- Use existing patterns from models.py for new models
- All tables inherit from CapeModel base class
- Database migrations via Alembic (never bypass migrations)
- CLI scripts defined in pyproject.toml [tool.poetry.scripts]

### Security

- Never commit database URLs, passwords, or credentials
- Never log PII/PHI (see User model __repr__ TODO)
- Dev-only PostgreSQL setup is documented in README
