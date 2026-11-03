<!-- pyml disable MD024 -->
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> [!NOTE]
>
> - `[SemVer] - yyyy-mm-dd` or `[Unreleased]` for release heading.
> - `Added` for new features.
> - `Changed` for changes in existing functionality.
> - `Deprecated` for soon-to-be removed features.
> - `Removed` for now removed features.
> - `Fixed` for any bug fixes.
> - `Security` in case of vulnerabilities.

## [Unreleased]

### Added

- `-q`, `--no-color` & `--no-input` run flags, `GLOBAL OPTIONS:` in `--help` & `-h` after a usage
  error, from `pyclig` 0.3.0.
- `test_cli_conforms_to_the_guidelines` runs `pyclig`'s conformance kit against the CLI.

### Changed

- `pyclig` is pinned to `~=0.3.0` (was `~=0.2`).
- `--help` lists `EXAMPLES:` before `OPTIONS:`.
- `ToolNotFoundError` carries a `hint`. A hook shim whose tool is missing from `PATH` prints
  `error:` with the fact, then the remedy on the next line.

### Fixed

- `-q` on `pkgdx init` & `pkgdx config` drops the OK rows & the closing line. Warnings, failures &
  `config`'s STDOUT rows stay.

## [0.7.0] - 2026-11-02

### Added

- `[tool.pkgdx] exclude` in `pyproject.toml` lists paths the lint, format, typing & markdown hooks
  skip.
- `pkgdx config` lists each excluded path, marking one that does not exist `(not found)`.

### Changed

- `docs/guidance/toolchain-pkgdx.md` (1.1.0) & `toolchain-mypy.md` (1.0.1) describe the exclude
  list.

### Fixed

