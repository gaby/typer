"""Break Typer's start-up cost down into stages and components.

Sections (all run with the interpreter under test, in fresh processes unless
noted):

* ``waterfall``: where the time of one CLI invocation goes: interpreter
  start, ``import typer``, the app module body, building the Click command
  (``get_command``), parsing and Pydantic validation, the command body and
  interpreter shutdown.
* ``adapters``: what Typer's Pydantic-based validation costs per annotation:
  the import, the first ``TypeAdapter`` built in a process, and later ones.
* ``get-command``: how building the command tree scales with the number of
  commands and parameters (in-process, steady state).
* ``warm-invoke``: per-invocation cost inside an already-running process, as
  in a test suite using ``CliRunner`` (in-process, steady state).
* ``import-splits``: wall time of importing selected sets of modules, to size
  what lazy imports could save.
* ``shutdown``: how long interpreter shutdown takes once Typer, Pydantic or
  Rich are loaded, measured as the wall-time difference between a normal exit
  and ``os._exit()`` (which skips finalization), plus ``gc.freeze()``.

Usage (from the repository root):

    python benchmarks/profile_inprocess.py --python /path/to/venv/bin/python
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from run_benchmarks import APPS_DIR, RESULTS_DIR, clean_env

# -- waterfall -----------------------------------------------------------------

WATERFALL_DRIVER = r"""
import os, sys, time
t_driver = time.time_ns()
t_import_start = t_driver
import typer, typer.core, typer.main
t_import = time.time_ns()
# Imported after typer, so they do not pre-load modules typer needs.
import json, runpy
stats = {"get_command_ns": 0, "get_command_start": None, "get_command_end": None,
         "adapters_ns": 0, "adapters": 0, "first_adapter_ns": None}
_get_command = typer.main.get_command
def get_command(app):
    start = time.time_ns()
    if stats["get_command_start"] is None:
        stats["get_command_start"] = start
    try:
        return _get_command(app)
    finally:
        end = time.time_ns()
        stats["get_command_ns"] += end - start
        stats["get_command_end"] = end
typer.main.get_command = get_command
_build = typer.core.build_runtime_param
def build_runtime_param(descriptor):
    start = time.time_ns()
    try:
        return _build(descriptor)
    finally:
        elapsed = time.time_ns() - start
        if stats["first_adapter_ns"] is None:
            stats["first_adapter_ns"] = elapsed
        stats["adapters_ns"] += elapsed
        stats["adapters"] += 1
typer.core.build_runtime_param = build_runtime_param
script, *argv = sys.argv[1:]
sys.argv = [script, *argv]
t_run = time.time_ns()
code = 0
try:
    runpy.run_path(script, run_name="__main__")
except SystemExit as exc:
    code = exc.code
stats.update(t_driver=t_driver, t_import_start=t_import_start, t_import=t_import,
             t_run=t_run, t_exit=time.time_ns(),
             pydantic_loaded="pydantic" in sys.modules, rich_loaded="rich" in sys.modules)
with open(os.environ["BENCH_STAGES_FILE"], "w") as f:
    json.dump(stats, f)
