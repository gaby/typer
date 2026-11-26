"""Measure how long Typer CLI apps take to start and run a command.

Each case is a real process launch (``python app.py ARGS``), the way a user
runs a CLI. Before anything is timed, every case is run once and its exit code
and output are checked, so a broken case is reported as a failure instead of
being recorded as a timing. Cases are then timed in shuffled, interleaved
rounds so that machine noise is spread evenly across all of them.

Two numbers are recorded per run:

* ``total``: wall time from spawning the process until it exits.
* ``to callback``: wall time from spawning the process until the command
  function starts running (the apps write a timestamp when ``BENCH_MARK_FILE``
  is set). What is left (``total - to callback``) is the command body plus
  interpreter shutdown.

Usage (from the repository root):

    python benchmarks/run_benchmarks.py --python /path/to/venv/bin/python

Use a virtual environment with a regular (non-editable) install of Typer and
only its runtime dependencies, so the numbers match what users get.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import math
import os
import platform
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent
APPS_DIR = BENCH_DIR / "apps"
RESULTS_DIR = BENCH_DIR / "results"
REPO_DIR = BENCH_DIR.parent

FLOOR_CASE = "baseline/python-floor"
NO_RICH = (("TYPER_USE_RICH", "0"),)


@dataclass(frozen=True)
class Case:
    id: str
    title: str
    argv: tuple[str, ...]
    # "python": the interpreter under test; "typer-cli": the `typer` console
    # script next to it; "click": the interpreter given with --click-python.
    runner: str = "python"
    expect_code: int = 0
    # Every substring must appear in the combined stdout/stderr.
    expect: tuple[str, ...] = ()
    env: tuple[tuple[str, str], ...] = ()
    stdin: str | None = None
    # Whether the command function is expected to run (and write its mark).
    reaches_callback: bool = True
    # Also measured under a pseudo-terminal when --tty is given.
    tty: bool = False

    @property
    def group(self) -> str:
        return self.id.split("/", 1)[0]


def build_cases() -> list[Case]:
    a = "{apps}/"
    basic_run = (a + "basic.py", "World", "--count", "3", "--loud")
    many = (
        a + "many_params.py",
        "Alice",
        "--count",
        "2",
        "--ratio",
        "0.5",
        "--loud",
        "--color",
        "blue",
        "--config",
        a + "many_params.py",
        "--when",
        "2026-11-26",
        "--tag",
        "a",
        "--tag",
        "b",
        "--retries",
        "5",
        "--output",
        "result.txt",
        "-vv",
        "--dry-run",
    )
    return [
        # -- Baselines -------------------------------------------------------
        Case(
            FLOOR_CASE,
            "python -c pass (interpreter start-up floor)",
            ("-c", "pass"),
            reaches_callback=False,
        ),
        Case(
            "baseline/import-typer",
            'python -c "import typer"',
            ("-c", "import typer"),
            reaches_callback=False,
        ),
        Case(
            "baseline/argparse",
            "basic.py written with argparse (stdlib)",
            (a + "argparse_basic.py", "World", "--count", "3", "--loud"),
            expect=("HELLO WORLD",),
        ),
        Case(
            "baseline/click",
            "basic.py written with upstream Click",
            (a + "click_basic.py", "World", "--count", "3", "--loud"),
            runner="click",
            expect=("HELLO WORLD",),
        ),
        # -- Parameters and arguments (typer.run, one command) ---------------
        Case(
            "params/no-params",
            "no parameters",
            (a + "no_params.py",),
            expect=("Hello World",),
        ),
        Case(
            "params/arg-required",
            "required str argument",
            (a + "arg_required.py", "World"),
            expect=("Hello World",),
        ),
        Case(
            "params/arg-optional",
            "optional argument, default used",
            (a + "arg_optional.py",),
            expect=("Hello World",),
        ),
        Case(
            "params/opt-required",
            "required str option",
            (a + "opt_required.py", "--name", "Alice"),
            expect=("Hello Alice",),
        ),
        Case(
            "params/opt-int",
            "int option",
            (a + "opt_int.py", "--count", "3"),
            expect=("Count: 3",),
        ),
        Case(
            "params/opt-int-range",
            "int option with min/max",
            (a + "opt_int_range.py", "--retries", "7"),
            expect=("Retries: 7",),
        ),
        Case(
            "params/opt-float",
            "float option",
            (a + "opt_float.py", "--ratio", "0.25"),
            expect=("Ratio: 0.25",),
        ),
        Case(
            "params/opt-bool",
            "bool flag",
            (a + "opt_bool.py", "--force"),
            expect=("Force: True",),
        ),
        Case(
            "params/opt-enum",
            "Enum choice",
            (a + "opt_enum.py", "--color", "blue"),
            expect=("Color: blue",),
        ),
        Case(
            "params/opt-literal",
            "Literal choice",
            (a + "opt_literal.py", "--level", "high"),
            expect=("Level: high",),
        ),
        Case(
            "params/opt-path",
            "Path option, file must exist",
            (a + "opt_path.py", "--config", a + "opt_path.py"),
            expect=("Config: opt_path.py",),
        ),
        Case(
            "params/opt-datetime",
            "datetime option",
            (a + "opt_datetime.py", "--when", "2026-11-26T10:30:00"),
            expect=("When: 2026-11-26T10:30:00",),
        ),
        Case(
            "params/opt-list",
            "repeated list option (x3)",
            (a + "opt_list.py", "--tag", "a", "--tag", "b", "--tag", "c"),
            expect=("Tags: a, b, c",),
        ),
        Case(
            "params/opt-envvar",
            "option read from an env var",
            (a + "opt_envvar.py",),
            env=(("APP_API_URL", "https://example.invalid/api"),),
            expect=("API: https://example.invalid/api",),
        ),
        Case(
            "params/opt-prompt",
            "option prompted on stdin",
            (a + "opt_prompt.py",),
            stdin="Alice\n",
            expect=("Hello Alice",),
        ),
        Case(
            "params/many-params",
            "12 mixed parameters, all given",
            many,
            expect=("Hello Alice x2", "verbose=2", "dry_run=True"),
        ),
        # -- App shapes ------------------------------------------------------
        Case(
            "shape/typer-run",
            "typer.run(main): arg + int option + bool flag",
            basic_run,
            expect=("HELLO WORLD",),
        ),
        Case(
            "shape/app-1-command",
            "Typer() app, 1 command (same params)",
            (a + "basic_app.py", "World", "--count", "3", "--loud"),
            expect=("HELLO WORLD",),
        ),
        Case(
            "shape/app-1-command-no-completion",
            "Typer(add_completion=False), 1 command",
            (a + "basic_app_nocomp.py", "World", "--count", "3", "--loud"),
            expect=("HELLO WORLD",),
        ),
        Case(
            "shape/app-2-commands",
            "Typer() app, 2 commands, run one",
            (a + "multi_commands.py", "hello", "World"),
            expect=("Hello World",),
        ),
        Case(
            "shape/nested-sub-app",
            "nested sub-apps: users create NAME",
            (a + "nested.py", "users", "create", "Alice", "--admin"),
            expect=("Created user Alice (admin)",),
        ),
        Case(
            "shape/app-50-commands",
            "Typer() app, 50 commands x 3 params, run one",
            (a + "scale_commands.py", "cmd25", "World", "--count", "2"),
            expect=("cmd25: World x2",),
        ),
        Case(
            "shape/typer-command",
            "`typer basic.py run ...` (the typer runner CLI)",
            ("{apps}/basic.py", "run", "World", "--count", "3", "--loud"),
            runner="typer-cli",
            expect=("HELLO WORLD",),
        ),
        # -- Help output -----------------------------------------------------
        Case(
            "help/typer-run",
            "basic.py --help (Rich)",
            (a + "basic.py", "--help"),
            expect=("Usage:", "--count"),
            reaches_callback=False,
            tty=True,
        ),
        Case(
            "help/typer-run-no-rich",
            "basic.py --help, TYPER_USE_RICH=0",
            (a + "basic.py", "--help"),
            env=NO_RICH,
            expect=("Usage:", "--count"),
            reaches_callback=False,
            tty=True,
        ),
        Case(
            "help/app-root",
            "multi_commands.py --help (Rich)",
            (a + "multi_commands.py", "--help"),
            expect=("Usage:", "hello", "goodbye"),
            reaches_callback=False,
            tty=True,
        ),
        Case(
            "help/app-root-no-rich",
            "multi_commands.py --help, TYPER_USE_RICH=0",
            (a + "multi_commands.py", "--help"),
            env=NO_RICH,
            expect=("Usage:", "hello", "goodbye"),
            reaches_callback=False,
            tty=True,
        ),
        Case(
            "help/subcommand",
            "nested.py users create --help (Rich)",
            (a + "nested.py", "users", "create", "--help"),
            expect=("Usage:", "--admin"),
            reaches_callback=False,
        ),
        Case(
            "help/app-50-commands",
            "scale_commands.py --help (Rich, 50 commands)",
            (a + "scale_commands.py", "--help"),
            expect=("Usage:", "cmd49"),
            reaches_callback=False,
        ),
        Case(
            "help/argparse",
            "argparse_basic.py --help (stdlib)",
            (a + "argparse_basic.py", "--help"),
            expect=("usage:", "--count"),
            reaches_callback=False,
        ),
        # -- Errors ----------------------------------------------------------
        Case(
            "error/missing-argument",
            "basic.py with no args (Rich)",
            (a + "basic.py",),
            expect_code=2,
            expect=("Missing argument",),
            reaches_callback=False,
            tty=True,
        ),
        Case(
            "error/missing-argument-no-rich",
            "basic.py with no args, TYPER_USE_RICH=0",
            (a + "basic.py",),
            env=NO_RICH,
            expect_code=2,
            expect=("Missing argument",),
            reaches_callback=False,
            tty=True,
        ),
        Case(
            "error/bad-int",
            "basic.py World --count abc (Rich)",
            (a + "basic.py", "World", "--count", "abc"),
            expect_code=2,
            expect=("Invalid value for '--count'",),
            reaches_callback=False,
            tty=True,
        ),
        Case(
            "error/bad-int-no-rich",
            "basic.py World --count abc, TYPER_USE_RICH=0",
            (a + "basic.py", "World", "--count", "abc"),
            env=NO_RICH,
            expect_code=2,
            expect=("Invalid value for '--count'",),
            reaches_callback=False,
            tty=True,
        ),
        Case(
            "error/argparse-bad-int",
            "argparse_basic.py World --count abc (stdlib)",
            (a + "argparse_basic.py", "World", "--count", "abc"),
            expect_code=2,
            expect=("invalid int value",),
            reaches_callback=False,
        ),
    ]


# -- Running processes ---------------------------------------------------------


@dataclass
class RunResult:
    code: int
    output: str
    total_ms: float
    callback_ms: float | None


def clean_env(extra: tuple[tuple[str, str], ...] = ()) -> dict[str, str]:
    """A minimal environment: nothing Typer, Rich or Python-specific leaks in.

    In particular this drops the test-suite settings (TERMINAL_WIDTH,
    _TYPER_FORCE_DISABLE_TERMINAL), FORCE_COLOR/NO_COLOR, CI variables,
    PYTHONPATH and PYTHONUNBUFFERED.
    """
    env = {
        key: os.environ[key]
        for key in ("PATH", "HOME", "USER", "LOGNAME", "TMPDIR")
        if key in os.environ
    }
    env["LANG"] = "C.UTF-8"
    env["TERM"] = "xterm-256color"
    env.update(extra)
    return env


def run_process(
    cmd: list[str],
    env: dict[str, str],
    cwd: Path,
    mark_file: Path,
    *,
    stdin: str | None = None,
    capture: bool = False,
    tty: bool = False,
) -> RunResult:
    mark_file.unlink(missing_ok=True)
    env = {**env, "BENCH_MARK_FILE": str(mark_file)}
    if tty:
        code, output, total_ns, t0_wall = _run_in_pty(cmd, env, cwd)
    else:
        sink = subprocess.PIPE if capture else subprocess.DEVNULL
        t0_wall = time.time_ns()
        t0 = time.perf_counter_ns()
        proc = subprocess.run(
            cmd,
            env=env,
            cwd=cwd,
            input=stdin.encode() if stdin is not None else None,
            stdin=None if stdin is not None else subprocess.DEVNULL,
            stdout=sink,
            stderr=subprocess.STDOUT if capture else subprocess.DEVNULL,
            check=False,
        )
        total_ns = time.perf_counter_ns() - t0
        code = proc.returncode
        output = proc.stdout.decode(errors="replace") if capture else ""
    callback_ms = None
    if mark_file.exists():
        callback_ms = (int(mark_file.read_text()) - t0_wall) / 1e6
    return RunResult(code, output, total_ns / 1e6, callback_ms)


def _run_in_pty(
    cmd: list[str], env: dict[str, str], cwd: Path
) -> tuple[int, str, int, int]:
    """Run with stdout/stderr attached to a pseudo-terminal (100x40)."""
    import fcntl
    import pty
    import struct
    import termios

    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 100, 0, 0))
    chunks: list[bytes] = []
    t0_wall = time.time_ns()
    t0 = time.perf_counter_ns()
    proc = subprocess.Popen(
        cmd,
        env=env,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=slave,
        stderr=slave,
        close_fds=True,
    )
    os.close(slave)
    while True:
        try:
            data = os.read(master, 65536)
        except OSError:  # EIO: the child closed the terminal
            break
        if not data:
            break
        chunks.append(data)
    code = proc.wait()
    total_ns = time.perf_counter_ns() - t0
    os.close(master)
    return code, b"".join(chunks).decode(errors="replace"), total_ns, t0_wall


def strip_ansi(text: str) -> str:
    import re

    text = re.sub(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)", "", text)
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)


# -- Target environment --------------------------------------------------------

PROBE = r"""
import importlib.metadata as md, json, platform, sys, sysconfig
info = {
    "python": platform.python_version(),
    "implementation": platform.python_implementation(),
    "executable": sys.executable,
    "purelib": sysconfig.get_paths()["purelib"],
    "packages": {},
}
for name in ("typer", "pydantic", "pydantic-core", "rich", "shellingham",
             "annotated-doc", "markdown-it-py", "pygments", "click",
             "typing-extensions"):
    try:
        info["packages"][name] = md.version(name)
    except md.PackageNotFoundError:
        pass
