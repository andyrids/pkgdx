# Package Developer Experience (DX) Toolkit [`Pkgdx`]

I created `pkgdx` as a way to improve DX for Python projects. The package is intended for
installation as a development dependency, providing a main command-line interface (CLI) and
a nested CLI commands and options for common development tasks.

## Current features

### (1) Canonical standards maintenance

`pkgdx` centralises creation and implementation of coding standards across projects, providing a
single source of truth for toolchain configuration:

1. Mypy (Python static type checking)
2. Ruff (Python linting & formatting)
3. PyMarkdown (Markdown linting)
4. detect-secrets (secret detection)
5. Prek (hook framework)

> [!INFO]
> To quickly demo `pkgdx`, clone this repository and run the `test-consumer` Justfile recipe via
> `just test-consumer`. If [Just](https://github.com/casey/just) command runner is unavailable,
> run `uv run --directory consumers/testing pkgdx --debug init --reset` to use `pkgdx` against
> the `consumers/testing` workspace package.

![Demo Preview](docs/consumer-demo.gif)

#### Why?

Other methods of maintaining standards include templating tools like `Cookiecutter` or `Copier`,
which inject configurations directly into the project `pyproject.toml` and/or root directory.

`pkgdx` automates the implementation of a common standard through pre-commit hooks and CI/CD,
removing the need for extensive `pyproject.toml` boilerplate.

> [!TIP]
> `pkgdx` compliments project templating tools - it does not replace them.

#### How?

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

To see verbose logging output, use the `--debug` or `-d` option:

```bash
uv run pkgdx -d init
```

To overwrite or reset an existing `prek.toml` in the project root, use the `--reset` option:

```bash
uv run pkgdx init --reset
```

## Installation

Currently, this project is hosted on GitLab and deployed to a project Package Registry. The project
is also mirrored on GitHub.

> [!NOTE]
> Pkgdx installation is package-manager agnostic. Use another manager like Poetry and replace the
> `uv run` accordingly or omit entirely, with an activated virtual environment.

### Package registry

```bash
uv add pkgdx --dev --index gitlab=https://gitlab.com/api/v4/projects/82928123/packages/pypi/simple
```

### Project URL

```bash
uv add --dev git+https://gitlab.com/apridya/pkgdx.git
```

```bash
uv add --dev git+https://gitlab.com/apridya/pkgdx.git@v0.2.0
```

## CI/CD integration

Pkgdx can be included in GitLab/Github CI/CD pipelines to enforce centralised standards without
heavy boilerplate across each CI/CD YAML config.

> [!TIP]
> See `ruff-lint-job` in the project [.gitlab-ci.yml](.gitlab-ci.yml) for an example.

## Adopting your own standards (external users)

If you wish to use the Pkgdx framework, but want to apply your own rules, follow the steps below.

### (1) Fork the repo

Start by forking the repo to your own namespace.

### (2) Modify the configuration Files

Modify the configuration files located in `src/pkgdx/standards/`.

- `mypy.ini` - Mypy static typing rules
- `pymarkdown.toml` - PyMarkdown linting rules
- `ruff.toml` - Ruff linting & formatting rules
- `hooks.toml` - Prek config template

> [!TIP]
> Hooks can be added to `hooks.toml` or removed as needed. The CLI `init` command parses this
> file to determine which hooks should be configured in the consuming repository `prek.toml`.

### (3) Update hook configuration URL

Edit the `src/pkgdx/standards/hooks.toml` and change the `repo` value from
`"https://gitlab.com/andyrids/pkgdx"` to your forked repo URL and the `rev` to the new tag you
will create once you have finished.

### (4) Tag a new release

Tag a new release and the CI/CD pipeline will build and publish the package to your Package
Registry. You can install your fork as a dev dependency in your projects via the repo URL or
Package Registry URL.

## Contribution

Contributions are welcome and these should be made through the
[GitLab repository](https://gitlab.com/andyrids/pkgdx).
