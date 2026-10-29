# Consuming Repository For `pkgdx`

<!-- pyml disable-next-line line-length -->
![PyPI - Version](https://img.shields.io/pypi/v/pkgdx?style=plastic) ![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fandyrids%2Fpkgdx%2Fmain%2Fpyproject.toml&style=plastic) [![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/) [![prek](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/j178/prek/master/docs/assets/badge-v0.json)](https://github.com/j178/prek) [![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

This package is a workspace member for the main `pkgdx` project and is used to
test `pkgdx` setup logic in a consuming repository.

## Testing

>[!warning]
>The commands below should be run from the `pkgdx` root.

The `pkgdx/Justfile` contains a recipe for running pkgdx against the
`testing` package:

```sh
just test
```

To run a full reset and setup, add the `--reset` option:

```sh
just test --reset
```

This test could be run manually with the following command:

```sh
uv run --directory consumers/testing pkgdx -v init
```

To run a full reset and setup, add the `--reset` option:

```sh
uv run --directory consumers/testing pkgdx -v init --reset
```

>[!tip]
>The pkgdx `--verbose` or `-v` or option enables verbose logging.
