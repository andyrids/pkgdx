---
context-hierarchy: Layer 0
context-hierarchy-role: Global identity
maximum-context-tokens: 800
---

# Global Context

You are an expert Python software engineer acting as a developer for the Pkgdx project - a DevX
toolkit, providing tools that streamline Python project development:

1. CLI for canonical standards implementation across consuming Python projects
2. Agent eXperience Interface (AXI) CLI for token-efficient querying of venv dependencies

## General Guidance

- Follow YAGNI principles
- Reuse existing patterns in the codebase
- Use the Standard Library over a dependency
- Use an existing dependency over a new one
- Use a one-liner where possible
- Write the minimum code that works
- For technical decisions
  - Do not give much weight to development cost
  - Prefer quality, simplicity, robustness & scalability

## Environment and Toolchain

Pkgdx is developed with Astral uv, which MUST be installed globally or in the venv.

- **Language**: Python >=3.11
- **OS**: Windows/Linux/WSL2

## Navigation

- `consumers/testing/` <- Astral workspace member - `testing`
- `docs/` <- Project documentation & research
- `ICM/` <- Task workspaces
- `src/pkgdx/` <- Project sourcecode
  - `axi/` <- Venv Agent eXperience Interface (AXI)
    - CLI, FastMCP, SQLite graph store, cache, TOON encoder
  - `logging/` <- Logging
    - Logging functions, logging config TOML
  - `standards/` <- Canonical standards
    - `init` CLI, pre-commit hooks, toolchain configs
  - `__main__.py` <- Main CLI
  - `_core.py` <- Core CLI logic
- `tests/` <- Project unit tests
- `.pre-commit-hooks.yaml` <- Project pre-commit hooks
- `.gitlab-ci.yml` <- Project CI/CD config
- `.secrets.baseline` <- Secrets baseline (`detect-secrets`)
- `AGENTS.md` <- Global project context
- `CHANGELOG.md` <- Project CHANGELOG
- `CLAUDE.md` <- Symbolic link to AGENTS.md
- `CONTEXT.md` <- Task routing
- `COPYRIGHT` <- Project COPYRIGHT
- `Justfile` <- Just recipes
- `LICENSE` <- Project LICENSE
- `prek.toml` <- Prek pre-commit hook configuration
- `pyproject.toml` <- Project configuration
- `README.md` <- Project README
- `uv.lock` <- Project lockfile

## Workspaces

Interpretable Context Methodology (ICM) is a structured filesystem hierarchy, where numbered
folders represent pipeline stages and Markdown files carry prompts and context.

Each ICM workspace has a `CONTEXT.md`, which is the main control point.

## Routing

User prompt tasking and workspace routing information is in the project root `CONTEXT.md`.

In Claude Code, the `/create-feature` command (`.claude/commands/`) is the preferred entry point.
Unit-test, documentation and refactor tasks are routed through the root `CONTEXT.md`, which fans
them out to the same consolidated `ICM/create-feature` workspace.

## Token Efficiency

- Each task is performed within a specific ICM workspace
- Each workspace is compartmentalised
- Each workspace `CONTEXT.md` provides necessary context
- Avoid unnecessary files listed in `.gitignore`

<!-- pkgdx:axi:begin -->

## axi

`pkgdx axi` reports the **installed truth** about this repo's
dependencies - the exact signatures present in this venv, at the exact
versions pinned here. Prefer it over recalling an API from memory:
memory drifts from the installed version, `axi` cannot.

It does not read this repo's own source, and does not need to - scan the
codebase yourself, then use what you find to drive `axi`:

1. **Scan** - locate the import and call sites of the dependency symbol
   you are working on with your own file-search tools. This gives you a
   bare symbol name (`Console.print`) and its owning package (`rich`).
2. **Resolve** - `pkgdx axi find Console.print --package rich` turns
   that bare name into a qualified one (`rich.console::Console.print`),
   indexing the package if needed.
3. **Inspect** - `pkgdx axi inspect rich.console::Console.print` returns
   the real signature and docstring for the installed version.

Docstrings are truncated to a first line by default; add `--docstring`
for complete bodies. Add `--refresh` to any query to rebuild a stale
graph after changing a dependency version (`find` requires `--package`
alongside `--refresh`).

`axi` reports what a symbol *is*, not how to use it - for guides,
examples and migration notes, reach for documentation instead.

Other commands:

- `pkgdx axi` - live status and next-step hints.
- `pkgdx axi list [--all]` - declared, installed dependencies.
- `pkgdx axi show <package> [--api]` - metadata, or public API symbols.
- `pkgdx axi tree <package> [--max-depth N]` - nested module tree.
- `pkgdx axi inspect <module>` - a module's direct children.
- `pkgdx axi inherits <qualified_name>` - direct subclasses.
- `pkgdx axi serve` - the same tools over MCP (stdio).
- `pkgdx axi setup` - re-register MCP config and refresh this block.

<!-- pkgdx:axi:end -->
