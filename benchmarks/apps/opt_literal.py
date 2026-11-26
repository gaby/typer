"""A Literal choice option."""

import os
import time
from typing import Annotated, Literal

import typer


def _mark() -> None:
    """Benchmark hook: record when user code starts running."""
    path = os.environ.get("BENCH_MARK_FILE")
    if path:
        with open(path, "w") as f:
            f.write(str(time.time_ns()))


def main(
    level: Annotated[
        Literal["low", "medium", "high"], typer.Option(help="Level.")
    ] = "low",
) -> None:
    _mark()
    typer.echo(f"Level: {level}")


if __name__ == "__main__":
    typer.run(main)
