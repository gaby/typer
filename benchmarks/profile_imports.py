"""Attribute import time to packages for selected benchmark cases.

Each case is run several times with ``python -X importtime``. The *self* time
of every imported module is summed by package group and the median per group
is reported.

Summing self time, not reading the cumulative column, matters here: Pydantic
and Rich load many submodules lazily, so in the cumulative column their cost
shows up under whichever Typer module happened to trigger them.

``-X importtime`` adds its own overhead, so read these numbers as proportions.
The wall-clock numbers come from ``run_benchmarks.py``.

Usage (from the repository root):

    python benchmarks/profile_imports.py --python /path/to/venv/bin/python
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import statistics
import subprocess
import sys
import tempfile
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

from run_benchmarks import APPS_DIR, RESULTS_DIR, build_cases, clean_env

DEFAULT_CASES = (
    "baseline/import-typer",
    "baseline/argparse",
    "params/no-params",
    "shape/typer-run",
    "shape/app-50-commands",
    "help/typer-run",
    "help/typer-run-no-rich",
    "help/subcommand",
    "error/bad-int",
    "error/bad-int-no-rich",
)


def _starts(*prefixes: str) -> Callable[[str], bool]:
    return lambda mod: any(mod == p or mod.startswith(p + ".") for p in prefixes)


def make_groups(stdlib: set[str]) -> list[tuple[str, Callable[[str], bool]]]:
    return [
        ("typer._click (vendored Click)", _starts("typer._click")),
        ("typer (own code)", _starts("typer")),
        ("pydantic", _starts("pydantic")),
        ("pydantic_core", _starts("pydantic_core")),
        (
            "pydantic deps",
            _starts("annotated_types", "typing_inspection", "typing_extensions"),
        ),
        ("rich", _starts("rich")),
        ("markdown_it + mdurl", _starts("markdown_it", "mdurl")),
        ("pygments", _starts("pygments")),
        ("click (upstream)", _starts("click")),
        ("stdlib", lambda mod: mod.split(".", 1)[0] in stdlib),
        ("other", lambda mod: True),
    ]


def parse_importtime(stderr: str) -> list[tuple[str, int]]:
    """Return (module, self_us) pairs from ``-X importtime`` output."""
    rows = []
    for line in stderr.splitlines():
        if not line.startswith("import time:") or "self [us]" in line:
            continue
        self_us, _cumulative, name = line.removeprefix("import time:").split("|")
        rows.append((name.strip(), int(self_us)))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--python", required=True)
    parser.add_argument("--click-python")
    parser.add_argument("--label", default="typer")
    parser.add_argument("--repeat", type=int, default=7)
    parser.add_argument("--only", action="append", default=[], metavar="GLOB")
    parser.add_argument(
        "--top", type=int, default=12, help="Also list the N slowest modules."
    )
    parser.add_argument("--out", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()

    patterns = args.only or list(DEFAULT_CASES)
    cases = [
        c for c in build_cases() if any(fnmatch.fnmatch(c.id, p) for p in patterns)
    ]
    python = str(Path(args.python).absolute())
    cwd = Path(tempfile.mkdtemp(prefix="typer-imports-"))
    stdlib = set(
        subprocess.run(
            [python, "-c", "import sys; print('\\n'.join(sys.stdlib_module_names))"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
    )
    groups = make_groups(stdlib)
    group_names = [name for name, _ in groups]

    report: dict[str, dict] = {}
    for case in cases:
        if case.runner == "click":
            if not args.click_python:
                continue
            interpreter = str(Path(args.click_python).absolute())
        elif case.runner == "python":
            interpreter = python
        else:  # the typer console script is not a plain interpreter invocation
            continue
        argv = [arg.replace("{apps}", str(APPS_DIR)) for arg in case.argv]
        per_run_groups: list[dict[str, float]] = []
        per_run_modules: list[dict[str, int]] = []
        for _ in range(args.repeat):
            proc = subprocess.run(
                [interpreter, "-X", "importtime", *argv],
                env=clean_env(case.env),
                cwd=cwd,
                input=case.stdin.encode() if case.stdin else None,
                stdin=None if case.stdin else subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                check=False,
            )
            rows = parse_importtime(proc.stderr.decode(errors="replace"))
            sums: dict[str, float] = defaultdict(float)
            modules: dict[str, int] = {}
            for module, self_us in rows:
                modules[module] = modules.get(module, 0) + self_us
                for name, matches in groups:
                    if matches(module):
                        sums[name] += self_us / 1000
                        break
            per_run_groups.append(sums)
            per_run_modules.append(modules)
        medians = {
            name: statistics.median(run.get(name, 0.0) for run in per_run_groups)
            for name in group_names
        }
        medians["total"] = statistics.median(
            sum(run.values()) for run in per_run_groups
        )
        all_modules = set().union(*per_run_modules)
        module_medians = {
            m: statistics.median(run.get(m, 0) for run in per_run_modules) / 1000
            for m in all_modules
        }
        top = sorted(module_medians.items(), key=lambda kv: kv[1], reverse=True)
        report[case.id] = {
            "title": case.title,
            "groups_ms": {k: round(v, 2) for k, v in medians.items()},
            "modules_imported": statistics.median(len(m) for m in per_run_modules),
            "top_modules_ms": [(m, round(ms, 2)) for m, ms in top[: args.top]],
        }
        print(f"{case.id}: {medians['total']:.1f} ms of import self-time")

    # Markdown: one column per group that is non-zero somewhere.
    used = [
        g
        for g in group_names
        if any(r["groups_ms"][g] >= 0.05 for r in report.values())
    ]
    lines = [
        f"# Import-time attribution: {args.label}",
        "",
        f"Median over {args.repeat} runs of the summed `-X importtime` self time, in ms.",
        "",
        "| Case | Modules | " + " | ".join(used) + " | Total |",
        "|---|---:|" + "---:|" * len(used) + "---:|",
    ]
    for case_id, r in report.items():
        cells = " | ".join(f"{r['groups_ms'][g]:.1f}" for g in used)
        lines.append(
            f"| `{case_id}` | {r['modules_imported']:.0f} | {cells} | "
            f"{r['groups_ms']['total']:.1f} |"
        )
    if args.top:
        lines += ["", f"## Slowest {args.top} modules per case (self time, ms)", ""]
        for case_id, r in report.items():
            top_str = ", ".join(f"`{m}` {ms:.1f}" for m, ms in r["top_modules_ms"])
            lines.append(f"- `{case_id}`: {top_str}")
    markdown = "\n".join(lines) + "\n"
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"imports-{args.label}.json").write_text(
        json.dumps(report, indent=1) + "\n"
    )
    (args.out / f"imports-{args.label}.md").write_text(markdown)
    print(markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
