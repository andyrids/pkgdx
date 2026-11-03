"""Core pre-commit hook logic for the `pkgdx` canonical standards."""

import json
import os
import re
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
        raise exceptions.ToolNotFoundError(
            f"`{cmd[0]}` not found on PATH"
        ) from e
    else:
        return proc.returncode


# PROJECT EXCLUDES


def _ruff_exclude_args() -> list[str]:
    """Translate the project excludes into Ruff arguments.

    NOTE: Inline `--config`, as `ruff format --extend-exclude` needs ruff
    0.15.21 & Ruff glob-expands flag values on Windows. `./` anchors a path
    to the working directory; a bare name would match at any depth. Never
    `--exclude`, which would replace Ruff's default exclusions.

    Returns:
        The arguments, empty if the project excludes nothing.

    Raises:
        exceptions.ProjectConfigError: If the project list is invalid.
    """
    excludes = standards.project_excludes()
    if not excludes:
        return []
    paths = [f"./{path}" for path in excludes]
    value = json.dumps(paths, ensure_ascii=False)
    return ["--config", f"extend-exclude={value}"]


def _mypy_exclude_args(args: list[str]) -> list[str]:
    """Translate the project excludes into Mypy arguments.

    NOTE: `--exclude` adds to the config's `exclude` & only filters discovery.
    With no args the whole project is checked, so `--follow-imports=silent`
    only hides errors in excluded code the project imports, which a consumer
    cannot do as the shim pins the config file. Args may narrow the target,
    where the flag would hide errors in first-party code too, so it stays off.

    Args:
        args: The hook arguments.

    Returns:
        The arguments, empty if the project excludes nothing.

    Raises:
        exceptions.ProjectConfigError: If the project list is invalid.
    """
    excludes = standards.project_excludes()
    patterns = [
        arg
        for path in excludes
        for arg in ("--exclude", f"^{re.escape(path)}(/|$)")
    ]
    silent = excludes and not args
    return [*patterns, "--follow-imports=silent"] if silent else patterns


def _is_excluded(arg: str, excludes: list[str]) -> bool:
    """Check whether a hook argument is a path under an excluded path.

    NOTE: Compares strings, as Mypy does, so that a match is case-sensitive
    on every platform.

    Args:
        arg: The hook argument.
        excludes: The project excludes, relative to the working directory.

    Returns:
        True if the argument is an excluded path or is below one.
    """
    try:
        path = os.path.relpath(arg).replace(os.sep, "/")
    except ValueError:  # on another Windows drive, so outside the project
        return False
    return any(
        path == exclude or path.startswith(f"{exclude}/")
        for exclude in excludes
    )


# CORE HOOK LOGIC


def core_ruff_format(args: list[str]) -> int:
    """Core logic for ruff formatting."""
    config = standards.resolve_config(standards.RUFF_CONFIG).as_posix()
    cmd = ["ruff", "format", "--config", config, *_ruff_exclude_args(), *args]
    return _run_tool(cmd)


def core_ruff_lint(args: list[str]) -> int:
    """Core logic for ruff linting."""
    config = standards.resolve_config(standards.RUFF_CONFIG).as_posix()
    cmd = ["ruff", "check", "--config", config, *_ruff_exclude_args(), *args]
    return _run_tool(cmd)


def core_mypy_typing(args: list[str]) -> int:
    """Core logic for mypy type checking."""
    config = standards.resolve_config(standards.MYPY_CONFIG).as_posix()
    cmd = ["mypy", "--config-file", config, *_mypy_exclude_args(args), *args]
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

    Project excludes are dropped from a plain list of paths, which is what
    prek passes, not passed as `-e`: PyMarkdown exits 1 silently when `-e`
    leaves it nothing to scan, so the hook returns 0. A command with `scan`
    options is hand-written & runs as given, as an option's value is no path.

    Args:
        args: The hook arguments: paths, `scan` & global options.

    Returns:
        The PyMarkdown return code, or 0 if every path was dropped.

    Raises:
        exceptions.ProjectConfigError: If the project list is invalid.
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

    excludes = standards.project_excludes()
    has_options = any(
        arg.startswith("-") and not os.path.lexists(arg) for arg in scan_args
    )
    if scan_args and not has_options:
        scan_args = [a for a in scan_args if not _is_excluded(a, excludes)]
        if not scan_args:
            return 0

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
