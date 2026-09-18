"""Main entry point for pkgdx pre-commit hooks and CLI."""

import argparse
import logging
import sys
import textwrap
from typing import NoReturn

from pkgdx import __version__, _core, exceptions
from pkgdx.logging import CLI_CONSOLE, configure_cli_logging
from pkgdx.standards import _hooks
from pkgdx.standards._cli import add_subparser as add_standards_subparser

logger = logging.getLogger(__package__)


__all__: list[str] = [
    "detect_secrets",
    "main",
    "mypy_typing",
    "pymarkdown_lint",
    "ruff_format",
    "ruff_lint",
]


# PRE-COMMIT ENTRYPOINTS [project.scripts]


def ruff_format() -> NoReturn:
    """Run ruff formatting with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdx-format`, with
    entry point `pkgdx-format-hook`.
    """
    sys.exit(_hooks.core_ruff_format(sys.argv[1:]))


def ruff_lint() -> NoReturn:
    """Run ruff linting with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdx-lint`, with
    entry point `pkgdx-lint-hook`.
    """
    sys.exit(_hooks.core_ruff_lint(sys.argv[1:]))


def mypy_typing() -> NoReturn:
    """Run mypy type checking with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdx-typing`, with
    entry point `pkgdx-typing-hook`.
    """
    sys.exit(_hooks.core_mypy_typing(sys.argv[1:]))


def detect_secrets() -> NoReturn:
    """Run detect-secrets with the provided arguments.

    NOTE: Relates to pre-commit hook ID `pkgdx-secrets`, with
    entry point `pkgdx-secrets-hook`.
    """
    sys.exit(_hooks.core_detect_secrets(sys.argv[1:]))


def pymarkdown_lint() -> NoReturn:
    """Run pymarkdown linting with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdx-markdown`, with
    entry point `pkgdx-markdown-hook`.
    """
    sys.exit(_hooks.core_pymarkdown_lint(sys.argv[1:]))


# MAIN CLI COMMANDS


class CLIArgumentParser(argparse.ArgumentParser):
    """Custom CLI ArgumentParser."""

    def error(self, message: str) -> NoReturn:
        """Handle CLI errors by printing a formatted message and exiting.

        Args:
            message: The error message to display.
        """

        CLI_CONSOLE.print(f"[red]ERROR:[/red] [b]{message}[/b]", end="\n\n")
        self.print_usage(sys.stderr)
        CLI_CONSOLE.print(
            f"\n[dim]Try [cyan]{self.prog} --help[/cyan].[/dim]",
        )

        sys.exit(_core.ExitCode.EX_USAGE)


def main() -> NoReturn:
    """Provide a unified `pkgdx` CLI entrypoint - init."""

    # Provides a base parser for shared arguments across subcommands
    base_parser = CLIArgumentParser(add_help=False)
    base_parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show this help message and exit",
    )

    description = textwrap.dedent(
        """pkgdx centralises creation and implementation of coding standards
        across projects, providing a single source of truth for toolchain
        configuration."""
    )

    epilog = textwrap.fill(
        "For more information see https://gitlab.com/andyrids/pkgdx.",
        width=79,
        initial_indent="",
    )

    # Main parser for the CLI
    parser = CLIArgumentParser(
        prog=__package__,
        description=textwrap.fill(description, width=79),
        usage="USAGE:\n %(prog)s [options] <command>",
        epilog=epilog,
        add_help=False,
        parents=[base_parser],
        formatter_class=_core.CLIGFormatter,
    )

    parser._optionals.title = "OPTIONS"

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Print debug output",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"pkgdx version {__version__}",
        help="Show program's version number and exit",
    )

    subparsers = parser.add_subparsers(
        title="COMMANDS",
        # Mitigate subparser usage display issue by explicitly setting prog
        # https://github.com/python/cpython/issues/86463
        prog=parser.prog,
        dest="command",
        required=False,
        metavar="<command>",
    )

    add_standards_subparser(subparsers, base_parser)

    args = parser.parse_args()

    # Empty command (`pkgdx`) shows header and help
    if args.command is None:
        sys.stdout.write(
            f"Package Developer Experience (DX) Toolkit [v{__version__}]\n\n"
        )

        # Prints; USAGE, description, OPTIONS, COMMANDS & epilog
        parser.print_help()

        sys.exit(_core.ExitCode.EX_OK)

    # Configure logging based on debug flag
    is_debug = args.debug
    configure_cli_logging(logging.DEBUG if is_debug else logging.WARNING)

    ctx = _core.CLIContext(args=args, console=CLI_CONSOLE, is_debug=is_debug)

    try:
        exit_code = int(args.func(ctx))
    except exceptions.Error as err:
        logger.error(str(err))
        exit_code = _core.ExitCode.EX_FAILURE
    except Exception:
        logger.exception("Unexpected error")
        exit_code = _core.ExitCode.EX_SYNTAX
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
