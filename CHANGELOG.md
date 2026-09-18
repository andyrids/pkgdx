<!-- pyml disable MD024 -->
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> [!NOTE]
> Types of changes:
>
> - `Added` for new features.
> - `Changed` for changes in existing functionality.
> - `Deprecated` for soon-to-be removed features.
> - `Removed` for now removed features.
> - `Fixed` for any bug fixes.
> - `Security` in case of vulnerabilities.

## [0.3.0] - 2026-09-18

### Added

- New documentation for project standards & toolchain guidance ([`docs/`](docs/)).
- Custom argparse help formatter (`_core.CLIGFormatter`).
- Custom argparse.ArgumentParser class `CLIArgumentParser` with rich error formatting.
- Concise help display on empty CLI command (`pkgdx`).
- A new CLI version option - `-v` or `--version`.

### Changed

- Excluded `.venv` from `detect-secrets` scan in `secrets-baseline` Justfile recipe.
- Made `pkgdx-typing` (mypy) hook output verbose and local only in bundled Prek config.
- Primary CLI output is now on STDOUT.
- Logs, errors, progress and other diagnostic metadata is now on STDERR.
- CLI verbosity options (`-v` or `--verbose`) have been replaced with `-d` and `--debug`.
- `pkgdx init` progress is now a multi-task checklist with a spinner, full-width overall bar, MofN
  and elapsed   time.

### Removed

- `tryceratops` [TRY003](https://docs.astral.sh/ruff/rules/raise-vanilla-args/) rule was removed
  due to false positives (builtin exceptions like `ValueError` & `TypeError`).

### Fixed

- Removed `types_or: ["python", "pyi"]` constraint from `pkgdx-secrets` hook, which defeated secret
  detection.

## [0.2.0] - 2026-08-06

### Removed

- AXI CLI & MCP server extracted to [`venv-axi`](https://github.com/andyrids/venv-axi) package.

## [0.1.0] - 2026-08-04

### Added

- AXI CLI `find --package <package>` indexes a package on a miss, then re-searches.
- AXI CLI `--refresh` flag on `show`, `find`, `tree` & `inspect`, rebuilding a stale symbol graph.
- AXI CLI `inspect --docstring` flag for complete docstring bodies.
- AXI MCP `help[]` footers, and `docstring`/`package` parameters, for CLI parity.
- TOON token-efficiency benchmark.

### Changed

- AXI `find` results are now deterministically ranked.
- AXI symbol graph schema v4.
- AXI failed signature introspection now reports `(signature unavailable)`.

### Fixed

- AXI `inherits` silently returned `count: 0` for re-exported classes.
- AXI `setup` registered an unstartable MCP server without `fastmcp`.
- AXI `serve` misreported any runtime `ImportError` as a missing `pkgdx[axi]` extra.

## [0.1.0rc8] - 2026-07-31

### Added

- AXI CLI `inherits <qualified_name>` command.

### Changed

- Renamed the canonical standards CLI subcommand `setup` to `init`.
- Moved standards & AXI CLI to separate subpackages; `axi`, `standards`.
- Clearer AXI CLI `show` & `inspect` help text.
- More consistant AXI CLI `help[]` footers on empty results.
- AXI CLI `inspect` command now accepts bare module names.
- `CLIContext.console` docstring note on relevance to `standards` subpackage.

### Fixed

- AXI CLI `show` & `inspect` raw-traceback on unimportable names.
- AXI CLI symbols mis-attributed to the wrong module.
- AXI CLI silent errors on incorrect names passed to `list` & `find` commands.

## [0.1.0rc7] - 2026-07-29

### Added

- `axi` (`pkgdx-axi`) - an Agent eXperience Interface (AXI).
  - Provides a CLI & MCP interface.
  - Fetches venv package metadata for a consuming repo.
  - Fetches public API/docstring introspection.
  - Output uses a token-efficient TOON format.
  - A `setup` command installs ambient context (`AGENTS.md`, `.vscode/mcp.json`, `.mcp.json`).
- `axi` symbol introspection is now backed by a recursive, SQLite-backed graph store.
  - Per-project, version-hash-keyed on-disk caching for introspection results.

### Changed

- `pkgdx setup` now validates the consumer `prek.toml` shape at parse time.
- Dataclass serialization is now stdlib-driven and field-agnostic.
- TOON table encoding now defaults to a pipe (`|`) delimiter mitigating comma-containing values.

### Fixed

- Introspection no longer crashes (`sqlite3.IntegrityError`) on `__module__` present, but `None`.
- A crash partway through building the symbol cache now invalidates it for future runs.

## [0.1.0rc6] - 2026-07-14

### Added

- Rich progress bar to the `setup` command, tracking the setup stages.
- Automatic disabling of the progress bar in non-TTY environments.
- Render log messages above the live progress display.

### Fixed

- Unit tests for `setup` progress now configure logging before exercising `_setup_progress()`.

## [0.1.0rc5] - 2026-07-10

### Added

- CLI setup script for automated project configuration.
- `--reset` option for CLI setup script.
- Detect missing hooks based on pkgdx config.
- Build & publish to GitLab package registry.
- Unit tests.

### Fixed

- Updated with correct Prek `update` command.
