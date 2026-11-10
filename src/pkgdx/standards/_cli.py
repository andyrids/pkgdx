"""CLI commands for a canonical standards interface and pre-commit hooks.

NOTE: `pkgdx.__main__` adds these commands (`command_init`,
`command_config`) to the `pkgdx` group. The ledger, notes & closing lines go
to the run's STDERR console (`ctx.err`); `config` source & exclude rows
to STDOUT.
"""

import dataclasses
import os
import time
from collections.abc import Callable, Sequence
from functools import partial
from pathlib import Path

import click
import pyclig
from rich.console import Console
from rich.text import Text

from pkgdx import _core, exceptions, standards
from pkgdx._core import Change, Outcome, StepResult

_BADGES = {
    Outcome.OK: ("ok", "green"),
    Outcome.WARN: ("warn", "bold yellow"),
    Outcome.FAIL: ("FAIL", "bold red"),
}
_STOP = ("stop", "bold red")
_CHANGED = frozenset({Change.CREATED, Change.UPDATED})
_KIND = max(map(len, Change)) + 2  # widest change word, then a gap
_INDENT = 8


def _row(
    console: Console,
    badge: tuple[str, str],
    label: str,
    detail: Text,
    width: int,
) -> None:
    """Print one aligned ledger line for a step.

    NOTE: The line is never wrapped, so a long path stays whole (a terminal
    may still soft-wrap it on screen) and a piped log has one line per step.

    Args:
        console: The STDERR console.
        badge: The state word and its Rich style.
        label: The step label.
        detail: The detail column text.
        width: The label column width.
    """
    word, style = badge
    row = Text.assemble(
        (f"  {word}".ljust(8), style),
        "  ",
        label.ljust(width),
        "  ",
        detail,
    )
    console.print(row, soft_wrap=True)


def _note(console: Console, text: str) -> None:
    """Print an indented continuation line under a ledger line.

    NOTE: Printed as `Text`, so markup, backticks and Windows paths are
    shown as written. Like `_row`, the line is never wrapped, so a long path
    stays whole (a terminal may still soft-wrap it on screen).

    Args:
        console: The STDERR console.
        text: The line text.
    """
    console.print(Text(" " * _INDENT + text), soft_wrap=True)


def _detail(result: StepResult) -> Text:
    """Build the detail column for a step result.

    Args:
        result: The step result.

    Returns:
        The detail text, or the padded change word followed by the subject.
    """
    if result.change is None:
        return Text(result.detail)
    style = "bold" if result.change in _CHANGED else "dim"
    return Text.assemble((f"{result.change:<{_KIND}}", style), result.subject)


def _report(
    console: Console, label: str, result: StepResult, width: int
) -> None:
    """Print a ledger line, plus the cause & hint for a WARN or FAIL result.

    Args:
        console: The STDERR console.
        label: The step label.
        result: The step result.
        width: The label column width.
    """
    _row(console, _BADGES[result.outcome], label, _detail(result), width)
    if result.outcome is not Outcome.OK:
        if result.message:
            _note(console, result.message)
        _note(console, f"-> {result.hint}")


@dataclasses.dataclass(slots=True)
class _InitState:
    """The paths found by the first init steps, for the later steps.

    Attributes:
        reset: Clean installation flag (`--reset`).
        root: The project root, set by the first step.
        git_toplevel: The Git top-level, or None outside a Git repository.
    """

    reset: bool
    root: Path = Path()
    git_toplevel: Path | None = None


def _find_project_root(state: _InitState) -> StepResult:
    """Find the project root & record it on the init state.

    Args:
        state: The init state to update.

    Returns:
        An OK result naming the root, or FAIL if no root is found.
    """
    try:
        state.root = _core.get_project_root()
    except exceptions.ProjectRootNotFoundError as e:
        return StepResult(
            Outcome.FAIL,
            "project root not found",
            str(e),
            "Run `pkgdx init` from inside a Python project",
        )
    return StepResult(Outcome.OK, f"{state.root} (pyproject.toml)")