sys.exit(code)
"""

WATERFALL_CASES = (
    ("no_params.py", ()),
    ("basic.py", ("World", "--count", "3", "--loud")),
    ("multi_commands.py", ("hello", "World")),
    ("scale_commands.py", ("cmd25", "World", "--count", "2")),
    ("basic.py", ("--help",)),
)


def run_waterfall(python: str, cwd: Path, repeat: int) -> list[dict]:
    out = []
    workdir = Path(tempfile.mkdtemp(prefix="typer-waterfall-"))
    driver = workdir / "driver.py"
    driver.write_text(WATERFALL_DRIVER)
    stages_file = workdir / "stages.json"
    mark_file = workdir / "mark"
    for script, argv in WATERFALL_CASES:
        runs = []
        for i in range(repeat + 2):
            mark_file.unlink(missing_ok=True)
            env = clean_env(
                (
                    ("BENCH_STAGES_FILE", str(stages_file)),
                    ("BENCH_MARK_FILE", str(mark_file)),
                )
            )
            t_spawn = time.time_ns()
            subprocess.run(
                [python, str(driver), str(APPS_DIR / script), *argv],
                env=env,
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            t_end = time.time_ns()
            if i < 2:  # warm-up
                continue
            s = json.loads(stages_file.read_text())
            t_mark = int(mark_file.read_text()) if mark_file.exists() else None
            ms = 1e6
            stage = {
                "interpreter start": (s["t_driver"] - t_spawn) / ms,
                "import typer": (s["t_import"] - s["t_import_start"]) / ms,
                "app module body": (s["get_command_start"] - s["t_run"]) / ms,
                "build command (get_command)": s["get_command_ns"] / ms,
            }
            if t_mark is not None:
                stage["parse + validate params"] = (t_mark - s["get_command_end"]) / ms
                stage["command body + exit"] = (s["t_exit"] - t_mark) / ms
            else:
                stage["parse + render help"] = (s["t_exit"] - s["get_command_end"]) / ms
            stage["interpreter shutdown"] = (t_end - s["t_exit"]) / ms
            stage["(other: driver overhead)"] = (t_end - t_spawn) / ms - sum(
                stage.values()
            )
            stage["TOTAL"] = (t_end - t_spawn) / ms
            stage["  of which Pydantic adapters"] = s["adapters_ns"] / ms
            stage["  of which first adapter (incl. Pydantic import)"] = (
                s["first_adapter_ns"] or 0
            ) / ms
            runs.append((stage, s["adapters"], s["pydantic_loaded"], s["rich_loaded"]))
        medians = {
            key: statistics.median(run[0][key] for run in runs) for key in runs[0][0]
        }
        out.append(
            {
                "case": f"{script} {' '.join(argv)}".strip(),
                "stages_ms": {k: round(v, 2) for k, v in medians.items()},
                "adapters_built": runs[0][1],
                "pydantic_loaded": runs[0][2],
                "rich_loaded": runs[0][3],
            }
        )
        print(f"waterfall {out[-1]['case']}: {medians['TOTAL']:.1f} ms")
    return out


# -- adapters ------------------------------------------------------------------

ADAPTER_DRIVER = r"""
import json, sys, time
t0 = time.perf_counter_ns()
import typer
from typer._coercion import resolve_type_descriptor, build_runtime_param
from typer.models import OptionInfo
t1 = time.perf_counter_ns()
import pydantic, typer._adapters
t2 = time.perf_counter_ns()
{setup}
annotation = {annotation}
info = {info}
t3 = time.perf_counter_ns()
build_runtime_param(resolve_type_descriptor(annotation, info))
t4 = time.perf_counter_ns()
n = 200
for _ in range(n):
    build_runtime_param(resolve_type_descriptor(annotation, info))
t5 = time.perf_counter_ns()
print(json.dumps({{
    "import_typer_ms": (t1 - t0) / 1e6,
    "import_pydantic_ms": (t2 - t1) / 1e6,
    "first_build_ms": (t4 - t3) / 1e6,
    "warm_build_us": (t5 - t4) / n / 1e3,
}}))
"""

ADAPTER_SPECS = (
    ("bool (also --help, completion flags)", "", "bool", "OptionInfo()"),
    ("str", "", "str", "OptionInfo()"),
    ("int", "", "int", "OptionInfo()"),
    ("int with min/max", "", "int", "OptionInfo(min=0, max=10)"),
    ("float", "", "float", "OptionInfo()"),
    (
        "Enum",
        "from enum import StrEnum\nclass Color(StrEnum):\n    red = 'red'\n    blue = 'blue'",
        "Color",
        "OptionInfo()",
    ),
    (
        "Literal",
        "from typing import Literal",
        "Literal['low', 'medium', 'high']",
        "OptionInfo()",
    ),
    ("Path", "from pathlib import Path", "Path", "OptionInfo()"),
    (
        "Path, exists=True",
        "from pathlib import Path",
        "Path",
        "OptionInfo(exists=True)",
    ),
    ("datetime", "from datetime import datetime", "datetime", "OptionInfo()"),
    ("UUID", "from uuid import UUID", "UUID", "OptionInfo()"),
    ("list[str]", "", "list[str]", "OptionInfo()"),
    ("tuple[str, int]", "", "tuple[str, int]", "OptionInfo()"),
)


def run_adapters(python: str, cwd: Path, repeat: int) -> list[dict]:
    out = []
    for label, setup, annotation, info in ADAPTER_SPECS:
        code = ADAPTER_DRIVER.format(setup=setup, annotation=annotation, info=info)
        runs = []
        for _ in range(repeat):
            proc = subprocess.run(
                [python, "-c", code],
                env=clean_env(),
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
            runs.append(json.loads(proc.stdout))
        row = {"annotation": label}
        for key in runs[0]:
            row[key] = round(statistics.median(r[key] for r in runs), 3)
        out.append(row)
        print(f"adapter {label}: first {row['first_build_ms']:.2f} ms")
    return out


# -- get-command ---------------------------------------------------------------

GET_COMMAND_DRIVER = r"""
import json, statistics, sys, time
import typer
from typer.main import get_command

