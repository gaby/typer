"""Compare result files from run_benchmarks.py side by side.

Usage (from the repository root):

    python benchmarks/compare.py benchmarks/results/A.json benchmarks/results/B.json

With two or more files, the last column is the change from the first file to
the last one.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FLOOR_CASE = "baseline/python-floor"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument(
        "--metric", choices=("median", "min", "p95", "mean"), default="median"
    )
    parser.add_argument(
        "--delta",
        action="store_true",
        help="Subtract each file's own `python -c pass` floor.",
    )
    parser.add_argument(
        "--callback",
        action="store_true",
        help="Compare the time until the command function starts instead.",
    )
    args = parser.parse_args()

    results = [json.loads(path.read_text()) for path in args.files]
    labels = [r["meta"]["label"] for r in results]
    case_ids: list[str] = []
    for r in results:
        case_ids += [cid for cid in r["cases"] if cid not in case_ids]

    key = "to_callback" if args.callback else "total"

    def value(r: dict, cid: str) -> float | None:
        data = r["cases"].get(cid)
        if not data or data.get("status") != "ok" or key not in data:
            return None
        v = data[key][args.metric]
        if args.delta:
            floor = r["cases"].get(FLOOR_CASE, {}).get("total")
            if floor is None:
                return None
            v -= floor[args.metric]
        return v

    what = "to callback" if args.callback else "total"
    suffix = ", minus the python -c pass floor" if args.delta else ""
    print(f"{args.metric} {what} time in ms{suffix}\n")
    header = "| Case | " + " | ".join(labels)
    divider = "|---|" + "---:|" * len(labels)
    if len(results) > 1:
        header += " | Change |"
        divider += "---:|"
    else:
        header += " |"
    print(header)
    print(divider)
    for cid in case_ids:
        values = [value(r, cid) for r in results]
        cells = ["—" if v is None else f"{v:.1f}" for v in values]
        row = f"| `{cid}` | " + " | ".join(cells)
        if len(results) > 1:
            first, last = values[0], values[-1]
            if first is not None and last is not None and first > 0:
                diff = last - first
                row += f" | {diff:+.1f} ({diff / first:+.0%}) |"
            else:
                row += " | |"
        else:
            row += " |"
        print(row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
