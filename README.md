# Package Developer Experience (DX) Toolkit [`Pkgdx`]

I created `pkgdx` as a way to improve DX for Python projects. The package is intended for
installation as a development dependency, providing a main command-line interface (CLI) and
a nested CLI commands and options for common development tasks.

Current nested CLI features:

1. Setup canonical standards toolchain
2. Agent interface for dependency introspection

## (1) Maintaining Canonical Standards

`pkgdx` centralises creation and implementation of coding standards across projects, providing a
single source of truth for toolchain configuration:

1. Mypy (Python static type checking)
2. Ruff (Python linting & formatting)
3. PyMarkdown (Markdown linting)
4. detect-secrets (secret detection)
5. Prek (hook framework)

### (1) Why?

Other methods of maintaining standards include templating tools like `Cookiecutter` or `Copier`,
which inject configurations directly into the project `pyproject.toml` and/or root directory.

`pkgdx` automates the implementation of a common standard through pre-commit hooks and CI/CD,
removing the need for extensive `pyproject.toml` boilerplate.

### (1) How?

Configuration files and CLI are contained in the `standards/` subpackage and developments tools
have console scripts (`[project.scripts]`) and pre-commit hooks (`.pre-commit-hooks.yaml`), which
are installed through the CLI via Prek.

> [!NOTE]
> [`Prek`](https://prek.j178.dev/) is a Rust-based, drop-in replacement for
> [`pre-commit`](https://pre-commit.com/) that maintains compatibility with
> any existing `.pre-commit-config.yaml`.

When Prek runs a hook (e.g. `pkgdx-lint`), the CLI intercepts the command and executes the
corresponding tool with a bundled configuration.

As `pkgdx` is versioned and tagged, updates can be implemented across all projects via standard
dependency updates and `prek update` command.

Consuming projects can add project-specific requirements to the `pyproject.toml`, which can be
implemented through commands such as `uv run mypy`.

To apply the canonical standards to a project, run the `init` command:

```bash
uv run pkgdx init
```

> [!TIP]
> To see verbose output, use the `--verbose` or `-v` option:
> `uv run pkgdx -v init`

To overwrite or reset an existing `prek.toml` in the project root, use the `--reset` option:

```bash
uv run pkgdx init --reset
```

## (2) Introspect Project Dependencies

`pkgdx` provides an [Agent eXperience Interface (AXI)](https://axi.md/), which introspects
dependencies for a consuming project - querying exact signatures present in that venv, at the
exact versions pinned there - in a token-efficient [TOON](https://github.com/toon-format/spec)
format, on STDOUT.

### (2) Why?

The AXI allows introspection of installed packages by importing them, thereby covering
private, internal and undocumented distributions that documentation-retrieval tools cannot see.

The interface cannot drift from the pinned version - reporting what a symbol is rather than how to
use it - complimenting a documentation source such as `Context7`, `King Context` etc.

The AXI answers "does this exist, and what is its exact shape in the version I have
installed?" - other tools answer "how do I use this and why?"

### (2) How?

An agent scans the codebase with available tools and uses its findings to drive the AXI:

1. Scan the codebase -> bare name (`Console.print`) & package (`rich`)
2. Resolve bare name -> qualified name

```bash
uv run pkgdx axi find Console.print --package rich
```

```bash
uv run pkgdx axi inspect rich.console::Console.print
```

Other commands:

- `pkgdx axi` - Live status & next-step hints
- `pkgdx axi list` - Installed, declared dependencies
- `pkgdx axi show rich --api` - Public API symbols
- `pkgdx axi tree rich --max-depth 1` - Nested module tree
- `pkgdx axi inspect rich.console` - Direct children
- `pkgdx axi inherits <qualified_name>` - Direct subclasses

Docstrings are truncated to a first line by default - add `--docstring` for complete bodies. The
`--refresh` option rebuilds a stale graph after a dependency version change.

Ambient context for agents can be injected into `AGENTS.md` alongside MCP server entries in
`.vscode/mcp.json` and `.mcp.json`:

```bash
pkgdx axi setup
```

The AXI tools can be served over MCP (STDIO) with the `pkgdx axi serve` command, which requires the
`axi` extra:

```bash
uv add pkgdx \
  --dev \
  --extra axi \
  --index gitlab=https://gitlab.com/api/v4/projects/82928123/packages/pypi/simple
```

The MCP server exposes; `list_packages_tool`, `show_package_tool`, `show_package_api_tool`,
`show_module_tool`, `get_symbol_tool`, `find_symbol_tool`, `get_inheritors_tool` and
`get_module_tree_tool`

## Installation

Currently, this project is hosted on GitLab and deployed to a project Package Registry. The project
is also mirrored on GitHub.

> [!NOTE]
> Pkgdx installation is package-manager agnostic. Use another manager like Poetry and replace the
> `uv run` accordingly or omit entirely, with an activated virtual environment.

### Package Registry

```bash
uv add pkgdx --dev --index gitlab=https://gitlab.com/api/v4/projects/82928123/packages/pypi/simple
```

### Project URL

```bash
uv add --dev git+https://gitlab.com/apridya/pkgdx.git
```

```bash
uv add --dev git+https://gitlab.com/apridya/pkgdx.git@v1.0.0
```

## CI/CD Integration

Pkgdx can be included in GitLab/Github CI/CD pipelines to enforce centralised standards without
heavy boilerplate across each CI/CD YAML config.

> [!TIP]
> See `ruff-lint-job` in the project [.gitlab-ci.yml](.gitlab-ci.yml) for an example.

## Adopting Your Own Standards (External Users)

If you wish to use the Pkgdx framework, but want to apply your own rules, follow the steps below.

### (1) Fork the Repo

Start by forking the repo to your own namespace.

### (2) Modify the Configuration Files

Modify the configuration files located in `src/pkgdx/standards/`.

- `mypy.ini` - Mypy static typing rules
- `pymarkdown.toml` - PyMarkdown linting rules
- `ruff.toml` - Ruff linting & formatting rules
- `hooks.toml` - Prek config template

> [!TIP]
> Hooks can be added to `hooks.toml` or removed as needed. The CLI `init` command parses this
> file to determine which hooks should be configured in the consuming repository `prek.toml`.

### (3) Update Hook Configuration URL

Edit the `src/pkgdx/standards/hooks.toml` and change the `repo` value from
`"https://gitlab.com/andyrids/pkgdx"` to your forked repo URL and the `rev` to the new tag you
will create once you have finished.

### (4) Tag a New Release

Tag a new release and the CI/CD pipeline will build and publish the package to your Package
Registry. You can install your fork as a dev dependency in your projects via the repo URL or
Package Registry URL.

### Contribution

Contributions are welcome and these should be made through the
[GitLab repository](https://gitlab.com/andyrids/pkgdx).

## A Note on AI Usage

This project is being used as a testbed for Interpretable Context Methodology (ICM), which uses
folder structure as Agent Architecture. A copy of the research paper can be found at
[docs/2603.16021v2.pdf](/docs/2603.16021v2.pdf).

ICM replaces framework-level orchestration with filesystem structure. Numbered folders represent
stages. Plain markdown files carry prompts and context that tell a single AI agent what role to
play at each step.

The system is self-documenting - read `AGENTS.md` (symlink -> `CLAUDE.md`), which provide
development context. Navigate to `CONTEXT.md` as per `AGENTS.md` [`Routing`](AGENTS.md#routing)
instructions to see the necessary routing, context and reference that an agent would follow.

A community dedicated to this methodology can be found at [https://www.skool.com/cliefnotes](https://www.skool.com/cliefnotes/about?ref=478219c6d94340bd984dde6a8d1046e6).

> [!NOTE]
> ICM can leverage AI in a way that streamlines development, but also generates enough friction
> in the right areas to promote continued development (Friction Doctrine).

## Attribution

### `code-review-graph`

The SQLite Node|Edge graph architecture and symbol-graph walking patters used in the AXI modules
are heavily inspired by `code-review-graph`.

`code-review-graph` populates its graph from a static AST, whereas the `pkgdx` AXI populates its
graph from live object introspection.

`code-review-graph` walks a static AST, whereas the `pkgdx` AXI walks live objects via `importlib`
and `inspect`.

- **Repository**: [tirth8205/code-review-graph](https://github.com/tirth8205/code-review-graph)
- **License**: MIT License - Copyright (c) 2026 Tirth Kanani

### `toon-python`

The regex patterns, structural tokens and constant-extraction patterns for TOON format are directly
adapted from the official `toon-python` reference implementation.

- **Repository**: [toon-format/toon-python](https://github.com/toon-format/toon-python)
- **License**: MIT License - Copyright (c) 2025 TOON Format Organization
