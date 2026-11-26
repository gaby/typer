# Typer CLI timings: typer-0.29.3-py3.11-no-bytecode

- Python 3.11.18 (CPython), annotated-doc 0.0.7, markdown-it-py 4.3.0, pydantic 2.14.4, pydantic-core 2.50.5, pygments 2.21.0, rich 15.0.0, shellingham 1.5.4, typer 0.29.3, typing-extensions 4.16.0
- Intel(R) Xeon(R) Processor @ 2.10GHz x4, Linux-6.18.44-fc-v880-x86_64-with-glibc2.39
- 20 timed runs per case after 1 warm-up runs, interleaved in shuffled rounds (seed 20261126), bytecode cache disabled
- Load average before/after: [1.04, 1.01, 0.75] / [1.1, 1.03, 0.76]

Times in milliseconds. Δ is the median over the `python -c pass` floor. 'To callback' is the median time until the command function starts.

| Case | Description | Median | Δ floor | Min | p95 | To callback |
|---|---|---:|---:|---:|---:|---:|
| `baseline/python-floor` | python -c pass (interpreter start-up floor) | 11.4 | +0.0 | 9.1 | 14.8 |  |
| `baseline/import-typer` | python -c "import typer" | 111.8 | +100.4 | 93.6 | 138.6 |  |
| `shape/typer-run` | typer.run(main): arg + int option + bool flag | 339.5 | +328.0 | 315.3 | 385.9 | 304.5 |
| `help/typer-run` | basic.py --help (Rich) | 329.3 | +317.8 | 307.0 | 375.0 |  |
