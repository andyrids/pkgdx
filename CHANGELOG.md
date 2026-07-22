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

## [0.1.0rc7]

### Added

- `venv-axi` (`pytack-venv-axi`) - an Agent eXperience Interface (AXI).
  - Provides a CLI & MCP interface.
  - Fetches venv package metadata for a consuming repo.
  - Fetches public API/docstring introspection.
  - Output uses a token-efficient TOON format.
  - A `setup` command installs ambient context (`AGENTS.md`, `.vscode/mcp.json`, `.mcp.json`)
- `venv-axi` symbol introspection is now backed by a recursive,
  SQLite-backed graph store (`find`/`tree`/`inspect` CLI subcommands;
  `show_module`/`get_symbol`/`find_symbol`/`get_inheritors`/
  `get_module_tree` MCP tools), replacing the previous flat,
  top-level-only API scan.
- Per-project, version-hash-keyed on-disk caching for introspection
  results, invalidated automatically when a package's installed
  version changes.

### Changed

- TOON table encoding now defaults to a pipe (`|`) delimiter instead
  of comma, to avoid ambiguity with comma-containing docstrings/values
  (**breaking change** for any consumer parsing `venv-axi`/MCP TOON
  output with a hardcoded comma delimiter).

### Fixed

- Introspection no longer crashes (`sqlite3.IntegrityError`) when a
  walked object's `__module__` attribute is present but `None`.
- A crash partway through building the symbol cache no longer leaves
  behind a partially-populated cache that is silently treated as
  valid on the next run; it now clears the partial state and raises
  `pytack.exceptions.StoreError`.

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
- Detect missing hooks based on pkgdevx config.
- Build & publish to GitLab package registry.
- Unit tests.

### Fixed

- Updated with correct Prek `update` command.
