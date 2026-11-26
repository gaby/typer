"""A required option read from an environment variable."""

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
    api_url: Annotated[str, typer.Option(envvar="APP_API_URL", help="API URL.")],
) -> None:
    _mark()
    typer.echo(f"API: {api_url}")


if __name__ == "__main__":
    typer.run(main)
