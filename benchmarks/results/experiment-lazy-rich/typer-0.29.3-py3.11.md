# Typer CLI timings: typer-0.29.3-py3.11

- Python 3.11.18 (CPython), annotated-doc 0.0.7, markdown-it-py 4.3.0, pydantic 2.14.4, pydantic-core 2.50.5, pygments 2.21.0, rich 15.0.0, shellingham 1.5.4, typer 0.29.3, typing-extensions 4.16.0
- Intel(R) Xeon(R) Processor @ 2.10GHz x4, Linux-6.18.44-fc-v880-x86_64-with-glibc2.39
- 40 timed runs per case after 1 warm-up runs, interleaved in shuffled rounds (seed 1001-1004 (4 chunks, alternated with the other side))
- Load average before/after: [0.04, 0.49, 0.71] / [0.97, 0.7, 0.76]

Times in milliseconds. Δ is the median over the `python -c pass` floor. 'To callback' is the median time until the command function starts.

| Case | Description | Median | Δ floor | Min | p95 | To callback |
|---|---|---:|---:|---:|---:|---:|
| `baseline/python-floor` | python -c pass (interpreter start-up floor) | 10.9 | +0.0 | 9.6 | 14.7 |  |
| `baseline/import-typer` | python -c "import typer" | 66.1 | +55.2 | 58.2 | 95.2 |  |
| `shape/typer-run` | typer.run(main): arg + int option + bool flag | 172.5 | +161.6 | 145.4 | 219.7 | 136.6 |
| `help/typer-run` | basic.py --help (Rich) | 153.6 | +142.7 | 135.4 | 189.4 |  |
| `help/typer-run-no-rich` | basic.py --help, TYPER_USE_RICH=0 | 72.5 | +61.6 | 62.7 | 95.4 |  |
| `help/app-root` | multi_commands.py --help (Rich) | 148.7 | +137.8 | 138.0 | 196.2 |  |
| `help/subcommand` | nested.py users create --help (Rich) | 245.4 | +234.4 | 220.9 | 308.9 |  |
| `help/app-50-commands` | scale_commands.py --help (Rich, 50 commands) | 171.2 | +160.3 | 152.3 | 208.0 |  |
| `error/missing-argument` | basic.py with no args (Rich) | 240.5 | +229.6 | 210.0 | 303.9 |  |
| `error/bad-int` | basic.py World --count abc (Rich) | 236.6 | +225.6 | 204.5 | 276.0 |  |
| `error/bad-int-no-rich` | basic.py World --count abc, TYPER_USE_RICH=0 | 163.6 | +152.6 | 146.3 | 186.5 |  |
