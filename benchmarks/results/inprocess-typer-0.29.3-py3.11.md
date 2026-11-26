# In-process breakdown: typer-0.29.3-py3.11

## Waterfall of one invocation (median ms)

| Stage | `no_params.py` | `basic.py World --count 3 --loud` | `multi_commands.py hello World` | `scale_commands.py cmd25 World --count 2` | `basic.py --help` |
|---|---:|---:|---:|---:|---:|
| interpreter start | 9.4 | 9.3 | 9.8 | 9.8 | 9.1 |
| import typer | 47.7 | 46.4 | 49.2 | 47.1 | 46.3 |
| app module body | 0.6 | 0.8 | 0.8 | 3.1 | 0.8 |
| build command (get_command) | 0.1 | 0.4 | 0.7 | 7.4 | 0.4 |
| parse + validate params | 74.4 | 71.9 | 71.2 | 72.3 |  |
| command body + exit | 0.1 | 0.2 | 0.1 | 0.3 |  |
| interpreter shutdown | 36.6 | 35.4 | 35.5 | 35.3 | 30.4 |
| (other: driver overhead) | 1.4 | 1.5 | 1.5 | 1.5 | 1.5 |
| **TOTAL** | 175.8 | 165.8 | 172.0 | 181.1 | 156.2 |
|   of which Pydantic adapters | 74.0 | 71.2 | 70.2 | 71.4 | 0.0 |
|   of which first adapter (incl. Pydantic import) | 74.0 | 70.8 | 69.6 | 70.7 | 0.0 |
| parse + render help |  |  |  |  | 64.5 |
| Pydantic adapters built | 1 | 3 | 5 | 6 | 0 |
| Pydantic / Rich loaded | yes / no | yes / no | yes / no | yes / no | no / yes |

## Pydantic validation cost per annotation (fresh process each)

| Annotation | import typer (ms) | import Pydantic + adapters module (ms) | first TypeAdapter (ms) | each later one (µs) |
|---|---:|---:|---:|---:|
| bool (also --help, completion flags) | 43.7 | 63.2 | 11.79 | 66 |
| str | 41.8 | 61.4 | 11.49 | 66 |
| int | 40.9 | 59.8 | 11.40 | 28 |
| int with min/max | 40.5 | 60.9 | 11.77 | 119 |
| float | 39.6 | 58.2 | 11.60 | 29 |
| Enum | 40.0 | 57.6 | 11.10 | 87 |
| Literal | 43.9 | 60.2 | 11.73 | 89 |
| Path | 41.0 | 60.9 | 12.05 | 88 |
| Path, exists=True | 40.3 | 57.5 | 11.98 | 91 |
| datetime | 42.0 | 63.7 | 11.91 | 28 |
| UUID | 41.4 | 62.8 | 11.47 | 35 |
| list[str] | 46.9 | 68.1 | 14.30 | 179 |
| tuple[str, int] | 41.0 | 58.9 | 12.38 | 198 |

## Building the Click command tree (`get_command`, steady state)

| Commands | Params per command | Median (ms) |
|---:|---:|---:|
| 1 | 1 | 0.27 |
| 1 | 3 | 0.29 |
| 1 | 10 | 0.32 |
| 1 | 30 | 0.64 |
| 10 | 3 | 0.94 |
| 50 | 3 | 4.71 |
| 200 | 3 | 19.45 |

## Per-invocation cost inside a running process (median µs)

| Call | Median (µs) |
|---|---:|
| Typer app(), 1 command | 669 |
| Typer app(), 50 commands | 5610 |
| CliRunner().invoke(), 1 command | 919 |
| argparse: build parser + parse | 221 |

## Import sets, wall time of `python -c ...`

| What | Median (ms) | Min (ms) |
|---|---:|---:|
| python -c pass | 11.2 | 9.1 |
| import typer | 67.8 | 65.0 |
| import typer + typer._adapters (Pydantic) | 135.0 | 119.4 |
| import typer + first bool TypeAdapter | 165.6 | 148.7 |
| import typer + typer.rich_utils | 148.3 | 122.4 |
| Rich modules rich_utils needs, minus markdown/traceback | 61.0 | 58.2 |
| ... + rich.markdown | 106.5 | 92.2 |
| ... + rich.traceback | 87.6 | 74.6 |
| ... + rich.markdown + rich.traceback (what rich_utils imports) | 113.7 | 99.4 |

## Interpreter shutdown, wall time of `python -c ...` (median ms)

| State before exit | normal exit | os._exit(0) | gc.freeze() then exit | Shutdown (normal − os._exit) |
|---|---:|---:|---:|---:|
| python -c pass | 12.1 | 9.0 | 9.7 | 3.1 |
| import typer | 72.0 | 63.6 | 60.7 | 8.4 |
| import typer + 3 Pydantic adapters | 168.9 | 140.6 | 151.4 | 28.4 |
| import typer + typer.rich_utils | 133.2 | 111.5 | 131.1 | 21.7 |
| run a 3-param command (standalone) | 172.7 | 133.0 | 134.8 | 39.7 |
