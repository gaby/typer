"""An int option."""

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
    count: Annotated[int, typer.Option(help="How many.")] = 1,
) -> None:
    _mark()
    typer.echo(f"Count: {count}")


if __name__ == "__main__":
    typer.run(main)
