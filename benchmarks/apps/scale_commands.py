"""A large app: 50 commands with 3 parameters each (the whole tree is built on start)."""

import os
import time
from collections.abc import Callable
from typing import Annotated

import typer


def _mark() -> None:
    """Benchmark hook: record when user code starts running."""
    path = os.environ.get("BENCH_MARK_FILE")
    if path:
        with open(path, "w") as f:
            f.write(str(time.time_ns()))


app = typer.Typer(help="Large app with 50 commands.")


def _make_command(number: int) -> Callable[..., None]:
    def command(
        name: Annotated[str, typer.Argument(help="Target name.")],
        count: Annotated[int, typer.Option(help="Repeat count.")] = 1,
        force: Annotated[bool, typer.Option(help="Force it.")] = False,
    ) -> None:
        _mark()
        suffix = " (forced)" if force else ""
        typer.echo(f"cmd{number:02d}: {name} x{count}{suffix}")

    command.__doc__ = f"Run task number {number}."
    return command


for i in range(50):
    app.command(name=f"cmd{i:02d}")(_make_command(i))


if __name__ == "__main__":
    app()
