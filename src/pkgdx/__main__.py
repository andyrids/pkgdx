"""Main entry point for pkgdx pre-commit hooks and CLI."""

import argparse
import logging
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from typing import NoReturn

import tomlkit
import tomlkit.exceptions
from pkgdx import _core, exceptions, standards
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, TaskID

from pkgdx.logging import configure_cli_logging


logger = logging.getLogger(__package__)


@contextmanager
def _setup_progress(console: Console) -> Iterator[Progress]:
    """Create a TTY-aware Rich progress bar for the setup command."""

    handlers = [h for h in logger.handlers if isinstance(h, RichHandler)]

    if not handlers:
        logger.error("Failed to find logging handlers")
        raise exceptions.RichHandlerNotFound

    original_consoles = {h: h.console for h in handlers}

    for h in handlers:
        h.console = console

    progress = Progress(
        *Progress.get_default_columns(),
        console=console,
        disable=not console.is_terminal,
    )

    try:
        with progress:
            yield progress
    finally:
        for handler, original_console in original_consoles.items():
            handler.console = original_console


def _advance_progress(
    progress: Progress,
    task_id: TaskID,
    description: str,
) -> None:
    """Update the description & advance a progress task by one step."""
    progress.update(task_id, description=description, advance=1)


# ------------------------------------------------------------------------
# CORE HOOK LOGIC
# ------------------------------------------------------------------------


def core_ruff_format(args: list[str]) -> int:
    """Core logic for ruff formatting."""
    config = standards.RUFF_CONFIG.as_posix()
    cmd = ["ruff", "format", "--config", config] + args
    return subprocess.run(cmd).returncode


def core_ruff_lint(args: list[str]) -> int:
    """Core logic for ruff linting."""
    config = standards.RUFF_CONFIG.as_posix()
    cmd = ["ruff", "check", "--config", config] + args
    return subprocess.run(cmd).returncode


def core_mypy_typing(args: list[str]) -> int:
    """Core logic for mypy type checking."""
    config = standards.MYPY_CONFIG.as_posix()
    cmd = ["mypy", "--config-file", config] + args
    return subprocess.run(cmd).returncode


def core_detect_secrets(args: list[str]) -> int:
    """Core logic for detect-secrets."""
    if "--baseline" not in args:
        args = ["--baseline", ".secrets.baseline"] + args
    cmd = ["detect-secrets-hook"] + args
    return subprocess.run(cmd).returncode


def core_pymarkdown_lint(args: list[str]) -> int:
    """Core logic for pymarkdown linting."""
    config = standards.PYMARKDOWN_CONFIG.as_posix()
    cmd = ["pymarkdown", "--config", config, "scan"] + args
    return subprocess.run(cmd).returncode


# ------------------------------------------------------------------------
# PRE-COMMIT ENTRYPOINTS [project.scripts]
# ------------------------------------------------------------------------


def ruff_format() -> NoReturn:
    """Runs ruff formatting with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdx-format`, with
    entry point `pkgdx-format-hook`.
    """
    sys.exit(core_ruff_format(sys.argv[1:]))


def ruff_lint() -> NoReturn:
    """Runs ruff linting with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdx-lint`, with
    entry point `pkgdx-lint-hook`.
    """
    sys.exit(core_ruff_lint(sys.argv[1:]))


def mypy_typing() -> NoReturn:
    """Runs mypy type checking with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdx-typing`, with
    entry point `pkgdx-typing-hook`.
    """
    sys.exit(core_mypy_typing(sys.argv[1:]))


def detect_secrets() -> NoReturn:
    """Runs detect-secrets with the provided arguments.

    NOTE: Relates to pre-commit hook ID `pkgdx-secrets`, with
    entry point `pkgdx-secrets-hook`.
    """
    sys.exit(core_detect_secrets(sys.argv[1:]))


