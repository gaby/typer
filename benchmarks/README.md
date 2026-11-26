# CLI start-up benchmarks

Tools to measure how long a Typer CLI takes to start and run a command, and
where that time goes. The findings are in [REPORT.md](REPORT.md).

## What is measured

Every case is a real process launch (`python app.py ARGS`), the way a user
runs a CLI. The apps in [`apps/`](apps) cover the basic parameter and argument
use cases (`str` arguments, `int`/`float`/`bool` options, `Enum`, `Literal`,
`Path`, `datetime`, lists, environment variables, prompts), several app shapes
(`typer.run`, one or two commands, nested sub-apps, a 50-command app, the
`typer` runner command), `--help` output, and error messages. There are also
baselines: `python -c pass`, `import typer`, and the same app written with
argparse and with upstream Click.

Each run records two numbers:

* **total**: from spawning the process until it exits.
* **to callback**: from spawning the process until the command function starts
  (the apps write a timestamp when `BENCH_MARK_FILE` is set).

Before anything is timed, every case is run once and its exit code and output
are checked, so a broken case is reported as a failure rather than recorded as
a timing. Cases are then timed in shuffled, interleaved rounds (3 warm-up
rounds, 40 timed rounds by default), so machine noise spreads evenly.

## Running

Measure a regular install of Typer with only its runtime dependencies. The
development `.venv` has an editable install and extra packages, so its numbers
differ from what users get.

```console
$ python3.11 -m venv --without-pip /tmp/bench-venv
$ uv pip install --python /tmp/bench-venv/bin/python .
$ python3.11 -m venv --without-pip /tmp/click-venv
$ uv pip install --python /tmp/click-venv/bin/python click

$ python benchmarks/run_benchmarks.py --python /tmp/bench-venv/bin/python \
    --click-python /tmp/click-venv/bin/python --tty
$ python benchmarks/profile_imports.py --python /tmp/bench-venv/bin/python
$ python benchmarks/profile_inprocess.py --python /tmp/bench-venv/bin/python
$ python benchmarks/compare.py benchmarks/results/A.json benchmarks/results/B.json
```

The scripts need only the standard library, and any Python 3.11+ can run them.
`--python` selects the interpreter under test. Results go to
[`results/`](results) as JSON (with every raw sample) and Markdown.

| Script | What it does |
|---|---|
| `run_benchmarks.py` | Validates and times every case. `--only 'help/*'` filters cases, `--tty` also times help and error output on a pseudo-terminal, and `--no-bytecode` measures the first run after an install without compiled bytecode (it deletes the target's `__pycache__` dirs, so use a throwaway venv). |
| `profile_imports.py` | Runs selected cases with `-X importtime` and sums self time per package (Typer, vendored Click, Pydantic, Rich, markdown-it, Pygments, stdlib). |
| `profile_inprocess.py` | Splits one invocation into stages, measures Pydantic `TypeAdapter` cost per annotation, how `get_command` scales with app size, per-call cost inside a running process (as in tests), the cost of selected import sets, and interpreter shutdown cost. The `waterfall`, `adapters` and `import-splits` sections use Typer internals that exist only from 0.29.0 on; pick sections with `--section`. |
| `compare.py` | Puts several result files side by side. |

[`experiments/skip-none-coercion.patch`](experiments/skip-none-coercion.patch)
is the change evaluated in recommendation 1 of the report. Its A/B results are
in [`results/experiment-skip-none/`](results/experiment-skip-none). To repeat
it, apply the patch to a checkout, install that checkout into a second venv,
and run `run_benchmarks.py` against both.

## Caveats

* Absolute times depend on the machine. Compare against the `python -c pass`
  floor and the argparse and Click baselines measured in the same run.
* Output goes to `/dev/null` unless `--tty` is used. Rich renders a bit
  differently for a terminal.
* `-X importtime` adds overhead of its own, so use `profile_imports.py` for
  proportions and `run_benchmarks.py` for wall time.
