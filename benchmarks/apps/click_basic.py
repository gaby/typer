"""Baseline: basic.py written with upstream Click (run in a venv with `click`)."""

import os
import time

import click


def _mark() -> None:
    """Benchmark hook: record when user code starts running."""
    path = os.environ.get("BENCH_MARK_FILE")
    if path:
        with open(path, "w") as f:
            f.write(str(time.time_ns()))


@click.command()
@click.argument("name")
@click.option("--count", type=int, default=1, help="Number of greetings.")
@click.option("--loud/--no-loud", default=False, help="Shout the greeting.")
def main(name: str, count: int, loud: bool) -> None:
    """Greet NAME."""
    _mark()
    for _ in range(count):
        message = f"Hello {name}"
        click.echo(message.upper() if loud else message)


if __name__ == "__main__":
    main()
