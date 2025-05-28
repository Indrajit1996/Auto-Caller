"""
Migration-related database commands.
"""

from io import StringIO
from typing import Annotated

import typer
from alembic import command as alembic_command
from alembic.script import ScriptDirectory
from rich.panel import Panel

from cli.common import console

from .utils import (
    complete_branch_names,
    complete_revision_names,
    get_alembic_config,
    get_branch_heads,
)


def create_migration(
    message: Annotated[str, typer.Argument(help="Migration message")],
    autogenerate: Annotated[
        bool,
        typer.Option(
            "--autogenerate/--no-autogenerate",
            help="Autogenerate migration based on model changes",
        ),
    ] = True,
    branch: Annotated[
        str,
        typer.Option(
            "--branch",
            "-b",
            help="Branch name to use (project or keystone). 'project' branch is for project-specific customizations, while 'keystone' branch contains core system migrations.",
            autocompletion=complete_branch_names,
        ),
    ] = "project",  # Default to project branch instead of keystone
) -> None:
    """
    Create a new database migration (alias for 'alembic revision').

    Examples:
        db migrate "add user table"                      # Creates migration in project branch
        db migrate "modify column x" --no-autogenerate   # Creates empty migration in project branch
        db migrate "add core feature" --branch keystone  # Creates migration in keystone branch
    """
    print("yeysdhjasdhbdasjhdsabhhbjdsajbdbhsjbhjhasjbhjhadsjbhdjabhs")
    try:
        console.print(f"[yellow]Creating migration with message: {message}[/]")
        console.line()

        # Notify user about the branch being used
        if branch == "project":
            console.print(
                "[green]Using default 'project' branch for project-specific migrations[/]"
            )
            console.print(
                "[dim]To create core system migrations, use: --branch keystone[/]"
            )
        elif branch == "keystone":
            console.print("[blue]Using 'keystone' branch for core system migrations[/]")
            console.print(
                "[dim]Note: Only use keystone branch for core system changes[/]"
            )
        else:
            console.print(f"[yellow]Using custom branch: {branch}[/]")

        # Capture output to extract migration file information
        output = StringIO()
        alembic_cfg = get_alembic_config()
        alembic_cfg.stdout = output

        # Set the branch as an alembic option
        # This ensures the branch info is available to env.py
        alembic_cfg.attributes["branch"] = branch

        # Map branch name to version path
        version_locations = alembic_cfg.get_main_option("version_locations")
        locations = {}
        if version_locations:
            for location in version_locations.split():
                branch_name = location.split("/")[-1]
                locations[branch_name] = location

        # Validate branch
        if branch not in locations:
            console.print(f"[bold red]Unknown branch: {branch}[/]")
            console.print(f"[red]Available branches: {', '.join(locations.keys())}[/]")
            raise typer.Exit(1)

        # Add version path for this branch
        kwargs = {"version_path": locations[branch]}

        # Get the current heads for this branch
        branch_heads = get_branch_heads(alembic_cfg, branch)

        # Debug information
        console.print(f"[dim]Found {len(branch_heads)} heads for branch '{branch}'[/]")
        for head in branch_heads:
            console.print(f"[dim]  - {head}[/]")

        if branch_heads:
            # If multiple heads exist, ask the user to merge them first
            if len(branch_heads) > 1:
                console.print(
                    f"[bold red]Multiple heads found for branch '{branch}':[/]"
                )
                for head in branch_heads:
                    console.print(f"[red]  - {head}[/]")
                console.print(
                    "[yellow]Please merge heads using 'alembic merge' before creating new migrations[/]"
                )
                raise typer.Exit(1)

            # Use the current head of this branch as the base using branch@head syntax
            kwargs["head"] = f"{branch}@head"
            console.line()
            console.print(
                f"[yellow]Adding to existing branch head: {kwargs['head']}[/]"
            )
            console.line()
        else:
            # For first migration in the branch, specify the branch label
            kwargs["branch_label"] = branch
            console.print(
                f"[yellow]Creating initial migration with branch label: {branch}[/]"
            )

        # Create the revision
        revision = alembic_command.revision(
            alembic_cfg,
            message=message,
            autogenerate=autogenerate,
            **kwargs,
        )

        result = output.getvalue()
        console.print(f"[green]{result}[/]", end="")

        migration_file = ""

        if revision:
            # extract the migration file name from the revision object
            migration_file = revision.path.split("/")[-1]
            console.line()

            console.print(
                Panel(
                    f"[bold green]Migration file created:[/] {migration_file}",
                    border_style="green",
                    expand=False,
                )
            )

            if branch == "project":
                console.print(
                    "[green]This migration is in the project-specific 'project' branch[/]"
                )
            elif branch == "keystone":
                console.print(
                    "[blue]This migration is in the core 'keystone' branch[/]"
                )

        # Show migration tips
        console.print("\n[bold]Migration Tips:[/]")
        console.print("• To apply this migration: [cyan]kcli db upgrade[/]")
        console.print(
            f"• To view migration details: [cyan]kcli db show {revision.revision}[/]"
        )

    except Exception as e:
        console.line()
        console.print("[bold red]Migration creation failed:[/]")
        console.print(f"[red]{str(e)}[/]")
        raise typer.Exit(1)


