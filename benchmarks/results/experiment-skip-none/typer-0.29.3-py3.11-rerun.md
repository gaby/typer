# Typer CLI timings: typer-0.29.3-py3.11-rerun

- Python 3.11.18 (CPython), annotated-doc 0.0.7, markdown-it-py 4.3.0, pydantic 2.14.4, pydantic-core 2.50.5, pygments 2.21.0, rich 15.0.0, shellingham 1.5.4, typer 0.29.3, typing-extensions 4.16.0
- Intel(R) Xeon(R) Processor @ 2.10GHz x4, Linux-6.18.44-fc-v880-x86_64-with-glibc2.39
- 30 timed runs per case after 3 warm-up runs, interleaved in shuffled rounds (seed 20261126)
- Load average before/after: [0.93, 1.0, 0.78] / [1.01, 1.01, 0.81]

Times in milliseconds. Δ is the median over the `python -c pass` floor. 'To callback' is the median time until the command function starts.

| Case | Description | Median | Δ floor | Min | p95 | To callback |
|---|---|---:|---:|---:|---:|---:|
| `baseline/python-floor` | python -c pass (interpreter start-up floor) | 11.0 | +0.0 | 10.0 | 14.7 |  |
| `baseline/import-typer` | python -c "import typer" | 74.5 | +63.5 | 58.7 | 86.2 |  |
| `params/no-params` | no parameters | 165.8 | +154.8 | 147.4 | 225.2 | 131.3 |
| `params/arg-required` | required str argument | 172.2 | +161.2 | 151.7 | 211.4 | 136.1 |
| `params/opt-bool` | bool flag | 171.0 | +160.0 | 147.7 | 228.5 | 136.9 |
| `shape/typer-run` | typer.run(main): arg + int option + bool flag | 170.5 | +159.5 | 150.9 | 222.9 | 134.4 |
| `shape/app-2-commands` | Typer() app, 2 commands, run one | 170.5 | +159.5 | 141.6 | 198.5 | 134.9 |
| `shape/app-50-commands` | Typer() app, 50 commands x 3 params, run one | 183.1 | +172.1 | 159.4 | 234.8 | 147.2 |
| `help/typer-run` | basic.py --help (Rich) | 154.5 | +143.5 | 128.4 | 198.0 |  |
| `help/app-root` | multi_commands.py --help (Rich) | 152.9 | +141.9 | 133.0 | 187.7 |  |
| `help/subcommand` | nested.py users create --help (Rich) | 255.5 | +244.5 | 226.2 | 329.6 |  |
| `error/missing-argument` | basic.py with no args (Rich) | 243.7 | +232.7 | 207.9 | 301.8 |  |
| `error/missing-argument-no-rich` | basic.py with no args, TYPER_USE_RICH=0 | 172.4 | +161.4 | 143.6 | 203.1 |  |
| `error/bad-int` | basic.py World --count abc (Rich) | 237.1 | +226.1 | 224.9 | 280.4 |  |
| `error/bad-int-no-rich` | basic.py World --count abc, TYPER_USE_RICH=0 | 168.4 | +157.4 | 147.2 | 229.2 |  |
