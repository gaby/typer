# Typer CLI timings: typer-0.28.0-py3.11

- Python 3.11.18 (CPython), annotated-doc 0.0.7, markdown-it-py 4.3.0, pygments 2.21.0, rich 15.0.0, shellingham 1.5.4, typer 0.28.0
- Intel(R) Xeon(R) Processor @ 2.10GHz x4, Linux-6.18.44-fc-v880-x86_64-with-glibc2.39
- Click baseline: click 8.5.1 on Python 3.11.18
- 40 timed runs per case after 3 warm-up runs, interleaved in shuffled rounds (seed 20261126)
- Load average before/after: [0.7, 0.56, 0.4] / [1.05, 0.81, 0.53]

Times in milliseconds. Δ is the median over the `python -c pass` floor. 'To callback' is the median time until the command function starts.

| Case | Description | Median | Δ floor | Min | p95 | To callback |
|---|---|---:|---:|---:|---:|---:|
| `baseline/python-floor` | python -c pass (interpreter start-up floor) | 11.8 | +0.0 | 9.9 | 21.8 |  |
| `baseline/import-typer` | python -c "import typer" | 65.9 | +54.0 | 56.2 | 83.8 |  |
| `baseline/argparse` | basic.py written with argparse (stdlib) | 25.7 | +13.9 | 21.1 | 41.5 | 21.9 |
| `baseline/click` | basic.py written with upstream Click | 49.0 | +37.2 | 42.9 | 67.6 | 40.4 |
| `params/no-params` | no parameters | 70.2 | +58.4 | 61.1 | 91.5 | 54.0 |
| `params/arg-required` | required str argument | 71.4 | +59.6 | 58.3 | 96.3 | 55.6 |
| `params/arg-optional` | optional argument, default used | 74.0 | +62.1 | 63.0 | 100.0 | 58.2 |
| `params/opt-required` | required str option | 68.7 | +56.9 | 61.0 | 89.8 | 54.8 |
| `params/opt-int` | int option | 67.1 | +55.3 | 61.4 | 89.6 | 53.0 |
| `params/opt-int-range` | int option with min/max | 69.8 | +58.0 | 61.9 | 90.0 | 54.1 |
| `params/opt-float` | float option | 72.0 | +60.2 | 59.5 | 96.1 | 56.2 |
| `params/opt-bool` | bool flag | 72.1 | +60.3 | 58.5 | 93.5 | 57.1 |
| `params/opt-enum` | Enum choice | 73.1 | +61.2 | 60.6 | 101.0 | 57.1 |
| `params/opt-literal` | Literal choice | 69.8 | +58.0 | 60.5 | 84.3 | 55.3 |
| `params/opt-path` | Path option, file must exist | 72.9 | +61.0 | 58.4 | 92.3 | 57.9 |
| `params/opt-datetime` | datetime option | 72.4 | +60.5 | 62.8 | 92.8 | 58.2 |
| `params/opt-list` | repeated list option (x3) | 71.2 | +59.4 | 60.1 | 94.7 | 56.2 |
| `params/opt-envvar` | option read from an env var | 73.3 | +61.5 | 62.7 | 101.4 | 56.8 |
| `params/opt-prompt` | option prompted on stdin | 68.8 | +57.0 | 64.1 | 90.4 | 54.4 |
| `params/many-params` | 12 mixed parameters, all given | 76.3 | +64.5 | 64.3 | 100.8 | 61.5 |
| `shape/typer-run` | typer.run(main): arg + int option + bool flag | 72.7 | +60.9 | 59.3 | 94.0 | 57.2 |
| `shape/app-1-command` | Typer() app, 1 command (same params) | 69.8 | +58.0 | 61.2 | 93.8 | 54.3 |
| `shape/app-1-command-no-completion` | Typer(add_completion=False), 1 command | 70.7 | +58.9 | 60.4 | 90.1 | 55.5 |
| `shape/app-2-commands` | Typer() app, 2 commands, run one | 73.6 | +61.8 | 60.0 | 100.0 | 58.1 |
| `shape/nested-sub-app` | nested sub-apps: users create NAME | 75.2 | +63.3 | 60.9 | 98.7 | 60.0 |
| `shape/app-50-commands` | Typer() app, 50 commands x 3 params, run one | 86.0 | +74.2 | 71.6 | 119.4 | 68.3 |
| `shape/typer-command` | `typer basic.py run ...` (the typer runner CLI) | 71.3 | +59.4 | 61.2 | 90.8 | 56.2 |
| `help/typer-run` | basic.py --help (Rich) | 154.5 | +142.7 | 132.6 | 197.4 |  |
| `help/typer-run [tty]` | basic.py --help (Rich) [tty] | 158.6 | +146.8 | 133.9 | 214.1 |  |
| `help/typer-run-no-rich` | basic.py --help, TYPER_USE_RICH=0 | 70.0 | +58.2 | 60.9 | 90.2 |  |
| `help/typer-run-no-rich [tty]` | basic.py --help, TYPER_USE_RICH=0 [tty] | 73.5 | +61.7 | 61.3 | 99.0 |  |
| `help/app-root` | multi_commands.py --help (Rich) | 152.4 | +140.6 | 137.4 | 189.1 |  |
| `help/app-root [tty]` | multi_commands.py --help (Rich) [tty] | 152.8 | +141.0 | 135.1 | 197.4 |  |
| `help/app-root-no-rich` | multi_commands.py --help, TYPER_USE_RICH=0 | 70.4 | +58.6 | 59.9 | 99.1 |  |
| `help/app-root-no-rich [tty]` | multi_commands.py --help, TYPER_USE_RICH=0 [tty] | 72.6 | +60.7 | 62.6 | 92.2 |  |
| `help/subcommand` | nested.py users create --help (Rich) | 150.7 | +138.9 | 128.0 | 208.8 |  |
| `help/app-50-commands` | scale_commands.py --help (Rich, 50 commands) | 174.6 | +162.8 | 149.3 | 235.8 |  |
| `help/argparse` | argparse_basic.py --help (stdlib) | 27.8 | +16.0 | 25.3 | 39.2 |  |
| `error/missing-argument` | basic.py with no args (Rich) | 145.4 | +133.6 | 127.6 | 214.0 |  |
| `error/missing-argument [tty]` | basic.py with no args (Rich) [tty] | 150.2 | +138.3 | 129.2 | 198.8 |  |
| `error/missing-argument-no-rich` | basic.py with no args, TYPER_USE_RICH=0 | 71.4 | +59.6 | 59.6 | 97.1 |  |
| `error/missing-argument-no-rich [tty]` | basic.py with no args, TYPER_USE_RICH=0 [tty] | 72.1 | +60.2 | 62.5 | 94.0 |  |
| `error/bad-int` | basic.py World --count abc (Rich) | 149.8 | +138.0 | 126.7 | 189.2 |  |
| `error/bad-int [tty]` | basic.py World --count abc (Rich) [tty] | 150.8 | +139.0 | 125.3 | 186.0 |  |
| `error/bad-int-no-rich` | basic.py World --count abc, TYPER_USE_RICH=0 | 68.9 | +57.1 | 62.7 | 87.8 |  |
| `error/bad-int-no-rich [tty]` | basic.py World --count abc, TYPER_USE_RICH=0 [tty] | 70.6 | +58.8 | 61.5 | 89.3 |  |
| `error/argparse-bad-int` | argparse_basic.py World --count abc (stdlib) | 26.8 | +15.0 | 23.7 | 39.9 |  |
