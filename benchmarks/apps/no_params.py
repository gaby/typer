"""No parameters at all."""

import os
import time

import typer


def _mark() -> None:
    """Benchmark hook: record when user code starts running."""
    path = os.environ.get("BENCH_MARK_FILE")
    if path:
        with open(path, "w") as f:
            f.write(str(time.time_ns()))


def main() -> None:
    _mark()
    typer.echo("Hello World")


if __name__ == "__main__":
    typer.run(main)
