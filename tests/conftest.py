"""Shared unit test fixtures."""

import json
import pathlib
from collections.abc import Callable, Iterator
from unittest import mock

import pytest


@pytest.fixture(autouse=True)
def isolated_user_config(
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> pathlib.Path:
    """Point `PKGDX_CONFIG_DIR` at an empty dir so real config can't leak."""
    config_dir = tmp_path_factory.mktemp("user_config")
    monkeypatch.setenv("PKGDX_CONFIG_DIR", str(config_dir))
    return config_dir


@pytest.fixture
def excluded_project(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[..., pathlib.Path]:
    """Build a project with a `[tool.pkgdx] exclude` list & enter it."""

    def factory(*paths: str) -> pathlib.Path:
        exclude = json.dumps(paths, ensure_ascii=False)
        (tmp_path / "pyproject.toml").write_text(
            f"[tool.pkgdx]\nexclude = {exclude}\n",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        return tmp_path

    return factory


@pytest.fixture
def mock_subprocess_run() -> Iterator[mock.MagicMock]:
    """Mock `subprocess.run` to avoid calling external tools."""
    with mock.patch("subprocess.run") as mocked:
        mocked.return_value.returncode = 0
        yield mocked


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
