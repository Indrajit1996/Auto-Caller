from typing import Annotated

import typer
from loguru import logger
from rich.console import Console
from rich.panel import Panel

from data_pipeline.decorators import seeders_registry
from data_pipeline.seeders import initialize_seeders

initialize_seeders()

console = Console()
seeder_app = typer.Typer(help="Database seeding commands")


def get_available_seeders() -> list[str]:
    """Get list of available seeder modules."""
    return sorted(seeders_registry.keys())


@seeder_app.command("list")
def list_seeders() -> None:
    """List all available database seeders."""
    seeders = get_available_seeders()
    if not seeders:
        logger.warning("No seeders found.")
        return

    console.print(Panel("[bold]Available Seeders[/]", expand=False))
    for seeder in seeders:
        console.print(f"- {seeder}")


@seeder_app.command("run")
def run_seeder(
    seeder_name: Annotated[str, typer.Argument(help="Name of the seeder to run")],
    count: Annotated[
        int, typer.Option("--count", "-c", help="Number of records to seed")
    ] = 10,
) -> None:
    """Run a specific database seeder."""
    try:
        # Make sure the seeder exists
        if seeder_name not in seeders_registry:
            logger.error(f"Seeder '{seeder_name}' not found in registry")
            return

        # Get the registered seeder function and run it
        seeder_func = seeders_registry[seeder_name]
        logger.info(f"Running seeder: {seeder_name} with count: {count}")
        seeder_func(count=count)
        logger.success(f"Successfully ran seeder: {seeder_name}")
    except Exception as e:
        logger.error(f"Error running seeder {seeder_name}: {str(e)}")


@seeder_app.command("run-all")
def run_all(
    count: Annotated[
        int, typer.Option("--count", "-c", help="Number of records to seed")
    ] = 10,
) -> None:
    """Run all database seeders."""

    logger.info(f"Running all seeders individually with count: {count}")
    seeders = get_available_seeders()
    for seeder_name in seeders:
        try:
            seeder_func = seeders_registry[seeder_name]
            logger.info(f"Running seeder: {seeder_name} with count: {count}")
            seeder_func(count=count)
            logger.success(f"Successfully ran seeder: {seeder_name}")
        except Exception as e:
            logger.error(f"Error running seeder {seeder_name}: {str(e)}")
