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
    tty_stdout_disable: None,
    configured_logging: None,
) -> None:
    """Progress is disabled when stdout is non-TTY."""
    with _setup_progress() as progress:
        assert progress.disable is True


def test_setup_progress_enabled_in_tty(
    tty_stdout_enable: None,
    configured_logging: None,
) -> None:
    """Progress is enabled when stdout is a TTY."""
    with _setup_progress() as progress:
        assert progress.disable is False


def test_setup_progress_shares_console_with_rich_handler(
    tty_stdout_enable: None,
    configured_logging: None,
) -> None:
    """The Progress instance shares a Console with RichHandler."""
    handler = next(h for h in logger.handlers if isinstance(h, RichHandler))
    with _setup_progress() as progress:
        assert progress.console is handler.console


def test_setup_progress_restores_console_after_exit(
    tty_stdout_enable: None,
    configured_logging: None,
) -> None:
    """RichHandler console is restored after the Progress context exits."""
    handler = next(h for h in logger.handlers if isinstance(h, RichHandler))
    original_console = handler.console
    with _setup_progress():
        pass
    assert handler.console is original_console


def test_command_setup_complete(
    mock_project: Path,
    tty_stdout_enable: None,
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """The setup command advances through all six progress steps."""

    args = argparse.Namespace(verbose=False, reset=False)

    MAIN = "pytack.__main__"

    with (
        mock.patch(f"{MAIN}.get_project_root", return_value=mock_project),
        mock.patch(f"{MAIN}.get_git_toplevel", return_value=mock_project),
        mock.patch(f"{MAIN}._setup_progress") as msetup_progress,
    ):
        mprogress = mock.MagicMock(spec=Progress)
        mprogress_enter = mock.MagicMock(return_value=mprogress)
        mprogress_exit = mock.MagicMock(return_value=None)

        mtask_id = mock.MagicMock()
        mprogress.add_task.return_value = mtask_id

        msetup_progress.return_value.__enter__ = mprogress_enter
        msetup_progress.return_value.__exit__ = mprogress_exit

        command_setup(args)

    assert mprogress.add_task.call_count == 1
    update_calls = mprogress.update.call_args_list
    assert len(update_calls) == 7



def test_command_setup_exits_on_missing_project_root(
    mock_project: Path,
    tty_stdout_disable: None,
) -> None:
    """The setup command exits with code 1 when the project root is missing."""
    args = argparse.Namespace(verbose=False, reset=False)

    MAIN = "pytack.__main__"

    with (
        mock.patch(
            f"{MAIN}.get_project_root",
            side_effect=exceptions.ProjectRootNotFoundError(),
        ),
        mock.patch(f"{MAIN}._setup_progress") as msetup_progress,
    ):
        mprogress = mock.MagicMock(spec=Progress)
        mprogress_enter = mock.MagicMock(return_value=mprogress)
        mprogress_exit = mock.MagicMock(return_value=None)

        msetup_progress.return_value.__enter__ = mprogress_enter
        msetup_progress.return_value.__exit__ = mprogress_exit

        with pytest.raises(SystemExit) as exc_info:
            command_setup(args)

    assert exc_info.value.code == 1


def test_command_setup_exits_on_prek_config_error(
    mock_project: Path,
    tty_stdout_enable: None,
) -> None:
    """The setup command exits with code 1 when prek.toml config fails."""

    args = argparse.Namespace(verbose=False, reset=False)

    MAIN = "pytack.__main__"

    with (
        mock.patch(f"{MAIN}.get_project_root", return_value=mock_project),
        mock.patch(f"{MAIN}.get_git_toplevel", return_value=mock_project),
        mock.patch(
            f"{MAIN}.setup_prek_config",
            side_effect=tomlkit.exceptions.TOMLKitError("bad TOML"),
        ),
        mock.patch(f"{MAIN}._setup_progress") as msetup_progress,
    ):
        mprogress = mock.MagicMock(spec=Progress)
        mprogress_enter = mock.MagicMock(return_value=mprogress)
        mprogress_exit = mock.MagicMock(return_value=None)

        msetup_progress.return_value.__enter__ = mprogress_enter
        msetup_progress.return_value.__exit__ = mprogress_exit

        with pytest.raises(SystemExit) as exc_info:
            command_setup(args)

    assert exc_info.value.code == 1


def test_command_setup_non_tty_runs_without_progress(
    mock_project: Path,
    tty_stdout_disable: None,
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """The setup command runs without progress rendering in non-TTY mode."""

    args = argparse.Namespace(verbose=False, reset=False)

    MAIN = "pytack.__main__"

    with (
        mock.patch(f"{MAIN}.get_project_root", return_value=mock_project),
        mock.patch(f"{MAIN}.get_git_toplevel", return_value=mock_project),
        mock.patch(f"{MAIN}._setup_progress") as msetup_progress,
    ):
        mprogress = mock.MagicMock(spec=Progress)

        mprogress_enter = mock.MagicMock(return_value=mprogress)
        mprogress_exit = mock.MagicMock(return_value=None)

        msetup_progress.return_value.__enter__ = mprogress_enter
        msetup_progress.return_value.__exit__ = mprogress_exit

        mock_task_id = mock.MagicMock()
        mprogress.add_task.return_value = mock_task_id

        command_setup(args)

    msetup_progress.assert_called_once()
