# Typer CLI timings: typer-0.29.3-py3.13

- Python 3.13.18 (CPython), annotated-doc 0.0.7, markdown-it-py 4.3.0, pydantic 2.14.4, pydantic-core 2.50.5, pygments 2.21.0, rich 15.0.0, shellingham 1.5.4, typer 0.29.3, typing-extensions 4.16.0
- Intel(R) Xeon(R) Processor @ 2.10GHz x4, Linux-6.18.44-fc-v880-x86_64-with-glibc2.39
- Click baseline: click 8.5.1 on Python 3.13.18
- 40 timed runs per case after 3 warm-up runs, interleaved in shuffled rounds (seed 20261126)
- Load average before/after: [0.89, 0.79, 0.53] / [1.07, 0.96, 0.67]

Times in milliseconds. Δ is the median over the `python -c pass` floor. 'To callback' is the median time until the command function starts.

| Case | Description | Median | Δ floor | Min | p95 | To callback |
|---|---|---:|---:|---:|---:|---:|
| `baseline/python-floor` | python -c pass (interpreter start-up floor) | 12.7 | +0.0 | 11.2 | 19.9 |  |
| `baseline/import-typer` | python -c "import typer" | 75.6 | +62.9 | 66.3 | 107.2 |  |
| `baseline/argparse` | basic.py written with argparse (stdlib) | 28.1 | +15.4 | 24.3 | 40.8 | 23.9 |
| `baseline/click` | basic.py written with upstream Click | 50.9 | +38.2 | 43.9 | 68.2 | 41.3 |
| `params/no-params` | no parameters | 171.3 | +158.7 | 149.3 | 209.9 | 137.3 |
| `params/arg-required` | required str argument | 173.0 | +160.3 | 151.6 | 235.1 | 137.5 |
| `params/arg-optional` | optional argument, default used | 174.7 | +162.1 | 145.6 | 201.9 | 138.3 |
| `params/opt-required` | required str option | 171.7 | +159.1 | 148.1 | 199.8 | 137.6 |
| `params/opt-int` | int option | 173.8 | +161.1 | 152.6 | 218.4 | 139.1 |
| `params/opt-int-range` | int option with min/max | 178.2 | +165.5 | 149.0 | 205.4 | 144.8 |
| `params/opt-float` | float option | 175.9 | +163.2 | 159.8 | 208.8 | 139.6 |
| `params/opt-bool` | bool flag | 177.0 | +164.3 | 148.4 | 220.0 | 141.8 |
| `params/opt-enum` | Enum choice | 175.5 | +162.8 | 156.2 | 229.6 | 139.0 |
| `params/opt-literal` | Literal choice | 175.5 | +162.8 | 157.4 | 201.6 | 139.2 |
| `params/opt-path` | Path option, file must exist | 178.3 | +165.6 | 150.9 | 217.7 | 141.6 |
| `params/opt-datetime` | datetime option | 173.4 | +160.7 | 150.4 | 206.3 | 136.3 |
| `params/opt-list` | repeated list option (x3) | 178.4 | +165.7 | 154.8 | 209.0 | 139.5 |
| `params/opt-envvar` | option read from an env var | 172.4 | +159.8 | 150.9 | 205.1 | 138.0 |
| `params/opt-prompt` | option prompted on stdin | 173.2 | +160.5 | 151.8 | 201.7 | 138.8 |
| `params/many-params` | 12 mixed parameters, all given | 180.4 | +167.8 | 151.2 | 223.6 | 146.6 |
| `shape/typer-run` | typer.run(main): arg + int option + bool flag | 171.8 | +159.1 | 158.2 | 206.8 | 136.3 |
| `shape/app-1-command` | Typer() app, 1 command (same params) | 175.8 | +163.1 | 149.6 | 202.5 | 140.4 |
| `shape/app-1-command-no-completion` | Typer(add_completion=False), 1 command | 174.3 | +161.7 | 157.7 | 201.3 | 140.2 |
| `shape/app-2-commands` | Typer() app, 2 commands, run one | 182.7 | +170.0 | 153.9 | 224.8 | 145.6 |
| `shape/nested-sub-app` | nested sub-apps: users create NAME | 174.4 | +161.7 | 151.1 | 225.2 | 138.2 |
| `shape/app-50-commands` | Typer() app, 50 commands x 3 params, run one | 192.0 | +179.3 | 168.8 | 232.4 | 157.3 |
| `shape/typer-command` | `typer basic.py run ...` (the typer runner CLI) | 182.0 | +169.3 | 152.1 | 222.8 | 143.2 |
| `help/typer-run` | basic.py --help (Rich) | 167.4 | +154.8 | 151.0 | 197.1 |  |
| `help/typer-run-no-rich` | basic.py --help, TYPER_USE_RICH=0 | 77.1 | +64.4 | 67.9 | 94.9 |  |
| `help/app-root` | multi_commands.py --help (Rich) | 166.9 | +154.3 | 151.0 | 199.8 |  |
| `help/app-root-no-rich` | multi_commands.py --help, TYPER_USE_RICH=0 | 78.8 | +66.1 | 69.7 | 101.9 |  |
| `help/subcommand` | nested.py users create --help (Rich) | 262.0 | +249.3 | 236.6 | 307.4 |  |
| `help/app-50-commands` | scale_commands.py --help (Rich, 50 commands) | 190.6 | +177.9 | 160.9 | 222.7 |  |
| `help/argparse` | argparse_basic.py --help (stdlib) | 28.4 | +15.8 | 26.1 | 39.4 |  |
| `error/missing-argument` | basic.py with no args (Rich) | 265.6 | +252.9 | 232.7 | 323.3 |  |
| `error/missing-argument-no-rich` | basic.py with no args, TYPER_USE_RICH=0 | 178.3 | +165.6 | 158.6 | 205.5 |  |
| `error/bad-int` | basic.py World --count abc (Rich) | 259.6 | +246.9 | 221.4 | 305.3 |  |
| `error/bad-int-no-rich` | basic.py World --count abc, TYPER_USE_RICH=0 | 174.2 | +161.5 | 153.1 | 203.9 |  |
| `error/argparse-bad-int` | argparse_basic.py World --count abc (stdlib) | 28.0 | +15.3 | 23.5 | 35.8 |  |
