"""Baseline: basic.py written with the standard library's argparse."""

import argparse
import os
import time


def _mark() -> None:
    """Benchmark hook: record when user code starts running."""
    path = os.environ.get("BENCH_MARK_FILE")
    if path:
        with open(path, "w") as f:
            f.write(str(time.time_ns()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Greet NAME.")
    parser.add_argument("name", help="Who to greet.")
    parser.add_argument("--count", type=int, default=1, help="Number of greetings.")
    parser.add_argument(
        "--loud",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Shout the greeting.",
    )
    args = parser.parse_args()
    _mark()
    for _ in range(args.count):
        message = f"Hello {args.name}"
        print(message.upper() if args.loud else message)


if __name__ == "__main__":
    main()
