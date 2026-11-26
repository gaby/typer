# Typer CLI timings: typer-0.29.3-py3.11

- Python 3.11.18 (CPython), annotated-doc 0.0.7, markdown-it-py 4.3.0, pydantic 2.14.4, pydantic-core 2.50.5, pygments 2.21.0, rich 15.0.0, shellingham 1.5.4, typer 0.29.3, typing-extensions 4.16.0
- Intel(R) Xeon(R) Processor @ 2.10GHz x4, Linux-6.18.44-fc-v880-x86_64-with-glibc2.39
- 30 timed runs per case after 3 warm-up runs, interleaved in shuffled rounds (seed 20261126)
- Load average before/after: [1.07, 0.96, 0.68] / [1.15, 1.02, 0.73]

Times in milliseconds. Δ is the median over the `python -c pass` floor. 'To callback' is the median time until the command function starts.

| Case | Description | Median | Δ floor | Min | p95 | To callback |
|---|---|---:|---:|---:|---:|---:|
| `baseline/python-floor` | python -c pass (interpreter start-up floor) | 11.6 | +0.0 | 10.1 | 15.3 |  |
| `baseline/import-typer` | python -c "import typer" | 72.1 | +60.6 | 63.5 | 94.6 |  |
| `params/no-params` | no parameters | 186.6 | +175.1 | 156.4 | 235.8 | 144.7 |
| `params/arg-required` | required str argument | 180.7 | +169.1 | 151.6 | 215.1 | 143.1 |
| `params/opt-bool` | bool flag | 169.1 | +157.6 | 150.5 | 241.2 | 131.3 |
| `shape/typer-run` | typer.run(main): arg + int option + bool flag | 182.4 | +170.8 | 151.0 | 219.8 | 141.1 |
| `shape/app-2-commands` | Typer() app, 2 commands, run one | 172.9 | +161.4 | 156.1 | 203.3 | 137.0 |
| `shape/app-50-commands` | Typer() app, 50 commands x 3 params, run one | 189.1 | +177.6 | 169.2 | 235.2 | 150.8 |
| `help/typer-run` | basic.py --help (Rich) | 163.1 | +151.5 | 133.0 | 232.8 |  |
| `help/app-root` | multi_commands.py --help (Rich) | 164.3 | +152.7 | 138.6 | 210.5 |  |
| `help/subcommand` | nested.py users create --help (Rich) | 275.0 | +263.4 | 224.4 | 360.1 |  |
| `error/missing-argument` | basic.py with no args (Rich) | 251.4 | +239.8 | 211.5 | 363.7 |  |
| `error/missing-argument-no-rich` | basic.py with no args, TYPER_USE_RICH=0 | 173.1 | +161.5 | 144.7 | 217.5 |  |
| `error/bad-int` | basic.py World --count abc (Rich) | 249.0 | +237.5 | 221.6 | 332.9 |  |
| `error/bad-int-no-rich` | basic.py World --count abc, TYPER_USE_RICH=0 | 175.2 | +163.6 | 151.0 | 221.5 |  |