def upgrade_db(
    revision: Annotated[
        str,
        typer.Argument(
            help="Revision to upgrade to (default: head)",
            autocompletion=complete_revision_names,
        ),
    ] = "head",
    branch: Annotated[
        str,
        typer.Option(
            "--branch",
            "-b",
            help="Branch to upgrade (keystone or project)",
            autocompletion=complete_branch_names,
        ),
    ] = None,
    sql: Annotated[
        bool,
        typer.Option(
            "--sql", help="Don't emit SQL to database - dump to standard output instead"
        ),
    ] = False,
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Skip confirmation prompt")
    ] = False,
) -> None:
    """
    Upgrade database to a later version.

    Examples:
        db upgrade                          # Upgrade all branches to head
        db upgrade --branch keystone        # Upgrade only keystone branch to its head
        db upgrade 27c6a30d7c24 --branch project  # Upgrade project branch to specific revision
        db upgrade +1 --branch keystone     # Upgrade keystone branch by 1 revision
    """
    try:
        alembic_cfg = get_alembic_config()

        # Set branch in config attributes so env.py can pick it up
        if branch:
            alembic_cfg.attributes["branch"] = branch

        # Format revision with branch if specified
        if branch and revision == "head":
            # Use branch@head syntax when specifying a branch
            target_revision = f"{branch}@head"
        elif not branch and revision == "head":
            # When no branch specified, using "heads" upgrades all branches
            target_revision = "heads"

            # Warn user since this will upgrade all branches
            if not force:
                # Get available branches
                script = ScriptDirectory.from_config(alembic_cfg)
                branches = set()
                for head in script.get_revisions("heads"):
                    branches.update(head.branch_labels or [])

                if branches:
                    console.print(
                        f"[yellow]Available branches: {', '.join(sorted(branches))}[/]"
                    )
                    typer.confirm(
                        "No branch specified. This will upgrade ALL branches to their latest versions. Continue?",
                        abort=True,
                    )
        else:
            # Handle other revision formats (relative like +1 or specific revision)
            if branch and not (revision.startswith("+") or revision.startswith("-")):
                # For specific revisions with a branch, use revision@branch syntax
                target_revision = f"{revision}@{branch}"
            else:
                target_revision = revision

        console.print(f"[yellow]Running database upgrade to '{target_revision}'...[/]")

        output = StringIO()
        alembic_cfg.stdout = output

        if sql:
            alembic_command.upgrade(alembic_cfg, target_revision, sql=True)
            sql_output = output.getvalue()
            console.print("[cyan]SQL for upgrade:[/]")
            console.print(sql_output)
        else:
            alembic_command.upgrade(alembic_cfg, target_revision)
            result = output.getvalue()
            if result:
                console.print(f"[green]{result}[/]", end="")
            console.print("[bold green]Database upgrade completed successfully![/]")

    except Exception as e:
        console.print("[bold red]Database upgrade failed:[/]")
        console.print(f"[red]{str(e)}[/]")
        raise typer.Exit(1)


