#!/usr/bin/env python3

import subprocess
from pathlib import Path
from typing import TypeVar

import typer
from rich.console import Console

from app.core.config import config

app_cmd = typer.Typer(help="Application development commands")
console = Console()

T = TypeVar("T")


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


@app_cmd.command("lint")
def lint(
    path: str = typer.Argument(".", help="Path to lint"),
    fix: bool = typer.Option(False, "--fix", "-f", help="Automatically fix violations"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output"),
) -> typer.Exit | int:
    """Run Ruff linter on specified path."""
    if not config.is_local:
        console.print(
            "[bold red]This command is not available in the current environment.[/bold red]"
        )
        return typer.Exit(code=1)
    root = get_project_root()
    cmd = ["ruff", "check"]
    if fix:
        cmd.append("--fix")
    if verbose:
        cmd.append("--verbose")
    cmd.append(path)

    console.print(f"[bold]Running Ruff lint on {path}...[/bold]")
    try:
        result = subprocess.run(cmd, cwd=root, check=False)
        if result.returncode == 0:
            console.print("[bold green]Linting passed![/bold green]")
        else:
            console.print("[bold red]Linting found issues![/bold red]")
        return result.returncode
    except Exception as e:
        console.print(f"[bold red]Error running Ruff lint: {e}[/bold red]")
        return 1


@app_cmd.command("format")
def format_code(
    path: str = typer.Argument(".", help="Path to format"),
    check: bool = typer.Option(
        False,
        "--check",
        "-c",
        help="Check if files are formatted without modifying them",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output"),
) -> typer.Exit | int:
    """Run Ruff formatter on specified path."""
    if not config.is_local:
        console.print(
            "[bold red]This command is not available in the current environment.[/bold red]"
        )
        return typer.Exit(code=1)
    root = get_project_root()
    cmd = ["ruff", "format"]
    if check:
        cmd.append("--check")
    if verbose:
        cmd.append("--verbose")
    cmd.append(path)

    console.print(f"[bold]Running Ruff formatter on {path}[/bold]")
    try:
        result = subprocess.run(cmd, cwd=root, check=False, capture_output=True)
        if result.stdout:
            console.print(result.stdout.decode())
        if result.stderr:
            console.print(result.stderr.decode())
        if check:
            console.print("[bold yellow]Checking formatting...[/bold yellow]")
        console.line()
        return result.returncode
    except Exception as e:
        console.print(f"[bold red]Error running Ruff formatter: {e}[/bold red]")
        return 1
