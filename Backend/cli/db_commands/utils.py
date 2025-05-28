"""
Utility functions for database management commands.
"""

import importlib
import inspect
from pathlib import Path

import typer
from alembic.config import Config
from alembic.script import ScriptDirectory
from loguru import logger
from sqlmodel import SQLModel

from cli.common import console


def get_all_models() -> list[type[SQLModel]]:
    """
    Dynamically get all model classes from app.models.__all__ list.

    This makes it easier to maintain as new models are added to the application.
    """
    try:
        # Import the models module
        models_module = importlib.import_module("app.models")

        # Get the __all__ list which defines exported models
        all_models = getattr(models_module, "__all__", [])

        # Collect actual model classes
        model_classes = []
        for model_name in all_models:
            model_class = getattr(models_module, model_name, None)
            if (
                model_class
                and inspect.isclass(model_class)
                and issubclass(model_class, SQLModel)
            ):
                model_classes.append(model_class)

        return model_classes
    except Exception as e:
        # If anything fails, log it and return an empty list
        logger.warning(f"Failed to dynamically load models: {str(e)}")
        return []


def get_branch_heads(alembic_cfg: Config, branch_name: str | None = None) -> list[str]:
    """Get revision heads for a specific branch or all branches."""
    script = ScriptDirectory.from_config(alembic_cfg)

    if branch_name:
        heads = script.get_revisions("heads")
        branch_heads = []

        for head in heads:
            if branch_name in head.branch_labels:
                branch_heads.append(head.revision)

        return branch_heads
    else:
        return [head.revision for head in script.get_revisions("heads")]


def get_alembic_config() -> Config:
    """Get Alembic configuration."""
    current_dir = Path(__file__).parent.parent.parent
    alembic_ini_path = current_dir / "alembic.ini"
    if not alembic_ini_path.exists():
        console.print(
            "[bold red]Alembic configuration file (alembic.ini) not found![/]"
        )
        raise typer.Exit(1)

    alembic_cfg = Config(str(alembic_ini_path))

    ensure_alembic_directories()

    return alembic_cfg


def ensure_alembic_directories() -> None:
    """Ensure all required alembic directories exist."""
    alembic_dir = Path(__file__).parent.parent.parent / "app" / "migrations"
    if not alembic_dir.exists() or not alembic_dir.is_dir():
        console.print("[bold red]Alembic directory not found![/]")
        raise typer.Exit(1)

    if not (alembic_dir / "env.py").exists():
        console.print("[bold red]Alembic environment file (env.py) not found![/]")
        raise typer.Exit(1)

    keystone_dir = alembic_dir / "keystone"
    if not keystone_dir.exists():
        console.print("[yellow]Creating keystone versions directory...[/]")
        keystone_dir.mkdir(exist_ok=True)

    project_dir = alembic_dir / "project"
    if not project_dir.exists():
        console.print("[yellow]Creating project versions directory...[/]")
        project_dir.mkdir(exist_ok=True)


# Autocompletion functions
def get_available_branches() -> list[str]:
    """Get available migration branches for autocompletion."""
    try:
        alembic_cfg = get_alembic_config()
        script = ScriptDirectory.from_config(alembic_cfg)
        branches = set()

        # Get all branch labels from all heads
        for head in script.get_revisions("heads"):
            if head.branch_labels:
                branches.update(head.branch_labels)

        # Ensure we always include keystone and project branches
        branches.add("keystone")
        branches.add("project")

        return sorted(branches)
    except Exception:
        # Return default branches if anything fails
        return ["keystone", "project"]


def complete_branch_names(incomplete: str) -> list[str]:
    """Complete branch names for CLI autocompletion."""
    branches = get_available_branches()
    return [branch for branch in branches if branch.startswith(incomplete)]


def complete_revision_names(incomplete: str) -> list[str]:
    """Complete revision identifiers and special values for CLI autocompletion."""
    # Special revision identifiers
    special_revisions = ["head", "heads", "base", "-1", "+1"]

    # Try to get actual revision IDs if possible
    try:
        alembic_cfg = get_alembic_config()
        script = ScriptDirectory.from_config(alembic_cfg)
        revisions = []

        # Get all revisions
        for rev in script.walk_revisions():
            revisions.append(rev.revision)

        # Combine special and actual revisions
        all_revisions = special_revisions + revisions

        # Return matches
        return [rev for rev in all_revisions if rev.startswith(incomplete)]
    except Exception:
        # If we can't get revisions, just return special values
        return [rev for rev in special_revisions if rev.startswith(incomplete)]
