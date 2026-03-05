from alembic import command
from alembic.config import CommandLine, Config


def current(config: Config, verbose=False) -> None:
    """Displays the current version of the database with optional verbosity.

    Args:
        verbose: True for verbose output, else False. Defaults to `False`.
    """
    command.current(config, verbose)


def upgrade(config: Config, revision: str) -> None:
    """Upgrades the DB to the specified revision.

    Args:
        config: a Config instance.
        revision: the revision to upgrade to.
    """

    command.upgrade(config, revision)


def downgrade(config: Config, revision: str) -> None:
    """Downgrades the DB to the specified revision.

    Args:
        config: a Config instance.
        revision: the revision to downgrade to.
    """

    command.downgrade(config, revision)


def main():
    cli = CommandLine()
    cli.register_command(current)
    cli.register_command(upgrade)
    cli.register_command(downgrade)
    cli.main()


if __name__ == "__main__":
    main()
