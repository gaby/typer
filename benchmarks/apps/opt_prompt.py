"""An option that prompts for its value (answered on stdin)."""

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
    name: Annotated[str, typer.Option(prompt=True, help="Your name.")],
) -> None:
    _mark()
    typer.echo(f"Hello {name}")


if __name__ == "__main__":
    typer.run(main)
