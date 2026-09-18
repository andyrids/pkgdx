"""CLI commands for a canonical standards interface and pre-commit hooks.

NOTE: The `__main__` `argparse.ArgumentParser` pgkdx CLI entry point uses this
module to register subcommands (`add_subparser`) for managing canonical
standards and pre-commit hooks.
"""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Optional

import tomlkit
import tomlkit.exceptions
from rich.progress import Progress, TaskID

from pkgdx import _core, exceptions
from pkgdx._core import CLIContext, CLIGFormatter, ExitCode
from pkgdx.logging import GLOBAL_CONSOLE

if TYPE_CHECKING:
    import argparse

logger = logging.getLogger(__package__)


@contextmanager
def _setup_progress() -> Generator[Progress, None, None]:
    """Create a Rich progress bar for the setup command.

    NOTE: Like logs, progress bars and spinners are diagnostic metadata, which
    are kept on STDERR and share the same console instance (`GLOBAL_CONSOLE`).

    Returns:
        A Rich `Progress` instance for use within a context manager.
    """

    progress = Progress(
        *Progress.get_default_columns(),
        console=GLOBAL_CONSOLE,
        disable=not GLOBAL_CONSOLE.is_terminal,
    )

    try:
        with progress:
            yield progress
    finally:
        pass


def _advance_progress(
    progress: Progress,
    task_id: TaskID,
    description: str,
) -> None:
    """Update the description & advance a progress task by one step."""
    progress.update(task_id, description=description, advance=1)


def command_init(ctx: CLIContext) -> int:
    """Configure a consuming repo with `pkgdx` standards.

    Attempts to identify the root of the consuming repo and ensures that
    `Prek` is configured with the expected `pkgdx` hooks.

    Args:
        ctx: The CLI context.

    Returns:
        The integer process exit code. 0 indicates success, non-zero
        indicates failure. Uses `_core.ExitCode`.
    """
    with _setup_progress() as progress:
        task = progress.add_task("[cyan]pkgdx init", total=6)

        _advance_progress(progress, task, "[cyan]Find project root")
        try:
            root = _core.get_project_root()
        except exceptions.ProjectRootNotFoundError:
            progress.update(
                task,
                description="[red]Failed to find project root",
            )
            logger.exception("Failed to find project root")
            return ExitCode.EX_FAILURE

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
            return ExitCode.EX_FAILURE

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
            return ExitCode.EX_FAILURE

        progress.update(task, description="[green]pkgdx complete")
        return ExitCode.EX_OK


def add_subparser(
    subparsers: "argparse._SubParsersAction[Any]",
    parent: Optional["argparse.ArgumentParser"] = None,
) -> None:
    """Add the `init` subcommand with the shared `pkgdx` CLI parser.

    Args:
        subparsers: The main CLI parser's subparsers action.
        parent: A parent parser to include for shared arguments.
    """

    init_text = "Setup canonical standards & pre-commit hooks"
    parser_init = subparsers.add_parser(
        "init",
        help=init_text,
        description=init_text,
        usage="USAGE:\n %(prog)s [options]",
        add_help=False,
        parents=[parent] if parent else [],
        formatter_class=CLIGFormatter,
    )

    parser_init._optionals.title = "OPTIONS"

    parser_init.add_argument(
        "--reset", action="store_true", help="Reset existing pre-commit hooks"
    )

    parser_init.set_defaults(func=command_init)
