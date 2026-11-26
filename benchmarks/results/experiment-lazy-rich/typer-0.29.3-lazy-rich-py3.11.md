# Typer CLI timings: typer-0.29.3-lazy-rich-py3.11

- Python 3.11.18 (CPython), annotated-doc 0.0.7, markdown-it-py 4.3.0, pydantic 2.14.4, pydantic-core 2.50.5, pygments 2.21.0, rich 15.0.0, shellingham 1.5.4, typer 0.29.3, typing-extensions 4.16.0
- Intel(R) Xeon(R) Processor @ 2.10GHz x4, Linux-6.18.44-fc-v880-x86_64-with-glibc2.39
- 40 timed runs per case after 1 warm-up runs, interleaved in shuffled rounds (seed 1001-1004 (4 chunks, alternated with the other side))
- Load average before/after: [0.37, 0.53, 0.72] / [0.98, 0.72, 0.76]

Times in milliseconds. Δ is the median over the `python -c pass` floor. 'To callback' is the median time until the command function starts.

| Case | Description | Median | Δ floor | Min | p95 | To callback |
|---|---|---:|---:|---:|---:|---:|
| `baseline/python-floor` | python -c pass (interpreter start-up floor) | 11.4 | +0.0 | 10.1 | 14.6 |  |
| `baseline/import-typer` | python -c "import typer" | 67.4 | +56.0 | 60.4 | 87.0 |  |
| `shape/typer-run` | typer.run(main): arg + int option + bool flag | 173.0 | +161.6 | 138.3 | 226.3 | 134.2 |
| `help/typer-run` | basic.py --help (Rich) | 115.8 | +104.4 | 97.5 | 148.4 |  |
| `help/typer-run-no-rich` | basic.py --help, TYPER_USE_RICH=0 | 74.7 | +63.3 | 64.8 | 90.4 |  |
| `help/app-root` | multi_commands.py --help (Rich) | 110.9 | +99.5 | 97.6 | 153.2 |  |
| `help/subcommand` | nested.py users create --help (Rich) | 212.8 | +201.5 | 181.6 | 241.6 |  |
| `help/app-50-commands` | scale_commands.py --help (Rich, 50 commands) | 134.9 | +123.6 | 117.5 | 167.7 |  |
| `error/missing-argument` | basic.py with no args (Rich) | 202.2 | +190.8 | 173.1 | 243.3 |  |
| `error/bad-int` | basic.py World --count abc (Rich) | 201.0 | +189.7 | 172.5 | 244.5 |  |
| `error/bad-int-no-rich` | basic.py World --count abc, TYPER_USE_RICH=0 | 166.6 | +155.2 | 144.0 | 216.5 |  |
