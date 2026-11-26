"""An Enum choice option."""

import os
import time
from enum import StrEnum
from typing import Annotated

import typer


def _mark() -> None:
    """Benchmark hook: record when user code starts running."""
    path = os.environ.get("BENCH_MARK_FILE")
    if path:
        with open(path, "w") as f:
            f.write(str(time.time_ns()))


class Color(StrEnum):
    red = "red"
    green = "green"
    blue = "blue"


def main(
    color: Annotated[Color, typer.Option(help="Pick a color.")] = Color.red,
) -> None:
    _mark()
    typer.echo(f"Color: {color.value}")


if __name__ == "__main__":
    typer.run(main)
