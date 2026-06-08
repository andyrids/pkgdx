# `pkgdev`

## Configuration Context

When `prek` runs your hook (e.g., `pkgdev.__main__:ruff_lint`), the current working directory will
be the _consuming_ project's root. By default, Ruff and Mypy will look for a `pyproject.toml` in
that consuming project, completely ignoring the standards defined inside your installed `pkgdev`
package.

## Extract your Standards to a Bundled File

Because the root `pyproject.toml` is not bundled into the `site-packages` directory when a Python
package is installed, your wrapper scripts won't be able to easily find it.

You should move the `[tool.ruff]`, `[tool.mypy]`, etc., configurations out of your root
`pyproject.toml` and into a new file located at **`src/pkgdev/standards.toml`**. Because it is
inside the `src` folder, `hatchling` will automatically package it inside the built wheel.

How this works in practice:

1. When a downstream project configures prek to use your repo, prek will:
2. Create an isolated virtual environment.
3. Install pkgdev and its dependencies (ruff, mypy) into that environment.
4. Run ruff-lint-hook file1.py file2.py.
5. Your __main__.py intercepts this, finds standards.toml embedded inside the virtual environment,
and executes ruff check --config /path/to/standards.toml file1.py file2.py.
6. The downstream project gets perfectly standardized linting without a single line of Ruff
configuration in their own repo!

TODO
