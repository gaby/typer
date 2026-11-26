"""A datetime option."""

import os
import time
from datetime import datetime
from typing import Annotated

import typer


def _mark() -> None:
    """Benchmark hook: record when user code starts running."""
    path = os.environ.get("BENCH_MARK_FILE")
    if path:
        with open(path, "w") as f:
            f.write(str(time.time_ns()))


def main(
    when: Annotated[datetime, typer.Option(help="When.")],
) -> None:
    _mark()
    typer.echo(f"When: {when.isoformat()}")


if __name__ == "__main__":
    typer.run(main)
