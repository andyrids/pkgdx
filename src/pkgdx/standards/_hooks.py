"""Core pre-commit hook logic for the `pkgdx` canonical standards."""

import subprocess

from pkgdx import standards

# CORE HOOK LOGIC


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