try:
    import typer
    info["typer_file"] = typer.__file__
except ImportError:
    info["typer_file"] = None
print(json.dumps(info))
"""


def probe_interpreter(python: str, cwd: Path) -> dict:
    out = subprocess.run(
        [python, "-c", PROBE],
        env=clean_env(),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout)


def machine_info() -> dict:
    cpu = platform.processor() or ""
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    commit = None
    try:
        commit = subprocess.run(
            ["git", "-C", str(REPO_DIR), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        pass
    return {
        "platform": platform.platform(),
        "cpu": cpu,
        "cpu_count": os.cpu_count(),
        "repo_commit": commit,
    }


def purge_bytecode(purelib: str) -> int:
    removed = 0
    for cache_dir in Path(purelib).rglob("__pycache__"):
        shutil.rmtree(cache_dir, ignore_errors=True)
        removed += 1
    return removed


# -- Statistics and output -----------------------------------------------------


def summarize(samples: list[float]) -> dict[str, float | int]:
    s = sorted(samples)
    n = len(s)
    return {
        "n": n,
        "min": s[0],
        "median": statistics.median(s),
        "mean": statistics.fmean(s),
        "stdev": statistics.stdev(s) if n > 1 else 0.0,
        "p95": s[max(0, math.ceil(0.95 * n) - 1)],
        "max": s[-1],
    }


def render_markdown(result: dict) -> str:
    meta = result["meta"]
    target = meta["target"]
    pkgs = ", ".join(f"{k} {v}" for k, v in sorted(target["packages"].items()))
    lines = [
        f"# Typer CLI timings: {meta['label']}",
        "",
        f"- Python {target['python']} ({target['implementation']}), {pkgs}",
        f"- {meta['machine']['cpu']} x{meta['machine']['cpu_count']}, "
        f"{meta['machine']['platform']}",
        *(
            [
                f"- Click baseline: click {meta['click_baseline']['click']} on "
                f"Python {meta['click_baseline']['python']}"
            ]
            if meta.get("click_baseline")
            else []
        ),
        f"- {meta['samples']} timed runs per case after {meta['warmup']} warm-up "
        f"runs, interleaved in shuffled rounds (seed {meta['seed']})"
        + (", bytecode cache disabled" if meta["no_bytecode"] else ""),
        f"- Load average before/after: {meta['loadavg_before']} / "
        f"{meta['loadavg_after']}",
        "",
        "Times in milliseconds. Δ is the median over the `python -c pass` floor. "
        "'To callback' is the median time until the command function starts.",
        "",
        "| Case | Description | Median | Δ floor | Min | p95 | To callback |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    floor = result["cases"].get(FLOOR_CASE, {}).get("total")
    for case_id, data in result["cases"].items():
        if data.get("status") != "ok":
            lines.append(
                f"| `{case_id}` | {data['title']} | {data.get('status')} | | | | |"
            )
            continue
        total = data["total"]
        delta = f"+{total['median'] - floor['median']:.1f}" if floor else ""
        cb = data.get("to_callback")
        cb_str = f"{cb['median']:.1f}" if cb else ""
        lines.append(
            f"| `{case_id}` | {data['title']} | {total['median']:.1f} | {delta} | "
            f"{total['min']:.1f} | {total['p95']:.1f} | {cb_str} |"
        )
    failures = [
        (cid, d) for cid, d in result["cases"].items() if d.get("status") == "failed"
    ]
    if failures:
        lines += ["", "## Failed validation", ""]
        for cid, d in failures:
            lines += [f"### `{cid}`", "", "```", d["detail"][-2000:], "```", ""]
    return "\n".join(lines) + "\n"


# -- Main ------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--python",
        required=True,
        help="Interpreter of the virtual environment under test.",
    )
    parser.add_argument(
        "--click-python",
        help="Interpreter with upstream click installed (for baseline/click).",
    )
    parser.add_argument("--label", help="Name for the result files.")
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20261126)
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="GLOB",
        help="Only run cases whose id matches (repeatable), e.g. 'help/*'.",
    )
    parser.add_argument(
        "--tty",
        action="store_true",
        help="Also time the help and error cases under a pseudo-terminal.",
    )
    parser.add_argument(
        "--no-bytecode",
        action="store_true",
        help=(
            "Delete the target's site-packages __pycache__ dirs and run with "
            "PYTHONDONTWRITEBYTECODE=1 (first run after an install without "
            "bytecode compilation). Modifies the target venv: use a throwaway one."
        ),
    )
    parser.add_argument("--out", type=Path, default=RESULTS_DIR)
    parser.add_argument("--list", action="store_true", help="List cases and exit.")
    args = parser.parse_args()

    cases = build_cases()
    if args.only:
        cases = [
            c for c in cases if any(fnmatch.fnmatch(c.id, pat) for pat in args.only)
        ]
    if args.list:
        for c in cases:
            print(f"{c.id:40} {c.title}")
        return 0

    python = str(Path(args.python).absolute())
    typer_cli = str(Path(python).parent / "typer")
    workdir = Path(tempfile.mkdtemp(prefix="typer-bench-"))
    mark_file = workdir / "mark"
    cwd = workdir / "cwd"
    cwd.mkdir()

    target = probe_interpreter(python, cwd)
    typer_file = target.pop("typer_file")
    if typer_file is None:
        parser.error(f"Typer is not importable with {python}")
    from_checkout = Path(typer_file).resolve().is_relative_to(REPO_DIR)
    target["typer_imported_from"] = "checkout" if from_checkout else "site-packages"
    if from_checkout:
        print(
            "warning: Typer is imported from this checkout (editable install?); "
            "numbers will not match a regular install.",
            file=sys.stderr,
        )
    purelib = target.pop("purelib")
    target.pop("executable")
    click_target = None
    if args.click_python:
        click_info = probe_interpreter(str(Path(args.click_python).absolute()), cwd)
        click_target = {
            "python": click_info["python"],
            "click": click_info["packages"].get("click"),
        }
    label = args.label or (
        f"typer-{target['packages'].get('typer', 'unknown')}-py{target['python']}"
    )
    base_env: tuple[tuple[str, str], ...] = ()
    if args.no_bytecode:
        removed = purge_bytecode(purelib)
        print(f"Removed {removed} __pycache__ dirs from {purelib}")
        base_env = (("PYTHONDONTWRITEBYTECODE", "1"),)

    def command_for(case: Case) -> list[str] | None:
        argv = [arg.replace("{apps}", str(APPS_DIR)) for arg in case.argv]
        if case.runner == "python":
            return [python, *argv]
        if case.runner == "typer-cli":
            return [typer_cli, *argv]
        if case.runner == "click":
            if not args.click_python:
                return None
            return [str(Path(args.click_python).absolute()), *argv]
        raise ValueError(case.runner)

    # Variants: (case, tty)
    variants: list[tuple[Case, bool]] = []
    for case in cases:
        variants.append((case, False))
        if args.tty and case.tty:
            variants.append((case, True))

    def variant_id(case: Case, tty: bool) -> str:
        return f"{case.id} [tty]" if tty else case.id

    results: dict[str, dict] = {}
    runnable: list[tuple[Case, bool, list[str]]] = []
    print(f"Validating {len(variants)} cases with {python} ...")
    for case, tty in variants:
        vid = variant_id(case, tty)
        entry: dict = {"title": case.title + (" [tty]" if tty else "")}
        results[vid] = entry
        cmd = command_for(case)
        if cmd is None:
            entry["status"] = "skipped (no --click-python)"
            continue
        entry["argv"] = [case.runner, *case.argv]
        if case.env:
            entry["env"] = dict(case.env)
        env = clean_env(base_env + case.env)
        run = run_process(
            cmd, env, cwd, mark_file, stdin=case.stdin, capture=True, tty=tty
        )
        output = strip_ansi(run.output)
        problems = []
        if run.code != case.expect_code:
            problems.append(f"exit code {run.code}, expected {case.expect_code}")
        problems += [f"missing {s!r} in output" for s in case.expect if s not in output]
        if case.reaches_callback and run.callback_ms is None:
            problems.append("the command function did not run (no mark)")
        if problems:
            entry["status"] = "failed"
            entry["detail"] = "; ".join(problems) + "\n--- output ---\n" + output
            print(f"  FAIL {vid}: {'; '.join(problems)}")
            continue
        entry["status"] = "ok"
        runnable.append((case, tty, cmd))

    rng = random.Random(args.seed)
    samples: dict[str, list[RunResult]] = {variant_id(c, t): [] for c, t, _ in runnable}
    loadavg_before = [round(x, 2) for x in os.getloadavg()]
    rounds = args.warmup + args.samples
    print(f"Timing {len(runnable)} cases x {rounds} rounds ({args.warmup} warm-up) ...")
    for round_no in range(rounds):
        order = list(runnable)
        rng.shuffle(order)
        for case, tty, cmd in order:
            env = clean_env(base_env + case.env)
            run = run_process(cmd, env, cwd, mark_file, stdin=case.stdin, tty=tty)
            if run.code != case.expect_code:
                raise RuntimeError(f"{case.id}: exit code changed to {run.code}")
            if round_no >= args.warmup:
                samples[variant_id(case, tty)].append(run)
        print(f"  round {round_no + 1}/{rounds}", end="\r", flush=True)
    print()
    loadavg_after = [round(x, 2) for x in os.getloadavg()]

    for vid, runs in samples.items():
        totals = [r.total_ms for r in runs]
        results[vid]["total"] = summarize(totals)
        results[vid]["samples_total_ms"] = [round(x, 3) for x in totals]
        callbacks = [r.callback_ms for r in runs if r.callback_ms is not None]
        if callbacks:
            results[vid]["to_callback"] = summarize(callbacks)
            results[vid]["samples_to_callback_ms"] = [round(x, 3) for x in callbacks]

    result = {
        "meta": {
            "label": label,
            "samples": args.samples,
            "warmup": args.warmup,
            "seed": args.seed,
            "tty": args.tty,
            "no_bytecode": args.no_bytecode,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "machine": machine_info(),
            "target": target,
            "click_baseline": click_target,
            "loadavg_before": loadavg_before,
            "loadavg_after": loadavg_after,
        },
        "cases": results,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    json_path = args.out / f"{label}.json"
    md_path = args.out / f"{label}.md"
    json_path.write_text(json.dumps(result, indent=1) + "\n")
    md_path.write_text(render_markdown(result))
    print(render_markdown(result))
    print(f"Wrote {json_path} and {md_path}")
    shutil.rmtree(workdir, ignore_errors=True)
    failed = [vid for vid, d in results.items() if d.get("status") == "failed"]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
