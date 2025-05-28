import os
import sys
from typing import Annotated

import typer
import uvicorn
from dotenv import find_dotenv, set_key
from pydantic import ValidationError
from rich.panel import Panel
from rich.table import Table

from app.core.config import Config, config
from cli.common import console
from cli.db_commands import upgrade_db, verify_connection
from cli.user_commands import create_user
from data_pipeline.cli import initialize_data

server_app = typer.Typer(help="Server management commands")
DOTENV_LOCAL = find_dotenv(".env.local", usecwd=True)


@server_app.command("config")
def show_config() -> None:
    """Show the current server configuration."""
    table = Table("Setting", "Value", title="Server Configuration")

    for key, value in config.model_dump().items():
        # Skip sensitive information
        if "SECRET" in key or "PASSWORD" in key:
            value = "********"
        table.add_row(key, str(value))

    console.print(table, end="\n\n")


@server_app.command("set-config")
def set_config(
    key: Annotated[str, typer.Argument(help="Environment variable name")],
    value: Annotated[str, typer.Argument(help="New value")],
) -> None:
    """
    Set and persist a configuration variable (in .env.local).
    Validates the value based on the Config class definition.
    """
    if not DOTENV_LOCAL:
        # Create .env.local if it doesn't exist
        with open(".env.local", "w") as f:
            f.write("# This file is auto-generated. Do not edit manually.\n")
            f.write("# Add your custom environment variables here.\n")
        console.print("[yellow]Created .env.local[/]")

    # Check if the key exists in the Config class
    if not hasattr(Config, key) and key not in Config.model_fields:
        console.print(
            f"[yellow]Warning: {key} is not a recognized configuration option[/yellow]"
        )

        # Ask for confirmation
        confirm = typer.confirm("Do you want to set this value anyway?")
        if not confirm:
            console.print("[yellow]Operation cancelled.[/yellow]")
            return

    # Validate the value by attempting to create a partial Config with just this field
    if hasattr(Config, key) or key in Config.model_fields:
        try:
            # Create a test dictionary with just this key to validate
            test_config = {key: value}
            # Try to create a new config with just this field to see if it validates
            Config.model_validate({**Config().model_dump(), **test_config})
            # Value is valid
        except ValidationError as e:
            console.print(f"[red]❌ Invalid value for {key}: {str(e)}[/red]")
            return

    # Set the environment variable
    set_key(str(DOTENV_LOCAL), key, value)
    console.print(f"[green]✅ Set {key} = {value} in .env.local[/]")
    console.print(
        "[yellow]Note: You may need to restart the application for changes to take effect.[/yellow]"
    )


@server_app.command("run")
def run_server(
    host: Annotated[str, typer.Option(help="Host to bind")] = "0.0.0.0",
    port: Annotated[int, typer.Option(help="Port to bind")] = 8000,
    reload: Annotated[bool, typer.Option(help="Enable auto-reload")] = config.is_local,
    workers: Annotated[
        int | None, typer.Option(help="Number of worker processes")
    ] = None,
    log_level: Annotated[str | None, typer.Option(help="Log level")] = None,
    timeout: Annotated[
        int, typer.Option(help="Timeout for the server in seconds")
    ] = config.API_TIMEOUT_IN_SECONDS,
) -> None:
    """Run the application server."""
    if workers is None:
        workers = 1 if config.is_local else min((os.cpu_count() or 1) * 2 + 1, 8)

    if log_level is None:
        log_level = "debug" if config.is_local else "info"

    # Create a panel with server configuration details
    server_url = f"http://{host}:{port}"
    panel_content = [
        f"[bold cyan]URL:[/] [green]{server_url}[/]",
        f"[bold cyan]OpenAPI URL:[/] [green]{server_url}/docs[/]",
        f"[bold cyan]Redoc URL:[/] [green]{server_url}/redoc[/]",
        f"[bold cyan]Environment:[/] [{'green' if config.is_local else 'red'}]{'Development' if config.is_local else 'Production'}[/]",
        f"[bold cyan]Workers:[/] [yellow]{workers}[/]",
        f"[bold cyan]Auto-reload:[/] [yellow]{'Enabled' if reload else 'Disabled'}[/]",
        f"[bold cyan]Log level:[/] [yellow]{log_level}[/]",
        f"[bold cyan]Timeout:[/] [yellow]{timeout}s[/]",
    ]

    panel = Panel(
        "\n".join(panel_content),
        title="[bold]Server Configuration[/]",
        title_align="left",
        border_style="blue",
        width=60,
        padding=(1, 2),
    )
    console.print(panel)
    console.line()

    uvicorn.run(
        app="app.main:app",
        host=host,
        port=port,
        log_level=log_level,
        workers=workers,
        limit_concurrency=1000,
        limit_max_requests=10000,
        timeout_keep_alive=5,
        timeout_graceful_shutdown=timeout,
        proxy_headers=True,
        forwarded_allow_ips="*" if not config.is_local else "127.0.0.1",
        use_colors=True,
        reload=reload,
    )


