"""An app with nested sub-apps: `nested.py users create NAME`."""

import os
import time
from typing import Annotated

import typer


def _mark() -> None:
    """Benchmark hook: record when user code starts running."""
    path = os.environ.get("BENCH_MARK_FILE")
    if path:
        with open(path, "w") as f:
            f.write(str(time.time_ns()))


app = typer.Typer(help="Admin tool.")
users_app = typer.Typer(help="Manage users.")
items_app = typer.Typer(help="Manage items.")
app.add_typer(users_app, name="users")
app.add_typer(items_app, name="items")


@users_app.command("create")
def users_create(
    name: Annotated[str, typer.Argument(help="User name.")],
    admin: Annotated[bool, typer.Option(help="Grant admin rights.")] = False,
) -> None:
    """Create a user."""
    _mark()
    typer.echo(f"Created user {name}{' (admin)' if admin else ''}")


@users_app.command("delete")
def users_delete(
    name: Annotated[str, typer.Argument(help="User name.")],
    force: Annotated[bool, typer.Option(help="Skip confirmation.")] = False,
) -> None:
    """Delete a user."""
    _mark()
    typer.echo(f"Deleted user {name}")


@items_app.command("list")
def items_list(
    limit: Annotated[int, typer.Option(help="Max items to show.")] = 10,
) -> None:
    """List items."""
    _mark()
    typer.echo(f"Listing up to {limit} items")


if __name__ == "__main__":
    app()
