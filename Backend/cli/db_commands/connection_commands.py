"""
Database connection verification commands.
"""

import logging
import time
from typing import Annotated

import typer
from rich.panel import Panel
from sqlalchemy import text
from sqlmodel import select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.config import config
from app.core.db import SessionLocal
from cli.common import console

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def verify_connection(
    retries: Annotated[
        int, typer.Option("--retries", "-r", help="Number of retry attempts")
    ] = 5,
    interval: Annotated[
        int, typer.Option("--interval", "-i", help="Seconds between retries")
    ] = 1,
    timeout: Annotated[
        int, typer.Option("--timeout", "-t", help="Total timeout in seconds")
    ] = 30,
    silent: Annotated[
        bool, typer.Option("--silent", "-s", help="Suppress verbose output")
    ] = False,
) -> bool:
    """
    Verify database connection by attempting to execute a simple query.

    This command attempts to connect to the database and run a test query,
    retrying if needed based on the specified parameters.

    Examples:
        con verify           # Basic verification with default settings
        con verify --retries 10 --interval 2  # More retries with longer interval
        con verify --timeout 60  # Allow up to 60 seconds for connection
    """
    max_retries = min(retries, timeout // interval) if interval > 0 else retries

    @retry(
        stop=stop_after_attempt(max_retries),
        wait=wait_fixed(interval),
        before=before_log(logger, logging.INFO)
        if not silent
        else lambda *args, **kwargs: None,
        after=after_log(logger, logging.WARN)
        if not silent
        else lambda *args, **kwargs: None,
    )
    def _verify_db() -> bool:
        """Try connecting to database with retries."""
        try:
            with SessionLocal() as session:
                # Execute a simple query
                result = session.scalar(select(1))
                if result != 1:
                    raise ValueError("Unexpected query result")
                return True
        except Exception as e:
            if not silent:
                console.print(f"[yellow]Connection attempt failed:[/] {str(e)}")
            raise e

    start_time = time.time()
    success = False

    console.print("[yellow]Verifying database connection...[/]")

    try:
        _verify_db()
        elapsed = time.time() - start_time
        console.print(f"[bold green]Database connection verified![/] ({elapsed:.2f}s)")
        success = True
    except Exception as e:
        elapsed = time.time() - start_time
        console.print(
            f"[bold red]Database connection failed after {elapsed:.2f}s:[/] {str(e)}",
        )
        success = False
        # Exit with error code when verification fails
        raise typer.Exit(code=1)

    return success


def test_db_connection() -> None:
    """
    Test database connection and execute a simple query.

    Unlike 'verify', this doesn't retry - it just checks once and reports detailed results.
    """
    console.print("[yellow]Testing database connection...[/]")

    try:
        # Report connection string (with password masked)
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

        # Test basic connection
        start = time.time()
        with SessionLocal() as session:
            # Test simple query
            query_start = time.time()
            result = session.scalar(select(1))
            query_time = time.time() - query_start

            console.print(f"[green]Simple query result:[/] {result}")
            console.print(f"[green]Query execution time:[/] {query_time:.4f}s")

            # Get connection info
            db_info = session.execute(text("SELECT version()")).scalar()
            console.print(f"[green]Database version:[/] {db_info}")

            # Get connection metadata
            try:
                connection_info = session.execute(
                    text(
                        "SELECT state, client_addr, client_port FROM pg_stat_activity WHERE pid = pg_backend_pid()"
                    )
                ).first()
                if connection_info:
                    console.print(f"[green]Connection state:[/] {connection_info[0]}")
                    console.print(
                        f"[green]Client address:[/] {connection_info[1]}:{connection_info[2]}"
                    )
            except Exception:
                # This may not work on all databases or might need different syntax
                pass

        total_time = time.time() - start
        console.print("[bold green]Database connection test successful![/]")
        console.print(f"[green]Total connection time:[/] {total_time:.4f}s")

    except Exception as e:
        console.print(f"[bold red]Database connection test failed:[/] {str(e)}")
        import traceback

        console.print("[red]Error details:[/]")
        console.print(traceback.format_exc())
        raise typer.Exit(code=1)
