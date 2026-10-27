"""Unit tests for user config resolution (`pkgdx.standards`)."""

import logging
import sys
from pathlib import Path

import pytest

from pkgdx import exceptions, standards


def test_env_dir_wins(isolated_user_config: Path) -> None:
    """A valid `PKGDX_CONFIG_DIR` is returned as is."""
    assert standards.user_config_dir() == isolated_user_config


def test_env_dir_missing_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing env dir raises `ConfigDirError`."""
    monkeypatch.setenv(standards.CONFIG_DIR_ENV, str(tmp_path / "nope"))
    with pytest.raises(exceptions.ConfigDirError):
        standards.user_config_dir()


def test_env_dir_file_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An env path that is a file raises `ConfigDirError`."""
    file = tmp_path / "file"
    file.write_text("x")
    monkeypatch.setenv(standards.CONFIG_DIR_ENV, str(file))
    with pytest.raises(exceptions.ConfigDirError):
        standards.user_config_dir()


def test_env_dir_empty_ignored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An empty env value falls through to the platform directory."""
    monkeypatch.setenv(standards.CONFIG_DIR_ENV, "")
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert standards.user_config_dir() == tmp_path / "pkgdx"


def test_windows_appdata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Windows uses the `APPDATA` directory."""
    monkeypatch.delenv(standards.CONFIG_DIR_ENV)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert standards.user_config_dir() == tmp_path / "pkgdx"


def test_absolute_xdg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An absolute `XDG_CONFIG_HOME` is honoured."""
    monkeypatch.delenv(standards.CONFIG_DIR_ENV)
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert standards.user_config_dir() == tmp_path / "pkgdx"


def test_relative_xdg_falls_back_to_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A relative `XDG_CONFIG_HOME` is ignored for `~/.config`."""
    monkeypatch.delenv(standards.CONFIG_DIR_ENV)
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", "relative/dir")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert standards.user_config_dir() == tmp_path / ".config" / "pkgdx"


def test_windows_without_appdata_falls_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Windows without `APPDATA` falls through to `~/.config`."""
    monkeypatch.delenv(standards.CONFIG_DIR_ENV)
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert standards.user_config_dir() == tmp_path / ".config" / "pkgdx"


def test_resolve_prefers_user_file(isolated_user_config: Path) -> None:
    """A user file replaces the bundled one."""
    user_file = isolated_user_config / "ruff.toml"
    user_file.write_text("")
    assert standards.resolve_config(standards.RUFF_CONFIG) == user_file


def test_resolve_falls_back_per_file(isolated_user_config: Path) -> None:
    """Only the file present in the user dir is overridden."""
    (isolated_user_config / "ruff.toml").write_text("")
    assert standards.resolve_config(standards.MYPY_CONFIG) == (
        standards.MYPY_CONFIG
    )


def test_resolve_ignores_directory(isolated_user_config: Path) -> None:
    """A directory named like a config file is ignored."""
    (isolated_user_config / "ruff.toml").mkdir()
    assert standards.resolve_config(standards.RUFF_CONFIG) == (
        standards.RUFF_CONFIG
    )


def test_resolve_logs_debug(
    isolated_user_config: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The resolver logs which source it used."""
    (isolated_user_config / "ruff.toml").write_text("")
    with caplog.at_level(logging.DEBUG, logger="pkgdx"):
        standards.resolve_config(standards.RUFF_CONFIG)
        standards.resolve_config(standards.MYPY_CONFIG)
    assert "Using user config" in caplog.text
    assert "Using bundled config" in caplog.text


def test_get_config_revision_ignores_user_hooks(
    isolated_user_config: Path,
) -> None:
    """The revision comes from the bundled `hooks.toml` only."""
    (isolated_user_config / "hooks.toml").write_text("repos = []")
    standards.get_config_revision.cache_clear()
    standards._load_prek_config.cache_clear()
    try:
        assert standards.get_config_revision()
    finally:
        standards.get_config_revision.cache_clear()
        standards._load_prek_config.cache_clear()
