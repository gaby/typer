# In-process breakdown: typer-0.28.0-py3.11

## Building the Click command tree (`get_command`, steady state)

| Commands | Params per command | Median (ms) |
|---:|---:|---:|
| 1 | 1 | 0.15 |
| 1 | 3 | 0.20 |
| 1 | 10 | 0.30 |
| 1 | 30 | 0.62 |
| 10 | 3 | 0.94 |
| 50 | 3 | 4.25 |
| 200 | 3 | 16.66 |

## Per-invocation cost inside a running process (median µs)

| Call | Median (µs) |
|---|---:|
| Typer app(), 1 command | 325 |
| Typer app(), 50 commands | 4485 |
| CliRunner().invoke(), 1 command | 387 |
| argparse: build parser + parse | 242 |