def make_app(n_commands, n_params):
    kinds = ("int = 1", "str = 'x'", "bool = False")
    params = ", ".join(f"p{i}: {kinds[i % 3]}" for i in range(n_params))
    app = typer.Typer()
    for c in range(n_commands):
        namespace = {}
        exec(f"def cmd{c}({params}):\n    pass\n", namespace)
        app.command(name=f"cmd{c}")(namespace[f"cmd{c}"])
    return app

results = []
for n_commands, n_params in ((1, 1), (1, 3), (1, 10), (1, 30), (10, 3), (50, 3), (200, 3)):
    app = make_app(n_commands, n_params)
    get_command(app)
    times = []
    for _ in range(15):
        start = time.perf_counter_ns()
        get_command(app)
        times.append(time.perf_counter_ns() - start)
    results.append({"commands": n_commands, "params_per_command": n_params,
                    "median_ms": round(statistics.median(times) / 1e6, 3)})
print(json.dumps(results))
"""


def run_get_command(python: str, cwd: Path) -> list[dict]:
    proc = subprocess.run(
        [python, "-c", GET_COMMAND_DRIVER],
        env=clean_env(),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    result = json.loads(proc.stdout)
    print("get-command:", result)
    return result


# -- warm-invoke ---------------------------------------------------------------

WARM_DRIVER = r"""
import argparse, contextlib, io, json, statistics, time
import typer
from typer.testing import CliRunner

app = typer.Typer()

@app.command()
def main(name: str, count: int = 1, loud: bool = False):
    pass

big = typer.Typer()
for c in range(50):
    namespace = {}
    exec(f"def cmd{c}(name: str, count: int = 1, force: bool = False):\n    pass\n",
         namespace)
    big.command(name=f"cmd{c:02d}")(namespace[f"cmd{c}"])

def argparse_build_and_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--loud", action=argparse.BooleanOptionalAction, default=False)
    parser.parse_args(["World", "--count", "3", "--loud"])

runner = CliRunner()
cases = {
    "Typer app(), 1 command": lambda: app(["World", "--count", "3", "--loud"],
                                          standalone_mode=False),
    "Typer app(), 50 commands": lambda: big(["cmd25", "World", "--count", "2"],
                                            standalone_mode=False),
    "CliRunner().invoke(), 1 command": lambda: runner.invoke(
        app, ["World", "--count", "3", "--loud"]),
    "argparse: build parser + parse": argparse_build_and_parse,
}
results = {}
with contextlib.redirect_stdout(io.StringIO()):
    for name, fn in cases.items():
        for _ in range(20):
            fn()
        times = []
        for _ in range(300):
            start = time.perf_counter_ns()
            fn()
            times.append(time.perf_counter_ns() - start)
        results[name] = round(statistics.median(times) / 1e3, 1)
