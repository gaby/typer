# In-process breakdown: typer-0.29.3-py3.13

## Waterfall of one invocation (median ms)

| Stage | `no_params.py` | `basic.py World --count 3 --loud` | `multi_commands.py hello World` | `scale_commands.py cmd25 World --count 2` | `basic.py --help` |
|---|---:|---:|---:|---:|---:|
| interpreter start | 14.1 | 13.1 | 12.7 | 11.3 | 11.0 |
| import typer | 62.0 | 63.0 | 57.6 | 50.9 | 54.2 |
| app module body | 0.9 | 1.1 | 1.0 | 2.8 | 0.9 |
| build command (get_command) | 0.1 | 0.4 | 0.9 | 7.3 | 0.4 |
| parse + validate params | 85.9 | 85.8 | 85.0 | 78.6 |  |
| command body + exit | 0.2 | 0.2 | 0.2 | 0.3 |  |
| interpreter shutdown | 39.4 | 40.9 | 41.5 | 39.1 | 37.6 |
| (other: driver overhead) | 2.1 | 2.0 | 2.1 | 1.7 | 1.8 |
| **TOTAL** | 204.0 | 205.9 | 197.7 | 199.4 | 185.2 |
|   of which Pydantic adapters | 85.2 | 85.0 | 84.0 | 77.7 | 0.0 |
|   of which first adapter (incl. Pydantic import) | 85.2 | 84.6 | 83.3 | 76.9 | 0.0 |
| parse + render help |  |  |  |  | 79.1 |
| Pydantic adapters built | 1 | 3 | 5 | 6 | 0 |
| Pydantic / Rich loaded | yes / no | yes / no | yes / no | yes / no | no / yes |

## Import sets, wall time of `python -c ...`

| What | Median (ms) | Min (ms) |
|---|---:|---:|
| python -c pass | 11.9 | 11.0 |
| import typer | 79.3 | 68.6 |
| import typer + typer._adapters (Pydantic) | 164.5 | 138.8 |
| import typer + first bool TypeAdapter | 170.9 | 160.5 |
| import typer + typer.rich_utils | 173.6 | 150.8 |
| Rich modules rich_utils needs, minus markdown/traceback | 82.8 | 66.7 |
| ... + rich.markdown | 120.0 | 106.7 |
| ... + rich.traceback | 108.2 | 91.6 |
| ... + rich.markdown + rich.traceback (what rich_utils imports) | 166.4 | 120.5 |

## Interpreter shutdown, wall time of `python -c ...` (median ms)

| State before exit | normal exit | os._exit(0) | gc.freeze() then exit | Shutdown (normal − os._exit) |
|---|---:|---:|---:|---:|
| python -c pass | 15.0 | 12.4 | 13.3 | 2.5 |
| import typer | 85.0 | 71.2 | 68.6 | 13.9 |
| import typer + 3 Pydantic adapters | 200.1 | 148.1 | 154.3 | 52.1 |
| import typer + typer.rich_utils | 157.3 | 150.7 | 141.3 | 6.6 |
| run a 3-param command (standalone) | 199.7 | 156.2 | 167.4 | 43.5 |
