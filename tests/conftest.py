"""Shared fixtures accross the `tests/` directory."""

from collections.abc import Iterator
from unittest import mock

import pytest


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
