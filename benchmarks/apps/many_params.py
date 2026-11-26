"""One command with 12 parameters of mixed types, all supplied on the command line."""

import os
import time
from datetime import datetime
from enum import StrEnum
from pathlib import Path
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
    name: Annotated[str, typer.Argument(help="Who to greet.")],
    count: Annotated[int, typer.Option(help="Number of greetings.")] = 1,
    ratio: Annotated[float, typer.Option(help="A ratio.")] = 1.0,
    loud: Annotated[bool, typer.Option(help="Shout the greeting.")] = False,
    color: Annotated[Color, typer.Option(help="Pick a color.")] = Color.red,
    config: Annotated[
        Path | None, typer.Option(exists=True, dir_okay=False, help="Config file.")
    ] = None,
    when: Annotated[datetime | None, typer.Option(help="When.")] = None,
    tag: Annotated[list[str] | None, typer.Option(help="Tags.")] = None,
    retries: Annotated[int, typer.Option(min=0, max=10, help="Retries.")] = 3,
    output: Annotated[Path, typer.Option(help="Output file.")] = Path("out.txt"),
    verbose: Annotated[
        int, typer.Option("--verbose", "-v", count=True, help="Verbosity.")
    ] = 0,
    dry_run: Annotated[bool, typer.Option(help="Do nothing.")] = False,
) -> None:
    """Greet NAME with many knobs."""
    _mark()
    typer.echo(
        f"Hello {name} x{count} ratio={ratio} loud={loud} color={color.value} "
        f"config={config.name if config else None} when={when} tags={tag} "
        f"retries={retries} output={output} verbose={verbose} dry_run={dry_run}"
    )


if __name__ == "__main__":
    typer.run(main)
