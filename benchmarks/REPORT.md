# Typer CLI start-up performance audit

Measured on 2026-11-26 at commit `a917950` (Typer 0.29.3). Typer was installed
normally (not editable) with only its runtime dependencies: Pydantic 2.14.4
(pydantic-core 2.50.5), Rich 15.0.0, shellingham 1.5.4 and annotated-doc 0.0.7.
The main runs use Python 3.11.18; a second run uses Python 3.13.18. The machine
is a shared cloud VM with 4 vCPUs (Intel Xeon @ 2.10 GHz) running Linux.

Absolute times depend on the machine, so compare each number with the
`python -c pass` floor and the argparse and Click baselines from the same run.
Unless noted, every number is the median of 40 process launches. Run-to-run
noise on this VM is about ±10 ms (the interquartile range of a Typer case is
15–30 ms wide), so smaller differences are not meaningful.

## Summary

| Python 3.11, median of 40 runs | Total | Over the floor |
|---|---:|---:|
| `python -c pass` (interpreter floor) | 10.7 ms | — |
| The basic app (argument, `int` option, flag) written with argparse | 26.3 ms | +15.7 ms |
| The same app written with Click 8.5.1 | 46.8 ms | +36.2 ms |
| `python -c "import typer"` | 69.1 ms | +58.4 ms |
| **The same app written with Typer 0.29.3** | **164.7 ms** | **+154.0 ms** |
| Any Typer parameter case (no params up to 12 mixed params) | 161–174 ms | +151–164 ms |
| Typer 0.28.0 (before Pydantic), the same app | 72.7 ms | +60.9 ms |
| Typer `--help`, Rich (default) | 148–152 ms | +137–142 ms |
| Typer `--help` with `TYPER_USE_RICH=0` | 73–76 ms | +62–66 ms |
| Typer subcommand `--help` (`nested.py users create --help`) | 248.3 ms | +237.6 ms |
| Typer error message, Rich (missing argument or bad value) | 237–239 ms | +226–228 ms |

1. **Every Typer command costs about 165 ms. Typer's overhead (about 154 ms
   over the floor) is roughly 10 times argparse's and 4 times Click's.** The
   parameter types make no measurable difference: a command with no parameters
   costs the same as one with twelve.
2. **Pydantic accounts for about 70 ms (43%) of every run, even for a command
   with no parameters.** The built-in `--help` flag (and `--install-completion`
   and `--show-completion`) have the value `None` when not passed.
   `_TyperParameter.process_value` builds the parameter's Pydantic
   `TypeAdapter` before `RuntimeParam.coerce()` gets to return early for
   `None`. So the first parameter processed imports Pydantic and builds a
   schema whose result is thrown away. This arrived with Pydantic validation
   in 0.29.0: Typer 0.28.0 ran the same commands in about 70 ms, so every
   command run is now 88–102 ms slower (2.1–2.5×). `import typer` and root
   `--help` are unchanged.
3. **Interpreter shutdown takes about 35 ms (21%) of a run.** That's the time
   between the command function returning and the process exiting. It's about
   8 ms after a bare `import typer` and grows to 28–40 ms once Pydantic is
   loaded.
4. **`import typer` costs about 46–58 ms (28%), more than the whole Click
   app.** Most of it is standard-library modules (`inspect`/`ast`,
   `pathlib`/`urllib`, `subprocess`, `platform`, `difflib`, `uuid`, ...). Some
   of these are only needed by `typer.launch()`, typo suggestions or exception
   tracebacks.
5. **Rich adds 70–75 ms to `--help` and error messages, doubling the cost
   of `--help`.** `typer.rich_utils` imports `rich.markdown` (markdown-it-py,
   Pygments) and `rich.traceback` at module level. They're only needed for
   `rich_markup_mode="markdown"` and pretty tracebacks. Importing them lazily
   saved 33–38 ms per Rich `--help` or error message in an A/B run.
6. **The worst paths pay for both.** Subcommand `--help` is 100 ms slower than
   root `--help`, because the parent group's `None`-valued flags load Pydantic
   before the eager `--help` exits. Rich error messages (about 237 ms) load
   Pydantic and Rich.
