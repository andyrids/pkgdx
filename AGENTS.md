# Package Developer Experience (DX) Toolkit [`Pkgdx`]

The pkgdx project provides a DX toolkit, which centralises the maintenance and implementation of
canonical standards for consuming projects. Consumer-facing behaviour (commands, hooks, excludes,
resets, upgrades, config overrides) is documented in [docs/reference.md](docs/reference.md); keep
it in step with code changes.

## Conventions

- Implement only what is asked; prefer the standard library, then an existing dependency, and ask
  before adding one

## This repository

`pkgdx` develops the standards it ships, so its own setup differs from a consuming project:

- `src/pkgdx/standards/` holds the canonical configs and `hooks.toml`. Changing them changes the
  standard, released with a version bump (see Release workflow)
- `prek.toml` is maintained by hand. Its local `format`, `lint` and `markdown` hooks pass the
  in-repo configs by path and ignore the user config directory; `typing` runs `pkgdx-typing-hook`
  and follows it
- Do not run `pkgdx init` here. It adds the published `pkgdx` hooks alongside the local ones, so
  every check runs twice
- `uv run pymarkdown --config src/pkgdx/standards/pymarkdown.toml scan <file>` - Lint a file
  against the in-repo config

## Release workflow

Consumer hooks reference this repo by the `rev` in `src/pkgdx/standards/hooks.toml`. On a release
or release candidate:

- Set the `rev` of the `https://gitlab.com/andyrids/pkgdx` repo in
  `src/pkgdx/standards/hooks.toml` to the new release version (repo tag). The
  `conventional-pre-commit` `rev` is pinned separately; bump it when `test_prek_revision_update`
  flags it
- Tag the project with that same version
- If `pkgdx-typing` in `hooks.toml` changed, say so in the CHANGELOG, as consumers only pick it up
  with `pkgdx init --reset`
