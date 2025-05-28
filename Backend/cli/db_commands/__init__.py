"""
Database management commands module.

This module organizes database-related CLI commands into a structured package.
"""

import typer

from .backup_commands import (
    db_backup,
    db_restore,
    list_backups,
)
from .commands import (
    db_status,
    reset_db,
)
from .connection_commands import (
    test_db_connection,
    verify_connection,
)
from .migration_commands import (
    create_migration,
    downgrade_db,
    show_current,
    show_revision,
    upgrade_db,
)

# Create the Typer app for database commands
db_app = typer.Typer(help="Database management commands")
con_app = typer.Typer(help="Database connection commands")
backup_app = typer.Typer(help="Database backup and restore commands")

# Register core DB commands
db_app.command("status")(db_status)
db_app.command("reset")(reset_db)

# Register connection commands under con namespace
con_app.command("verify")(verify_connection)
con_app.command("test")(test_db_connection)

# Register migration commands with appropriate help panel
db_app.command("migrate", rich_help_panel="Migration Commands")(create_migration)
db_app.command("upgrade", rich_help_panel="Migration Commands")(upgrade_db)
db_app.command("downgrade", rich_help_panel="Migration Commands")(downgrade_db)
db_app.command("show-revision", rich_help_panel="Migration Commands")(show_revision)
db_app.command("migration-status", rich_help_panel="Migration Commands")(show_current)

# Register backup commands under backup namespace with enhanced options
backup_app.command("list", help="List available backups")(list_backups)
backup_app.command("create", help="Create a backup of the database")(db_backup)

# Configure the restore command with enhanced autocompletion
backup_app.command("restore", help="Restore the database from a backup")(db_restore)

# Add the connection app as a sub-app
db_app.add_typer(
    con_app, name="con", help="Database connection commands", no_args_is_help=True
)

# Add the backup app as a sub-app
db_app.add_typer(
    backup_app,
    name="backup",
    help="Database backup and restore commands",
    no_args_is_help=True,
)

# Export the typer app and utility functions
__all__ = ["db_app"]
