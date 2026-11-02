"""Unit tests for user config resolution (`pkgdx.standards`)."""

import logging
import sys
from collections.abc import Callable
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


@pytest.mark.parametrize(
    "pyproject",
    [None, "[project]\nname = 'x'\n", "[tool.pkgdx]\nexclude = []\n"],
    ids=["no-file", "no-table", "empty-list"],
)
def test_project_excludes_empty_when_unset(
    pyproject: str | None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A project that sets nothing excludes nothing."""
    if pyproject is not None:
        (tmp_path / "pyproject.toml").write_text(pyproject)
    monkeypatch.chdir(tmp_path)

    assert standards.project_excludes() == []


def test_project_excludes_normalises_entries(
    excluded_project: Callable[..., Path],
) -> None:
    """Entries keep their literal text, without decoration."""
    excluded_project("vendor/", "./gen/a.py", "a b/c,d", "x//y", "NUL")

    assert standards.project_excludes() == [
        "vendor",
        "gen/a.py",
        "a b/c,d",
        "x/y",
        "NUL",
    ]


def test_project_excludes_relative_to_working_directory(
    excluded_project: Callable[..., Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A run from a subfolder still honours the project list."""
    root = excluded_project("vendor")
    subfolder = root / "src" / "app"
    subfolder.mkdir(parents=True)
    monkeypatch.chdir(subfolder)

    assert standards.project_excludes() == ["../../vendor"]


@pytest.mark.parametrize(
    ("working_directory", "expected"),
    [
        ("src", "gen"),
        ("src/app", "../gen"),
        ("docs", "../src/gen"),
        ("src/gen", "../../src/gen"),
    ],
    ids=["parent", "sibling", "unrelated", "the-entry"],
)
def test_project_excludes_collapse_shared_folders(
    working_directory: str,
    expected: str,
    excluded_project: Callable[..., Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Folders shared by the working directory & an entry collapse."""
    root = excluded_project("src/gen")
    (root / working_directory).mkdir(parents=True)
    monkeypatch.chdir(root / working_directory)

    assert standards.project_excludes() == [expected]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows ignores case")
def test_project_excludes_ignore_working_directory_case_on_windows(
    excluded_project: Callable[..., Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A working directory spelled in another case still shares the folder."""
    root = excluded_project("src/gen")
    (root / "src").mkdir()
    monkeypatch.chdir(root / "SRC")

    assert standards.project_excludes() == ["gen"]


def test_project_excludes_stay_literal_inside_an_excluded_folder(
    excluded_project: Callable[..., Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An entry never collapses to `..`, which would match all above it."""
    root = excluded_project("vendor")
    inside = root / "vendor" / "sub"
    inside.mkdir(parents=True)
    monkeypatch.chdir(inside)

    assert standards.project_excludes() == ["../../vendor"]


def test_project_excludes_nearest_file_wins(
    excluded_project: Callable[..., Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A nested `pyproject.toml` is not merged with its parent."""
    root = excluded_project("vendor")
    member = root / "packages" / "member"
    member.mkdir(parents=True)
    (member / "pyproject.toml").write_text("[project]\nname = 'member'\n")
    monkeypatch.chdir(member)

    assert standards.project_excludes() == []


@pytest.mark.parametrize(
    "toml",
    [
        "tool = 1\n",
        "[tool]\npkgdx = 1\n",
        '[tool.pkgdx]\nextend-exclude = ["vendor"]\n',
        '[tool.pkgdx]\nexclude = "vendor"\n',
        "[tool.pkgdx]\nexclude = [1]\n",
        '[tool.pkgdx]\nexclude = [""]\n',
        '[tool.pkgdx]\nexclude = ["."]\n',
        '[tool.pkgdx]\nexclude = [".."]\n',
        '[tool.pkgdx]\nexclude = ["a/../b"]\n',
        '[tool.pkgdx]\nexclude = ["/abs"]\n',
        '[tool.pkgdx]\nexclude = ["C:/abs"]\n',
        '[tool.pkgdx]\nexclude = ["C:rel"]\n',
        "[tool.pkgdx]\nexclude = ['a\\b']\n",
        '[tool.pkgdx]\nexclude = ["*.py"]\n',
        '[tool.pkgdx]\nexclude = ["a?"]\n',
        '[tool.pkgdx]\nexclude = ["a["]\n',
        '[tool.pkgdx]\nexclude = ["a]"]\n',
        '[tool.pkgdx]\nexclude = ["a{"]\n',
        '[tool.pkgdx]\nexclude = ["a}"]\n',
        '[tool.pkgdx]\nexclude = ["a\\u0000b"]\n',
        '[tool.pkgdx]\nexclude = ["a\\nb"]\n',
        '[tool.pkgdx]\nexclude = ["a\\u007fb"]\n',
        '[tool.pkgdx]\nexclude = ["vendor."]\n',
        '[tool.pkgdx]\nexclude = ["vendor "]\n',
        '[tool.pkgdx]\nexclude = ["x/ /y"]\n',
        '[tool.pkgdx]\nexclude = ["..."]\n',
        '[tool.pkgdx]\nexclude = [" "]\n',
        "[tool.pkgdx\n",
    ],
    ids=[
        "tool-not-table",
        "pkgdx-not-table",
        "unknown-key",
        "not-a-list",
        "not-a-string",
        "empty",
        "dot",
        "dot-dot",
        "parent-segment",
        "absolute",
        "drive",
        "drive-relative",
        "backslash",
        "glob-star",
        "glob-question",
        "glob-open-bracket",
        "glob-close-bracket",
        "glob-open-brace",
        "glob-close-brace",
        "control-nul",
        "control-newline",
        "control-delete",
        "trailing-dot",
        "trailing-space",
        "space-segment",
        "dots-only",
        "space-only",
        "broken-toml",
    ],
)
def test_project_excludes_rejects_invalid(
    toml: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An invalid table fails closed, naming the file to fix."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(toml)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(exceptions.ProjectConfigError) as exc_info:
        standards.project_excludes()

    assert str(pyproject) in str(exc_info.value)


def test_project_excludes_rejects_a_non_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A `pyproject.toml` that is no file fails closed, unskipped."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.mkdir()
    monkeypatch.chdir(tmp_path)

    with pytest.raises(exceptions.ProjectConfigError) as exc_info:
        standards.project_excludes()

    assert str(pyproject) in str(exc_info.value)


def test_project_excludes_rejects_non_utf8(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An undecodable `pyproject.toml` fails closed, naming the file."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_bytes(b"\xff")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(exceptions.ProjectConfigError) as exc_info:
        standards.project_excludes()

    assert str(pyproject) in str(exc_info.value)
