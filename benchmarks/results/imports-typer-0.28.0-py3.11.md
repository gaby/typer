# Import-time attribution: typer-0.28.0-py3.11

Median over 7 runs of the summed `-X importtime` self time, in ms.

| Case | Modules | typer._click (vendored Click) | typer (own code) | rich | markdown_it + mdurl | pygments | stdlib | other | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `baseline/import-typer` | 132 | 4.6 | 5.8 | 0.0 | 0.0 | 0.0 | 43.9 | 0.8 | 57.5 |
| `params/no-params` | 133 | 5.7 | 6.2 | 0.0 | 0.0 | 0.0 | 45.4 | 0.7 | 58.8 |
| `shape/typer-run` | 133 | 4.4 | 5.6 | 0.0 | 0.0 | 0.0 | 42.3 | 0.8 | 53.8 |
| `help/typer-run` | 300 | 6.7 | 10.3 | 39.8 | 24.0 | 8.0 | 77.5 | 1.4 | 164.6 |
| `help/subcommand` | 300 | 5.0 | 7.5 | 29.1 | 16.7 | 6.3 | 58.8 | 1.2 | 123.4 |
| `error/bad-int` | 300 | 4.7 | 6.6 | 29.2 | 18.1 | 5.2 | 52.9 | 0.9 | 117.5 |

## Slowest 12 modules per case (self time, ms)

- `baseline/import-typer`: `typing` 2.4, `inspect` 1.8, `gettext` 1.8, `platform` 1.7, `threading` 1.4, `enum` 1.3, `ipaddress` 1.3, `typer.main` 1.2, `ast` 1.1, `_ast` 1.1, `tokenize` 1.0, `typer.params` 1.0
- `params/no-params`: `typing` 2.8, `platform` 2.2, `gettext` 2.0, `inspect` 2.0, `threading` 1.6, `ipaddress` 1.4, `enum` 1.3, `typer._click.core` 1.3, `typer.main` 1.2, `ast` 1.2, `tokenize` 1.1, `_ast` 1.1
- `shape/typer-run`: `typing` 2.5, `inspect` 2.0, `enum` 1.9, `platform` 1.7, `difflib` 1.6, `threading` 1.4, `ipaddress` 1.2, `typer.main` 1.1, `typer.params` 1.0, `ast` 1.0, `collections` 0.9, `urllib.parse` 0.9
- `help/typer-run`: `rich.console` 4.0, `typing` 3.6, `rich.traceback` 3.6, `enum` 2.7, `logging` 2.6, `inspect` 2.6, `platform` 2.5, `rich._emoji_codes` 2.5, `difflib` 2.5, `rich.pretty` 2.4, `rich.syntax` 2.3, `rich.table` 2.2
- `help/subcommand`: `rich.console` 4.2, `typing` 3.2, `enum` 2.7, `rich.traceback` 2.5, `inspect` 2.2, `rich._emoji_codes` 2.1, `platform` 1.8, `rich.table` 1.7, `rich.pretty` 1.7, `difflib` 1.7, `logging` 1.6, `ipaddress` 1.5
- `error/bad-int`: `rich.console` 3.2, `typing` 3.0, `rich.traceback` 2.3, `inspect` 2.1, `enum` 2.1, `rich._emoji_codes` 2.0, `platform` 1.7, `logging` 1.6, `rich.table` 1.6, `rich.pretty` 1.6, `rich.syntax` 1.6, `threading` 1.6