@server_app.command("prestart")
def prestart() -> None:
    """
    Perform all necessary prestart operations like database verification,
    database migration, and initial data setup.
    """
    console.line(1)
    console.print("[bold blue]════════════════════════════════════════[/bold blue]")
    console.print("[bold green]🚀 Starting prestart operations[/bold green]")
    console.print("[bold blue]════════════════════════════════════════[/bold blue]")
    console.line()

    # Verify database connection
    console.print("[bold cyan]STEP 1/4:[/bold cyan] Verifying database connection...")
    if not verify_connection():
        console.print("[bold red]❌ Database connection failed. Exiting...[/bold red]")
        sys.exit(1)
    console.print("[bold green]✓ Database connection successful[/bold green]")
    console.line()

    # Run database migrations
    console.print("[bold cyan]STEP 2/4:[/bold cyan] Running database migrations...")
    try:
        upgrade_db(revision="heads")
        console.print(
            "[bold green]✓ Database migrations completed successfully[/bold green]"
        )
    except Exception as e:
        console.print(f"[bold red]❌ Database upgrade failed:[/bold red] {str(e)}")
        sys.exit(2)
    console.line()

    # Create users if not exist
    console.print(
        "[bold cyan]STEP 3/4:[/bold cyan] Creating users if not exist..."
    )
    try:
        create_user(
            first_name="Admin",
            last_name="User",
            is_superuser=True,
            email="admin@dtn.asu.edu",
            password="Admin@1234",
        )
        console.print(
            "[bold green]✓ Superuser created or verified successfully[/bold green]"
        )
        create_user(
            first_name="Indrajit",
            last_name="V",
            is_superuser=True,
            email="vindrajit1996@gmail.com",
            password="Admin@1234",
        )
        console.print(
            "[bold green]✓ Superuser created or verified successfully[/bold green]"
        )

        create_user(
            first_name="Normal",
            last_name="User",
            is_superuser=False,
            email="user@dtn.asu.edu",
            password="User@1234",
        )
        console.print(
            "[bold green]✓ Normal user created or verified successfully[/bold green]"
        )
    except Exception as e:
        console.print(f"[bold red]❌ User creation failed:[/bold red] {str(e)}")
        sys.exit(3)
    console.line()

    # Import initial data
    console.print("[bold cyan]STEP 4/4:[/bold cyan] Importing initial data...")
    try:
        initialize_data()
        console.print("[bold green]✓ Data import completed successfully[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Data import failed:[/bold red] {str(e)}")
        sys.exit(4)
    console.line()

    console.print("[bold blue]════════════════════════════════════════[/bold blue]")
    console.print(
        "[bold green]✨ Prestart operations completed successfully! ✨[/bold green]"
    )
    console.print("[bold blue]════════════════════════════════════════[/bold blue]")
    console.line()
