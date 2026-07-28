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
from pkgdx.logging import configure_cli_logging
from pkgdx.venvaxi._packages import PackageInfo
from pkgdx.venvaxi._store import NodeKind, SymbolNode


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
def tty_stdout_enable() -> Iterator[None]:
    """Mock `sys.stdout.isatty()` to return `True`."""
    with mock.patch("sys.stdout.isatty", return_value=True):
        yield


@pytest.fixture
def tty_stdout_disable() -> Iterator[None]:
    """Mock `sys.stdout.isatty()` to return `False`."""
    with mock.patch("sys.stdout.isatty", return_value=False):
        yield


@pytest.fixture
def mock_subprocess_run() -> Iterator[mock.MagicMock]:
    """Mock `subprocess.run` to avoid calling external tools."""
    with mock.patch("subprocess.run") as mocked:
        mocked.return_value.returncode = 0
        yield mocked


@pytest.fixture
def isolated_venv_axi_cache(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> pathlib.Path:
    """Isolates the `venv-axi` `SymbolStore` cache dir to `tmp_path`.

    Prevents tests from reading/writing the real `~/.pkgdx/venv-axi/`
    cache directory.
    """
    monkeypatch.setattr("pkgdx.venvaxi._cache.get_cache_dir", lambda: tmp_path)
    return tmp_path


@pytest.fixture
def make_symbol_node() -> Callable[..., SymbolNode]:
    """Factory-build a `SymbolNode` with defaults for every field.

    NOTE: Field-change insulation - a `SymbolNode` field addition only
    requires a new default here, not edits across every test module.
    """

    def factory(**overrides: Any) -> SymbolNode:
        defaults: dict[str, Any] = {
            "qualified_name": "pkg::Foo",
            "kind": NodeKind.CLASS,
            "name": "Foo",
            "module": "pkg",
            "signature": "",
            "doc": "",
            "package": "pkg",
            "version": "1.0.0",
        }
        return SymbolNode(**{**defaults, **overrides})

    return factory


@pytest.fixture
def make_package_info() -> Callable[..., PackageInfo]:
    """Factory-build a `PackageInfo` with defaults for every field."""

    def factory(**overrides: Any) -> PackageInfo:
        defaults: dict[str, Any] = {
            "name": "rich",
            "version": "15.0.0",
            "location": "/venv",
            "summary": "",
        }
        return PackageInfo(**{**defaults, **overrides})

    return factory


@pytest.fixture
def make_cli_context() -> Callable[..., CLIContext]:
    """Factory-build a `CLIContext` with defaults for every field."""

    def factory(**overrides: Any) -> CLIContext:
        defaults: dict[str, Any] = {
            "args": argparse.Namespace(),
            "console": Console(stderr=True),
            "is_verbose": False,
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
