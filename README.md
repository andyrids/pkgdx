# Canonical Standards Management Tool [`PyTack`]

I created `pytack` to centralise the creation and implementation of coding standards across my
Python projects.

The package provides a standardised and opinionated workflow, but it call also be easily forked and
modified to suit individual requirements.

`pytack` is intended for installation as a development dependency, granting the consuming repo a
single source of truth for toolchain configurations:

1. Mypy (Python static type checking)
2. Ruff (Python linting & formatting)
3. PyMarkdown (Markdown linting)
4. detect-secrets (secret detection)
5. Prek (hook framework)

> [!NOTE]
> This repository is mirrored from [GitLab](https://gitlab.com/andyrids/pytack).

## Why `PyTack`?

Other methods of maintaining standards across repositories include templating tools like
`Cookiecutter` or `Copier`, which can inject configurations directly into the `pyproject.toml`.

PyTack acts as a single source of canonical standards, which can be implemented through CLI
pre-commit hook setup and in CI/CD pipelines as an installable package.

### The `PyTack` Approach

PyTack provides toolchain configurations in a `standards/` module and exposes console scripts
(`[project.scripts]`), which implement them.

Each entrypoint runs a specific tool in a dedicated pre-commit hook in `.pre-commit-hooks.yaml`,
which the PyTack CLI installs into a consuming repository via `Prek`.

> [!NOTE]
> [`Prek`](https://prek.j178.dev/) is a Rust-based, drop-in replacement for
> [`pre-commit`](https://pre-commit.com/) that maintains compatibility with
> existing `.pre-commit-config.yaml`.

#### Bundled Configuration Files

Configuration files are bundled directly within the `pytack/standards` module.

#### Hook Interception

When Prek runs a hook (e.g. `pytack-lint`), the `pytack` CLI intercepts the command and executes
the underlying tool using the bundled configuration files embedded within the virtual environment.

#### Auto-update Feature

Because PyTack is versioned and tagged, you can update standards across all projects via standard
dependency updates and `prek update` command.

#### Flexibility

Consuming projects get standardised tooling without any configuration, but can still maintain
project-specific requirements in their `pyproject.toml`. These would be implemented through
commands such as; `uv run mypy` or `poetry run ruff format`.

Any configuration in `pyproject.toml` would be project-specific and the common, canonical standards
would be neatly compartmentalised behind `pytack`.

## Installation

Install PyTack as a development dependency in your consuming project.

> [!NOTE]
> PyTack installation is package-manager agnostic. Use another manager like Poetry and replace the
> `uv run` accordingly or omit entirely, with an activated virtual environment.

```bash
uv add pytack --dev
```

## Setup & Usage

To apply the canonical standards to your project, run the `setup` command:

```bash
uv run pytack setup
```

To see verbose output, use the `--verbose` or `-v` option:

```bash
uv run pytack setup -v
```

The `setup` command automates the entire ['golden path'](https://www.redhat.com/en/topics/platform-engineering/golden-paths):

1. Finds the consuming project root
2. Configures `prek.toml` & injects expected pre-commit hooks
3. Installs the pre-commit hooks into your `.git/hooks/pre-commit` directory
4. Checks for hook updates based on tagged versions in the remote PyTack repository
5. Runs detect-secrets to create a `.secrets.baseline` file at the project root

To overwrite or reset an existing `prek.toml` in the project root, use the `--reset` option:

```bash
uv run pytack setup --reset
```

## `venv-axi`

`venv-axi` is an Agent eXperience Interface (AXI) tool for agents working in a `pytack`-consuming
repo. It surfaces installed venv package metadata and public API/docstring introspection in a
token-efficient [TOON](https://github.com/toon-format/spec) format, on STDOUT.

```bash
uv run venv-axi          # live status & next-step hints
uv run venv-axi list      # installed, declared dependencies
uv run venv-axi show rich --api   # a package's public API symbols
uv run venv-axi find rich "Console"   # free-text symbol search
uv run venv-axi tree rich --max-depth 1   # nested module tree
uv run venv-axi inspect rich::Console.print   # a single symbol's full detail
```

To install ambient context for agents (an `AGENTS.md` block plus MCP server entries in
`.vscode/mcp.json` and `.mcp.json`), run:

```bash
uv run venv-axi setup
```

`venv-axi serve` runs the same tools over MCP (stdio), and requires the `venv-axi` extra:

```bash
uv add pytack --dev --extra venv-axi
```

The MCP server exposes `list_packages`, `show_package`, `show_package_api`, `show_module`,
`get_symbol`, `find_symbol`, `get_inheritors`, and `get_module_tree`.

## CI/CD Integration

PyTack can be included in GitLab/Github CI/CD pipelines to enforce centralised standards without
heavy boilerplate across each CI/CD YAML config.

> [!TIP]
> See `ruff-lint-job` in the project [.gitlab-ci.yml](.gitlab-ci.yml) for an example.

## Adopting Your Own Standards (External Users)

If you wish to use the PyTack framework, but want to apply your own rules, follow the steps below.

### (1) Fork the Repo

Start by forking the repo to your own namespace.

### (2) Modify the Configuration Files

Modify the configuration files located in `src/pytack/standards/`.

- `mypy.ini` - Mypy static typing rules
- `pymarkdown.toml` - PyMarkdown linting rules
- `ruff.toml` - Ruff linting & formatting rules
- `hooks.toml` - Prek config template

> [!TIP]
> Hooks can be added to `hooks.toml` or removed as needed. The CLI `setup` command parses this
> file to determine which hooks should be configured in the consuming repository `prek.toml`.

### (3) Update Hook Configuration URL

Edit the `src/pytack/standards/hooks.toml` and change the `repo` value from
`"https://gitlab.com/andyrids/pytack"` to your forked repo URL and the `rev` to the new tag you
will create once you have finished.

### (4) Tag a New Release

Tag a new release and the CI/CD pipeline will build and publish the package to your Package
Registry. You can install your fork as a dev dependency in your projects via the repo URL or
Package Registry URL.

### Contribution

Contributions are welcome and these should be made through the
[GitLab repository](https://gitlab.com/andyrids/pytack).

## A Note on AI Usage

This project is being used as a testbed for Interpretable Context Methodology (ICM), which uses
folder structure as Agent Architecture. A copy of the research paper can be found at
[docs/2603.16021v2.pdf](/docs/2603.16021v2.pdf).

ICM replaces framework-level orchestration with filesystem structure. Numbered folders represent
stages. Plain markdown files carry prompts and context that tell a single AI agent what role to
play at each step.

The system is self-documenting - read `AGENTS.md` (symlink -> `CLAUDE.md`), which will provide
PyTack development context. With a prompt to create a new feature in mind, navigate to
`CONTEXT.md` as per `AGENTS.md` [`Routing`](AGENTS.md#routing) instructions to see the necessary
routing, context and reference that an agent would follow with that prompt.

A community dedicated to this methodology can be found at [https://www.skool.com/cliefnotes](https://www.skool.com/cliefnotes/about?ref=478219c6d94340bd984dde6a8d1046e6).

> [!NOTE]
> ICM can leverage AI in a way that streamlines development, but also generates enough friction
> in the right areas to promote continued development (Friction Doctrine).