def _find_git_toplevel(state: _InitState) -> StepResult:
    """Find the Git top-level & record it on the init state.

    Args:
        state: The init state to update.

    Returns:
        An OK result naming the top-level (or `same as project root`), or
        WARN without `git` or outside a Git repository.
    """
    try:
        state.git_toplevel = _core.get_git_toplevel()
    except exceptions.GitNotFoundError:
        return StepResult(
            Outcome.WARN,
            "`git` not found on PATH, using project root",
            hint="Install Git to enable pre-commit hooks",
        )
    except exceptions.GitTopLevelError:
        return StepResult(
            Outcome.WARN,
            "not a Git repository, using project root",
            hint="Run `git init` to enable pre-commit hooks",
        )
    if state.git_toplevel == state.root:
        return StepResult(Outcome.OK, "same as project root")
    return StepResult(Outcome.OK, str(state.git_toplevel))


# Lambdas look up `_core.<fn>` when called, so tests can patch them
_STEPS: tuple[tuple[str, Callable[[_InitState], StepResult]], ...] = (
    ("identify project root", _find_project_root),
    ("identify Git top-level", _find_git_toplevel),
    (
        "configure pre-commit hooks",
        lambda s: _core.setup_prek_config(s.root, s.reset),
    ),
    (
        "prek install",
        lambda s: _core.install_prek_hooks(s.root, s.git_toplevel),
    ),
    ("prek update --check", lambda s: _core.update_prek_hooks(s.root)),
    ("detect-secrets scan", lambda s: _core.create_secrets_baseline(s.root)),
)


def _run_steps(
    console: Console,
    command: str,
    steps: Sequence[tuple[str, Callable[[], StepResult]]],
    quiet: bool = False,
) -> int:
    """Run ledger steps in order, printing one line per step & a summary.

    NOTE: Prints to STDERR, with a transient spinner only when STDERR is an
    interactive terminal. Debug log lines (`-d`) appear above the line of
    the step that emitted them. Stops at the first FAIL. With `quiet`, OK
    rows & the `done` line are skipped; warnings & failures stay.

    Args:
        console: The STDERR console, shared with logging.
        command: The `pkgdx` subcommand, named in the closing line.
        steps: The step labels & callables, in run order.
        quiet: Skip OK rows & the `done` line (`-q`).

    Returns:
        The integer process exit code. 0 on success (with or without
        warnings), 1 on a failed step and 130 on Ctrl-C.
    """
    width = max(len(label) for label, _ in steps)
    start = time.monotonic()
    warnings = changed = unchanged = 0
    label = ""
    try:
        for number, (label, run) in enumerate(steps, 1):
            if console.is_interactive:
                with console.status(f"{label} ...", spinner="dots"):
                    result = run()
            else:
                result = run()

            if not (quiet and result.outcome is Outcome.OK):
                _report(console, label, result, width)
            if result.outcome is Outcome.FAIL:
                closing = (
                    f"pkgdx {command}: failed at step {number}/{len(steps)}"
                )
                if unrun := [name for name, _ in steps[number:]]:
                    _note(console, f"not run: {', '.join(unrun)}")
                    count = f"{len(unrun)} step{'s' * (len(unrun) != 1)}"
                    closing += f" ({count} not run)"
                console.print(Text(closing))
                return pyclig.ExitCode.FAILURE

            warnings += result.outcome is Outcome.WARN
            changed += result.change in _CHANGED
            unchanged += result.change is Change.UNCHANGED
    except KeyboardInterrupt:
        _row(console, _STOP, label, Text("interrupted"), width)
        raise

    tail = (
        f" with {warnings} warning{'s' * (warnings != 1)}" if warnings else ""
    )
    counts = (
        f"{changed} changed, {unchanged} unchanged"
        if changed
        else "nothing to change"
    )
    elapsed = time.monotonic() - start
    if not quiet:
        console.print(
            Text(f"pkgdx {command}: done in {elapsed:.1f}s{tail} ({counts})")
        )
    return pyclig.ExitCode.OK