7. **App size matters less.** All commands are built on every start, at about
   0.1 ms per command: a 50-command app adds about 8–12 ms, 200 commands about
   20 ms. Inside a running process (tests using `CliRunner`), each call
   rebuilds the command tree and the Pydantic adapters: 0.7 ms for one command,
   5.6 ms for 50 commands, against 0.2 ms for argparse.

## Recommendations

Ranked by impact for typical CLIs. None of these were applied to this branch.

1. **Don't build a `TypeAdapter` for a `None` value** (`typer/core.py:106-109`).
   `RuntimeParam.coerce()` already returns `None`, or `()` for multi-value
   parameters, without using the adapter, so `process_value` can do the same
   before calling `get_runtime_param()`. The 3-line change is in
   [`experiments/skip-none-coercion.patch`](experiments/skip-none-coercion.patch).
   It brought commands with no parameters or only flags, subcommand `--help`
   and missing-argument errors back to 0.28.0 speed, about 90 ms faster (see
   [the experiment](#experiment-skip-none-before-building-the-adapter)). The
   test suite gives the same result with and without it (1634 passed,
   29 skipped, 3 xfailed).
2. **Validate the common simple types without Pydantic.** `str`, `int`,
   `float`, `bool`, `Enum`, `Literal`, `Path`, `datetime`, `UUID` and lists of
   them cover nearly every CLI parameter. Converting these natively, and
   importing Pydantic only for annotations without a native converter, would
   remove the import (about 60 ms), the first-schema warm-up (about 12 ms) and
   much of the shutdown cost (about 20 ms) from most runs. Typer 0.28.0, which
   had no Pydantic, shows what is at stake: the same runs took about 70 ms
   instead of 165 ms.
3. **Import `rich.markdown` and `rich.traceback` lazily in
   `typer/rich_utils.py`** (lines 17 and 24), inside the functions that use
   `Markdown` and `Traceback`. The change is in
   [`experiments/lazy-rich-imports.patch`](experiments/lazy-rich-imports.patch).
   In an alternating A/B run it saved 33–38 ms (13–25%) on every Rich
   `--help` and error message (see
   [the experiment](#experiment-lazy-rich-imports)), and the test suite gives
   the same result.
4. **Defer standard-library imports used only on rare paths**: `platform` and
   `subprocess` in `typer/main.py` (used only by `launch()`), `traceback`
   (exception hook), `difflib` in `typer/core.py` (typo suggestions), and
   `uuid` in `typer/_param_types.py`. Together they account for about 8 ms
   of `import typer`'s 63 ms of `-X importtime` time.
5. **Consider caching the built Click command** for repeated in-process calls
   (`Typer.__call__` runs `get_command()` every time). This only helps test
   suites and embedding; it doesn't change CLI start-up. Low priority.

What app authors can do today:

* Set `TYPER_USE_RICH=0`, or create the app with
  `typer.Typer(rich_markup_mode=None)`. Help output and error messages then
  skip Rich entirely (checked with `-X importtime`: no Rich module is
  loaded), and `--help` drops from about 150 ms to 75 ms.
* Install with bytecode compilation (pip does this by default; for uv set
  `UV_COMPILE_BYTECODE=1` or pass `--compile-bytecode`). Without it, the first
  run compiles Typer, Pydantic and Rich from source: the basic app took
  340 ms instead of 165 ms (see below).
* There's no practical way to avoid the Pydantic cost from app code today.
  The built-in `--help` flag triggers it, and so does any non-flag parameter
  that has a value.

## Where the time goes

### One invocation, stage by stage

`profile_inprocess.py` runs an app under a small driver that timestamps each
stage (median of 15 runs, Python 3.11, ms):

| Stage | `no_params.py` | `basic.py World --count 3 --loud` | `scale_commands.py cmd25 ...` | `basic.py --help` |
|---|---:|---:|---:|---:|
| Interpreter start | 9.4 | 9.3 | 9.8 | 9.1 |
| `import typer` | 47.7 | 46.4 | 47.1 | 46.3 |
| App module body (defining commands) | 0.6 | 0.8 | 3.1 | 0.8 |
| Build the Click command (`get_command`) | 0.1 | 0.4 | 7.4 | 0.4 |
| Parse and validate parameters | 74.4 | 71.9 | 72.3 | — |
| … of which Pydantic (import + first `TypeAdapter`) | 74.0 | 70.8 | 70.7 | — |
| Parse and render help (Rich) | — | — | — | 64.5 |
| Command body | 0.1 | 0.2 | 0.3 | — |
| Interpreter shutdown | 36.6 | 35.4 | 35.3 | 30.4 |
| **Total** | **175.8** | **165.8** | **181.1** | **156.2** |
| Pydantic `TypeAdapter`s built | 1 | 3 | 6 | 0 |

The command with no parameters still builds one adapter, for the `--help`
flag. In 0.28.0 the whole run took about 70 ms, roughly what `import typer`
costs on its own today.

Comparing the time until the command function starts with the total time
shows the same split. From 0.28.0 to 0.29.3 the basic app went from 57.2 to
130.9 ms before the callback (+74 ms, Pydantic) and from 15.0 to 34.6 ms
after it (+20 ms, shutdown). argparse spends 3.9 ms after its callback and
Click 7.9 ms.

### Imports by package

`profile_imports.py` sums the `-X importtime` self time of every module by
package (median of 7 runs, Python 3.11, ms). `-X importtime` adds overhead, so
read these as proportions.

| Case | Modules | Typer | Vendored Click | Pydantic + core + deps | Rich | markdown-it | Pygments | stdlib | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `import typer` | 135 | 10.2 | 5.3 | — | — | — | — | 43.3 | 63.1 |
| basic app run | 247 | 15.0 | 4.8 | 47.8 | — | — | — | 59.5 | 131.5 |
| `--help`, Rich | 301 | 10.1 | 4.4 | — | 27.3 | 17.5 | 6.0 | 47.3 | 117.3 |
| `--help`, no Rich | 137 | 9.6 | 4.9 | — | — | — | — | 44.6 | 61.6 |
| subcommand `--help`, Rich | 398 | 18.4 | 5.5 | 46.7 | 28.2 | 16.4 | 5.4 | 67.3 | 192.3 |
| bad value error, Rich | 398 | 16.1 | 5.0 | 46.2 | 29.5 | 17.2 | 5.5 | 67.2 | 188.4 |

For comparison, the whole argparse app imports 56 modules (17.1 ms), and the
Click app 84 modules (35.5 ms, 6.3 ms of it in Click itself).
On Typer 0.28.0 a command run imports 133 modules, essentially the same
set as `import typer` (132). On 0.29.3 it imports 247: the extra ones are
Pydantic and its dependencies (about 48 ms of self time) plus the
standard-library modules they need (about 16 ms).

### Pydantic cost per annotation

Each annotation was measured in a fresh process: the import, then the first
`TypeAdapter`, then the average of 200 more (Python 3.11, median of 7 runs).

| Annotation | Import Pydantic + `typer._adapters` | First `TypeAdapter` | Each later one |
|---|---:|---:|---:|
| `bool` (also `--help` and the completion flags) | 63.2 ms | 11.8 ms | 66 µs |
| `str` | 61.4 ms | 11.5 ms | 66 µs |
| `int` / `float` | 59.8 / 58.2 ms | 11.4 / 11.6 ms | 28 / 29 µs |
| `int` with `min`/`max` | 60.9 ms | 11.8 ms | 119 µs |
| `Enum` / `Literal` | 57.6 / 60.2 ms | 11.1 / 11.7 ms | 87 / 89 µs |
| `Path` / `Path(exists=True)` | 60.9 / 57.5 ms | 12.1 / 12.0 ms | 88 / 91 µs |
| `datetime` / `UUID` | 63.7 / 62.8 ms | 11.9 / 11.5 ms | 28 / 35 µs |
| `list[str]` / `tuple[str, int]` | 68.1 / 58.9 ms | 14.3 / 12.4 ms | 179 / 198 µs |

The cost is the import plus the first schema build, about 70 ms, paid once
per process whatever the types. Each additional parameter adds only
0.03–0.2 ms, which is why the parameter cases are indistinguishable.

### Rich

Wall time of importing the Rich modules `typer.rich_utils` uses (median of
15 runs):

| Import | Median |
|---|---:|
| `rich.console`, `panel`, `table`, `text`, `theme`, … (everything except the two below) | 61.0 ms |
| … + `rich.traceback` | 87.6 ms |
| … + `rich.markdown` | 106.5 ms |
| … + both (what `typer.rich_utils` imports today) | 113.7 ms |

These are wall times of separate processes, so they also include each
module set's shutdown cost; the measured saving is in
[the lazy-import experiment](#experiment-lazy-rich-imports).
`rich.markdown` pulls in markdown-it-py and, through `rich.syntax`, Pygments;
`rich.traceback` also pulls in Pygments. `typer/rich_utils.py` only builds a
`Markdown` object when `markup_mode == "markdown"` (line 177), and a
`Traceback` only for pretty exceptions (line 748). Both imports can move into
those functions, with the type annotations that mention `Markdown` moved
under `TYPE_CHECKING`.

### Interpreter shutdown

The difference between a normal exit and `os._exit(0)`, which skips
finalization, is the shutdown cost (median of 15 runs, ms):

| State before exit | Normal exit | `os._exit(0)` | `gc.freeze()` then exit | Shutdown |
|---|---:|---:|---:|---:|
| `python -c pass` | 12.1 | 9.0 | 9.7 | 3.1 |
| `import typer` | 72.0 | 63.6 | 60.7 | 8.4 |
| `import typer` + 3 Pydantic adapters | 168.9 | 140.6 | 151.4 | 28.4 |
| `import typer` + `typer.rich_utils` | 133.2 | 111.5 | 131.1 | 21.7 |
| A full 3-parameter command run | 172.7 | 133.0 | 134.8 | 39.7 |

Finalization tears down every loaded module and garbage-collects what they
created, so the cost grows with what was imported. Not loading Pydantic
(recommendations 1 and 2) shrinks it. `gc.freeze()` before exiting removes
most of it for a real command run. `os._exit()` removes all of it, but skips
atexit handlers and finalizers, so neither is a general-purpose fix for a
library.

### App size

Building the command tree (`get_command`) in a warm process (median of 15):

| Commands × params | 1 × 1 | 1 × 10 | 1 × 30 | 10 × 3 | 50 × 3 | 200 × 3 |
|---|---:|---:|---:|---:|---:|---:|
| `get_command` | 0.27 ms | 0.32 ms | 0.64 ms | 0.94 ms | 4.71 ms | 19.45 ms |

Per call inside a running process (median of 300; tests use this path):

| Call | Median |
|---|---:|
| Typer `app([...], standalone_mode=False)`, 1 command | 669 µs |
| Typer `app([...], standalone_mode=False)`, 50 commands | 5,610 µs |
| `CliRunner().invoke(app, [...])`, 1 command | 919 µs |
| argparse: build the parser and parse | 221 µs |

Typer 0.28.0 took 325 µs per `app()` call and 387 µs per
`CliRunner().invoke()`. Building Pydantic adapters on every call roughly
doubles that in 0.29.3.

## Detailed results

All Python 3.11, median of 40 launches, in ms. "To callback" is the time
until the command function starts. The 0.28.0 column is the same case on
Typer 0.28.0. Full tables with min and p95, plus raw samples, are in
[`results/`](results).

### Baselines

| Case | What it runs | Median | Over floor | To callback | 0.28.0 |
|---|---|---:|---:|---:|---:|
| `python-floor` | `python -c pass` | 10.7 | +0.0 | — | 11.8 |
| `import-typer` | `python -c "import typer"` | 69.1 | +58.4 | — | 65.9 |
| `argparse` | basic app written with argparse | 26.3 | +15.7 | 22.6 | 25.7 |
| `click` | basic app written with Click 8.5.1 | 46.8 | +36.2 | 38.8 | 49.0 |

### Parameters and arguments (`typer.run`, one command)

| Case | What it runs | Median | Over floor | To callback | 0.28.0 |
|---|---|---:|---:|---:|---:|
| `no-params` | no parameters | 165.6 | +155.0 | 131.8 | 70.2 |
| `arg-required` | required `str` argument | 168.4 | +157.8 | 131.0 | 71.4 |
| `arg-optional` | optional argument, default used | 161.5 | +150.9 | 125.8 | 74.0 |
| `opt-required` | required `str` option | 162.5 | +151.9 | 127.4 | 68.7 |
| `opt-int` | `int` option | 165.9 | +155.2 | 132.5 | 67.1 |
| `opt-int-range` | `int` option with `min`/`max` | 165.0 | +154.4 | 130.6 | 69.8 |
| `opt-float` | `float` option | 170.5 | +159.8 | 132.4 | 72.0 |
| `opt-bool` | `bool` flag | 165.4 | +154.8 | 129.2 | 72.1 |
| `opt-enum` | `Enum` choice | 161.5 | +150.9 | 129.0 | 73.1 |
| `opt-literal` | `Literal` choice | 169.8 | +159.2 | 134.8 | 69.8 |
| `opt-path` | `Path` option, file must exist | 162.9 | +152.2 | 128.0 | 72.9 |
| `opt-datetime` | `datetime` option | 167.2 | +156.6 | 132.4 | 72.4 |
| `opt-list` | repeated list option (×3) | 162.8 | +152.1 | 131.8 | 71.2 |
| `opt-envvar` | option read from an environment variable | 171.8 | +161.2 | 135.5 | 73.3 |
| `opt-prompt` | option prompted on stdin | 167.8 | +157.1 | 133.3 | 68.8 |
| `many-params` | 12 mixed parameters, all given | 174.4 | +163.8 | 139.9 | 76.3 |

### App shapes

| Case | What it runs | Median | Over floor | To callback | 0.28.0 |
|---|---|---:|---:|---:|---:|
| `typer-run` | `typer.run(main)`: argument, `int` option, flag | 164.7 | +154.0 | 130.9 | 72.7 |
| `app-1-command` | `Typer()` app, 1 command (same parameters) | 170.0 | +159.3 | 135.5 | 69.8 |
| `app-1-command-no-completion` | `Typer(add_completion=False)`, 1 command | 164.4 | +153.8 | 130.2 | 70.7 |
| `app-2-commands` | `Typer()` app, 2 commands, run one | 170.3 | +159.6 | 132.1 | 73.6 |
| `nested-sub-app` | nested sub-apps: `users create NAME` | 167.0 | +156.3 | 132.1 | 75.2 |
| `app-50-commands` | 50 commands × 3 parameters, run one | 177.3 | +166.6 | 140.3 | 86.0 |
| `typer-command` | `typer basic.py run ...` (the `typer` runner) | 169.6 | +158.9 | 134.9 | 71.3 |

### Help output

| Case | What it runs | Median | On a TTY | 0.28.0 |
|---|---|---:|---:|---:|
| `typer-run` | `basic.py --help` (Rich) | 152.3 | 154.2 | 154.5 |
| `typer-run-no-rich` | `basic.py --help`, `TYPER_USE_RICH=0` | 76.3 | 71.9 | 70.0 |
| `app-root` | `multi_commands.py --help` (Rich) | 147.9 | 150.8 | 152.4 |
| `app-root-no-rich` | `multi_commands.py --help`, `TYPER_USE_RICH=0` | 73.2 | 74.4 | 70.4 |
| `subcommand` | `nested.py users create --help` (Rich) | 248.3 | — | 150.7 |
| `app-50-commands` | `scale_commands.py --help` (Rich, 50 commands) | 166.6 | — | 174.6 |
| `argparse` | `argparse_basic.py --help` | 27.0 | — | 27.8 |

### Errors

| Case | What it runs | Median | On a TTY | 0.28.0 |
|---|---|---:|---:|---:|
| `missing-argument` | `basic.py` with no arguments (Rich) | 236.9 | 239.8 | 145.4 |
| `missing-argument-no-rich` | the same, `TYPER_USE_RICH=0` | 167.1 | 166.9 | 71.4 |
| `bad-int` | `basic.py World --count abc` (Rich) | 238.5 | 234.9 | 149.8 |
| `bad-int-no-rich` | the same, `TYPER_USE_RICH=0` | 170.6 | 166.2 | 68.9 |
| `argparse-bad-int` | `argparse_basic.py World --count abc` | 27.1 | — | 26.8 |

Rendering to a terminal (the pseudo-terminal column) makes no measurable
difference.

### Python 3.13

The same matrix on Python 3.13.18 (Click baseline also on 3.13), median of 40
launches in ms. Python 3.13 is a few percent slower here across the board,
including the floor; the structure of the costs is identical. This VM is
noisy, so don't read much into small differences between the two runs.

| Case | 3.11 | 3.11 over floor | 3.13 | 3.13 over floor |
|---|---:|---:|---:|---:|
| `baseline/python-floor` | 10.7 | +0.0 | 12.7 | +0.0 |
| `baseline/import-typer` | 69.1 | +58.4 | 75.6 | +62.9 |
| `baseline/argparse` | 26.3 | +15.7 | 28.1 | +15.4 |
| `baseline/click` | 46.8 | +36.2 | 50.9 | +38.2 |
| `params/no-params` | 165.6 | +155.0 | 171.3 | +158.7 |
| `shape/typer-run` | 164.7 | +154.0 | 171.8 | +159.1 |
| `params/many-params` | 174.4 | +163.8 | 180.4 | +167.8 |
| `shape/app-50-commands` | 177.3 | +166.6 | 192.0 | +179.3 |
| `help/typer-run` (Rich) | 152.3 | +141.6 | 167.4 | +154.8 |
| `help/typer-run-no-rich` | 76.3 | +65.7 | 77.1 | +64.4 |
| `help/subcommand` (Rich) | 248.3 | +237.6 | 262.0 | +249.3 |
| `error/bad-int` (Rich) | 238.5 | +227.9 | 259.6 | +246.9 |
| `error/bad-int-no-rich` | 170.6 | +160.0 | 174.2 | +161.5 |

All cases, with min and p95, are in
[`results/typer-0.29.3-py3.13.md`](results/typer-0.29.3-py3.13.md). The stage
breakdown on 3.13 has the same shape: about 78–85 ms in Pydantic and 39–41 ms
of shutdown per run
([`results/inprocess-typer-0.29.3-py3.13.md`](results/inprocess-typer-0.29.3-py3.13.md)).

### Experiment: skip `None` before building the adapter

An A/B run of Typer 0.29.3 with and without
[`experiments/skip-none-coercion.patch`](experiments/skip-none-coercion.patch)
(Python 3.11, 30 launches per case, ms). The unpatched build ran once before
and once after the patched one; its column is the median of both runs
pooled, with each run's own median in brackets.

| Case | 0.29.3 (run 1 / run 2) | 0.29.3 + patch | Change | 0.28.0 |
|---|---:|---:|---:|---:|
| `baseline/python-floor` | 11.4 (12 / 11) | 11.0 | -0.4 (-3%) | 11.8 |
| `baseline/import-typer` | 73.8 (72 / 74) | 67.4 | -6.4 (-9%) | 65.9 |
| `params/no-params` | 171.9 (187 / 166) | 72.1 | **-99.8 (-58%)** | 70.2 |
| `params/opt-bool` | 170.4 (169 / 171) | 78.1 | **-92.3 (-54%)** | 72.1 |
| `params/arg-required` | 177.3 (181 / 172) | 163.2 | -14.1 (-8%) | 71.4 |
| `shape/typer-run` | 178.1 (182 / 170) | 161.1 | -17.0 (-10%) | 72.7 |
| `shape/app-2-commands` | 171.6 (173 / 170) | 166.2 | -5.4 (-3%) | 73.6 |
| `shape/app-50-commands` | 186.8 (189 / 183) | 184.8 | -2.1 (-1%) | 86.0 |
| `help/typer-run` | 158.5 (163 / 155) | 156.5 | -1.9 (-1%) | 154.5 |
| `help/app-root` | 156.0 (164 / 153) | 155.2 | -0.7 (-0%) | 152.4 |
| `help/subcommand` | 259.1 (275 / 256) | 153.9 | **-105.2 (-41%)** | 150.7 |
| `error/missing-argument` | 246.3 (251 / 244) | 150.1 | **-96.2 (-39%)** | 145.4 |
| `error/missing-argument-no-rich` | 172.4 (173 / 172) | 76.8 | **-95.6 (-55%)** | 71.4 |
| `error/bad-int` | 241.1 (249 / 237) | 250.3 | +9.2 (+4%) | 149.8 |
| `error/bad-int-no-rich` | 171.0 (175 / 168) | 172.0 | +0.9 (+1%) | 68.9 |

The patch helps wherever every non-flag parameter is unset: commands with
no parameters or only flags, `--help` on subcommands, and errors raised
before any value is validated. Those cases land within a few milliseconds
of 0.28.0.

The machine drifted between these runs. `import typer`, which the patch
can't affect, came out 9% faster in the patched run, and so did the cases
that still load Pydantic for a value (`arg-required`, `typer-run`). So part
of each change above is drift. Against the main 40-launch run, the improved
cases are 87–94 ms faster: no parameters 165.6 → 72.1, flag only
165.4 → 78.1, subcommand `--help` 248.3 → 153.9, missing argument
236.9 → 150.1 (Rich) and 167.1 → 76.8 (no Rich). Commands that pass a value
still load Pydantic for it. Recommendation 2 is what would speed those up.

### Experiment: lazy Rich imports

An A/B run of Typer 0.29.3 with and without
[`experiments/lazy-rich-imports.patch`](experiments/lazy-rich-imports.patch),
which moves the `rich.markdown` and `rich.traceback` imports into the two
functions that use them. To cancel drift, the two builds ran alternately in
4 chunks of 10 launches each; each column pools all 40 launches (Python
3.11, ms).

| Case | 0.29.3 | 0.29.3 + patch | Change |
|---|---:|---:|---:|
| `baseline/python-floor` | 10.9 | 11.4 | +0.4 (+4%) |
| `baseline/import-typer` | 66.1 | 67.4 | +1.3 (+2%) |
| `shape/typer-run` | 172.5 | 173.0 | +0.5 (+0%) |
| `help/typer-run` (Rich) | 153.6 | 115.8 | **-37.8 (-25%)** |
| `help/app-root` (Rich) | 148.7 | 110.9 | **-37.8 (-25%)** |
| `help/subcommand` (Rich) | 245.4 | 212.8 | **-32.6 (-13%)** |
| `help/app-50-commands` (Rich) | 171.2 | 134.9 | **-36.3 (-21%)** |
| `error/missing-argument` (Rich) | 240.5 | 202.2 | **-38.3 (-16%)** |
| `error/bad-int` (Rich) | 236.6 | 201.0 | **-35.5 (-15%)** |
| `help/typer-run-no-rich` | 72.5 | 74.7 | +2.2 (+3%) |
| `error/bad-int-no-rich` | 163.6 | 166.6 | +3.0 (+2%) |

Every Rich help and error path is 33–38 ms faster; the cases that don't use
Rich are unchanged. The test suite gives the same result with the patch
(1634 passed, 29 skipped, 3 xfailed). Combined with recommendation 1,
subcommand `--help` should drop from about 250 ms to about 115–120 ms. That
figure is an estimate; the two patches were not measured together.

### First run without compiled bytecode

For this run the venv's `__pycache__` directories were removed and
`PYTHONDONTWRITEBYTECODE=1` was set, so each launch compiles every module in
site-packages from source. That's what happens on the first run after an
install without bytecode compilation (20 launches, Python 3.11, ms; the
compiled column is from the main run):

| Case | Compiled bytecode | No bytecode |
|---|---:|---:|
| `python -c "import typer"` | 69.1 | 111.8 |
| Basic app (`typer.run`) | 164.7 | 339.5 |
| `basic.py --help` (Rich) | 152.3 | 329.3 |

Normally only the first run pays this, because Python then writes the `.pyc`
files. Every run pays it when site-packages isn't writable by the user
running the CLI, for example a container image built without bytecode
compilation and run as another user.

## Method

* **Cases** are the scripts in [`apps/`](apps). Each command function
  starts by writing a timestamp when `BENCH_MARK_FILE` is set, which gives
  the "to callback" time.
* **Validation first.** Before timing, every case runs once and its exit
  code and output are checked; all cases passed on both Typer versions.
* **Timing.** Each run is a fresh process launched from an empty directory,
  with output sent to `/dev/null` (or a 100×40 pseudo-terminal for the TTY
  columns). The environment is minimal: no `TERMINAL_WIDTH`,
  `_TYPER_FORCE_DISABLE_TERMINAL`, `FORCE_COLOR`, `PYTHON*` or CI variables
  leak in. There are 3 warm-up rounds, then 40 timed rounds, each running
  every case once in a shuffled order (fixed seed).
* **Environments.** Each version has its own fresh virtual environment
  (`python -m venv`), with Typer installed from the checkout as a regular
  wheel and only runtime dependencies. Typer 0.28.0 came from a worktree at
  `bf5cfc1`. Click 8.5.1 has its own environment.
* **Reproduce** with the commands in [README.md](README.md). The raw
  per-run samples are in the JSON files in [`results/`](results).
