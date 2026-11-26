"""Same command as basic.py, declared on `typer.Typer(add_completion=False)`."""

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


app = typer.Typer(add_completion=False)


@app.command()
def main(
    name: Annotated[str, typer.Argument(help="Who to greet.")],
    count: Annotated[int, typer.Option(help="Number of greetings.")] = 1,
    loud: Annotated[bool, typer.Option(help="Shout the greeting.")] = False,
) -> None:
    """Greet NAME."""
    _mark()
    for _ in range(count):
        message = f"Hello {name}"
        typer.echo(message.upper() if loud else message)


if __name__ == "__main__":
    app()
