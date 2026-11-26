# Typer CLI timings: typer-0.29.3-py3.11

- Python 3.11.18 (CPython), annotated-doc 0.0.7, markdown-it-py 4.3.0, pydantic 2.14.4, pydantic-core 2.50.5, pygments 2.21.0, rich 15.0.0, shellingham 1.5.4, typer 0.29.3, typing-extensions 4.16.0
- Intel(R) Xeon(R) Processor @ 2.10GHz x4, Linux-6.18.44-fc-v880-x86_64-with-glibc2.39
- Click baseline: click 8.5.1 on Python 3.11.18
- 40 timed runs per case after 3 warm-up runs, interleaved in shuffled rounds (seed 20261126)
- Load average before/after: [0.39, 0.14, 0.04] / [1.02, 0.75, 0.35]

Times in milliseconds. Δ is the median over the `python -c pass` floor. 'To callback' is the median time until the command function starts.

| Case | Description | Median | Δ floor | Min | p95 | To callback |
|---|---|---:|---:|---:|---:|---:|
| `baseline/python-floor` | python -c pass (interpreter start-up floor) | 10.7 | +0.0 | 8.9 | 14.1 |  |
| `baseline/import-typer` | python -c "import typer" | 69.1 | +58.4 | 59.2 | 78.6 |  |
| `baseline/argparse` | basic.py written with argparse (stdlib) | 26.3 | +15.7 | 22.5 | 34.3 | 22.6 |
| `baseline/click` | basic.py written with upstream Click | 46.8 | +36.2 | 41.0 | 63.9 | 38.8 |
| `params/no-params` | no parameters | 165.6 | +155.0 | 142.8 | 195.2 | 131.8 |
| `params/arg-required` | required str argument | 168.4 | +157.8 | 146.0 | 199.1 | 131.0 |
| `params/arg-optional` | optional argument, default used | 161.5 | +150.9 | 137.8 | 204.4 | 125.8 |
| `params/opt-required` | required str option | 162.5 | +151.9 | 139.8 | 190.2 | 127.4 |
| `params/opt-int` | int option | 165.9 | +155.2 | 144.7 | 193.9 | 132.5 |
| `params/opt-int-range` | int option with min/max | 165.0 | +154.4 | 141.7 | 191.8 | 130.6 |
| `params/opt-float` | float option | 170.5 | +159.8 | 143.7 | 212.5 | 132.4 |
| `params/opt-bool` | bool flag | 165.4 | +154.8 | 146.2 | 198.7 | 129.2 |
| `params/opt-enum` | Enum choice | 161.5 | +150.9 | 145.1 | 193.7 | 129.0 |
| `params/opt-literal` | Literal choice | 169.8 | +159.2 | 142.7 | 203.2 | 134.8 |
| `params/opt-path` | Path option, file must exist | 162.9 | +152.2 | 141.0 | 213.0 | 128.0 |
| `params/opt-datetime` | datetime option | 167.2 | +156.6 | 143.4 | 212.3 | 132.4 |
| `params/opt-list` | repeated list option (x3) | 162.8 | +152.1 | 148.7 | 202.8 | 131.8 |
| `params/opt-envvar` | option read from an env var | 171.8 | +161.2 | 156.3 | 218.1 | 135.5 |
| `params/opt-prompt` | option prompted on stdin | 167.8 | +157.1 | 141.6 | 219.1 | 133.3 |
| `params/many-params` | 12 mixed parameters, all given | 174.4 | +163.8 | 147.1 | 206.1 | 139.9 |
| `shape/typer-run` | typer.run(main): arg + int option + bool flag | 164.7 | +154.0 | 138.6 | 202.2 | 130.9 |
| `shape/app-1-command` | Typer() app, 1 command (same params) | 170.0 | +159.3 | 141.5 | 188.7 | 135.5 |
| `shape/app-1-command-no-completion` | Typer(add_completion=False), 1 command | 164.4 | +153.8 | 143.1 | 203.5 | 130.2 |
| `shape/app-2-commands` | Typer() app, 2 commands, run one | 170.3 | +159.6 | 140.6 | 209.4 | 132.1 |
| `shape/nested-sub-app` | nested sub-apps: users create NAME | 167.0 | +156.3 | 143.9 | 205.6 | 132.1 |
| `shape/app-50-commands` | Typer() app, 50 commands x 3 params, run one | 177.3 | +166.6 | 155.2 | 220.5 | 140.3 |
| `shape/typer-command` | `typer basic.py run ...` (the typer runner CLI) | 169.6 | +158.9 | 142.7 | 209.7 | 134.9 |
| `help/typer-run` | basic.py --help (Rich) | 152.3 | +141.6 | 131.5 | 216.8 |  |
| `help/typer-run [tty]` | basic.py --help (Rich) [tty] | 154.2 | +143.5 | 134.9 | 191.7 |  |
| `help/typer-run-no-rich` | basic.py --help, TYPER_USE_RICH=0 | 76.3 | +65.7 | 61.2 | 109.0 |  |
| `help/typer-run-no-rich [tty]` | basic.py --help, TYPER_USE_RICH=0 [tty] | 71.9 | +61.3 | 62.2 | 95.8 |  |
| `help/app-root` | multi_commands.py --help (Rich) | 147.9 | +137.3 | 132.5 | 170.4 |  |
| `help/app-root [tty]` | multi_commands.py --help (Rich) [tty] | 150.8 | +140.1 | 130.7 | 196.0 |  |
| `help/app-root-no-rich` | multi_commands.py --help, TYPER_USE_RICH=0 | 73.2 | +62.5 | 64.8 | 100.6 |  |
| `help/app-root-no-rich [tty]` | multi_commands.py --help, TYPER_USE_RICH=0 [tty] | 74.4 | +63.8 | 61.9 | 100.4 |  |
| `help/subcommand` | nested.py users create --help (Rich) | 248.3 | +237.6 | 216.9 | 328.2 |  |
| `help/app-50-commands` | scale_commands.py --help (Rich, 50 commands) | 166.6 | +155.9 | 149.0 | 206.2 |  |
| `help/argparse` | argparse_basic.py --help (stdlib) | 27.0 | +16.3 | 23.3 | 34.6 |  |
| `error/missing-argument` | basic.py with no args (Rich) | 236.9 | +226.2 | 201.5 | 257.4 |  |
| `error/missing-argument [tty]` | basic.py with no args (Rich) [tty] | 239.8 | +229.2 | 209.5 | 281.3 |  |
| `error/missing-argument-no-rich` | basic.py with no args, TYPER_USE_RICH=0 | 167.1 | +156.4 | 146.9 | 219.5 |  |
| `error/missing-argument-no-rich [tty]` | basic.py with no args, TYPER_USE_RICH=0 [tty] | 166.9 | +156.3 | 144.5 | 205.6 |  |
| `error/bad-int` | basic.py World --count abc (Rich) | 238.5 | +227.9 | 210.2 | 269.0 |  |
| `error/bad-int [tty]` | basic.py World --count abc (Rich) [tty] | 234.9 | +224.2 | 201.4 | 292.9 |  |
| `error/bad-int-no-rich` | basic.py World --count abc, TYPER_USE_RICH=0 | 170.6 | +160.0 | 144.9 | 208.1 |  |
| `error/bad-int-no-rich [tty]` | basic.py World --count abc, TYPER_USE_RICH=0 [tty] | 166.2 | +155.5 | 148.7 | 214.6 |  |
| `error/argparse-bad-int` | argparse_basic.py World --count abc (stdlib) | 27.1 | +16.4 | 22.4 | 36.0 |  |
