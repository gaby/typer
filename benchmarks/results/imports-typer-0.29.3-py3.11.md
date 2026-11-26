# Import-time attribution: typer-0.29.3-py3.11

Median over 7 runs of the summed `-X importtime` self time, in ms.

| Case | Modules | typer._click (vendored Click) | typer (own code) | pydantic | pydantic_core | pydantic deps | rich | markdown_it + mdurl | pygments | click (upstream) | stdlib | other | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `baseline/python-floor` | 24 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 5.0 | 0.1 | 5.1 |
| `baseline/import-typer` | 135 | 5.3 | 10.2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 43.3 | 1.0 | 63.1 |
| `baseline/argparse` | 56 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 17.0 | 0.1 | 17.1 |
| `baseline/click` | 84 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 6.3 | 29.5 | 0.1 | 35.5 |
| `params/no-params` | 247 | 4.5 | 17.7 | 25.1 | 9.9 | 9.5 | 0.0 | 0.0 | 0.0 | 0.0 | 62.8 | 1.3 | 132.3 |
| `shape/typer-run` | 247 | 4.8 | 15.0 | 27.1 | 10.6 | 10.1 | 0.0 | 0.0 | 0.0 | 0.0 | 59.5 | 1.3 | 131.5 |
| `shape/app-50-commands` | 247 | 4.8 | 15.4 | 25.9 | 11.2 | 9.8 | 0.0 | 0.0 | 0.0 | 0.0 | 60.7 | 1.3 | 130.5 |
| `help/typer-run` | 301 | 4.4 | 10.1 | 0.0 | 0.0 | 0.0 | 27.3 | 17.5 | 6.0 | 0.0 | 47.3 | 1.0 | 117.3 |
| `help/typer-run-no-rich` | 137 | 4.9 | 9.6 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 44.6 | 0.8 | 61.6 |
| `help/subcommand` | 398 | 5.5 | 18.4 | 26.2 | 10.6 | 9.9 | 28.2 | 16.4 | 5.4 | 0.0 | 67.3 | 1.6 | 192.3 |
| `error/bad-int` | 398 | 5.0 | 16.1 | 26.6 | 9.9 | 9.7 | 29.5 | 17.2 | 5.5 | 0.0 | 67.2 | 1.5 | 188.4 |
| `error/bad-int-no-rich` | 248 | 4.8 | 14.8 | 27.4 | 10.2 | 9.6 | 0.0 | 0.0 | 0.0 | 0.0 | 57.3 | 1.2 | 127.5 |

## Slowest 12 modules per case (self time, ms)

- `baseline/python-floor`: `_collections_abc` 0.8, `site` 0.5, `encodings.aliases` 0.5, `encodings` 0.5, `os` 0.3, `_frozen_importlib_external` 0.3, `codecs` 0.3, `posix` 0.3, `encodings.utf_8` 0.2, `time` 0.2, `io` 0.2, `abc` 0.1
- `baseline/import-typer`: `typer._coercion` 3.1, `typing` 2.4, `typer.core` 1.9, `inspect` 1.9, `platform` 1.7, `enum` 1.4, `ipaddress` 1.4, `typer._click.termui` 1.1, `typer.params` 1.1, `re._constants` 1.1, `_ast` 1.1, `datetime` 1.0
- `baseline/argparse`: `enum` 1.3, `argparse` 1.2, `locale` 1.0, `collections` 0.8, `gettext` 0.8, `_sre` 0.8, `shutil` 0.7, `_collections_abc` 0.7, `re` 0.6, `encodings` 0.6, `functools` 0.5, `re._parser` 0.5
- `baseline/click`: `typing` 2.4, `enum` 2.0, `click.types` 1.7, `inspect` 1.6, `platform` 1.5, `click.core` 1.4, `ast` 1.1, `_weakrefset` 1.0, `datetime` 1.0, `collections` 0.9, `locale` 0.9, `tokenize` 0.8
- `params/no-params`: `pydantic_core.core_schema` 8.0, `typer._adapters` 6.6, `pydantic.types` 5.3, `annotated_types` 5.0, `pydantic._internal._decorators` 2.9, `typer._coercion` 2.9, `typing` 2.3, `typing_extensions` 2.2, `pydantic.json_schema` 2.1, `_hashlib` 2.0, `typer.core` 1.7, `platform` 1.6
- `shape/typer-run`: `pydantic_core.core_schema` 8.4, `typer._adapters` 5.7, `pydantic.types` 5.5, `annotated_types` 5.4, `pydantic._internal._decorators` 2.9, `typer._coercion` 2.7, `typing` 2.4, `typing_extensions` 2.2, `pydantic.json_schema` 2.0, `_hashlib` 1.9, `enum` 1.9, `inspect` 1.9
- `shape/app-50-commands`: `pydantic_core.core_schema` 9.0, `pydantic.types` 5.5, `typer._adapters` 5.5, `annotated_types` 5.3, `pydantic.json_schema` 3.0, `pydantic._internal._decorators` 2.9, `typer._coercion` 2.8, `typing` 2.6, `typing_extensions` 2.2, `_hashlib` 2.0, `enum` 2.0, `inspect` 1.9
- `help/typer-run`: `rich.console` 3.1, `typer._coercion` 2.9, `rich.traceback` 2.5, `typing` 2.5, `fractions` 2.1, `rich._emoji_codes` 2.0, `enum` 1.9, `inspect` 1.9, `rich.pretty` 1.8, `platform` 1.6, `logging` 1.6, `typer.core` 1.5
- `help/typer-run-no-rich`: `typer._coercion` 3.1, `typing` 2.6, `inspect` 2.0, `enum` 2.0, `platform` 1.8, `typer.core` 1.6, `ipaddress` 1.1, `typer.main` 1.1, `typer._click.termui` 1.1, `ast` 1.1, `tokenize` 1.0, `datetime` 1.0
- `help/subcommand`: `pydantic_core.core_schema` 8.5, `typer._adapters` 6.3, `pydantic.types` 5.5, `annotated_types` 5.3, `rich.console` 2.9, `rich._emoji_codes` 2.8, `typing` 2.7, `pydantic._internal._decorators` 2.7, `typing_extensions` 2.7, `typer._coercion` 2.6, `inspect` 2.2, `rich.traceback` 2.1
- `error/bad-int`: `pydantic_core.core_schema` 8.0, `pydantic.types` 5.5, `annotated_types` 5.4, `typer._adapters` 5.3, `pydantic._internal._decorators` 3.0, `rich.console` 2.9, `rich._emoji_codes` 2.8, `typer._coercion` 2.7, `typing` 2.5, `typing_extensions` 2.3, `rich.traceback` 2.2, `markdown_it.rules_block.html_block` 2.2
- `error/bad-int-no-rich`: `pydantic_core.core_schema` 8.4, `typer._adapters` 5.6, `pydantic.types` 5.4, `annotated_types` 5.1, `pydantic._internal._decorators` 3.2, `typer._coercion` 2.7, `typing` 2.4, `typing_extensions` 2.3, `pydantic.json_schema` 2.0, `_hashlib` 1.9, `enum` 1.9, `platform` 1.9
