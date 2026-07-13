"""Unit tests for the `pytack setup` command."""

import argparse
from pathlib import Path
from unittest import mock

import pytest
import tomlkit.exceptions
from pytack import exceptions
from pytack.__main__ import _setup_progress, command_setup, logger
from rich.logging import RichHandler
from rich.progress import Progress


def test_setup_progress_disabled_in_non_tty(
    non_tty_stdout: None,
    configured_logging: None,
) -> None:
    """Progress is disabled when stdout is not a TTY."""
    with _setup_progress() as progress:
        assert progress.disable is True


def test_setup_progress_enabled_in_tty(
    tty_stdout: None,
    configured_logging: None,
) -> None:
    """Progress is enabled when stdout is a TTY."""
    with _setup_progress() as progress:
        assert progress.disable is False


def test_setup_progress_shares_console_with_rich_handler(
    tty_stdout: None,
    configured_logging: None,
) -> None:
    """The progress instance shares a Console with RichHandler."""
    handler = next(h for h in logger.handlers if isinstance(h, RichHandler))
    with _setup_progress() as progress:
        assert progress.console is handler.console


def test_setup_progress_restores_console_after_exit(
    tty_stdout: None,
    configured_logging: None,
) -> None:
    """RichHandler console is restored after the progress context exits."""
    handler = next(h for h in logger.handlers if isinstance(h, RichHandler))
    original_console = handler.console
    with _setup_progress():
        pass
    assert handler.console is original_console


def test_command_setup_advances_all_steps(
    tmp_path: Path,
    tty_stdout: None,
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """The setup command advances through all six progress steps."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "pyproject.toml").write_text("[project]\nname = 'test'\n")
    git_dir = project_root / ".git"
    git_dir.mkdir()
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "pre-commit").write_text("#!/bin/sh\n")
    (project_root / "prek.toml").write_text("repos = []\n")
    (project_root / ".secrets.baseline").write_text("{}")

    args = argparse.Namespace(verbose=False, reset=False)

    with (
        mock.patch(
            "pytack.__main__.get_project_root", return_value=project_root
        ),
        mock.patch(
            "pytack.__main__.get_git_toplevel", return_value=project_root
        ),
        mock.patch("pytack.__main__._setup_progress") as mock_setup_progress,
    ):
        mock_progress = mock.MagicMock(spec=Progress)
        mock_task_id = mock.MagicMock()
        mock_progress.add_task.return_value = mock_task_id
        mock_setup_progress.return_value.__enter__ = mock.MagicMock(
            return_value=mock_progress
        )
        mock_setup_progress.return_value.__exit__ = mock.MagicMock(
            return_value=None
        )

        command_setup(args)

    assert mock_progress.add_task.call_count == 1
    update_calls = mock_progress.update.call_args_list
    assert len(update_calls) == 7  # 6 advances + final completion message


def test_command_setup_exits_on_missing_project_root(
    tmp_path: Path,
    tty_stdout: None,
) -> None:
    """The setup command exits with code 1 when the project root is missing."""
    args = argparse.Namespace(verbose=False, reset=False)

    with (
        mock.patch(
            "pytack.__main__.get_project_root",
            side_effect=exceptions.ProjectRootNotFoundError("not found"),
        ),
        mock.patch("pytack.__main__._setup_progress") as mock_setup_progress,
    ):
        mock_progress = mock.MagicMock(spec=Progress)
        mock_setup_progress.return_value.__enter__ = mock.MagicMock(
            return_value=mock_progress
        )
        mock_setup_progress.return_value.__exit__ = mock.MagicMock(
            return_value=None
        )

        with pytest.raises(SystemExit) as exc_info:
            command_setup(args)

    assert exc_info.value.code == 1


def test_command_setup_exits_on_prek_config_error(
    tmp_path: Path,
    tty_stdout: None,
) -> None:
    """The setup command exits with code 1 when prek.toml config fails."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    args = argparse.Namespace(verbose=False, reset=False)

    with (
        mock.patch(
            "pytack.__main__.get_project_root", return_value=project_root
        ),
        mock.patch(
            "pytack.__main__.get_git_toplevel", return_value=project_root
        ),
        mock.patch(
            "pytack.__main__.setup_prek_config",
            side_effect=tomlkit.exceptions.TOMLKitError("bad TOML"),
        ),
        mock.patch("pytack.__main__._setup_progress") as mock_setup_progress,
    ):
        mock_progress = mock.MagicMock(spec=Progress)
        mock_setup_progress.return_value.__enter__ = mock.MagicMock(
            return_value=mock_progress
        )
        mock_setup_progress.return_value.__exit__ = mock.MagicMock(
            return_value=None
        )

        with pytest.raises(SystemExit) as exc_info:
            command_setup(args)

    assert exc_info.value.code == 1


def test_command_setup_non_tty_runs_without_progress(
    tmp_path: Path,
    non_tty_stdout: None,
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """The setup command runs without progress rendering in non-TTY mode."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "pyproject.toml").write_text("[project]\nname = 'test'\n")
    git_dir = project_root / ".git"
    git_dir.mkdir()
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "pre-commit").write_text("#!/bin/sh\n")
    (project_root / "prek.toml").write_text("repos = []\n")
    (project_root / ".secrets.baseline").write_text("{}")

    args = argparse.Namespace(verbose=False, reset=False)

    with (
        mock.patch(
            "pytack.__main__.get_project_root", return_value=project_root
        ),
        mock.patch(
            "pytack.__main__.get_git_toplevel", return_value=project_root
        ),
        mock.patch("pytack.__main__._setup_progress") as mock_setup_progress,
    ):
        mock_progress = mock.MagicMock(spec=Progress)
        mock_task_id = mock.MagicMock()
        mock_progress.add_task.return_value = mock_task_id
        mock_setup_progress.return_value.__enter__ = mock.MagicMock(
            return_value=mock_progress
        )
        mock_setup_progress.return_value.__exit__ = mock.MagicMock(
            return_value=None
        )

        command_setup(args)

    mock_setup_progress.assert_called_once()