print(json.dumps(results))
"""


def run_warm_invoke(python: str, cwd: Path) -> dict:
    proc = subprocess.run(
        [python, "-c", WARM_DRIVER],
        env=clean_env(),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    result = json.loads(proc.stdout)
    print("warm-invoke (us):", result)
    return result


# -- import-splits -------------------------------------------------------------

RICH_CORE = (
    "from rich import box; from rich.align import Align; "
    "from rich.columns import Columns; from rich.console import Console, group; "
    "from rich.emoji import Emoji; from rich.highlighter import RegexHighlighter; "
    "from rich.markup import escape; from rich.padding import Padding; "
    "from rich.panel import Panel; from rich.table import Table; "
    "from rich.text import Text; from rich.theme import Theme"
)
FIRST_ADAPTER = (
    "from typer._coercion import resolve_type_descriptor, build_runtime_param; "
    "from typer.models import OptionInfo; "
    "build_runtime_param(resolve_type_descriptor(bool, OptionInfo()))"
)
IMPORT_SPLITS = (
    ("python -c pass", "pass"),
    ("import typer", "import typer"),
    ("import typer + typer._adapters (Pydantic)", "import typer, typer._adapters"),
    ("import typer + first bool TypeAdapter", "import typer; " + FIRST_ADAPTER),
    ("import typer + typer.rich_utils", "import typer, typer.rich_utils"),
    ("Rich modules rich_utils needs, minus markdown/traceback", RICH_CORE),
    ("... + rich.markdown", RICH_CORE + "; from rich.markdown import Markdown"),
    ("... + rich.traceback", RICH_CORE + "; from rich.traceback import Traceback"),
    (
        "... + rich.markdown + rich.traceback (what rich_utils imports)",
        RICH_CORE
        + "; from rich.markdown import Markdown; from rich.traceback import Traceback",
    ),
)


def run_import_splits(python: str, cwd: Path, repeat: int) -> list[dict]:
    out = []
    for label, code in IMPORT_SPLITS:
        times = []
        for i in range(repeat + 2):
            start = time.perf_counter_ns()
            subprocess.run(
                [python, "-c", code],
                env=clean_env(),
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                check=True,
            )
            if i >= 2:
                times.append((time.perf_counter_ns() - start) / 1e6)
        out.append(
            {
                "what": label,
                "median_ms": round(statistics.median(times), 2),
                "min_ms": round(min(times), 2),
            }
        )
        print(f"import-split {label}: {out[-1]['median_ms']:.1f} ms")
    return out


# -- shutdown ------------------------------------------------------------------

THREE_ADAPTERS = (
    "from typer._coercion import resolve_type_descriptor, build_runtime_param\n"
    "from typer.models import OptionInfo\n"
    "for ann in (bool, str, int):\n"
    "    build_runtime_param(resolve_type_descriptor(ann, OptionInfo()))\n"
)
SHUTDOWN_STATES = (
    ("python -c pass", "pass\n"),
    ("import typer", "import typer\n"),
    ("import typer + 3 Pydantic adapters", "import typer\n" + THREE_ADAPTERS),
    ("import typer + typer.rich_utils", "import typer, typer.rich_utils\n"),
    (
        "run a 3-param command (standalone)",
        "import typer\n"
        "app = typer.Typer()\n"
        "@app.command()\n"
        "def main(name: str, count: int = 1, loud: bool = False):\n"
        "    pass\n"
        "try:\n"
        "    app(['World', '--count', '3', '--loud'])\n"
        "except SystemExit:\n"
        "    pass\n",
    ),
)
SHUTDOWN_EXITS = (
    ("normal exit", ""),
    ("os._exit(0)", "import os, sys\nsys.stdout.flush()\nos._exit(0)\n"),
    ("gc.freeze() then exit", "import gc\ngc.freeze()\n"),
)


def run_shutdown(python: str, cwd: Path, repeat: int) -> list[dict]:
    samples: dict[tuple[str, str], list[float]] = {}
    for i in range(repeat + 2):
        for state, code in SHUTDOWN_STATES:
            for exit_name, suffix in SHUTDOWN_EXITS:
                start = time.perf_counter_ns()
                subprocess.run(
                    [python, "-c", code + suffix],
                    env=clean_env(),
                    cwd=cwd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    check=True,
                )
                if i >= 2:
                    elapsed = (time.perf_counter_ns() - start) / 1e6
                    samples.setdefault((state, exit_name), []).append(elapsed)
    rows = []
    for state, _ in SHUTDOWN_STATES:
        medians = {
            exit_name: statistics.median(samples[(state, exit_name)])
            for exit_name, _ in SHUTDOWN_EXITS
        }
        row = {"state": state, **{k: round(v, 2) for k, v in medians.items()}}
        row["shutdown_ms"] = round(medians["normal exit"] - medians["os._exit(0)"], 2)
        rows.append(row)
        print(f"shutdown {state}: {row['shutdown_ms']:.1f} ms")
    return rows


# -- report --------------------------------------------------------------------


def render(result: dict) -> str:
    lines = [f"# In-process breakdown: {result['label']}", ""]
    if "waterfall" in result:
        cases = result["waterfall"]
        keys: list[str] = []
        for case in cases:
            keys += [k for k in case["stages_ms"] if k not in keys]
        lines += [
            "## Waterfall of one invocation (median ms)",
            "",
            "| Stage | " + " | ".join(f"`{c['case']}`" for c in cases) + " |",
            "|---|" + "---:|" * len(cases),
        ]
        for key in keys:
            cells = []
            for case in cases:
                value = case["stages_ms"].get(key)
                cells.append("" if value is None else f"{value:.1f}")
            name = f"**{key}**" if key == "TOTAL" else key
            lines.append(f"| {name} | " + " | ".join(cells) + " |")
        lines.append(
            "| Pydantic adapters built | "
            + " | ".join(str(c["adapters_built"]) for c in cases)
            + " |"
        )
        lines.append(
            "| Pydantic / Rich loaded | "
            + " | ".join(
                f"{'yes' if c['pydantic_loaded'] else 'no'} / "
                f"{'yes' if c['rich_loaded'] else 'no'}"
                for c in cases
            )
            + " |"
        )
        lines.append("")
    if "adapters" in result:
        lines += [
            "## Pydantic validation cost per annotation (fresh process each)",
            "",
            "| Annotation | import typer (ms) | import Pydantic + adapters module (ms) "
            "| first TypeAdapter (ms) | each later one (µs) |",
            "|---|---:|---:|---:|---:|",
        ]
        for row in result["adapters"]:
            lines.append(
                f"| {row['annotation']} | {row['import_typer_ms']:.1f} | "
                f"{row['import_pydantic_ms']:.1f} | {row['first_build_ms']:.2f} | "
                f"{row['warm_build_us']:.0f} |"
            )
        lines.append("")
    if "get_command" in result:
        lines += [
            "## Building the Click command tree (`get_command`, steady state)",
            "",
            "| Commands | Params per command | Median (ms) |",
            "|---:|---:|---:|",
        ]
        for row in result["get_command"]:
            lines.append(
                f"| {row['commands']} | {row['params_per_command']} | "
                f"{row['median_ms']:.2f} |"
            )
        lines.append("")
    if "warm_invoke" in result:
        lines += [
            "## Per-invocation cost inside a running process (median µs)",
            "",
            "| Call | Median (µs) |",
            "|---|---:|",
        ]
        for name, value in result["warm_invoke"].items():
            lines.append(f"| {name} | {value:.0f} |")
        lines.append("")
    if "import_splits" in result:
        lines += [
            "## Import sets, wall time of `python -c ...`",
            "",
            "| What | Median (ms) | Min (ms) |",
            "|---|---:|---:|",
        ]
        for row in result["import_splits"]:
            lines.append(
                f"| {row['what']} | {row['median_ms']:.1f} | {row['min_ms']:.1f} |"
            )
        lines.append("")
    if "shutdown" in result:
        exit_names = [name for name, _ in SHUTDOWN_EXITS]
        lines += [
            "## Interpreter shutdown, wall time of `python -c ...` (median ms)",
            "",
            "| State before exit | "
            + " | ".join(exit_names)
            + " | Shutdown (normal − os._exit) |",
            "|---|" + "---:|" * (len(exit_names) + 1),
        ]
        for row in result["shutdown"]:
            cells = " | ".join(f"{row[name]:.1f}" for name in exit_names)
            lines.append(f"| {row['state']} | {cells} | {row['shutdown_ms']:.1f} |")
        lines.append("")
    return "\n".join(lines)


SECTIONS = (
    "waterfall",
    "adapters",
    "get-command",
    "warm-invoke",
    "import-splits",
    "shutdown",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--python", required=True)
    parser.add_argument("--label", default="typer")
    parser.add_argument("--repeat", type=int, default=15)
    parser.add_argument(
        "--section", action="append", choices=SECTIONS, help="Default: all."
    )
    parser.add_argument("--out", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()
    python = str(Path(args.python).absolute())
    cwd = Path(tempfile.mkdtemp(prefix="typer-inprocess-"))
    sections = args.section or list(SECTIONS)
    result: dict = {"label": args.label}
    if "waterfall" in sections:
        result["waterfall"] = run_waterfall(python, cwd, args.repeat)
    if "adapters" in sections:
        result["adapters"] = run_adapters(python, cwd, max(5, args.repeat // 2))
    if "get-command" in sections:
        result["get_command"] = run_get_command(python, cwd)
    if "warm-invoke" in sections:
        result["warm_invoke"] = run_warm_invoke(python, cwd)
    if "import-splits" in sections:
        result["import_splits"] = run_import_splits(python, cwd, args.repeat)
    if "shutdown" in sections:
        result["shutdown"] = run_shutdown(python, cwd, args.repeat)
    markdown = render(result)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"inprocess-{args.label}.json").write_text(
        json.dumps(result, indent=1) + "\n"
    )
    (args.out / f"inprocess-{args.label}.md").write_text(markdown)
    print(markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
