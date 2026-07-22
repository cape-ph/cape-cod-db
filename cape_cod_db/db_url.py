"""Side-effect-free helper for resolving the database URL.

Kept separate from ``migrations/env.py`` so the resolution logic can be
imported (and unit tested) without triggering Alembic's import-time
migration side effects.
"""


def resolve_db_url(cli_args, environ, ini_url):
    """Resolve the DB URL by precedence: CLI -x db_url, then DB_URL env,
    then the alembic ini sqlalchemy.url. Returns the URL string."""
    db_url = cli_args.get("db_url") or environ.get("DB_URL") or ini_url
    if db_url is None:
        raise SystemExit(
            "DB_URL is not configured (CLI -x db_url, env DB_URL, or ini sqlalchemy.url)"
        )
    return db_url