def downgrade_db(
    revision: Annotated[
        str,
        typer.Argument(
            help="Revision to downgrade to (default: -1)",
            autocompletion=complete_revision_names,
        ),
    ] = "-1",
    branch: Annotated[
        str,
        typer.Option(
            "--branch",
            "-b",
            help="Branch to downgrade (keystone or project)",
            autocompletion=complete_branch_names,
        ),
    ] = None,
    sql: Annotated[
        bool,
        typer.Option(
            "--sql", help="Don't emit SQL to database - dump to standard output instead"
        ),
    ] = False,
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Skip confirmation prompt")
    ] = False,
) -> None:
    """
    Revert to a previous database version.

    Examples:
        db downgrade --branch keystone        # Downgrade keystone branch by 1 revision
        db downgrade base --branch project    # Downgrade project branch to base
        db downgrade -2 --branch keystone     # Downgrade keystone by 2 revisions
        db downgrade 27c6a30d7c24 --branch project  # Downgrade to specific revision
    """
    try:
        alembic_cfg = get_alembic_config()
        script = ScriptDirectory.from_config(alembic_cfg)

        # Get current revision(s)
        current_heads = script.get_revisions("heads")
        branches = set()
        rev_to_branch = {}

        # Map each head to its branch
        for head in current_heads:
            branch_labels = list(head.branch_labels or [])
            if branch_labels:
                branches.update(branch_labels)
                rev_to_branch[head.revision] = branch_labels[0]
            else:
                # For heads without branch labels, we'll call them "default"
                branches.add("default")
                rev_to_branch[head.revision] = "default"

        # We need a branch if there are multiple heads
        if len(current_heads) > 1 and not branch:
            console.print("[bold yellow]Multiple heads detected in database:[/]")
            for head in current_heads:
                branch_name = rev_to_branch.get(head.revision, "unknown")
                console.print(f"[yellow]  - {head.revision} (branch: {branch_name})[/]")

            console.print(
                "[bold red]You must specify a branch with --branch when downgrading from multiple heads[/]"
            )
            if branches:
                console.print(
                    f"[yellow]Available branches: {', '.join(sorted(branches))}[/]"
                )
            raise typer.Exit(1)

        # If there's only one branch available and no branch specified, we can use that one
        if len(branches) == 1 and not branch:
            branch = next(iter(branches))
            console.print(
                f"[yellow]No branch specified, using only available branch: {branch}[/]"
            )

        # Set branch in attributes
        if branch:
            alembic_cfg.attributes["branch"] = branch

        if branch:
            if revision == "base":
                # For base, we use branch@base syntax
                target_revision = f"{branch}@base"
            elif revision.startswith("-") and revision[1:].isdigit():
                # For relative revisions (-1, -2, etc.), use the proper branch@-N syntax
                # This directly handles the ambiguous downgrade warning
                target_revision = f"{branch}@{revision}"
            elif revision not in ("base", "head", "heads"):
                # For absolute revisions with branch (non-base, non-relative)
                target_revision = f"{revision}@{branch}"
            else:
                target_revision = revision
        else:
            # No branch specified (and only one head exists)
            target_revision = revision

        # Issue warning for base downgrade
        if "base" in str(target_revision).lower() and not force:
            message = "Warning: This will downgrade your database to the base state"
            if branch:
                message += f" for the {branch} branch"
            message += "! Are you sure?"
            typer.confirm(message, abort=True)

        console.print(
            f"[yellow]Running database downgrade to '{target_revision}'...[/]"
        )

        # Capture output
        output = StringIO()
        alembic_cfg.stdout = output

        # Run the downgrade command
        if sql:
            alembic_command.downgrade(alembic_cfg, target_revision, sql=True)
            sql_output = output.getvalue()
            console.print("[cyan]SQL for downgrade:[/]")
            console.print(sql_output)
        else:
            alembic_command.downgrade(alembic_cfg, target_revision)
            result = output.getvalue()
            if result:
                console.print(f"[green]{result}[/]", end="")
            console.print("[bold green]Database downgrade completed successfully![/]")

    except Exception as e:
        console.print("[bold red]Database downgrade failed:[/]")
        console.print(f"[red]{str(e)}[/]")
        raise typer.Exit(1)


def show_revision(
    revision: Annotated[
        str,
        typer.Argument(
            help="Revision identifier or branch name",
            autocompletion=complete_revision_names,
        ),
    ],
) -> None:
    """
    Show information about a specific revision.

    Examples:
        db show keystone     # Show information about keystone branch
        db show 27c6a30d7c24 # Show information about a specific revision
    """
    try:
        alembic_cfg = get_alembic_config()

        output = StringIO()
        alembic_cfg.stdout = output

        alembic_command.show(alembic_cfg, revision)

        result = output.getvalue()
        if result.strip():
            console.print("[bold]Revision details:[/]", end="\n\n")
            console.print(result)
        else:
            console.print(f"[yellow]No information found for revision: {revision}[/]")

    except Exception as e:
        console.print(f"[bold red]Failed to show revision information:[/] {e}")
        raise typer.Exit(1)


