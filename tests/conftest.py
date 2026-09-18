"""Shared unit test fixtures."""

import argparse
import logging
import pathlib
from collections.abc import Callable, Iterator
from typing import Any
from unittest import mock

import pytest
from rich.console import Console

from pkgdx._core import CLIContext
from pkgdx.logging import GLOBAL_CONSOLE, configure_cli_logging


@pytest.fixture
def configured_logging() -> Iterator[None]:
    """Configure CLI logging for tests & clean up handlers afterwards."""
    configure_cli_logging()
    try:
        yield
    finally:
        logger = logging.getLogger("pkgdx")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)


@pytest.fixture
def tty_stderr_enable() -> Iterator[None]:
    """Treat GLOBAL_CONSOLE (STDERR) as a TTY for progress/log tests."""
    with mock.patch.object(GLOBAL_CONSOLE, "_force_terminal", True):
        yield


@pytest.fixture
def tty_stderr_disable() -> Iterator[None]:
    """Treat GLOBAL_CONSOLE (STDERR) as non-TTY for progress/log tests."""
    with mock.patch.object(GLOBAL_CONSOLE, "_force_terminal", False):
        yield


@pytest.fixture
def mock_subprocess_run() -> Iterator[mock.MagicMock]:
    """Mock `subprocess.run` to avoid calling external tools."""
    with mock.patch("subprocess.run") as mocked:
        mocked.return_value.returncode = 0
        yield mocked


@pytest.fixture
def make_cli_context() -> Callable[..., CLIContext]:
    """Factory-build a `CLIContext` with defaults for every field."""

    def factory(**overrides: Any) -> CLIContext:
        args = argparse.Namespace()
        vars(args).update(vars(overrides.pop("args", argparse.Namespace())))
        defaults: dict[str, Any] = {
            "args": args,
            "console": Console(stderr=True),
            "is_debug": False,
        }
        return CLIContext(**{**defaults, **overrides})

    return factory


@pytest.fixture(scope="function")
def mock_project(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Create a temporary project directory for testing."""

    root = tmp_path_factory.mktemp("project")

    pyproject = root / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'test'")

    pre_commit = root / ".git" / "hooks" / "pre-commit"
    pre_commit.parent.mkdir(parents=True, exist_ok=True)
    pre_commit.write_text("#!/bin/sh")

    prek = root / "prek.toml"
    prek.write_text('[[repos]]\nrepo = "local"\nhooks = []')

    secrets = root / ".secrets.baseline"
    secrets.write_text("{}")

    return root
