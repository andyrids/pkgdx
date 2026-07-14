"""Shared fixtures across the unit tests."""

import logging
import pathlib
from collections.abc import Iterator
from unittest import mock

import pytest

from pytack.logging import configure_cli_logging


@pytest.fixture
def configured_logging() -> Iterator[None]:
    """Configures CLI logging for tests & cleans up handlers afterwards."""
    configure_cli_logging()
    try:
        yield
    finally:
        logger = logging.getLogger("pytack")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)


@pytest.fixture
def tty_stdout_enable() -> Iterator[None]:
    """Mocks `sys.stdout.isatty()` to return `True`."""
    with mock.patch("sys.stdout.isatty", return_value=True):
        yield


@pytest.fixture
def tty_stdout_disable() -> Iterator[None]:
    """Mocks `sys.stdout.isatty()` to return `False`."""
    with mock.patch("sys.stdout.isatty", return_value=False):
        yield


@pytest.fixture
def mock_subprocess_run() -> Iterator[mock.MagicMock]:
    """Mocks `subprocess.run` to avoid calling external tools."""
    with mock.patch("subprocess.run") as mocked:
        mocked.return_value.returncode = 0
        yield mocked

@pytest.fixture(scope="session")
def mock_project(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Creates a temporary project directory for testing."""

    root = tmp_path_factory.mktemp("project")

    pyproject = root / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'test'")

    pre_commit = root / ".git" / "hooks" / "pre-commit"
    pre_commit.parent.mkdir(parents=True, exist_ok=True)
    pre_commit.write_text("#!/bin/sh")

    prek = root / "prek.toml"
    prek.write_text("[[repos]]")

    secrets = root / ".secrets.baseline"
    secrets.write_text("{}")

    return root
