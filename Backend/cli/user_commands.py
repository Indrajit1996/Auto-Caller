from typing import Annotated

import typer

from app.core.db import SessionLocal
from app.models.user import UserStatus
from cli.common import console

from .utils import create_user as utils_create_user

user_app = typer.Typer(help="User management commands")


@user_app.command("create")
def create_user(
    email: Annotated[str, typer.Option(prompt=True)],
    password: Annotated[
        str, typer.Option(prompt=True, hide_input=True, confirmation_prompt=True)
    ],
    first_name: Annotated[str, typer.Option(prompt=True)],
    last_name: Annotated[str, typer.Option(prompt=True)],
    is_superuser: bool = False,
) -> None:
    """Create a new regular user."""

    _create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_superuser=is_superuser,
    )


def _create_user(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    is_superuser: bool = False,
) -> None:
    """
    Creates either a regular user or a superuser based on the is_superuser flag.
    """
    try:
        with SessionLocal() as session:
            try:
                new_user = utils_create_user(
                    session=session,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_superuser=is_superuser,
                    status=UserStatus.ACTIVE,
                )

                if new_user:
                    user_type = "Superuser" if is_superuser else "User"
                    console.print(
                        f"[bold green]{user_type} {new_user.email} created successfully![/]",
                        end="\n\n",
                    )
                else:
                    console.print(
                        f"[bold yellow]User with email {email} already exists![/]",
                        end="\n\n",
                    )
            except Exception as e:
                session.rollback()
                user_type = "superuser" if is_superuser else "user"
                console.print(
                    f"[bold red]Failed to create {user_type}:[/] {str(e)}", end="\n\n"
                )
                console.print(
                    "[yellow]Database transaction was rolled back.[/]", end="\n\n"
                )
                raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Database error:[/] {str(e)}", end="\n\n")
        raise typer.Exit(1)
