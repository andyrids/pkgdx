"""Core pre-commit hook logic for the `pkgdx` canonical standards."""

import os
import subprocess
from itertools import islice
from typing import Any

from pkgdx import exceptions, standards

# PyMarkdown's global options (`pymarkdown --help`, 0.9.41), which go before
# `scan`. The short `-e` is left out: after `scan` it means `--exclude`.
_PYMARKDOWN_FLAGS = frozenset(
    {"--continue-on-error", "--no-json5", "--stack-trace", "--strict-config"}
)
_PYMARKDOWN_OPTIONS = frozenset(
    {
        "--add-plugin",
        "-c",
        "--config",
        "-d",
        "--disable-rules",
        "--enable-extensions",
        "--enable-rules",
        "--log-file",
        "--log-level",
        "--return-code-scheme",
        "-s",
        "--set",
    }
)


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
    scan after it. The args that are global options move before `scan`, in
    order: a flag (`_PYMARKDOWN_FLAGS`, e.g. `--stack-trace`), or an option
    & its value (`_PYMARKDOWN_OPTIONS`, e.g. `-d md013` or `--set=k=v`).
    The rest - paths & `scan`'s own options, e.g. `-r` or `-e` (`--exclude`)
    - follow `scan` in order, as before.

    Args:
        args: The hook arguments: paths, `scan` & global options.

    Returns:
        The PyMarkdown return code.

    Raises:
        exceptions.ToolNotFoundError: If `pymarkdown` is not on `PATH`.
    """
    config = standards.resolve_config(standards.PYMARKDOWN_CONFIG).as_posix()
    options: list[str] = []
    scan_args: list[str] = []
    remaining = iter(args)
    for arg in remaining:
        if arg in _PYMARKDOWN_OPTIONS:
            options += [arg, *islice(remaining, 1)]  # the option & its value
        elif (
            arg in _PYMARKDOWN_FLAGS
            or arg.partition("=")[0] in _PYMARKDOWN_OPTIONS
        ):
            options.append(arg)
        else:
            scan_args.append(arg)
    cmd = [
        "pymarkdown",
        "--config",
        config,
        "--continue-on-error",
        *options,
        "scan",
        *scan_args,
    ]
    return _run_tool(cmd)
