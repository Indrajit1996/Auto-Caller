from collections.abc import Iterable
from logging.config import fileConfig

from alembic import context
from alembic.environment import MigrationContext
from alembic.operations import MigrationScript
from sqlalchemy import engine_from_config, pool

from app.core.config import config as app_config
from app.models import SQLModel

# Alembic Config
config = context.config
fileConfig(config.config_file_name)

# Metadata for 'autogenerate' support
target_metadata = SQLModel.metadata


def get_url():
    return str(app_config.SQLALCHEMY_DATABASE_URI)


def get_branch():
    """Determine current branch name."""
    # Priority: CLI attribute > -x args > cmd_opts
    if "branch" in config.attributes:
        return config.attributes["branch"]

    x_args = context.get_x_argument(as_dictionary=True)
    if "branch" in x_args:
        return x_args["branch"]

    if hasattr(config, "cmd_opts") and hasattr(config.cmd_opts, "branch"):
        return config.cmd_opts.branch

    return None


def get_version_path(branch_name):
    """Get version_path from version_locations config."""
    version_locations = config.get_main_option("version_locations")
    if not version_locations:
        return None

    location_map = {
        path.strip().split("/")[-1]: path.strip() for path in version_locations.split()
    }
    return location_map.get(branch_name)


def run_migrations_offline():
    url = get_url()
    branch = get_branch()
    version_path = get_version_path(branch)

    context_kwargs = {
        "url": url,
        "target_metadata": target_metadata,
        "literal_binds": True,
        "compare_type": True,
    }

    if version_path:
        context_kwargs["version_path"] = version_path

    context.configure(**context_kwargs)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    def process_revision_directives(
        context: MigrationContext,
        revision: str | Iterable[str | None] | Iterable[str],
        directives: list[MigrationScript],
    ) -> None:
        if getattr(config.cmd_opts, "autogenerate", False):
            script = directives[0]
            if script.upgrade_ops and script.upgrade_ops.is_empty():
                directives[:] = []

    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    branch = get_branch()
    version_path = get_version_path(branch)

    context_kwargs = {
        "connection": connectable.connect(),
        "target_metadata": target_metadata,
        "process_revision_directives": process_revision_directives,
        "compare_type": True,
    }

    if version_path:
        context_kwargs["version_path"] = version_path

    with context_kwargs["connection"] as connection:
        context_kwargs["connection"] = connection
        context.configure(**context_kwargs)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
