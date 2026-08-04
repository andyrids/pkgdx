"""Main entry point for pkgdx pre-commit hooks and CLI."""

import argparse
import logging
import sys
from typing import NoReturn

from rich.console import Console

from pkgdx import _core, exceptions
from pkgdx.axi._cli import add_subparser as add_axi_subparser
from pkgdx.axi._toon import format_error
from pkgdx.logging import configure_cli_logging
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


def main() -> NoReturn:
    """Provide a unified `pkgdx` CLI entrypoint - init | axi."""

    parser = argparse.ArgumentParser(
        prog=__package__, description="Canonical standards & AXI toolkit"
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging [DEBUG]",
    )

    subparsers = parser.add_subparsers(
        title="commands", dest="command", required=True
    )

    add_standards_subparser(subparsers)
    add_axi_subparser(subparsers)

    args = parser.parse_args()

    # Configure logging based on verbosity
    is_verbose = args.verbose
    configure_cli_logging(logging.DEBUG if is_verbose else logging.WARNING)

    console = Console(force_terminal=sys.stdout.isatty())
    ctx = _core.CLIContext(args=args, console=console, is_verbose=is_verbose)

    try:
        exit_code = int(args.func(ctx))
    except exceptions.AXIError as err:
        # NOTE: `ProjectRootNotFoundError` is also raised on the `init`
        # (standards) CLI path, which is not part of the AXI TOON
        # contract - only surface the TOON error block for `axi` commands.
        if args.command == "axi":
            # NOTE: The TOON block on stdout *is* the error report -
            # logging it again at error level would duplicate it on
            # stderr, so the log line is debug-only (`--verbose`).
            sys.stdout.write(f"{format_error(str(err))}\n")
            logging.getLogger("pkgdx.axi").debug(str(err))
        else:
            logger.error(str(err))
        exit_code = _core.ExitCode.EX_FAILURE
    except exceptions.Error as err:
        logger.error(str(err))
        exit_code = _core.ExitCode.EX_FAILURE
    except Exception as err:
        if args.command == "axi":
            # NOTE: Mirrors the AXIError branch - the TOON block on
            # stdout is the error report; the traceback goes to the
            # `pkgdx.axi` logger, whose handler is stderr-only (the
            # `pkgdx` logger's RichHandler writes to stdout).
            sys.stdout.write(f"{format_error(f'Unexpected error: {err}')}\n")
            logging.getLogger("pkgdx.axi").exception("Unexpected error")
        else:
            logger.exception("Unexpected error")
        exit_code = _core.ExitCode.EX_SYNTAX
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
