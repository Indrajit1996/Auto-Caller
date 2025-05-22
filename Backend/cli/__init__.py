#!/usr/bin/env python3

import typer
from rich.console import Console
from rich.panel import Panel

from cli.app_commands import app_cmd
from cli.db_commands import db_app
from cli.server_commands import server_app
from cli.user_commands import user_app
from data_pipeline.cli import data_app

app = typer.Typer(
    help="Keystone CLI management tool",
    no_args_is_help=True,  # Show help when no arguments are provided
    context_settings={"help_option_names": ["-h", "--help"]},
    name="kcli",
)
console = Console(force_terminal=True, color_system="auto", soft_wrap=True, width=80)


@app.callback()
def main():
    """Keystone Management CLI."""
    console.line()
    console.print(
        Panel(
            "[bold blue]Keystone CLI Management Tool[/bold blue]",
            border_style="blue",
            padding=(1, 2),
            width=60,
        )
    )
    console.line()


# Register subcommands
app.add_typer(db_app, name="db", no_args_is_help=True)
app.add_typer(server_app, name="server", no_args_is_help=True)
app.add_typer(user_app, name="user", no_args_is_help=True)
app.add_typer(data_app, name="data", no_args_is_help=True)
app.add_typer(app_cmd, name="app", no_args_is_help=True)

if __name__ == "__main__":
    app()
