import inspect
from typing import Annotated

import typer
from loguru import logger
from rich.console import Console
from rich.panel import Panel

from data_pipeline.decorators import importers_registry
from data_pipeline.importers import initialize_importers

initialize_importers()

console = Console()
importer_app = typer.Typer(help="Data import commands")


def get_available_importers() -> list[str]:
    """Get list of available importer modules."""
    return sorted(importers_registry.keys())


@importer_app.command("list")
def list_importers():
    """List all available data importers."""
    importers = get_available_importers()
    if not importers:
        logger.warning("No importers found.")
        return

    console.print(Panel("[bold]Available Importers[/]", expand=False))
    for importer in importers:
        console.print(f"- {importer}")


@importer_app.command("run")
def import_command(
    importer_name: Annotated[str, typer.Argument(help="Name of the importer to run")],
    file: Annotated[
        str | None, typer.Option("--file", "-f", help="Specific file to import")
    ] = None,
    truncate: Annotated[
        bool | None,
        typer.Option(
            "--truncate",
            "-t",
            is_eager=True,
            help="Truncate the database before importing",
        ),
    ] = False,
    skip_empty_rows: Annotated[
        bool | None,
        typer.Option(
            "--skip-empty-rows",
            "-s",
            is_eager=True,
            help="Skip empty rows in the import file",
        ),
    ] = False,
    unique_fields: Annotated[
        list[str] | None,
        typer.Option(
            "--unique-fields",
            "-u",
            help="List of unique fields to check for duplicates",
        ),
    ] = None,
) -> None:
    """Run a specific data importer."""
    try:
        # Check if the importer exists in the registry
        if importer_name not in importers_registry:
            logger.error(f"Importer '{importer_name}' not found in registry")

        importer_func = importers_registry[importer_name]

        logger.info(f"Running importer: {importer_name}")

        # Check if file_path has a default value if no file is provided
        if not file:
            sig = inspect.signature(importer_func)
            param = sig.parameters.get("file_path")
            if param and param.default is not param.empty:
                # Use the default file path
                importer_func(
                    truncate=truncate,
                    skip_empty_rows=skip_empty_rows,
                    unique_fields=unique_fields,
                )
            else:
                logger.error(f"File path is required for importer: {importer_name}")
                return
        else:
            importer_func(
                file_path=file,
                truncate=truncate,
                skip_empty_rows=skip_empty_rows,
                unique_fields=unique_fields,
            )

        logger.success(f"Successfully ran importer: {importer_name}")
    except Exception as e:
        logger.error(f"Error running importer {importer_name}: {str(e)}")
