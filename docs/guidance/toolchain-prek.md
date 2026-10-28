---
context-hierarchy: Layer 3
context-hierarchy-role: Reference material
immutable: true
recommended-context-tokens: 2500
tags: [prek, pre-commit]
---

# Toolchain - `Prek`

Prek is used as a pre-commit hook manager and is installed as a dependency. Running Prek through
`uv run` ensures that the project virtual environment is activated and utilized.

## Commands

- `uv run prek install` - Install Git shims
- `uv run prek run` - Run hooks for files staged in Git
- `uv run prek run -vvv` - Run hooks with verbose output
- `uv run prek run --all-files` - Run hooks for all files
- `uv run prek validate-config prek.toml` - Validate a Prek config

## Configuration

- Project config: `prek.toml`
  - Root Prek config for the Pkgdx package
  - MUST not be changed by hand - re-run `pkgdx init` instead
- Bundled config: `src/pkgdx/standards/hooks.toml`
  - Used by repositories that consume Pkgdx
  - Template for `pkgdx init` - a missing `prek.toml` or `--reset` copies it whole; otherwise
    `init` only adds missing repos (matched by `repo`) and hooks (matched by `id`), never editing
    or removing existing entries (`rev` included - use `prek update` for revisions)
- User config: `hooks.toml` in the user config directory replaces the bundled template
  - Directory: `PKGDX_CONFIG_DIR`, else `%APPDATA%\pkgdx` (Windows), else
    `$XDG_CONFIG_HOME/pkgdx` or `~/.config/pkgdx`
  - Read only by `pkgdx init` - after changing it or upgrading Pkgdx, re-run `pkgdx init --reset`
  - `uv run pkgdx config` shows whether the user or bundled template is in use

## Environment

- The `pkgdx-lint`, `pkgdx-format`, `pkgdx-typing` and `pkgdx-markdown` hooks resolve their config
  from the user config directory at run time, so `PKGDX_CONFIG_DIR` MUST be set in the environment
  that runs `prek` - CI included
- A set but invalid `PKGDX_CONFIG_DIR` fails those hooks with exit code 1; `pkgdx-secrets` is
  unaffected
- In this repo, the `format`, `lint` and `markdown` hooks pass the bundled config by path and
  ignore the user config directory; `typing` runs `pkgdx-typing-hook` and follows it
