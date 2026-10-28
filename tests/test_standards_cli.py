"""Unit tests for the `pkgdx init` command (`pkgdx.standards._cli`)."""

import argparse
import logging
from collections.abc import Callable
from pathlib import Path
from unittest import mock

import pytest
import tomlkit
import tomlkit.exceptions
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress

from pkgdx import __main__, exceptions
from pkgdx._core import (
    CLIContext,
    ExitCode,
    _validate_prek_repos,
    create_secrets_baseline,
    setup_prek_config,
)
from pkgdx.standards._cli import _setup_progress, command_init

STANDARDS_CLI = "pkgdx.standards._cli"

ContextFactory = Callable[..., CLIContext]


def test_setup_progress_disabled_in_non_tty(
    tty_stderr_disable: None,
    configured_logging: None,
) -> None:
    """Progress is disabled when STDERR is non-TTY."""
    with _setup_progress() as progress:
        assert progress.disable is True


def test_setup_progress_enabled_in_tty(
    tty_stderr_enable: None,
    configured_logging: None,
) -> None:
    """Progress is enabled when STDERR is a TTY."""
    with _setup_progress() as progress:
        assert progress.disable is False
        assert progress.expand is True
        assert progress.live.transient is False


def test_setup_progress_shares_console_with_rich_handler(
    tty_stderr_enable: None,
    configured_logging: None,
) -> None:
    """The Progress instance shares a Console with RichHandler."""
    cli_logger = logging.getLogger("pkgdx")
    handler = next(
        h for h in cli_logger.handlers if isinstance(h, RichHandler)
    )
    with _setup_progress() as progress:
        assert progress.console is handler.console


def test_setup_progress_restores_console_after_exit(
    tty_stderr_enable: None,
    configured_logging: None,
) -> None:
    """RichHandler console is restored after the Progress context exits."""
    cli_logger = logging.getLogger("pkgdx")
    handler = next(
        h for h in cli_logger.handlers if isinstance(h, RichHandler)
    )
    original_console = handler.console
    with _setup_progress():
        pass
    assert handler.console is original_console


def test_command_init_complete(
    mock_project: Path,
    tty_stderr_enable: None,
    mock_subprocess_run: mock.MagicMock,
    make_cli_context: ContextFactory,
) -> None:
    """The init command tracks one overall task and six completed steps."""

    ctx = make_cli_context(
        args=argparse.Namespace(debug=False, reset=False),
        console=Console(),
    )

    with (
        mock.patch(
            f"{STANDARDS_CLI}._core.get_project_root",
            return_value=mock_project,
        ),
        mock.patch(
            f"{STANDARDS_CLI}._core.get_git_toplevel",
            return_value=mock_project,
        ),
        mock.patch(f"{STANDARDS_CLI}._setup_progress") as msetup_progress,
    ):
        mprogress = mock.MagicMock(spec=Progress)
        mprogress_enter = mock.MagicMock(return_value=mprogress)
        mprogress_exit = mock.MagicMock(return_value=None)

        mtask_id = mock.MagicMock()
        mprogress.add_task.return_value = mtask_id

        msetup_progress.return_value.__enter__ = mprogress_enter
        msetup_progress.return_value.__exit__ = mprogress_exit

        exit_code = command_init(ctx)

    assert exit_code == ExitCode.EX_OK
    assert mprogress.add_task.call_count == 7
    first_add = mprogress.add_task.call_args_list[0]
    assert first_add.kwargs["total"] == 6
    assert first_add.kwargs["role"] == "overall"
    update_calls = mprogress.update.call_args_list
    assert len(update_calls) == 13


def test_command_init_exits_on_missing_project_root(
    mock_project: Path,
    tty_stderr_disable: None,
    make_cli_context: ContextFactory,
) -> None:
    """The init command exits with code 1 when the project root is missing."""
    ctx = make_cli_context(
        args=argparse.Namespace(debug=False, reset=False),
        console=Console(),
    )

    with (
        mock.patch(
            f"{STANDARDS_CLI}._core.get_project_root",
            side_effect=exceptions.ProjectRootNotFoundError(),
        ),
        mock.patch(f"{STANDARDS_CLI}._setup_progress") as msetup_progress,
    ):
        mprogress = mock.MagicMock(spec=Progress)
        mprogress_enter = mock.MagicMock(return_value=mprogress)
        mprogress_exit = mock.MagicMock(return_value=None)

        msetup_progress.return_value.__enter__ = mprogress_enter
        msetup_progress.return_value.__exit__ = mprogress_exit

        exit_code = command_init(ctx)

    assert exit_code == ExitCode.EX_FAILURE
    assert any(
        call.kwargs.get("failed") is True
        for call in mprogress.update.call_args_list
    )


