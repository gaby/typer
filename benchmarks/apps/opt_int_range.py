"""An int option with min/max bounds."""

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


def main(
    retries: Annotated[int, typer.Option(min=0, max=10, help="Retries.")] = 3,
) -> None:
    _mark()
    typer.echo(f"Retries: {retries}")


if __name__ == "__main__":
    typer.run(main)
