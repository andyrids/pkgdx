# Package Developer Experience (DX) Toolkit [`Pkgdx`]

I created `pkgdx` as a way to improve DX for my Python projects. The package is installed as
as a development dependency, providing a command-line interface (CLI) for canonical standards
configuration.

## Overview

`pkgdx` centralises creation and implementation of coding standards across projects, providing a
single source of truth for toolchain configuration:

1. Mypy (Python static type checking)
2. Ruff (Python linting & formatting)
3. PyMarkdown (Markdown linting)
4. detect-secrets (secret detection)
5. Prek (hook framework)

## Quick start

1. Run `uv add --dev pkgdx` for a consuming project
2. Run `uv run pkgdx init` to configure hooks and install Git shims
3. Run `uv run pkgdx config --export` to export toolchain config files

The config files; `hooks.toml`, `mypy.ini`, `pymarkdown.toml` and `ruff.toml` are exported to
`$PKGDX_CONFIG_DIR` | `%APPDATA%/pkgdx` | `$XDG_CONFIG_HOME/pkgdx` | `~/.config/pkgdx`.

1. Modify these files to maintain a new global canonical standards config
2. Delete a file to revert to the repsective, bundled config
3. Run `uv run pkgdx config` to check config detection and location

To quickly demo `pkgdx`, clone this repository, cd into `./pkgdx/` and run the command below:

```sh
just consumer-demo
```

> [!INFO]
> Use `uvx rust-just consumer-demo` if [Just](https://just.systems/man/en/) command runner
> is not installed.

Further installation and setup guidance is available below.

![Demo Preview](https://gitlab.com/andyrids/pkgdx/-/raw/main/docs/pkgdx-demo.webp)

## Why?

Other methods of maintaining standards include templating tools like `Cookiecutter` or `Copier`,
which inject configurations directly into the project `pyproject.toml` and/or root directory.

`pkgdx` automates the implementation of a common standard through pre-commit hooks and CI/CD,
removing the need for extensive `pyproject.toml` boilerplate.

> [!TIP]
> `pkgdx` compliments project templating tools - it does not replace them.

## How?

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

To see which configuration file each hook uses, run the `config` command. See
[Adopting your own standards](#adopting-your-own-standards-external-users).

```bash
uv run pkgdx config
```

## Installation

This project is hosted on GitLab and each release is published to PyPI and the GitLab project
Package Registry. The project is also mirrored on GitHub.

> [!NOTE]
> Pkgdx installation is package-manager agnostic. Use another manager like Poetry and replace the
> `uv run` accordingly or omit entirely, with an activated virtual environment.

### PyPI

```bash
uv add --dev pkgdx
```

### Package registry

```bash
uv add pkgdx --dev --index gitlab=https://gitlab.com/api/v4/projects/82928123/packages/pypi/simple
```

### Project URL

```bash
uv add --dev git+https://gitlab.com/andyrids/pkgdx.git
```

```bash
uv add --dev git+https://gitlab.com/andyrids/pkgdx.git@v0.5.0
```

## CI/CD integration

Pkgdx can be included in GitLab/Github CI/CD pipelines to enforce centralised standards without
heavy boilerplate across each CI/CD YAML config.

> [!TIP]
> See `ruff-lint-job` in the project
> [.gitlab-ci.yml](https://gitlab.com/andyrids/pkgdx/-/blob/main/.gitlab-ci.yml) for an example.

## Adopting your own standards (external users)

`pkgdx` ships bundled canonical standards. To change them without forking, place your own files in a
user config directory. Forking remains an option for teams that want versioned, tagged standards
(see [Fork the repo](#fork-the-repo-alternative-for-teams)).

### (1) Know where the user config directory is

`pkgdx` looks for the user config directory in this order:

1. The directory named by the `PKGDX_CONFIG_DIR` environment variable, if it is set and non-empty.
2. The platform default:
   - Windows: `%APPDATA%\pkgdx`
   - Linux, macOS and other OSes: `$XDG_CONFIG_HOME/pkgdx` if `XDG_CONFIG_HOME` is an absolute
     path, otherwise `~/.config/pkgdx`

If `PKGDX_CONFIG_DIR` is set but is not an existing directory, the lint, format, typing and markdown
hooks, `pkgdx init` and `pkgdx config` fail with exit code 1 and a single error message without a
traceback. A missing platform directory is normal and is ignored.

### (2) Add your configuration files

Place any of these files in the user config directory:

- `ruff.toml` - Ruff linting & formatting rules
- `mypy.ini` - Mypy static typing rules
- `pymarkdown.toml` - PyMarkdown linting rules
- `hooks.toml` - Prek config template

Each file is chosen independently. If the user config directory holds a file with one of these
names, `pkgdx` uses it; otherwise it uses the bundled file. A directory holding only `ruff.toml`
overrides Ruff and nothing else.

detect-secrets has no configuration file, so it always uses its bundled settings.

> [!IMPORTANT]
> `hooks.toml` affects only `pkgdx init`, which uses it to write the `prek.toml` template. A
> `prek.toml` that was already copied keeps its old hooks. After upgrading `pkgdx` or changing
> `hooks.toml`, refresh the copy with `uv run pkgdx init --reset`.

### (3) Check and seed with `pkgdx config`

```bash
uv run pkgdx config
```

This prints one row per file on standard output: its name, its source (`user` or `bundled`) and
its resolved path. A summary line on standard error names the user config directory and whether
`PKGDX_CONFIG_DIR` set it.

To start from the bundled files, export them into the user config directory:

```bash
uv run pkgdx config --export
```

`--export` creates the platform directory if needed, copies each bundled file that is missing and
never overwrites an existing file. It prints one line per file, `created` or `unchanged`, in the
same format as `pkgdx init`.

### (4) CI & team parity

The user config directory lives on your machine. Without further action, CI and collaborators fall
back to the bundled config, so results can differ between local runs and pipelines.

Recommended pattern:

1. Keep the four files in your own standards Git repository.
2. Clone that repository locally and either use it as the user config directory or point
   `PKGDX_CONFIG_DIR` at it.
3. In CI, clone the same repository and export `PKGDX_CONFIG_DIR` to the clone.

```yaml
lint-job:
  variables:
    PKGDX_CONFIG_DIR: $CI_PROJECT_DIR/.pkgdx-standards
  before_script:
    - git clone --depth 1 https://gitlab.com/your-group/your-standards.git "$PKGDX_CONFIG_DIR"
  script:
    - uv run pkgdx-lint-hook
```

Alternative: commit the four files to each project (for example in `.pkgdx/`) and set
`PKGDX_CONFIG_DIR=.pkgdx`. A relative path is resolved against the working directory.

### Fork the repo (alternative for teams)

Use a fork when you want standards that are versioned and released with the package.

1. Fork the repo to your own namespace.
2. Modify the files in `src/pkgdx/standards/` (`mypy.ini`, `pymarkdown.toml`, `ruff.toml` and
   `hooks.toml`).
3. In `src/pkgdx/standards/hooks.toml`, change the `repo` value from
   `"https://gitlab.com/andyrids/pkgdx"` to your forked repo URL, and set `rev` to the tag you
   will create.
4. Tag a new release. The CI/CD pipeline builds and publishes the package to your Package
   Registry, which you can install as a dev dependency via the repo URL or Package Registry URL.
5. The `publish-pypi-job` uploads to PyPI from protected `v*` tags only. To publish your fork
   there, rename the package and register your own PyPI trusted publisher; otherwise delete the
   job.

## Contribution

Contributions are welcome and these should be made through the
[GitLab repository](https://gitlab.com/andyrids/pkgdx).
