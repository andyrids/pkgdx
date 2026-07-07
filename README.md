# Canonical Standards Management Tool [`pkgdevx`]

I created `pkgdevx` as a strategic approach designed to centralise and enforce
coding standards across my Python projects. `pkgdevx` provides a standardised
and opinionated workflow, which could be used as is or forked and modified to
suit individual requirements and preferences.

When `pkgdevx` is installed as a development dependency, the consuming repo gains
a single source of truth for several toolchain configurations:

1. Mypy (static type checker)
2. Ruff (linter & code formatter)
3. PyMarkdown (markdown linter)
4. detect-secrets (prevent secret commits)
5. Prek (framework to run hooks)

## Why `pkgdevx`?

Previously, I maintained standards across multiple repositories using
templating tools like `Copier` to inject `[tool.mypy]` or `[tool.ruff]`
configurations directly into the `pyproject.toml`.

`Copier` has a feature to [sync updates](https://copier.readthedocs.io/en/stable/updating/)
from evolved templates, but injection of a large toolchain configuration can
create a lot of boilerplate.

`pkgdevx` compartmentalises common, canonical standards and facilitates their
implimentation locally, with pre-commit hooks and in CI/CD pipelines as an
installable package.

Projects can implement additional configuration in their `pyproject.toml`, which
is now more streamlined and cleaner.

Running `uv run ruff check` would utilise configuration under `[tool.ruff]` or
`ruff.toml`, whereas `git commit` would trigger implemention of the `pkgdevx`
standards.

### The `pkgdevx` Approach

`pkgdevx` maintains toolchain configurations in a `standards/` module and
exposes console scripts (`[project.scripts]`), which implement them.

Each script entrypoint utilises a specific tool and has a dedicated
pre-commit hook defined in `.pre-commit-hooks.yaml`. `pkgdevx` uses a CLI to
automate hook installation into a consuming repository via `Prek` and a
`prek.toml` file created/modified at the project root.

>[!NOTE]
>[`Prek`](https://prek.j178.dev/) is a Rust-based, drop-in replacement for
>[`pre-commit`](https://pre-commit.com/) that maintains compatibility with
>existing `.pre-commit-config.yaml`.

#### Bundled Configuration Files

Configuration files are bundled directly within the `pkgdevx/standards` module.

#### Hook Interception

When Prek runs a hook (e.g. `pkgdevx-lint`), the `pkgdevx` CLI intercepts the
command and executes the underlying tool using the bundled configuration files
embedded within the virtual environment.

### Auto-update Feature

Because `pkgdevx` is versioned and tagged, you can update standards across all
projects via standard dependency updates and `prek update`.

### Flexibility

Consuming projects get standardised tooling without a single line of
configuration in their own repository, but can still enter project-specific
requirements in their local `pyproject.toml`, which are implemented by
executing commands such as; `uv run mypy` or `uv run ruff check`.

This means that all visible configuration in the `pyproject.toml` is project
specific and easy to read and recognise. The common, canonical standards that
apply to all projects are compartmentalised behind `pkgdevx`.

## Installation

Install `pkgdevx` as a development dependency in your consuming project.

```bash
uv add pkgdevx --dev
```

>[!warning]
>`pkgdevx` requires Astral uv package manager to be installed globally or in
>your project `venv`. See [installation instructions](https://docs.astral.sh/uv/getting-started/installation/).

## Setup & Usage

To apply the canonical standards to your project, run the `setup` command:

```bash
uv run pkgdevx setup
```

To see verbose output, use the `--verbose` or `-v` option:

```bash
uv run pkgdevx -v setup
```

The `setup` command automates the entire ['golden path'](https://www.redhat.com/en/topics/platform-engineering/golden-paths):

1. Finds the consuming project root
2. Configures `prek.toml` & injects expected pre-commit hooks
3. Installs the pre-commit hooks into your `.git/hooks/pre-commit` directory
4. Checks for hook updates based on tagged versions in the remote pkgdevx repository
5. Runs detect-secrets to create a `.secrets.baseline` file at the project root

To overwrite or reset an existing `prek.toml` in the project root, use the
`--reset` option:

```bash
uv run pkgdevx setup --reset
```

## CI/CD Integration

`pkgdevx` is designed to run automatically within custom CI/CD jobs. By
including `pkgdevx` as part of a GitLab CI/CD components library or GitHub
Actions, linting, formatting, and typing standards can be strictly enforced on
every pipeline without replicating the toolchain configuration in every project.

## Adopting Your Own Standards (External Users)

If you wish to use the `pkgdevx` framework, but want to apply your own rules,
follow the guidance below.

### (1) Fork the Repo

Start by forking the repo to your own namespace.

### (2) Modify the Configuration Files

Modify the configuration files located in `src/pkgdevx/standards/`.

- `mypy.ini` - Mypy static typing rules
- `pymarkdown.toml` - PyMarkdown linting rules
- `ruff.toml` - Ruff linting & formatting rules

### (3) Update Hook Configuration URL

Edit the `src/pkgdevx/standards/hooks.toml` and change the `repo` to your
forked repo URL and the `rev` to the new tag you will create once you have
finished.

### (4) Tag a New Release

Tag a new release and the CI/CD pipeline will build and publish the package
to your Package Registry. You can install your fork as a dev dependency in your
projects via the repo URL or Package Registry URL.