def pymarkdown_lint() -> NoReturn:
    """Runs pymarkdown linting with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdx-markdown`, with
    entry point `pkgdx-markdown-hook`.
    """
    sys.exit(core_pymarkdown_lint(sys.argv[1:]))


def venv_axi() -> NoReturn:
    """Provides CLI entrypoint for `venv-axi`.

    NOTE: Relates to `[project.scripts]` entries `venv-axi` and
    `pkgdx-venv-axi`. Implementation lives in `pkgdx.venvaxi`.
    """
    # Lazy import keeps this module import light
    from pkgdx.venvaxi import main as _venv_axi_main

    sys.exit(_venv_axi_main())


# ------------------------------------------------------------------------
# MAIN CLI COMMANDS
# ------------------------------------------------------------------------


def command_setup(ctx: _core.CLIContext) -> int:
    """Configures a consuming repo with `pkgdx` standards.

    Attempts to identify the root of the consuming repo and ensures that
    `Prek` is configured with the expected `pkgdx` hooks.

    Args:
        ctx: ...

    Returns:
        The integer process exit code. 0 indicates success, non-zero
        indicates failure. Uses `_core.ExitCode`.
    """
    with _setup_progress(ctx.console) as progress:
        task = progress.add_task("[cyan]pkgdx setup", total=6)

        _advance_progress(progress, task, "[cyan]Find project root")
        try:
            root = _core.get_project_root()
        except exceptions.ProjectRootNotFoundError:
            progress.update(
                task,
                description="[red]Failed to find project root",
            )
            logger.exception("Failed to find project root")
            return _core.ExitCode.EX_FAILURE

        _advance_progress(progress, task, "[cyan]Find Git top-level")
        try:
            git_toplevel = _core.get_git_toplevel()
        except exceptions.GitTopLevelError as e:
            logger.warning(str(e))
            git_toplevel = None

        _advance_progress(progress, task, "[cyan]Setup pre-commit hooks")
        try:
            _core.setup_prek_config(root, reset=ctx.args.reset)
        except tomlkit.exceptions.TOMLKitError:
            progress.update(
                task,
                description="[red][strike]Setup pre-commit hooks",
            )
            logger.exception("Failed to setup pre-commit hooks")
            return _core.ExitCode.EX_FAILURE

        _advance_progress(
            progress, task, "[cyan]Prek install pre-commit hooks"
        )
        _core.install_prek_hooks(git_toplevel or root)

        _advance_progress(progress, task, "[cyan]Prek check updates")
        _core.update_prek_hooks(root)

        _advance_progress(progress, task, "[cyan]Create `.secrets.baseline`")

        try:
            _core.create_secrets_baseline(root)
        except exceptions.Error:
            progress.update(
                task,
                description="[red][strike]Create `.secrets.baseline`",
            )
            logger.exception("Error creating `.secrets.baseline`")
            return _core.ExitCode.EX_FAILURE

        progress.update(task, description="[green]pkgdx complete")
        return _core.ExitCode.EX_OK


def main() -> None:
    """Provides CLI entrypoint for `pkgdx`."""
    parser = argparse.ArgumentParser(
        description="`pkgdx` - Canonical standards management"
    )

    # Require a subcommand ('setup')
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=True,
        help="Available commands",
    )

    parser_setup = subparsers.add_parser(
        "setup", help="Setup pre-commit hooks"
    )

    parser_setup.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging [DEBUG]",
    )

    parser_setup.add_argument(
        "--reset", action="store_true", help="Reset existing pre-commit hooks"
    )

    parser_setup.set_defaults(func=command_setup)

    args = parser.parse_args()

    # Configure logging based on verbosity
    is_verbose = args.verbose
    configure_cli_logging(logging.DEBUG if is_verbose else logging.WARNING)

    console = Console(force_terminal=sys.stdout.isatty())
    ctx = _core.CLIContext(args=args, console=console, is_verbose=is_verbose)

    exit_code = args.func(ctx)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
