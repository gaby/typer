# Typer CLI timings: typer-0.29.3-skip-none-py3.11

- Python 3.11.18 (CPython), annotated-doc 0.0.7, markdown-it-py 4.3.0, pydantic 2.14.4, pydantic-core 2.50.5, pygments 2.21.0, rich 15.0.0, shellingham 1.5.4, typer 0.29.3, typing-extensions 4.16.0
- Intel(R) Xeon(R) Processor @ 2.10GHz x4, Linux-6.18.44-fc-v880-x86_64-with-glibc2.39
- 30 timed runs per case after 3 warm-up runs, interleaved in shuffled rounds (seed 20261126)
- Load average before/after: [1.15, 1.02, 0.73] / [1.04, 1.01, 0.75]

Times in milliseconds. Δ is the median over the `python -c pass` floor. 'To callback' is the median time until the command function starts.

| Case | Description | Median | Δ floor | Min | p95 | To callback |
|---|---|---:|---:|---:|---:|---:|
| `baseline/python-floor` | python -c pass (interpreter start-up floor) | 11.0 | +0.0 | 10.0 | 14.9 |  |
| `baseline/import-typer` | python -c "import typer" | 67.4 | +56.4 | 61.4 | 96.7 |  |
| `params/no-params` | no parameters | 72.1 | +61.1 | 65.1 | 103.7 | 58.2 |
| `params/arg-required` | required str argument | 163.2 | +152.2 | 146.7 | 215.3 | 128.6 |
| `params/opt-bool` | bool flag | 78.1 | +67.1 | 65.8 | 101.5 | 61.2 |
| `shape/typer-run` | typer.run(main): arg + int option + bool flag | 161.1 | +150.1 | 148.5 | 210.3 | 127.8 |
| `shape/app-2-commands` | Typer() app, 2 commands, run one | 166.2 | +155.2 | 150.8 | 225.4 | 130.5 |
| `shape/app-50-commands` | Typer() app, 50 commands x 3 params, run one | 184.8 | +173.8 | 159.9 | 212.1 | 147.2 |
| `help/typer-run` | basic.py --help (Rich) | 156.5 | +145.6 | 139.4 | 212.8 |  |
| `help/app-root` | multi_commands.py --help (Rich) | 155.2 | +144.3 | 137.0 | 203.7 |  |
| `help/subcommand` | nested.py users create --help (Rich) | 153.9 | +142.9 | 131.7 | 194.5 |  |
| `error/missing-argument` | basic.py with no args (Rich) | 150.1 | +139.1 | 128.5 | 215.8 |  |
| `error/missing-argument-no-rich` | basic.py with no args, TYPER_USE_RICH=0 | 76.8 | +65.8 | 62.1 | 102.4 |  |
| `error/bad-int` | basic.py World --count abc (Rich) | 250.3 | +239.3 | 216.3 | 331.9 |  |
| `error/bad-int-no-rich` | basic.py World --count abc, TYPER_USE_RICH=0 | 172.0 | +161.0 | 148.7 | 200.5 |  |
