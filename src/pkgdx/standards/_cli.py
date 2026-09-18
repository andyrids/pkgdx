"""CLI commands for a canonical standards interface and pre-commit hooks.

NOTE: The `__main__` `argparse.ArgumentParser` pgkdx CLI entry point uses this
module to register subcommands (`add_subparser`) for managing canonical
standards and pre-commit hooks.
"""

import logging
from collections.abc import Generator, Iterable
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Optional

import tomlkit
import tomlkit.exceptions
from rich.console import RenderableType
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    Task,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Column
from rich.text import Text

from pkgdx import _core, exceptions
from pkgdx._core import CLIContext, CLIGFormatter, ExitCode
from pkgdx.logging import GLOBAL_CONSOLE

if TYPE_CHECKING:
    import argparse

logger = logging.getLogger(__package__)

_INIT_STEP_COUNT = 6


class _StatusSpinnerColumn(SpinnerColumn):
    """A spinner that swaps to a check or cross when the task finishes."""

    def render(self, task: Task) -> RenderableType:
        """Render a spinner, a green check, or a red cross.

        Args:
            task: The progress task being rendered.

        Returns:
            The spinner animation, or a finished-state glyph.
        """
        if task.fields.get("failed"):
            return Text("✗", style="red")
        return super().render(task)


class _OverallColumn(ProgressColumn):
    """A column that renders only for the overall init task."""

    def __init__(self, column: ProgressColumn) -> None:
        """Wrap a column so step rows leave it blank.

        Args:
            column: The column rendered for the overall task.
        """
        self._column = column
        super().__init__(table_column=column.get_table_column())

    def render(self, task: Task) -> RenderableType:
        """Render the wrapped column for the overall task only.

        Args:
            task: The progress task being rendered.

        Returns:
            The wrapped column output, or empty text for step rows.
        """
        if task.fields.get("role") != "overall":
            return Text()
        return self._column.render(task)


class _InitProgress(Progress):
    """A progress display that renders the overall bar below init steps."""

    def get_renderables(self) -> Iterable[RenderableType]:
        """Yield the tasks table with the overall bar last.

        Yields:
            The reordered tasks table.
        """
        steps = [
            task for task in self.tasks if task.fields.get("role") != "overall"
        ]
        overall = [
            task for task in self.tasks if task.fields.get("role") == "overall"
        ]
        yield self.make_tasks_table([*steps, *overall])


@contextmanager
def _setup_progress() -> Generator[Progress, None, None]:
    """Create a Rich progress display for the init command.

    NOTE: Like logs, progress bars and spinners are diagnostic metadata, which
    are kept on STDERR and share the same console instance (`GLOBAL_CONSOLE`).

    Yields:
        A Rich `Progress` instance for use within a context manager.
    """
    progress = _InitProgress(
        _StatusSpinnerColumn(
            spinner_name="dots",
            style="cyan",
            finished_text="[green]✓",
        ),
        TextColumn(
            "[progress.description]{task.description}",
            table_column=Column(
                ratio=1,
                no_wrap=False,
                overflow="fold",
            ),
        ),
        _OverallColumn(
            BarColumn(
                bar_width=None,
                table_column=Column(ratio=2),
            )
        ),
        _OverallColumn(MofNCompleteColumn()),
        _OverallColumn(TimeElapsedColumn()),
        console=GLOBAL_CONSOLE,
        expand=True,
        disable=not GLOBAL_CONSOLE.is_terminal,
        transient=False,
    )
    with progress:
        yield progress


def _add_step(progress: Progress, description: str) -> TaskID:
    """Add a visible init step that starts incomplete.

    Args:
        progress: The active progress display.
        description: The step label shown beside the spinner.

    Returns:
        The new step's task ID.
    """
    return progress.add_task(description, total=1)


def _complete_step(
    progress: Progress,
    overall: TaskID,
    step: TaskID,
) -> None:
    """Mark a step complete and advance the overall bar.

    Args:
        progress: The active progress display.
        overall: The overall init task ID.
        step: The completed step task ID.
    """
    progress.update(step, completed=1)
    progress.update(overall, advance=1)


def _fail_step(
    progress: Progress,
    step: TaskID,
    description: str,
) -> None:
    """Mark a step failed with a red strikethrough description.

    Args:
        progress: The active progress display.
        step: The failed step task ID.
        description: The unstyled step label to strike through.
    """
    progress.update(
        step,
        description=f"[red][strike]{description}",
        completed=1,
        failed=True,
    )


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
    GLOBAL_CONSOLE.rule("[cyan]pkgdx init")
    with _setup_progress() as progress:
        overall = progress.add_task(
            "[cyan]pkgdx init",
            total=_INIT_STEP_COUNT,
            role="overall",
        )

        step = _add_step(progress, "[cyan]Find project root")
        try:
            root = _core.get_project_root()
        except exceptions.ProjectRootNotFoundError:
            _fail_step(progress, step, "Find project root")
            logger.exception("Failed to find project root")
            return ExitCode.EX_FAILURE
        _complete_step(progress, overall, step)

        step = _add_step(progress, "[cyan]Find Git top-level")
        try:
            git_toplevel = _core.get_git_toplevel()
        except exceptions.GitTopLevelError as e:
            logger.warning(str(e))
            git_toplevel = None
        _complete_step(progress, overall, step)

        step = _add_step(progress, "[cyan]Configure pre-commit hooks")
        try:
            _core.setup_prek_config(root, reset=ctx.args.reset)
        except tomlkit.exceptions.TOMLKitError:
            _fail_step(progress, step, "Configure pre-commit hooks")
            logger.exception("Failed to configure pre-commit hooks")
            return ExitCode.EX_FAILURE
        _complete_step(progress, overall, step)

        step = _add_step(progress, "[cyan]Prek install Git shims")
        _core.install_prek_hooks(git_toplevel or root)
        _complete_step(progress, overall, step)

        step = _add_step(progress, "[cyan]Prek check hook revisions")
        _core.update_prek_hooks(root)
        _complete_step(progress, overall, step)

        step = _add_step(progress, "[cyan]Configure `.secrets.baseline`")
        try:
            _core.create_secrets_baseline(root)
        except exceptions.Error:
            _fail_step(progress, step, "Configure `.secrets.baseline`")
            logger.exception("Error configuring `.secrets.baseline`")
            return ExitCode.EX_FAILURE
        _complete_step(progress, overall, step)

        progress.update(overall, description="[green]pkgdx init")
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
