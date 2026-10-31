"""Main entry point for pkgdx pre-commit hooks and CLI."""

import sys
from collections.abc import Callable
from typing import NoReturn

import pyclig

from pkgdx import exceptions
from pkgdx.standards import _cli, _hooks

__all__: list[str] = [
    "cli",
    "detect_secrets",
    "mypy_typing",
    "pymarkdown_lint",
    "ruff_format",
    "ruff_lint",
]


# PRE-COMMIT ENTRYPOINTS [project.scripts]


def _run_hook(func: Callable[[list[str]], int]) -> NoReturn:
    """Run a hook, reporting `pkgdx` errors as `error:` without a traceback.

    Args:
        func: The core hook logic, called with `sys.argv[1:]`.
    """
    pyclig.run(lambda: func(sys.argv[1:]), errors=(exceptions.Error,))


def ruff_format() -> NoReturn:
    """Run ruff formatting with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdx-format`, with
    entry point `pkgdx-format-hook`.
    """
    _run_hook(_hooks.core_ruff_format)


def ruff_lint() -> NoReturn:
    """Run ruff linting with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdx-lint`, with
    entry point `pkgdx-lint-hook`.
    """
    _run_hook(_hooks.core_ruff_lint)


def mypy_typing() -> NoReturn:
    """Run mypy type checking with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdx-typing`, with
    entry point `pkgdx-typing-hook`.
    """
    _run_hook(_hooks.core_mypy_typing)


def detect_secrets() -> NoReturn:
    """Run detect-secrets with the provided arguments.

    NOTE: Relates to pre-commit hook ID `pkgdx-secrets`, with
    entry point `pkgdx-secrets-hook`.
    """
    _run_hook(_hooks.core_detect_secrets)


def pymarkdown_lint() -> NoReturn:
    """Run pymarkdown linting with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdx-markdown`, with
    entry point `pkgdx-markdown-hook`.
    """
    _run_hook(_hooks.core_pymarkdown_lint)


# MAIN CLI COMMANDS

DESCRIPTION = (
    "pkgdx centralises creation and implementation of coding standards "
    "across projects, providing a single source of truth for toolchain "
    "configuration."
)


@pyclig.group(
    "pkgdx",
    help=DESCRIPTION,
    short_help="Package Developer Experience (DX) Toolkit",
    examples=["pkgdx init", "pkgdx config --export"],
    errors=(exceptions.Error,),
    epilog="For more information see https://gitlab.com/andyrids/pkgdx.",
)
def cli() -> None:
    """Provide a unified `pkgdx` CLI entrypoint - init, config."""


cli.add_command(_cli.command_init)
cli.add_command(_cli.command_config)


if __name__ == "__main__":
    cli()