- The lint, format & typing hooks can skip submodules & vendored code (#5). This needs no reset, but
  both a `pkgdx` lock upgrade & `prek update`.
- The bundled `ruff.toml` no longer clears Ruff's default exclusions. A directory Ruff skips by
  default, e.g. `dist`, `_build`, `venv` or `node_modules`, is no longer linted or formatted at any
  depth, even when not gitignored. Exported user copies keep the old `exclude = []` until that line
  is deleted.
- The `prek.toml` template's `#:schema` URL points at prek's `main` branch (it returned a 404).
- `pkgdx init` creates `.secrets.baseline` with the same exclude pattern as the `pkgdx-secrets` hook.

## [0.6.0] - 2026-10-31

### Added

- Shell completion (`_PKGDX_COMPLETE`), from click.
- `EXAMPLES:` in the help, as `docs/guidance/standard-cli.md` asks.
- Per-command `EXAMPLES:` in `pkgdx init --help` & `pkgdx config --help`.

### Changed

- The CLI is built on [pyclig](https://github.com/andyrids/pyclig) & click instead of argparse.
- Exit codes: usage errors exit `2` (was `64`), unexpected errors `70` (was `1`/`2`) (#11, §6).
- `-v` prints `pkgdx <version>` (was `v<version>`); bare `pkgdx` prints concise help.
- Help: click layout, `-d, --debug` listed for every command.
- Hook shims print `error: <message>` (was `pkgdx: <message>`) & map Ctrl-C & crashes too.
- The `init` spinner shows only on an interactive STDERR (honours `TTY_INTERACTIVE`).
- `docs/guidance/standard-cli.md`, `toolchain-logging.md` & `toolchain-pytest.md` describe the
  pyclig CLI, logging & tests (2.0.0 each, with MUST NOT rules).
- `docs/guidance/` files carry `version` & `updated` frontmatter; `reference-toolchain-uv.md` is
  now `toolchain-uv.md`, & `toolchain-pkgdx.md` is new.

### Removed

- argparse option prefixes, e.g. `--res` for `--reset`; Python 3.14 argparse help colours.
- `pkgdx.logging` (`GLOBAL_CONSOLE`, `CLI_CONSOLE`, `configure_*_logging`) & `config.toml`.
- `pkgdx._core.ExitCode`, `CLIContext` & `CLIGFormatter`.
- `docs/specification/`.

### Fixed

- Usage errors go to STDERR only & print user input literally (#7).
- Importing `pkgdx` no longer redirects Rich's global console to STDERR (#8).
- `-d/--debug` is accepted after the command name (#9).
- Ctrl-C outside the step runner, incl. hook shims, prints no traceback (#10).
- STDOUT honours `FORCE_COLOR`, `TTY_COMPATIBLE` & `NO_COLOR` (#11).
- `pkgdx.__main__` imports without distribution metadata (#12).
- CLI tests assert each stream & no longer patch Rich private attributes (#13).
- Logging uses one handler per run, with no unused `config.toml` entries (#14).
- Piped output on Windows is UTF-8, so `PKGDX_CONFIG_DIR` paths never fail to encode.
- A hook whose tool is not on `PATH` exits 1 with `error:` & a hint, not a traceback (was `70`).
- `pkgdx init` warns & uses the project root when `git` is not on `PATH`, instead of crashing.
- `pkgdx init` reads & writes `prek.toml` & `hooks.toml` as UTF-8, not the locale's cp1252.
- A non-UTF-8 `prek.toml` or `hooks.toml` fails its `pkgdx init` step instead of crashing.
- `pkgdx-markdown` puts PyMarkdown global options, e.g. `--stack-trace`, before `scan` (#2, part b).

## [0.5.0] - 2026-10-29

### Added

- Releases are published to PyPI via Trusted Publishing, after the GitLab Package Registry.
- User config directory: `ruff.toml`, `mypy.ini`, `pymarkdown.toml` and `hooks.toml` are read from
  `%APPDATA%\pkgdx` on Windows, or `$XDG_CONFIG_HOME/pkgdx` (else `~/.config/pkgdx`) elsewhere.
  Each file falls back to the bundled one. `PKGDX_CONFIG_DIR` overrides the directory and fails
  with exit code 1 when it is not an existing directory.
- `pkgdx config` lists each file with its source (user or bundled) and resolved path on standard
  output, and names the user config directory and whether `PKGDX_CONFIG_DIR` set it on standard
  error. `pkgdx config --export` copies the bundled files into the user config directory without
  overwriting existing files, and reports each file as created or unchanged, like `pkgdx init`.

### Changed

- Release tag pipelines run lint and tests before the package is built and published.
- pkgdx's own `secrets` hook in `prek.toml` runs `pkgdx-secrets-hook` instead of
  `detect-secrets-hook` directly.
- `pkgdx init` prints one ok / warn / FAIL line per step, saying what it created or updated, then a
  one-line summary.
- `pkgdx init` reports a missing Git repository, `prek install` failures and `prek update --check`
  results as inline warnings (exit code 0), not log lines.
- Ctrl-C during `pkgdx init` names the interrupted step and exits with code 130.

### Fixed

- `pkgdx-secrets` hook and `.secrets.baseline` creation run `detect-secrets` in Python UTF-8 mode
  (`PYTHONUTF8=1`), matching Linux CI. On Windows, UTF-8 files with characters that cp1252 cannot
  decode (e.g. Rich's heavy box-drawing `━`) were silently skipped. Windows users may see new
  findings and should audit or refresh their `.secrets.baseline`.
- `pkgdx init` reports an invalid `prek.toml` or `PKGDX_CONFIG_DIR`, or a user `hooks.toml` it
  cannot merge, on its step, with exit code 1 and no traceback.
- An interrupted `detect-secrets` scan no longer leaves a partial `.secrets.baseline`.
- `pkgdx init` no longer writes an invalid `prek.toml` when a repo lists its hooks inline
  (`hooks = [...]`). The inline hooks are kept and converted to `[[repos.hooks]]` tables.

## [0.4.1] - 2026-10-16

### Changed

- Disabled `plugins.table-column-style.enabled` to mitigate [MD060 false positives](https://github.com/jackdewinter/pymarkdown/issues/1698).

## [0.4.0] - 2026-09-26

### Added

- CI clean-tree and wheel-name guards in `build-package-job` for tag builds.

### Changed

- Added `{ git = { commit = true, tags = true } }` to `cache-keys` for uv.
- Added `maintainers`, `keywords` and `Documentation` URL to project metadata.
- Declared explicit sdist `include` and wheel `packages` build targets.

### Fixed

- Added `dist_name = "pkgdx"` to `[tool.hatch.version.raw-options]`, enabling
  `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PKGDX` to work correctly in CI/CD context.
- `pkgdx-typing` hook defaults to checking the project (`files = .`, tests excluded) instead of
  failing with "Missing target".
- `pkgdx-markdown` hook passes `--continue-on-error`, so a PyMarkdown tokenizer crash fails only the
  affected file (named in the output) instead of aborting the whole scan.

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
- GitLab CI no longer creates a duplicate push pipeline when an MR is already open.

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