@click.command(
    "init",
    cls=pyclig.Command,
    examples=["pkgdx init", "pkgdx init --reset"],
)
@click.option("--reset", is_flag=True, help="Reset existing pre-commit hooks")
@pyclig.pass_context
def command_init(ctx: pyclig.Context, reset: bool) -> int:
    """Set up canonical standards & pre-commit hooks.

    \f
    Attempts to identify the root of the consuming repo and ensures that
    `Prek` is configured with the expected `pkgdx` hooks.

    NOTE: Prints one ledger line per step to STDERR (`_run_steps`).

    Args:
        ctx: The CLI context.
        reset: Clean installation flag (`--reset`).

    Returns:
        The integer process exit code. 0 on success (with or without
        warnings), 1 on a failed step and 130 on Ctrl-C.
    """
    state = _InitState(reset=reset)
    return _run_steps(
        ctx.err,
        "init",
        [(label, partial(run, state)) for label, run in _STEPS],
        ctx.quiet,
    )


@click.command(
    "config",
    cls=pyclig.Command,
    examples=["pkgdx config", "pkgdx config --export"],
)
@click.option(
    "--export",
    is_flag=True,
    help="Copy bundled configs into the user config directory",
)
@pyclig.pass_context
def command_config(ctx: pyclig.Context, export: bool) -> int:
    """Show config sources & excludes or export bundled configs.

    \f
    NOTE: Source & project exclude rows go to STDOUT (`ctx.out`). The closing
    line, the `--export` ledger and errors go to STDERR (`ctx.err`).

    Args:
        ctx: The CLI context.
        export: Copy bundled configs into the user config directory.

    Returns:
        The integer process exit code. 0 on success, 1 on an invalid
        `PKGDX_CONFIG_DIR`, an invalid `[tool.pkgdx]` table or a failed copy
        and 130 on Ctrl-C during `--export`.

    Raises:
        exceptions.ProjectConfigError: If the `[tool.pkgdx]` table is invalid,
            before any row prints.
    """
    env = standards.CONFIG_DIR_ENV
    try:
        user_dir = standards.user_config_dir()
    except exceptions.ConfigDirError as e:
        _report(ctx.err, env, _core.config_dir_failure(e), len(env))
        ctx.err.print(Text("pkgdx config: failed"))
        return pyclig.ExitCode.FAILURE

    if export:
        return _run_steps(
            ctx.err,
            "config",
            [
                (bundled.name, partial(_core.export_config, bundled, user_dir))
                for bundled in standards.BUNDLED_CONFIGS
            ],
            ctx.quiet,
        )

    excludes = standards.project_excludes()
    width = max(len(bundled.name) for bundled in standards.BUNDLED_CONFIGS)
    users = 0
    for bundled in standards.BUNDLED_CONFIGS:
        resolved = standards.resolve_config(bundled)
        is_user = resolved != bundled
        users += is_user
        source, style = ("user", "bold") if is_user else ("bundled", "dim")
        row = Text.assemble(
            "  ",
            bundled.name.ljust(width),
            "  ",
            (f"{source:<{_KIND}}", style),
            str(resolved),
        )
        ctx.out.print(row, soft_wrap=True)

    for path in excludes:
        row = Text.assemble(
            "  ",
            "exclude".ljust(width),
            "  ",
            (f"{'project':<{_KIND}}", "bold"),
            path,
            "" if Path(path).exists() else " (not found)",
        )
        ctx.out.print(row, soft_wrap=True)

    via = f"from {env}" if os.environ.get(env) else f"{env} not set"
    sources = f"{users} user, {len(standards.BUNDLED_CONFIGS) - users} bundled"
    if not ctx.quiet:
        ctx.err.print(
            Text(
                f"pkgdx config: user config dir {user_dir}, {via} ({sources})"
            ),
            soft_wrap=True,
        )
    return pyclig.ExitCode.OK
