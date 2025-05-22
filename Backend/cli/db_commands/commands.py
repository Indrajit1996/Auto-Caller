"""
Core database commands for checking status, reset, and connection verification.
"""

from io import StringIO
from typing import Annotated

import typer
from alembic import command as alembic_command
from alembic.script import ScriptDirectory
from rich.panel import Panel
from rich.table import Table
from sqlmodel import func, select, text

from app.core.config import config
from app.core.db import SessionLocal
from app.models import (
    Group,
    Invitation,
    InvitationRegistration,
    Notification,
    PasswordReset,
    Transaction,
    User,
    UserGroup,
    UserSettings,
)
from cli.common import console

from .utils import get_alembic_config, get_all_models


def reset_db(
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Skip confirmation prompt")
    ] = False,
) -> None:
    """
    Reset database: drop all tables and recreate schema via migrations.
    WARNING: This will delete all data!
    """
    if not force:
        typer.confirm(
            "Warning: This will delete all data! Are you sure you want to proceed?",
            abort=True,
        )
        console.print("[bold green]Proceeding with database reset...[/]", end="\n\n")

    _reset_db()


def _reset_db() -> None:
    """Internal implementation of database reset."""
    try:
        # Get alembic configuration
        alembic_cfg = get_alembic_config()

        console.print(
            Panel(
                "[bold]Database Reset Operation[/]",
                subtitle="[italic]This will delete all data and recreate the schema[/]",
                border_style="yellow",
                expand=False,
            )
        )

        # Step 1: Drop schema
        with console.status(
            "[bold yellow]Dropping public schema...[/]", spinner="dots"
        ):
            with SessionLocal() as session:
                session.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
                session.execute(text("CREATE SCHEMA public"))
                session.commit()

        console.print(
            f"[bold green]✓[/] Database {config.POSTGRES_DB} dropped and recreated"
        )

        # Step 2: Run migrations
        console.print("\n[bold]Running migrations:[/]")

        try:
            with console.status("[bold blue]Applying migrations...[/]", spinner="dots"):
                # Use "heads" instead of "head" to ensure all branches are upgraded
                alembic_command.upgrade(alembic_cfg, "heads")

            # Get and display the current branches that were migrated
            output = StringIO()
            alembic_cfg.stdout = output
            alembic_command.current(alembic_cfg, verbose=True)
            result = output.getvalue()

            # Show which revisions were applied in a pretty format
            if result.strip():
                console.print("[bold green]✓[/] Migrations applied successfully")

                # Create a panel with the migration details
                migrations = []
                for line in result.splitlines():
                    if "Rev:" in line:
                        rev = line.split("Rev:", 1)[1].strip()
                        migrations.append(f"• [cyan]{rev}[/]")
                    elif "->" in line:
                        migrations.append(f"  [dim]{line.strip()}[/]")

                if migrations:
                    console.line()
                    console.print(
                        Panel(
                            "\n".join(migrations),
                            title="[bold]Applied Migrations[/]",
                            border_style="green",
                            expand=False,
                        )
                    )
        except Exception as e:
            console.print("[bold red]✗[/] Migration failed:", str(e))
            raise

        # Final success message
        console.print(
            Panel(
                "[bold green]Database reset completed successfully![/]",
                border_style="green",
                expand=False,
            )
        )

    except Exception as e:
        console.print(
            Panel(
                f"[bold red]Failed to reset database:[/] {str(e)}",
                title="[bold red]Error[/]",
                border_style="red",
            )
        )
        raise typer.Exit(1)


