"""Core pre-commit hook logic for the `pkgdx` canonical standards."""

import os
import subprocess
from pathlib import Path
from typing import Any

from pkgdx import exceptions, standards


def _run_tool(cmd: list[str], **kwargs: Any) -> int:
    """Run a hook tool & return its exit code.

    Args:
        cmd: The tool command, its executable first.
        **kwargs: Extra `subprocess.run` keyword arguments.

    Returns:
        The tool's return code.

    Raises:
        exceptions.ToolNotFoundError: If the executable is not on `PATH`.
    """
    try:
        proc = subprocess.run(cmd, **kwargs)
    except FileNotFoundError as e:
        msg = (
            f"`{cmd[0]}` not found on PATH - run the hook in the environment"
            " pkgdx is installed in, e.g. via `uv run`"
        )
        raise exceptions.ToolNotFoundError(msg) from e
    else:
        return proc.returncode


# CORE HOOK LOGIC


def core_ruff_format(args: list[str]) -> int:
    """Core logic for ruff formatting."""
    config = standards.resolve_config(standards.RUFF_CONFIG).as_posix()
    cmd = ["ruff", "format", "--config", config] + args
    return _run_tool(cmd)


def core_ruff_lint(args: list[str]) -> int:
    """Core logic for ruff linting."""
    config = standards.resolve_config(standards.RUFF_CONFIG).as_posix()
    cmd = ["ruff", "check", "--config", config] + args
    return _run_tool(cmd)


def core_mypy_typing(args: list[str]) -> int:
    """Core logic for mypy type checking."""
    config = standards.resolve_config(standards.MYPY_CONFIG).as_posix()
    cmd = ["mypy", "--config-file", config] + args
    return _run_tool(cmd)


def core_detect_secrets(args: list[str]) -> int:
    """Core logic for detect-secrets."""
    if "--baseline" not in args:
        args = ["--baseline", ".secrets.baseline"] + args
    cmd = ["detect-secrets-hook"] + args
    # detect-secrets opens files with the locale encoding & silently skips
    # files that fail to decode (cp1252 on Windows), so force UTF-8 mode.
    env = os.environ | {"PYTHONUTF8": "1"}
    return _run_tool(cmd, env=env)


def core_pymarkdown_lint(args: list[str]) -> int:
    """Core logic for pymarkdown linting.

    NOTE: PyMarkdown takes its global options before `scan` & the paths to
    scan after it. The args are split at the first one naming an existing
    path, as prek passes file names last: the args before it (e.g.
    `--stack-trace`, or `-d md013` with its value) go before `scan`, that
    path & the rest after it - so an option of `scan` itself (e.g. `-r`)
    must follow the first path. With no existing path, all the args follow
    `scan`, so PyMarkdown reports a missing file.

    Args:
        args: PyMarkdown global options, then the paths to scan.

    Returns:
        The PyMarkdown return code.

    Raises:
        exceptions.ToolNotFoundError: If `pymarkdown` is not on `PATH`.
    """
    config = standards.resolve_config(standards.PYMARKDOWN_CONFIG).as_posix()
    split = next((i for i, arg in enumerate(args) if Path(arg).exists()), 0)
    cmd = [
        "pymarkdown",
        "--config",
        config,
        "--continue-on-error",
        *args[:split],
        "scan",
        *args[split:],
    ]
    return _run_tool(cmd)