def show_current() -> None:
    """Show current revision."""
    try:
        alembic_cfg = get_alembic_config()

        console.print(
            "[bold]Current database revision information:[/]",
            end="\n\n",
        )

        with console.status(
            "[bold blue]Retrieving current revision info...[/]", spinner="dots"
        ):
            # Capture output using a custom writer
            output = StringIO()
            alembic_cfg.stdout = output

            # Run the current command
            alembic_command.current(alembic_cfg, verbose=True)
            result = output.getvalue()

            # Get script directory for branch information
            script = ScriptDirectory.from_config(alembic_cfg)
            heads = script.get_revisions("heads")

        if result.strip():
            # Split by branch and organize the information
            branch_info = {
                "keystone": {"revisions": [], "has_data": False},
                "project": {"revisions": [], "has_data": False},
                "other": {"revisions": [], "has_data": False},
            }

            current_branch = None
            current_rev = None

            # Parse the output and organize by branch
            for line in result.splitlines():
                # Detect branch from revision info
                if line.startswith("Rev:"):
                    current_rev = line.split("Rev:", 1)[1].strip()
                    # Extract just the revision identifier
                    rev_id = (
                        current_rev.split(" ", 1)[0]
                        if " " in current_rev
                        else current_rev
                    )

                    # Find which branch this revision belongs to
                    for head in heads:
                        if head.revision == rev_id:
                            branch_labels = list(head.branch_labels or [])
                            if branch_labels and "keystone" in branch_labels:
                                current_branch = "keystone"
                                branch_info["keystone"]["has_data"] = True
                                break
                            elif branch_labels and "project" in branch_labels:
                                current_branch = "project"
                                branch_info["project"]["has_data"] = True
                                break
                            else:
                                current_branch = "other"
                                branch_info["other"]["has_data"] = True

                    # Add the revision info to the appropriate branch
                    if current_branch:
                        branch_info[current_branch]["revisions"].append(
                            f"[bold cyan]{rev_id}[/] ({current_rev.replace(rev_id, '').strip()})"
                        )

                # Add additional information to the current branch
                elif current_branch and line.strip():
                    if "->" in line:
                        branch_info[current_branch]["revisions"].append(
                            f"  [dim]{line.strip()}[/]"
                        )
                    elif "Parent:" in line:
                        parent = line.split("Parent:", 1)[1].strip()
                        branch_info[current_branch]["revisions"].append(
                            f"  [green]Parent:[/] {parent}"
                        )
                    elif "Branch names:" in line:
                        branches = line.split("Branch names:", 1)[1].strip()
                        branch_info[current_branch]["revisions"].append(
                            f"  [yellow]Branch:[/] {branches}"
                        )
                    elif line.strip():
                        branch_info[current_branch]["revisions"].append(
                            f"  {line.strip()}"
                        )

            # Display panels for each branch
            console.print()

            # Keystone branch panel
            if branch_info["keystone"]["has_data"]:
                console.print(
                    Panel(
                        "\n".join(branch_info["keystone"]["revisions"]),
                        title="[bold blue]Keystone Branch[/]",
                        border_style="blue",
                        expand=False,
                    )
                )
            else:
                console.print(
                    Panel(
                        "[yellow]No migrations applied for keystone branch[/]",
                        title="[bold blue]Keystone Branch[/]",
                        border_style="blue",
                        expand=False,
                    )
                )

            # Project branch panel
            if branch_info["project"]["has_data"]:
                console.print(
                    Panel(
                        "\n".join(branch_info["project"]["revisions"]),
                        title="[bold green]Project Branch[/]",
                        border_style="green",
                        expand=False,
                    )
                )
            else:
                console.print(
                    Panel(
                        "[yellow]No migrations applied for project branch[/]",
                        title="[bold green]Project Branch[/]",
                        border_style="green",
                        expand=False,
                    )
                )

            # Any other branches or unclassified migrations
            if branch_info["other"]["has_data"]:
                console.print(
                    Panel(
                        "\n".join(branch_info["other"]["revisions"]),
                        title="[bold yellow]Other Migrations[/]",
                        border_style="yellow",
                        expand=False,
                    )
                )

            # If there are multiple heads, show a summary
            if len(heads) > 1:
                branches_list = []
                for head in heads:
                    branch_name = (
                        ", ".join(head.branch_labels)
                        if head.branch_labels
                        else "default"
                    )
                    branches_list.append(
                        f"[cyan]{head.revision}[/] ([yellow]{branch_name}[/])"
                    )

                console.print(
                    Panel(
                        "\n".join(branches_list),
                        title=f"[bold]Multiple Heads Detected ({len(heads)})[/]",
                        border_style="yellow",
                        expand=False,
                    )
                )
        else:
            console.print(
                Panel(
                    "[yellow]No revision information found[/]\n"
                    "The database may be at base state with no migrations applied.",
                    title="[bold yellow]Empty State[/]",
                    border_style="yellow",
                    expand=False,
                )
            )

    except Exception as e:
        console.print(
            Panel(
                f"[bold red]Failed to get current revision:[/]\n{str(e)}",
                title="[bold red]Error[/]",
                border_style="red",
                expand=False,
            )
        )
        raise typer.Exit(1)
