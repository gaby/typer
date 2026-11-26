"""A `typer.Typer()` app with two commands."""

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


app = typer.Typer(help="Greeting tool.")


@app.command()
def hello(name: Annotated[str, typer.Argument(help="Who to greet.")]) -> None:
    """Say hello."""
    _mark()
    typer.echo(f"Hello {name}")


@app.command()
def goodbye(
    name: Annotated[str, typer.Argument(help="Who to say goodbye to.")],
    formal: Annotated[bool, typer.Option(help="Be formal.")] = False,
) -> None:
    """Say goodbye."""
    _mark()
    typer.echo(f"Goodbye Ms. {name}." if formal else f"Bye {name}!")


if __name__ == "__main__":
    app()
