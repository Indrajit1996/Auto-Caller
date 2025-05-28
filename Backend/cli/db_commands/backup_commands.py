"""
Database backup and restore commands.

Provides functionality to backup and restore database in various formats.
"""

import csv
import datetime
import json
import os
import subprocess
from enum import Enum
from pathlib import Path

import sqlalchemy as sa
import typer
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.prompt import Confirm
from rich.table import Table

from app.core.config import config
from app.core.db import engine as get_engine


class BackupFormat(str, Enum):
    PGDUMP = "pg_dump"
    CSV = "csv"
    BOTH = "both"


def _get_timestamp():
    """Generate a timestamp string for filenames."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")


def _get_backup_dir() -> Path:
    """Get or create the backup directory."""
    current_dir = Path(__file__).resolve()
    backend_dir = None

    for parent in [current_dir, *current_dir.parents]:
        if parent.name == "backend":
            backend_dir = parent
            break

    if backend_dir:
        backup_dir = backend_dir / "backups"
        logger.info(f"Found backend directory. Creating backups in: {backup_dir}")
    else:
        app_dir = current_dir.parent.parent
        backup_dir = app_dir / "backups"
        logger.info(
            f"Backend directory not found. Creating backups near app: {backup_dir}"
        )

    backup_dir.mkdir(exist_ok=True, parents=True)
    return backup_dir


def _get_model_tables() -> list[str]:
    """Get all model table names from SQLAlchemy metadata."""
    engine = get_engine
    metadata = sa.MetaData()
    metadata.reflect(bind=engine)
    return list(metadata.tables.keys())


def _get_user_related_tables() -> list[str]:
    """Get tables related to user models but excluding transactions."""
    user_tables = [
        "user",
        "invitation",
        "invitation_registrations",
        "user_settings",
        "group",
        "user_groups",
        "notification",
        "password_reset",
    ]
    return user_tables


def _get_table_dependencies(metadata) -> dict:
    """Get dependencies between tables based on foreign key relationships."""
    dependencies = {}
    priority_tables = ["user", "group"]
    junction_tables = []

    for table_name, table in metadata.tables.items():
        dependencies[table_name] = {
            "depends_on": [],
            "priority": table_name in priority_tables,
            "is_junction": False,
        }

        for fk in table.foreign_keys:
            parent_table = fk.column.table.name
            if parent_table != table_name:
                dependencies[table_name]["depends_on"].append(parent_table)

        if len(dependencies[table_name]["depends_on"]) > 1:
            dependencies[table_name]["is_junction"] = True
            junction_tables.append(table_name)

    return dependencies


def _truncate_tables_safely(conn, tables_to_truncate, metadata, console):
    """Safely truncate tables by handling foreign key constraints properly."""
    console.print("📌 Temporarily disabling foreign key constraints")
    conn.execute(sa.text("SET session_replication_role = 'replica';"))

    try:
        dependencies = _get_table_dependencies(metadata)
        dependency_counts = {}
        for table in tables_to_truncate:
            if table in dependencies:
                count = sum(
                    1
                    for t in dependencies
                    if table in dependencies[t].get("depends_on", [])
                )
                dependency_counts[table] = count

        sorted_tables = sorted(
            tables_to_truncate, key=lambda t: dependency_counts.get(t, 0)
        )

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}")
        ) as progress:
            truncate_task = progress.add_task(
                "[cyan]Truncating tables...[/]", total=len(sorted_tables)
            )

            for table_name in sorted_tables:
                progress.update(
                    truncate_task,
                    description=f"[cyan]Truncating[/] [yellow]{table_name}[/]",
                )

                try:
                    conn.execute(sa.text(f'TRUNCATE TABLE "{table_name}" CASCADE;'))
                    console.print(f"  ✓ Truncated [cyan]{table_name}[/]")
                except Exception as e:
                    console.print(
                        f"  ⚠️ [yellow]Could not truncate {table_name}: {str(e)}[/]"
                    )

                progress.advance(truncate_task)

    finally:
        conn.execute(sa.text("SET session_replication_role = 'origin';"))
        console.print("📌 Re-enabled foreign key constraints")


def get_backup_paths() -> list[str]:
    """Get a list of available backup paths for autocompletion."""
    backup_dir = _get_backup_dir()
    sql_backups = list(backup_dir.glob("backup_*.sql"))
    csv_backups = [d for d in backup_dir.glob("csv_backup_*") if d.is_dir()]
    return [str(path) for path in sorted(sql_backups + csv_backups)]


def backup_path_completion(incomplete: str):
    """Provide autocompletion for backup paths."""
    backup_paths = get_backup_paths()
    if incomplete:
        return [path for path in backup_paths if incomplete.lower() in path.lower()]
    return backup_paths


def resolve_backup_path(backup_path: Path | None, format: BackupFormat) -> Path | None:
    """Resolve backup path if not provided, choosing the latest appropriate backup."""
    if backup_path:
        return backup_path

    backup_dir = _get_backup_dir()
    console = Console()

    if format == BackupFormat.PGDUMP:
        backups = list(backup_dir.glob("backup_*.sql"))
    elif format == BackupFormat.CSV:
        backups = [d for d in backup_dir.glob("csv_backup_*") if d.is_dir()]
    else:
        sql_backups = list(backup_dir.glob("backup_*.sql"))
        backups = (
            sql_backups
            if sql_backups
            else [d for d in backup_dir.glob("csv_backup_*") if d.is_dir()]
        )

    backups = sorted(backups, key=lambda x: x.stat().st_mtime, reverse=True)

    if not backups:
        console.print(
            f"[yellow]No {format.value} backups found in {backup_dir}[/yellow]"
        )
        return None

    latest_backup = backups[0]
    console.print(f"[green]Using most recent backup: {latest_backup}[/green]")
    return latest_backup


def _convert_value_to_appropriate_type(column, value):
    """Convert string values from CSV to appropriate Python types based on column type."""
    if value == "" or value is None:
        return None

    # Get column type name as string
    type_name = str(column.type).lower()

    # Handle boolean values
    if "boolean" in type_name or "bool" in type_name:
        # Convert string representation to actual boolean
        if value.lower() in ("true", "t", "yes", "y", "1"):
            return True
        elif value.lower() in ("false", "f", "no", "n", "0"):
            return False
        else:
            raise ValueError(
                f"Cannot convert '{value}' to boolean for column {column.name}"
            )

    # Handle UUID values
    elif "uuid" in type_name:
        return value  # Pass as string, SQLAlchemy will handle conversion

    # Handle JSON values
    elif "json" in type_name or "jsonb" in type_name:
        try:
            if isinstance(value, str):
                return json.loads(value)
            return value
        except json.JSONDecodeError:
            return value  # Return as is if can't parse

    # Handle numeric values
    elif any(t in type_name for t in ("int", "numeric", "float", "decimal")):
        if isinstance(value, str) and value.strip():
            if "int" in type_name:
                return int(value)
            else:
                return float(value)
        return value

    # For other types, return as is (string)
    return value


def backup_database(
    format: BackupFormat = BackupFormat.PGDUMP,
    user_models_only: bool = False,
    output_dir: Path | None = None,
    data_only: bool = False,
) -> Path:
    """Backup the database in the specified format."""
    timestamp = _get_timestamp()
    backup_dir = output_dir or _get_backup_dir()
    console = Console()

    user_tables = _get_user_related_tables() if user_models_only else []

    if format in (BackupFormat.PGDUMP, BackupFormat.BOTH):
        filename_suffix = "_data_only" if data_only else ""
        pg_dump_path = backup_dir / f"backup_{timestamp}{filename_suffix}.sql"

        cmd = [
            "pg_dump",
            f"--host={config.POSTGRES_SERVER}",
            f"--port={config.POSTGRES_PORT}",
            f"--username={config.POSTGRES_USER}",
            f"--dbname={config.POSTGRES_DB}",
            f"--file={pg_dump_path}",
        ]

        if data_only:
            cmd.append("--data-only")

        if user_models_only:
            console.print(
                "📋 Creating [cyan]user-specific[/] backup (excluding transactions)"
            )
            for table in user_tables:
                cmd.extend(["-t", table])
        else:
            console.print("📋 Creating [cyan]full database[/] backup")

        backup_type = "data only" if data_only else "complete (schema and data)"
        console.print(f"🔄 Creating [green]{backup_type}[/] pg_dump backup at:")
        console.print(f"  [dim]{pg_dump_path}[/]")

        env = os.environ.copy()
        env["PGPASSWORD"] = config.POSTGRES_PASSWORD

        with console.status("Backing up database with pg_dump...", spinner="dots"):
            subprocess.run(cmd, env=env, check=True)

        console.print("✅ [bold green]pg_dump backup completed successfully[/]")

    if format in (BackupFormat.CSV, BackupFormat.BOTH):
        csv_dir = backup_dir / f"csv_backup_{timestamp}"
        csv_dir.mkdir(exist_ok=True)

        engine = get_engine
        metadata = sa.MetaData()
        metadata.reflect(bind=engine)

        tables_to_backup = list(metadata.tables.keys())
        if user_models_only:
            tables_to_backup = [t for t in tables_to_backup if t in user_tables]
            console.print(
                f"📋 Creating [cyan]user-specific CSV[/] backup with tables: [yellow]{', '.join(tables_to_backup)}[/]"
            )
        else:
            console.print(
                f"📋 Creating [cyan]full CSV[/] backup with [yellow]{len(tables_to_backup)}[/] tables"
            )

        dependencies = _get_table_dependencies(metadata)
        backup_dependencies = {
            t: dependencies[t] for t in dependencies if t in tables_to_backup
        }

        restoration_order = []

        for table in tables_to_backup:
            if table in backup_dependencies and backup_dependencies[table]["priority"]:
                restoration_order.append(table)

        for table in tables_to_backup:
            if (
                table in backup_dependencies
                and not backup_dependencies[table]["depends_on"]
                and not backup_dependencies[table]["priority"]
                and not backup_dependencies[table]["is_junction"]
            ):
                restoration_order.append(table)

        dependency_added = True
        remaining_tables = [
            t
            for t in tables_to_backup
            if t not in restoration_order
            and t in backup_dependencies
            and not backup_dependencies[t]["is_junction"]
        ]

        while dependency_added and remaining_tables:
            dependency_added = False
            for table in list(remaining_tables):
                if all(
                    dep in restoration_order
                    for dep in backup_dependencies[table]["depends_on"]
                ):
                    restoration_order.append(table)
                    remaining_tables.remove(table)
                    dependency_added = True

        for table in tables_to_backup:
            if (
                table in backup_dependencies
                and backup_dependencies[table]["is_junction"]
                and table not in restoration_order
            ):
                restoration_order.append(table)

        for table in tables_to_backup:
            if table not in restoration_order:
                restoration_order.append(table)

        metadata_file = {
            "timestamp": timestamp,
            "tables": tables_to_backup,
            "dependencies": backup_dependencies,
            "suggested_restoration_order": restoration_order,
            "user_models_only": user_models_only,
        }

        with open(csv_dir / "backup_metadata.json", "w") as f:
            json.dump(metadata_file, f, indent=2)

        console.print(
            "📄 Created [bold green]backup_metadata.json[/] with restoration order information"
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task(
                "[cyan]Backing up tables...[/]", total=len(tables_to_backup)
            )

            with engine.connect() as conn:
                for table_name in tables_to_backup:
                    progress.update(
                        task, description=f"[cyan]Backing up[/] [yellow]{table_name}[/]"
                    )

                    table = metadata.tables[table_name]
                    result = conn.execute(sa.select(table))
                    rows = result.fetchall()

                    with open(
                        csv_dir / f"{table_name}.csv", "w", newline=""
                    ) as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([c.name for c in table.columns])
                        for row in rows:
                            writer.writerow(row)

                    progress.advance(task)

        console.print(
            f"✅ [bold green]CSV backup completed successfully[/] in [dim]{csv_dir}[/]"
        )

    return backup_dir


def restore_database(
    backup_path: Path,
    format: BackupFormat = BackupFormat.PGDUMP,
    user_models_only: bool = False,
    truncate_tables: bool = False,
    drop_cascade: bool = False,
) -> bool:
    """Restore database from backup."""
    console = Console()

    user_tables = _get_user_related_tables() if user_models_only else []
    is_data_only = (
        "_data_only" in str(backup_path) if format == BackupFormat.PGDUMP else False
    )

    if not backup_path.exists():
        console.print(f"[bold red]Error:[/] Backup path does not exist: {backup_path}")
        return False

    if format == BackupFormat.PGDUMP and backup_path.suffix == ".sql":
        env = os.environ.copy()
        env["PGPASSWORD"] = config.POSTGRES_PASSWORD

        if is_data_only:
            if truncate_tables:
                console.print(
                    "🗑️  [yellow]Truncating tables before restoring data...[/]"
                )
                engine = get_engine
                metadata = sa.MetaData()
                metadata.reflect(bind=engine)

                tables_to_truncate = list(metadata.tables.keys())
                if user_models_only:
                    tables_to_truncate = [
                        t for t in tables_to_truncate if t in user_tables
                    ]

                with engine.begin() as conn:
                    _truncate_tables_safely(conn, tables_to_truncate, metadata, console)
            else:
                console.print(
                    "[bold yellow]⚠️ Warning:[/] Restoring data without truncating tables first may cause conflicts."
                )
                console.print(
                    "If the restore fails, try again with the [cyan]--truncate-tables[/] option."
                )

        elif drop_cascade:
            console.print(
                "🗑️  [bold yellow]Dropping existing tables with CASCADE before restore...[/]"
            )
            console.print(
                "[green]All existing tables dropped. Proceeding with restore.[/]"
            )

        cmd = [
            "psql",
            f"--host={config.POSTGRES_SERVER}",
            f"--port={config.POSTGRES_PORT}",
            f"--username={config.POSTGRES_USER}",
            f"--dbname={config.POSTGRES_DB}",
            "-f",
            str(backup_path),
        ]

        console.print(f"🔄 [bold]Restoring database[/] from [cyan]{backup_path}[/]")
        try:
            with console.status("Running restore operation...", spinner="dots"):
                result = subprocess.run(cmd, env=env, check=True)
            console.print("✅ [bold green]Database restored successfully[/]")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]❌ Error during restore:[/] {e}")
            console.print(
                "If this is due to conflicts, try using the [cyan]--drop-cascade[/] option (for full backups)"
            )
            console.print(
                "or [cyan]--truncate-tables[/] option (for data-only backups)."
            )
            console.print(
                "For severe issues, consider using the [bold cyan]db:reset[/] command to fully reset the database."
            )
            return False

    elif format == BackupFormat.CSV and backup_path.is_dir():
        csv_files = list(backup_path.glob("*.csv"))
        if not csv_files:
            console.print(
                f"[bold red]Error:[/] No CSV files found in directory: {backup_path}"
            )
            return False

        engine = get_engine
        metadata = sa.MetaData()
        metadata.reflect(bind=engine)

        tables_to_restore = list(metadata.tables.keys())
        if user_models_only:
            tables_to_restore = [t for t in tables_to_restore if t in user_tables]

        console.print(
            "⚙️  Restoring tables in the following order:\n  "
            + ", ".join([f"[cyan]{t}[/]" for t in tables_to_restore])
        )

        try:
            with engine.begin() as conn:
                if truncate_tables:
                    console.print(
                        "🗑️  [yellow]Truncating tables before importing CSV data...[/]"
                    )
                    _truncate_tables_safely(conn, tables_to_restore, metadata, console)
                else:
                    console.print("🗑️  [yellow]Clearing existing data from tables...[/]")
                    conn.execute(sa.text("SET session_replication_role = 'replica';"))
                    try:
                        for table_name in reversed(tables_to_restore):
                            if table_name in metadata.tables:
                                console.print(
                                    f"  - Clearing data from [cyan]{table_name}[/]"
                                )
                                conn.execute(metadata.tables[table_name].delete())
                    finally:
                        conn.execute(
                            sa.text("SET session_replication_role = 'origin';")
                        )

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                ) as progress:
                    restore_task = progress.add_task(
                        "[cyan]Restoring tables...[/]", total=len(tables_to_restore)
                    )

                    for table_name in tables_to_restore:
                        if table_name not in metadata.tables:
                            console.print(
                                f"[bold yellow]⚠️ Warning:[/] Table [cyan]{table_name}[/] does not exist in the database"
                            )
                            progress.advance(restore_task)
                            continue

                        progress.update(
                            restore_task,
                            description=f"[cyan]Restoring[/] [yellow]{table_name}[/]",
                        )

                        table = metadata.tables[table_name]
                        csv_file = backup_path / f"{table_name}.csv"

                        if not csv_file.exists():
                            console.print(
                                f"[yellow]Warning:[/] CSV file for {table_name} not found"
                            )
                            progress.advance(restore_task)
                            continue

                        row_count = 0
                        with open(csv_file, newline="") as csvfile:
                            reader = csv.reader(csvfile)
                            header = next(reader)

                            batch = []
                            batch_size = 1000

                            columns = {c.name: c for c in table.columns}

                            for row in reader:
                                data = {}
                                for i, column_name in enumerate(header):
                                    if i < len(row) and column_name in columns:
                                        try:
                                            data[column_name] = (
                                                _convert_value_to_appropriate_type(
                                                    columns[column_name], row[i]
                                                )
                                            )
                                        except ValueError as e:
                                            console.print(
                                                f"[yellow]Warning: {e}[/yellow]"
                                            )
                                            data[column_name] = row[i]

                                batch.append(data)

                                if len(batch) >= batch_size:
                                    try:
                                        conn.execute(table.insert(), batch)
                                        row_count += len(batch)
                                    except Exception as e:
                                        console.print(
                                            f"[bold red]Error inserting batch into {table_name}:[/]"
                                        )
                                        console.print(f"[red]{str(e)}[/]")
                                        for i, row_data in enumerate(batch):
                                            try:
                                                conn.execute(table.insert(), [row_data])
                                                row_count += 1
                                            except Exception as row_e:
                                                console.print(
                                                    f"[red]Error with row {i}: {str(row_e)}[/]"
                                                )
                                                console.print(
                                                    f"[dim]Data: {row_data}[/dim]"
                                                )
                                    batch = []

                            if batch:
                                try:
                                    conn.execute(table.insert(), batch)
                                    row_count += len(batch)
                                except Exception as e:
                                    console.print(
                                        f"[bold red]Error inserting final batch into {table_name}:[/]"
                                    )
                                    console.print(f"[red]{str(e)}[/]")
                                    for i, row_data in enumerate(batch):
                                        try:
                                            conn.execute(table.insert(), [row_data])
                                            row_count += 1
                                        except Exception as row_e:
                                            console.print(
                                                f"[red]Error with row {i}: {str(row_e)}[/]"
                                            )
                                            console.print(
                                                f"[dim]Data: {row_data}[/dim]"
                                            )

                        console.print(
                            f"  ↳ Inserted [bold green]{row_count} rows[/] into [cyan]{table_name}[/]"
                        )
                        progress.advance(restore_task)

            console.print("✅ [bold green]CSV restore completed successfully[/]")
            return True

        except Exception as e:
            console.print(f"[bold red]❌ Error during restore:[/] {e}")
            return False


def list_backups(format: BackupFormat | None = None) -> list[Path]:
    """List all available backups."""
    backup_dir = _get_backup_dir()
    console = Console()

    sql_backups = []
    csv_backups = []

    if not format or format in (BackupFormat.PGDUMP, BackupFormat.BOTH):
        sql_backups = list(backup_dir.glob("backup_*.sql"))

    if not format or format in (BackupFormat.CSV, BackupFormat.BOTH):
        csv_backups = [d for d in backup_dir.glob("csv_backup_*") if d.is_dir()]

    backups = sorted(
        sql_backups + csv_backups, key=lambda x: x.stat().st_mtime, reverse=True
    )

    if not backups:
        console.print(
            Panel("No backups found", title="Database Backups", border_style="yellow")
        )
        return []

    pg_table = Table(
        title="PostgreSQL Dumps",
        show_header=True,
        header_style="bold cyan",
        title_justify="left",
    )
    pg_table.add_column("Filename", style="dim")
    pg_table.add_column("Date", style="green")
    pg_table.add_column("Type", style="yellow")
    pg_table.add_column("Size", style="blue")

    csv_table = Table(
        title="CSV Backups",
        show_header=True,
        header_style="bold cyan",
        title_justify="left",
    )
    csv_table.add_column("Directory", style="dim")
    csv_table.add_column("Date", style="green")
    csv_table.add_column("Tables", style="blue")
    csv_table.add_column("Size", style="magenta")

    for backup in backups:
        backup_stat = backup.stat()
        mod_time = datetime.datetime.fromtimestamp(backup_stat.st_mtime)
        formatted_date = mod_time.strftime("%Y-%m-%d %H:%M:%S")

        if backup.suffix == ".sql":
            size_mb = backup_stat.st_size / (1024 * 1024)
            backup_type = "Data only" if "_data_only" in backup.name else "Complete"
            pg_table.add_row(
                backup.name, formatted_date, backup_type, f"{size_mb:.2f} MB"
            )
        else:
            table_count = len(list(backup.glob("*.csv")))
            total_size = sum(f.stat().st_size for f in backup.glob("*.csv"))
            size_mb = total_size / (1024 * 1024)

            csv_table.add_row(
                backup.name, formatted_date, str(table_count), f"{size_mb:.2f} MB"
            )

    if backups:
        console.print(Panel("📂 [bold]Database Backups[/]", style="green", width=60))
        console.line()

        if sql_backups:
            console.print(pg_table)
            console.print(f"[dim]Found {len(sql_backups)} SQL backup files[/]")
            console.line(2)

        if csv_backups:
            console.print(csv_table)
            console.print(f"[dim]Found {len(csv_backups)} CSV backup directories[/]")
            console.line()

        if sql_backups or csv_backups:
            console.print(
                "\n👉 [bold cyan]Use the kcli db backup restore command to restore a backup[/]"
            )
    else:
        console.print(
            Panel("No backups found", title="Database Backups", border_style="yellow")
        )

    return backups


def db_backup(
    format: BackupFormat = BackupFormat.PGDUMP,
    user_only: bool = False,
    output: Path | None = None,
    data_only: bool = False,
):
    """Backup the database."""
    console = Console()
    try:
        console.print(Panel("🚀 [bold]Creating Database Backup[/]", style="blue"))
        backup_path = backup_database(format, user_only, output, data_only)
        console.print(
            Panel(
                f"✅ [bold green]Backup completed successfully[/]\nLocation: [cyan]{backup_path}[/]",
                title="Success",
                border_style="green",
            )
        )
    except Exception as e:
        console.print(
            Panel(
                f"❌ [bold red]Error creating backup:[/] {e}",
                title="Error",
                border_style="red",
            )
        )


def db_restore(
    backup_path: Path = typer.Argument(
        None,
        help="Path to backup file or directory (optional, uses latest if not specified)",
        autocompletion=backup_path_completion,
    ),
    format: BackupFormat = BackupFormat.PGDUMP,
    user_only: bool = False,
    truncate_tables: bool = False,
    drop_cascade: bool = False,
    is_data_only: bool = False,
):
    """Restore the database from backup."""
    console = Console()
    console.print(Panel("🔄 [bold]Database Restore[/]", style="blue"))

    resolved_path = resolve_backup_path(backup_path, format)
    if not resolved_path:
        console.print(
            "[bold yellow]⚠️ No backup found to restore.[/] Please create a backup first."
        )
        return

    inferred_format = format
    if backup_path is None or (format == BackupFormat.BOTH):
        if resolved_path.is_dir():
            inferred_format = BackupFormat.CSV
            console.print("Detected CSV backup directory, using CSV format")
        elif resolved_path.suffix == ".sql":
            inferred_format = BackupFormat.PGDUMP
            console.print("Detected SQL file, using pg_dump format")
        else:
            console.print(
                f"Warning: Could not infer format from path. Using specified format: {format.value}"
            )

    effective_is_data_only = is_data_only
    if inferred_format == BackupFormat.CSV:
        effective_is_data_only = True
        console.print(
            "CSV format contains only data (no schema), treating as data-only restore"
        )
    elif "_data_only" in str(resolved_path):
        effective_is_data_only = True
        console.print("Detected data-only backup file")

    if (
        inferred_format == BackupFormat.PGDUMP
        and not effective_is_data_only
        and drop_cascade
    ):
        if not Confirm.ask(
            "⚠️  [bold red]WARNING:[/] This will drop all existing tables in the database. Continue?",
            default=False,
        ):
            console.print("[yellow]Restore cancelled.[/]")
            return

    elif (
        inferred_format == BackupFormat.CSV or effective_is_data_only
    ) and truncate_tables:
        if not Confirm.ask(
            "⚠️  [bold red]WARNING:[/] This will truncate all affected tables before restoring data. Continue?",
            default=False,
        ):
            console.print("[yellow]Restore cancelled.[/]")
            return

    elif (
        inferred_format == BackupFormat.PGDUMP
        and not drop_cascade
        and not effective_is_data_only
    ):
        console.print(
            "Note: Restoring without dropping tables first. This is only safe for a fresh database."
        )
        console.print("If you encounter errors, try again with --drop-cascade option.")

    elif (
        inferred_format == BackupFormat.CSV or effective_is_data_only
    ) and not truncate_tables:
        console.print(
            "Note: Restoring without truncating tables first. This may cause conflicts."
        )
        console.print(
            "If you encounter errors, try again with --truncate-tables option."
        )

    try:
        with console.status("Starting restore operation...", spinner="dots"):
            success = restore_database(
                resolved_path, inferred_format, user_only, truncate_tables, drop_cascade
            )

        if success:
            console.print(
                Panel(
                    "✅ [bold green]Restore completed successfully[/]",
                    title="Success",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    "❌ [bold yellow]Restore failed.[/]\nIf problems persist, consider using [bold]db:reset[/] command.",
                    title="Warning",
                    border_style="yellow",
                )
            )
    except Exception as e:
        console.print(
            Panel(
                f"❌ [bold red]Error during restore:[/] {e}\n\nIf problems persist, consider using [bold]db:reset[/] command.",
                title="Error",
                border_style="red",
            )
        )
