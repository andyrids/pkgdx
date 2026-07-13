"""Shared fixtures accross the `tests/` directory."""

import logging
from collections.abc import Iterator
from unittest import mock

import pytest

from pytack.logging import configure_cli_logging


@pytest.fixture
def configured_logging() -> Iterator[None]:
    """Configures CLI logging for tests and cleans up handlers afterwards."""
    configure_cli_logging()
    try:
        yield
    finally:
        logger = logging.getLogger("pytack")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)


@pytest.fixture
def tty_stdout() -> Iterator[None]:
    """Mocks ``sys.stdout.isatty()`` to return ``True``."""
    with mock.patch("sys.stdout.isatty", return_value=True):
        yield


@pytest.fixture
def non_tty_stdout() -> Iterator[None]:
    """Mocks ``sys.stdout.isatty()`` to return ``False``."""
    with mock.patch("sys.stdout.isatty", return_value=False):
        yield


@pytest.fixture
def mock_subprocess_run() -> Iterator[mock.MagicMock]:
    """Mocks ``subprocess.run`` to avoid calling external tools."""
    with mock.patch("subprocess.run") as mocked:
        mocked.return_value.returncode = 0
        yield mocked
