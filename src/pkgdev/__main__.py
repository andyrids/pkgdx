"""Main entry point for pkgdev pre-commit hooks."""

import sys
import subprocess
from typing import NoReturn
from pkgdev import standards


def ruff_format() -> NoReturn:
    """Runs ruff formatting with the configured settings.

    Returns:
        None
    """
    config = standards.RUFF_CONFIG.as_posix()
    # Combine the base command, the explicit config flag, and any
    # args passed by prek
    cmd = ["ruff", "format", "--config", config] + sys.argv[1:]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def ruff_lint() -> NoReturn:
    """Runs ruff linting with the configured settings.

    Returns:
        None
    """
    config = standards.RUFF_CONFIG.as_posix()
    cmd = ["ruff", "check", "--config", config] + sys.argv[1:]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def mypy_typing() -> NoReturn:
    """Runs mypy type checking with the configured settings.

    Returns:
        None
    """
    config = standards.MYPY_CONFIG.as_posix()
    cmd = ["mypy", "--config-file", config] + sys.argv[1:]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def detect_secrets() -> NoReturn:
    """Runs detect-secrets with the provided arguments.

    Returns:
        None
    """
    # detect-secrets relies on a .secrets.baseline file which must live
    # in the consuming repo, so we just pass the arguments straight through.
    cmd = ["detect-secrets-hook"] + sys.argv[1:]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)