def test_command_init_exits_on_prek_config_error(
    mock_project: Path,
    tty_stderr_enable: None,
    make_cli_context: ContextFactory,
) -> None:
    """The init command exits with code 1 when prek.toml config fails."""

    ctx = make_cli_context(
        args=argparse.Namespace(debug=False, reset=False),
        console=Console(),
    )

    with (
        mock.patch(
            f"{STANDARDS_CLI}._core.get_project_root",
            return_value=mock_project,
        ),
        mock.patch(
            f"{STANDARDS_CLI}._core.get_git_toplevel",
            return_value=mock_project,
        ),
        mock.patch(
            f"{STANDARDS_CLI}._core.setup_prek_config",
            side_effect=tomlkit.exceptions.TOMLKitError("bad TOML"),
        ),
        mock.patch(f"{STANDARDS_CLI}._setup_progress") as msetup_progress,
    ):
        mprogress = mock.MagicMock(spec=Progress)
        mprogress_enter = mock.MagicMock(return_value=mprogress)
        mprogress_exit = mock.MagicMock(return_value=None)

        msetup_progress.return_value.__enter__ = mprogress_enter
        msetup_progress.return_value.__exit__ = mprogress_exit

        exit_code = command_init(ctx)

    assert exit_code == ExitCode.EX_FAILURE
    assert any(
        call.kwargs.get("failed") is True
        for call in mprogress.update.call_args_list
    )


def test_command_init_non_tty_runs_without_progress(
    mock_project: Path,
    tty_stderr_disable: None,
    mock_subprocess_run: mock.MagicMock,
    make_cli_context: ContextFactory,
) -> None:
    """The init command runs without progress rendering in non-TTY mode."""

    ctx = make_cli_context(
        args=argparse.Namespace(debug=False, reset=False),
        console=Console(),
    )

    with (
        mock.patch(
            f"{STANDARDS_CLI}._core.get_project_root",
            return_value=mock_project,
        ),
        mock.patch(
            f"{STANDARDS_CLI}._core.get_git_toplevel",
            return_value=mock_project,
        ),
        mock.patch(f"{STANDARDS_CLI}._setup_progress") as msetup_progress,
    ):
        mprogress = mock.MagicMock(spec=Progress)

        mprogress_enter = mock.MagicMock(return_value=mprogress)
        mprogress_exit = mock.MagicMock(return_value=None)

        msetup_progress.return_value.__enter__ = mprogress_enter
        msetup_progress.return_value.__exit__ = mprogress_exit

        mock_task_id = mock.MagicMock()
        mprogress.add_task.return_value = mock_task_id

        command_init(ctx)

    msetup_progress.assert_called_once()


def test_validate_prek_repos_accepts_valid_config() -> None:
    """A well-formed `[[repos]]` config passes validation silently."""
    doc = tomlkit.parse(
        '[[repos]]\nrepo = "local"\n[[repos.hooks]]\nid = "ruff"'
    )
    _validate_prek_repos(doc)


def test_validate_prek_repos_accepts_missing_repos() -> None:
    """A document without a `repos` key stays valid."""
    _validate_prek_repos(tomlkit.parse(""))


def test_validate_prek_repos_rejects_non_array_repos() -> None:
    """A non-array `repos` value raises `PrekConfigError`."""
    doc = tomlkit.parse("repos = 5")
    with pytest.raises(exceptions.PrekConfigError, match="array of tables"):
        _validate_prek_repos(doc)


def test_validate_prek_repos_rejects_missing_repo_key() -> None:
    """A repo entry without a string `repo` key raises `PrekConfigError`."""
    doc = tomlkit.parse('[[repos]]\nrev = "1.0.0"')
    with pytest.raises(exceptions.PrekConfigError, match=r"repos\[0\].*repo"):
        _validate_prek_repos(doc)


def test_validate_prek_repos_rejects_non_array_hooks() -> None:
    """A non-array `hooks` value raises `PrekConfigError`."""
    doc = tomlkit.parse('[[repos]]\nrepo = "local"\nhooks = "nope"')
    with pytest.raises(exceptions.PrekConfigError, match=r"repos\[0\]\.hooks"):
        _validate_prek_repos(doc)


def test_validate_prek_repos_rejects_hook_missing_id() -> None:
    """A hook entry without a string `id` key raises `PrekConfigError`."""
    doc = tomlkit.parse(
        '[[repos]]\nrepo = "local"\n[[repos.hooks]]\nname = "x"'
    )
    with pytest.raises(exceptions.PrekConfigError, match=r"hooks\[0\].*id"):
        _validate_prek_repos(doc)


