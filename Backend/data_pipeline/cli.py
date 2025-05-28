import typer
from loguru import logger
from rich.console import Console
from rich.table import Table

from data_pipeline.importers.cli import importer_app
from data_pipeline.initialize_data import initialize
from data_pipeline.scripts.cli import script_app
from data_pipeline.seeders.cli import seeder_app

data_app = typer.Typer(help="Data pipeline commands")
console = Console()

# Register sub-commands from modules
data_app.add_typer(importer_app, no_args_is_help=True, name="importer")
data_app.add_typer(script_app, no_args_is_help=True, name="script")
data_app.add_typer(seeder_app, no_args_is_help=True, name="seeder")


@data_app.command("status")
def show_status() -> None:
    """Show overall data pipeline status."""
    # This is a placeholder for potential status information
    table = Table(title="Data Pipeline Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")

    # Add example rows - in a real implementation this would query actual status
    table.add_row("Data Processing", "Available", "3 scripts ready")
    table.add_row("Data Import", "Available", "5 importers ready")
    table.add_row("Database Seeding", "Available", "8 seeders ready")

    console.print(table)


@data_app.command("initialize")
def initialize_data() -> None:
    """Initialize data in the database."""
    try:
        initialize()
    except Exception as e:
        logger.error(f"Error during data initialization: {e}")
        raise


# Make this script executable directly
if __name__ == "__main__":
    logger.info("Running data pipeline CLI directly")
    data_app()
