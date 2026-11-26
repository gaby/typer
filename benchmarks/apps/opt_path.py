"""A Path option that must point to an existing file."""

import os
import time
from pathlib import Path
from typing import Annotated

import typer


def _mark() -> None:
    """Benchmark hook: record when user code starts running."""
    path = os.environ.get("BENCH_MARK_FILE")
    if path:
        with open(path, "w") as f:
            f.write(str(time.time_ns()))


def main(
    config: Annotated[
        Path, typer.Option(exists=True, dir_okay=False, help="Config file.")
    ],
) -> None:
    _mark()
    typer.echo(f"Config: {config.name}")


if __name__ == "__main__":
    typer.run(main)