def test_setup_prek_config_rejects_malformed_consumer_file(
    tmp_path: Path,
) -> None:
    """A malformed consumer `prek.toml` fails fast with a clear error."""
    (tmp_path / "prek.toml").write_text('[[repos]]\nrev = "1.0.0"')
    with pytest.raises(exceptions.PrekConfigError):
        setup_prek_config(tmp_path)


def test_setup_prek_config_uses_user_hooks_toml(
    tmp_path: Path, isolated_user_config: Path
) -> None:
    """A user `hooks.toml` replaces the bundled template."""
    user_hooks = isolated_user_config / "hooks.toml"
    user_hooks.write_text('[[repos]]\nrepo = "local"\nhooks = []\n# user')
    project = tmp_path / "proj"
    project.mkdir()

    setup_prek_config(project)

    assert (project / "prek.toml").read_text() == user_hooks.read_text()


def test_create_secrets_baseline_forces_utf8_mode(
    tmp_path: Path,
    mock_subprocess_run: mock.MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Baseline scans run in UTF-8 mode so non-cp1252 files are not skipped."""
    monkeypatch.setenv("PYTHONUTF8", "0")
    monkeypatch.setenv("PKGDX_SENTINEL", "kept")

    create_secrets_baseline(tmp_path)

    env = mock_subprocess_run.call_args.kwargs["env"]
    assert env["PYTHONUTF8"] == "1"
    assert env["PKGDX_SENTINEL"] == "kept"


def _run_main(argv: list[str]) -> int:
    """Run `pkgdx.__main__.main` with `argv` & return the exit code."""
    with (
        mock.patch("sys.argv", ["pkgdx", *argv]),
        mock.patch("pkgdx.__main__.configure_cli_logging"),
        pytest.raises(SystemExit) as exc_info,
    ):
        __main__.main()

    code = exc_info.value.code
    assert isinstance(code, int)
    return code


def test_main_maps_error_to_exit_1(
    capsys: pytest.CaptureFixture,
) -> None:
    """An `Error` maps to exit code 1, reported via the logger."""
    error = exceptions.ProjectRootNotFoundError("no root")
    with mock.patch(f"{STANDARDS_CLI}.command_init", side_effect=error):
        exit_code = _run_main(["init"])
    out = capsys.readouterr().out
    assert exit_code == ExitCode.EX_FAILURE
    assert "error: true" not in out


def test_main_verbose_flag_reaches_init_context() -> None:
    """`pkgdx --debug init` parses & sets `CLIContext.is_debug`."""
    recorded: dict[str, CLIContext] = {}

    def record(ctx: CLIContext) -> int:
        recorded["ctx"] = ctx
        return ExitCode.EX_OK

    with mock.patch(f"{STANDARDS_CLI}.command_init", side_effect=record):
        exit_code = _run_main(["--debug", "init"])
    assert exit_code == ExitCode.EX_OK
    assert recorded["ctx"].is_debug is True


CONFIG_NAMES = ["mypy.ini", "hooks.toml", "pymarkdown.toml", "ruff.toml"]


def test_config_reports_bundled(capsys: pytest.CaptureFixture[str]) -> None:
    """With an empty user dir every file resolves to bundled."""
    assert _run_main(["config"]) == ExitCode.EX_OK
    rows = capsys.readouterr().out.splitlines()
    for name in CONFIG_NAMES:
        assert any(r.startswith(f"{name}\tbundled\t") for r in rows)


def test_config_reports_user_override(
    isolated_user_config: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A user file is reported with source `user`."""
    (isolated_user_config / "ruff.toml").write_text("")
    assert _run_main(["config"]) == ExitCode.EX_OK
    out = capsys.readouterr().out
    assert "ruff.toml\tuser\t" in out
    assert "mypy.ini\tbundled\t" in out


def test_config_export_writes_files(isolated_user_config: Path) -> None:
    """`--export` copies all bundled files into the user dir."""
    assert _run_main(["config", "--export"]) == ExitCode.EX_OK
    written = sorted(p.name for p in isolated_user_config.iterdir())
    assert written == sorted(CONFIG_NAMES)


def test_config_export_never_overwrites(isolated_user_config: Path) -> None:
    """`--export` leaves existing user files untouched."""
    existing = isolated_user_config / "ruff.toml"
    existing.write_text("# mine")
    assert _run_main(["config", "--export"]) == ExitCode.EX_OK
    assert existing.read_text() == "# mine"
    assert (isolated_user_config / "mypy.ini").is_file()


def test_config_bad_env_dir_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An invalid `PKGDX_CONFIG_DIR` exits 1."""
    monkeypatch.setenv("PKGDX_CONFIG_DIR", str(tmp_path / "nope"))
    assert _run_main(["config"]) == ExitCode.EX_FAILURE