def db_status() -> None:
    """Get database status and table counts."""
    try:
        console.print(
            "[bold]Database Status Check:[/]",
        )

        with console.status("[bold blue]Testing connection...[/]", spinner="dots"):
            with SessionLocal() as session:
                # Test connection
                result = session.exec(select(User).limit(1))
                result.first()  # Just to check if connection works

        console.print("[bold green]✓[/] Database connection successful!")

        # Display database URI (masked)
        db_uri = str(config.SQLALCHEMY_DATABASE_URI)
        if "://" in db_uri and "@" in db_uri:
            # Mask password in URI for security
            uri_parts = db_uri.split("://", 1)
            auth_parts = uri_parts[1].split("@", 1)
            if ":" in auth_parts[0]:
                user_parts = auth_parts[0].split(":", 1)
                masked_uri = (
                    f"{uri_parts[0]}://{user_parts[0]}:********@{auth_parts[1]}"
                )
                db_uri = masked_uri

        console.print(
            Panel(
                f"[bold]Database URI:[/] {db_uri}",
                border_style="cyan",
                expand=False,
            )
        )

        # Get table counts
        with console.status(
            "[bold blue]Gathering table statistics...[/]", spinner="dots"
        ):
            table = Table("Table", "Row Count", title="Table Statistics")
            table.title_style = "bold cyan"

            # Try to get models dynamically first
            models_to_check = get_all_models()

            # If dynamic loading failed, fall back to hardcoded list
            if not models_to_check:
                console.print(
                    "[yellow]Using hardcoded model list (dynamic loading failed)[/]"
                )
                models_to_check = [
                    User,
                    Group,
                    Invitation,
                    InvitationRegistration,
                    Notification,
                    PasswordReset,
                    Transaction,
                    UserGroup,
                    UserSettings,
                ]

            with SessionLocal() as session:
                for model in models_to_check:
                    try:
                        count = session.scalar(select(func.count()).select_from(model))
                        table.add_row(model.__name__, str(count))
                    except Exception as e:
                        table.add_row(model.__name__, f"Error: {str(e)}")

        console.print()
        console.print(table)

        # Get current migration information
        console.print()
        console.print("[bold]Current Migration Status:[/]")

        with console.status(
            "[bold blue]Retrieving migration information...[/]", spinner="dots"
        ):
            # Get Alembic information
            alembic_cfg = get_alembic_config()
            console.print(
                f"[bold]Using Alembic config:[/] {alembic_cfg.config_file_name}"
            )
            output = StringIO()
            alembic_cfg.stdout = output
            alembic_command.current(alembic_cfg, verbose=True)
            result = output.getvalue()

            console.print(
                f"[bold]Using Alembic config:[/] {alembic_cfg.config_file_name}"
            )
            script = ScriptDirectory.from_config(alembic_cfg)
            heads = script.get_revisions("heads")

        if result.strip():
            # Parse migration information by branch
            branch_info = {
                "keystone": {"head": None, "has_data": False},
                "project": {"head": None, "has_data": False},
            }

            # Extract heads for each branch
            for head in heads:
                if head.branch_labels and "keystone" in head.branch_labels:
                    branch_info["keystone"]["head"] = head.revision
                    branch_info["keystone"]["has_data"] = True
                elif head.branch_labels and "project" in head.branch_labels:
                    branch_info["project"]["head"] = head.revision
                    branch_info["project"]["has_data"] = True

            # Create a table for migration status
            migration_table = Table("Branch", "Current Revision", "Status")
            migration_table.title_style = "bold cyan"

            # Add keystone branch status
            if branch_info["keystone"]["has_data"]:
                migration_table.add_row(
                    "[blue]Keystone[/]",
                    f"[cyan]{branch_info['keystone']['head']}[/]",
                    "[green]✓[/]",
                )
            else:
                migration_table.add_row(
                    "[blue]Keystone[/]", "[yellow]Not applied[/]", "[yellow]⚠[/]"
                )

            # Add project branch status
            if branch_info["project"]["has_data"]:
                migration_table.add_row(
                    "[green]Project[/]",
                    f"[cyan]{branch_info['project']['head']}[/]",
                    "[green]✓[/]",
                )
            else:
                migration_table.add_row(
                    "[green]Project[/]", "[yellow]Not applied[/]", "[yellow]⚠[/]"
                )

            console.print(migration_table)

            # Show note about detailed view
            console.print(
                "\n[dim]For detailed migration information, use:[/] [bold]kcli db migration-status[/]"
            )
        else:
            console.print(
                Panel(
                    "[yellow]No migrations have been applied to the database[/]",
                    border_style="yellow",
                    expand=False,
                )
            )

    except Exception as e:
        console.print(
            Panel(
                f"[bold red]Database status check failed:[/]\n{str(e)}",
                title="[bold red]Error[/]",
                border_style="red",
                expand=False,
            )
        )
        raise typer.Exit(1)
