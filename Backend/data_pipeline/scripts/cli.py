from typing import Annotated

import typer
from loguru import logger
from rich.console import Console
from rich.panel import Panel

from data_pipeline.decorators import scripts_registry
from data_pipeline.scripts import initialize_scripts

initialize_scripts()

console = Console()
script_app = typer.Typer(help="Data processing commands")


def get_available_scripts() -> list[str]:
    """Get list of available script names from registry."""
    return sorted(scripts_registry.keys())


@script_app.command("list")
def list_scripts() -> None:
    """List all available data processing scripts."""
    scripts = get_available_scripts()
    if not scripts:
        logger.warning("No scripts found.")
        return

    console.print(Panel("[bold]Available Processing Scripts[/]", expand=False))
    for script in scripts:
        console.print(f"- {script}")


@script_app.command("run")
def run_script(
    script_name: Annotated[str, typer.Argument(help="Name of the script to run")],
    src: Annotated[str | None, typer.Option(help="Source file path")] = None,
    output: Annotated[str | None, typer.Option(help="Output file name")] = None,
) -> None:
    """Run a specific data processing script."""
    try:
        if script_name in scripts_registry:
            logger.info(f"Running script: {script_name}")

            # Prepare kwargs with only provided arguments
            kwargs = {}
            if src is not None:
                kwargs["src"] = src
            if output is not None:
                kwargs["output"] = output

            # Run the script with the provided arguments
            scripts_registry[script_name](**kwargs)
            logger.success(f"Successfully ran script: {script_name}")
        else:
            logger.error(f"Script '{script_name}' not found in registry")
    except Exception as e:
        logger.error(f"Error running script {script_name}: {str(e)}")
