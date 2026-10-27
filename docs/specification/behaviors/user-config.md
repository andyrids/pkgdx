---
context-hierarchy: Layer 3
context-hierarchy-role: Reference material
immutable: false
tags: [config, user-config, overrides, standards, PKGDX_CONFIG_DIR, platform]
---

# Behavior: user config directory

## Rule

Each bundled standard file MAY be replaced by a file of the same name in a per-user config
directory. Every applicable pkgdx hook and command resolves each file independently, at the time it runs.

## Applies to

Every hook and command that reads a bundled standard: the lint, format, typing and markdown
hooks, `init`, and `config`.

Recognised file names: `ruff.toml`, `mypy.ini`, `pymarkdown.toml` and `hooks.toml`.
The secrets hook (detect-secrets) has no configuration file and is not affected.

## Details

### Directory selection

- If the environment variable `PKGDX_CONFIG_DIR` is set and non-empty, its value is the user
  config directory.
- If the variable is unset or empty, the user config directory is the platform default:
  - Windows: the `%APPDATA%` directory, with `pkgdx` appended.
  - Other platforms, including macOS: `$XDG_CONFIG_HOME/pkgdx` when `XDG_CONFIG_HOME` is set to an
    absolute path, otherwise `~/.config/pkgdx`.
    > Follows the XDG convention that ruff also uses, so the same location applies on macOS.
- The directory is read on every invocation; nothing is remembered between runs.

### File selection

- If the user config directory contains a regular file with the name of a bundled file, that file
  is used. Otherwise the bundled file is used.
- A directory that happens to share a recognised file name is ignored.
- Selection is per file. A user config directory holding only `ruff.toml` changes Ruff
  configuration and leaves the other files bundled.

### Failure modes

- If `PKGDX_CONFIG_DIR` is set and does not name an existing directory, then the lint, format,
  typing and markdown hooks, `init` and `config` shall exit with status 1 and write a single error
  message to standard error, without a traceback. Nothing is
  linted, formatted or written.
  > A typo here would otherwise silently apply the bundled standards, which is the drift this
  > rule prevents.
- If the platform user config directory does not exist, then pkgdx shall treat it as empty
  without reporting an error.

### Consumer effects

- `hooks.toml` is read only when a project's `prek.toml` template is created or reset. A
  `prek.toml` that was already written keeps its hooks until it is regenerated.
  > Hook definitions copied into a project are a snapshot; re-reading the user file later does not
  > change them.
- Hook revisions and repositories for pkgdx's own template are always taken from the bundled
  `hooks.toml`, so a user file cannot make the package validate a template it did not ship.

## Out of scope

- Remote or versioned standards, such as a Git URL or tagged release, and any cache of them.
  Forking the package remains the route for versioned standards. Recorded in the README
  "Adopting your own standards" section.
- Merging a user file with the bundled file. Each file is replaced whole. The user file is
  responsible for being complete.
- Per-project configuration beyond the `PKGDX_CONFIG_DIR` override, such as a `.pkgdx/` folder
  discovered automatically. The README shows how to set the variable instead.
- Synchronising the user config directory between machines or into CI. The README "CI & team
  parity" section describes the recommended pattern.
