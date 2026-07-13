# Agent Instructions for cape-cod-db

## Project Wiki

This project keeps durable knowledge in `.llm-wiki/` (an Obsidian-compatible LLM
wiki). Treat it as the source of truth for decisions, architecture, and hard-won
findings. The hub page is `.llm-wiki/wiki/entities/cape-cod-db.md`.

- At task start, read relevant pages under `.llm-wiki/wiki/`.
- At task end, record durable decisions and findings as pages under
  `.llm-wiki/wiki/`: one page per thing, kebab-case filenames, cross-link with
  `[[folder/page]]`, and cite sources.
- Never edit `.llm-wiki/raw/**` (immutable captures) or `.llm-wiki/meta/**`
  (generated index). `meta/` is gitignored and rebuilt locally.
- With the `@zosmaai/pi-llm-wiki` extension, prefer its tools (`wiki_recall`,
  `wiki_retro`, `wiki_ensure_page`); they maintain `meta/` automatically.
  Without it, edit the markdown directly and leave `meta/` alone.
- The code in this repository is the ultimate source of truth. When the wiki and
  the code disagree, fix the wiki. Keep wiki pages synchronized with code
  changes in the same session.

### Completion Checklist

Before marking work as complete, verify:

- [ ] Relevant `.llm-wiki/wiki/` pages have been read and reflect current code
- [ ] New functionality, decisions, or architecture changes are captured in the
      wiki
- [ ] Test fixtures (fixtures/test/test_data.sql and cleanup_test_data.sql) are
      synchronized with schema changes
- [ ] Linting and type checking pass:
      `poetry run ruff check cape_cod_db/ && poetry run pyright`

## Project-Specific Guidelines

### Development Commands

- **Linting**: `poetry run ruff check cape_cod_db/` (check linting) or
  `poetry run ruff format cape_cod_db/` (auto-format)
- **Type checking**: `poetry run pyright` (configured via pyrightconfig.json)
- **Code formatting**: `poetry run black cape_cod_db/` (Black) or
  `poetry run isort cape_cod_db/` (import sorting)
- **Testing**: TBD (check if test framework exists before assuming)
- **Database Connection**: Requires `DB_URL` environment variable (set in `.env`
  file)
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
- Never log PII/PHI (see User model **repr** TODO)
- Dev-only PostgreSQL setup is documented in README
