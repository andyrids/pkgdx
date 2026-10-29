"""Unit tests for the `pkgdx init` & `config` commands (`standards._cli`)."""

import argparse
from collections.abc import Callable, Iterator
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

import pytest
import tomlkit
from rich.color import ColorSystem

from pkgdx import __main__, exceptions, standards
from pkgdx._core import Change, CLIContext, ExitCode, Outcome, StepResult
from pkgdx.logging import CLI_CONSOLE, GLOBAL_CONSOLE
from pkgdx.standards._cli import command_init

STANDARDS_CLI = "pkgdx.standards._cli"

ContextFactory = Callable[..., CLIContext]

ROOT = Path(r"C:\src\acme")

SUCCESS_LEDGER = [
    r"  ok      identify project root       C:\src\acme (pyproject.toml)",
    "  ok      identify Git top-level      same as project root",
    (
        "  ok      configure pre-commit hooks  updated    "
        "prek.toml (2 hooks added)"
    ),
    "  ok      prek install                unchanged  Git shims",
    "  ok      prek update --check         hook revisions up to date",
    "  ok      detect-secrets scan         created    .secrets.baseline",
    "pkgdx init: done in 2.9s (2 changed, 1 unchanged)",
]

WARN_LEDGER = [
    r"  ok      identify project root       C:\src\acme (pyproject.toml)",
    (
        "  warn    identify Git top-level      "
        "not a Git repository, using project root"
    ),
    "        -> Run `git init` to enable pre-commit hooks",
    (
        "  ok      configure pre-commit hooks  updated    "
        "prek.toml (2 hooks added)"
    ),
    (
        "  ok      prek install                created    "
        "Git shims (at project root)"
    ),
    "  warn    prek update --check         pkgdx v0.4.2 -> v0.5.0 available",
    "        -> Update remote hook revisions - `prek update`",
    "  ok      detect-secrets scan         unchanged  .secrets.baseline",
    "pkgdx init: done in 2.9s with 2 warnings (2 changed, 1 unchanged)",
]

FAIL_LEDGER = [
    r"  ok      identify project root       C:\src\acme (pyproject.toml)",
    "  ok      identify Git top-level      same as project root",
    "  FAIL    configure pre-commit hooks  prek.toml could not be parsed",
    "        Invalid value (at line 12, column 9)",
    "        -> Fix prek.toml, or regenerate it with `pkgdx init --reset`",
    "        not run: prek install, prek update --check, detect-secrets scan",
    "pkgdx init: failed at step 3/6 (3 steps not run)",
]


@pytest.fixture
def plain_stderr(tty_stderr_disable: None) -> Iterator[mock.MagicMock]:
    """Render `GLOBAL_CONSOLE` as an 80-column pipe, with `status` mocked."""
    with (
        mock.patch.object(GLOBAL_CONSOLE, "_width", 80),
        mock.patch.object(GLOBAL_CONSOLE, "status") as mstatus,
    ):
        yield mstatus


@pytest.fixture
def steps() -> Iterator[dict[str, mock.MagicMock]]:
    """Patch the `_core` init steps & `time`, defaulting to a success run."""
    defaults = {
        "get_project_root": ROOT,
        "get_git_toplevel": ROOT,
        "setup_prek_config": StepResult(
            Outcome.OK,
            change=Change.UPDATED,
            subject="prek.toml (2 hooks added)",
        ),
        "install_prek_hooks": StepResult(
            Outcome.OK, change=Change.UNCHANGED, subject="Git shims"
        ),
        "update_prek_hooks": StepResult(
            Outcome.OK, "hook revisions up to date"
        ),
        "create_secrets_baseline": StepResult(
            Outcome.OK, change=Change.CREATED, subject=".secrets.baseline"
        ),
    }
    with ExitStack() as stack:
        mocks = {
            name: stack.enter_context(
                mock.patch(f"{STANDARDS_CLI}._core.{name}", return_value=value)
            )
            for name, value in defaults.items()
        }
        mtime = stack.enter_context(mock.patch(f"{STANDARDS_CLI}.time"))
        mtime.monotonic.side_effect = [0.0, 2.9]
        yield mocks


def _run_init(
    make_cli_context: ContextFactory, capsys: pytest.CaptureFixture[str]
) -> tuple[int, list[str]]:
    """Run `command_init` & return the exit code and STDERR lines."""
    ctx = make_cli_context(args=argparse.Namespace(debug=False, reset=False))
    exit_code = command_init(ctx)
    out, err = capsys.readouterr()
    assert out == ""
    return exit_code, err.splitlines()


def test_init_success_ledger_matches_target(
    plain_stderr: mock.MagicMock,
    steps: dict[str, mock.MagicMock],
    make_cli_context: ContextFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A successful run prints one ledger line per step & a summary."""
    exit_code, lines = _run_init(make_cli_context, capsys)

    assert exit_code == ExitCode.EX_OK
    assert lines == SUCCESS_LEDGER


def test_init_warn_ledger_matches_target(
    plain_stderr: mock.MagicMock,
    steps: dict[str, mock.MagicMock],
    make_cli_context: ContextFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Warnings print inline hints & are counted in the summary."""
    steps["get_git_toplevel"].side_effect = exceptions.GitTopLevelError()
    steps["install_prek_hooks"].return_value = StepResult(
        Outcome.OK,
        change=Change.CREATED,
        subject="Git shims (at project root)",
    )
    steps["update_prek_hooks"].return_value = StepResult(
        Outcome.WARN,
        "pkgdx v0.4.2 -> v0.5.0 available",
        hint="Update remote hook revisions - `prek update`",
    )
    steps["create_secrets_baseline"].return_value = StepResult(
        Outcome.OK, change=Change.UNCHANGED, subject=".secrets.baseline"
    )

    exit_code, lines = _run_init(make_cli_context, capsys)

    assert exit_code == ExitCode.EX_OK
    assert lines == WARN_LEDGER
    steps["install_prek_hooks"].assert_called_once_with(ROOT, None)


def test_init_fail_ledger_matches_target(
    plain_stderr: mock.MagicMock,
    steps: dict[str, mock.MagicMock],
    make_cli_context: ContextFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A failed step prints its cause, hint & the steps not run."""
    steps["setup_prek_config"].return_value = StepResult(
        Outcome.FAIL,
        "prek.toml could not be parsed",
        "Invalid value (at line 12, column 9)",
        "Fix prek.toml, or regenerate it with `pkgdx init --reset`",
    )

    exit_code, lines = _run_init(make_cli_context, capsys)

    assert exit_code == ExitCode.EX_FAILURE
    assert lines == FAIL_LEDGER
    for name in [
        "install_prek_hooks",
        "update_prek_hooks",
        "create_secrets_baseline",
    ]:
        steps[name].assert_not_called()


def test_init_names_git_toplevel_above_project_root(
    plain_stderr: mock.MagicMock,
    steps: dict[str, mock.MagicMock],
    make_cli_context: ContextFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A Git top-level that differs from the project root is named."""
    steps["get_git_toplevel"].return_value = Path(r"C:\src")

    _, lines = _run_init(make_cli_context, capsys)

    assert lines[1] == r"  ok      identify Git top-level      C:\src"


def test_init_keeps_long_paths_on_one_line(
    plain_stderr: mock.MagicMock,
    steps: dict[str, mock.MagicMock],
    make_cli_context: ContextFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A path wider than the console stays whole on its ledger line."""
    root = Path("C:/projects", "a-very-long-directory-name" * 3, "acme")
    steps["get_project_root"].return_value = root
    steps["get_git_toplevel"].return_value = root

    _, lines = _run_init(make_cli_context, capsys)

    assert lines[0] == (
        f"  ok      identify project root       {root} (pyproject.toml)"
    )
    assert len(lines) == len(SUCCESS_LEDGER)


def test_init_reports_nothing_to_change_on_rerun(
    plain_stderr: mock.MagicMock,
    steps: dict[str, mock.MagicMock],
    make_cli_context: ContextFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A re-run with no changes ends `(nothing to change)`."""
    unchanged = Change.UNCHANGED
    steps["setup_prek_config"].return_value = StepResult(
        Outcome.OK, change=unchanged, subject="prek.toml"
    )
    steps["create_secrets_baseline"].return_value = StepResult(
        Outcome.OK, change=unchanged, subject=".secrets.baseline"
    )

    exit_code, lines = _run_init(make_cli_context, capsys)

    assert exit_code == ExitCode.EX_OK
    assert lines[-1] == "pkgdx init: done in 2.9s (nothing to change)"


def test_init_warning_count_singular(
    plain_stderr: mock.MagicMock,
    steps: dict[str, mock.MagicMock],
    make_cli_context: ContextFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A single warning is counted as `1 warning`."""
    steps["get_git_toplevel"].side_effect = exceptions.GitTopLevelError()

    _, lines = _run_init(make_cli_context, capsys)

    assert lines[-1] == (
        "pkgdx init: done in 2.9s with 1 warning (2 changed, 1 unchanged)"
    )


def test_init_warn_prints_message_above_hint(
    plain_stderr: mock.MagicMock,
    steps: dict[str, mock.MagicMock],
    make_cli_context: ContextFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A warning's message is printed between its row and its hint."""
    steps["install_prek_hooks"].return_value = StepResult(
        Outcome.WARN,
        "Git shims not installed",
        "caused by: y",
        "Fix the error, then run `prek install`",
    )

    exit_code, lines = _run_init(make_cli_context, capsys)

    assert exit_code == ExitCode.EX_OK
    index = lines.index("        caused by: y")
    assert lines[index - 1].startswith("  warn    prek install")
    assert lines[index + 1] == (
        "        -> Fix the error, then run `prek install`"
    )


def test_init_fails_on_missing_project_root(
    plain_stderr: mock.MagicMock,
    steps: dict[str, mock.MagicMock],
    make_cli_context: ContextFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A missing project root fails the first step & runs no other."""
    error = exceptions.ProjectRootNotFoundError("No pyproject.toml in X")
    steps["get_project_root"].side_effect = error

    exit_code, lines = _run_init(make_cli_context, capsys)

    assert exit_code == ExitCode.EX_FAILURE
    assert lines == [
        "  FAIL    identify project root       project root not found",
        "        No pyproject.toml in X",
        "        -> Run `pkgdx init` from inside a Python project",
        (
            "        not run: identify Git top-level, configure pre-commit"
            " hooks, prek install, prek update --check, detect-secrets scan"
        ),
        "pkgdx init: failed at step 1/6 (5 steps not run)",
    ]
    for name, step in steps.items():
        if name != "get_project_root":
            step.assert_not_called()


def test_init_fail_on_last_step_omits_not_run(
    plain_stderr: mock.MagicMock,
    steps: dict[str, mock.MagicMock],
    make_cli_context: ContextFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A failed last step prints no `not run` line or count."""
    steps["create_secrets_baseline"].return_value = StepResult(
        Outcome.FAIL,
        ".secrets.baseline not created",
        "ValueError: boom",
        "Run `detect-secrets scan` to see the full error",
    )

    exit_code, lines = _run_init(make_cli_context, capsys)

    assert exit_code == ExitCode.EX_FAILURE
    assert lines[-1] == "pkgdx init: failed at step 6/6"
    assert not any("not run" in line for line in lines)


def test_init_bad_config_dir_fails_without_traceback(
    mock_project: Path,
    plain_stderr: mock.MagicMock,
    make_cli_context: ContextFactory,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """An invalid `PKGDX_CONFIG_DIR` fails step 3 with no traceback."""
    monkeypatch.setenv("PKGDX_CONFIG_DIR", str(tmp_path / "nope"))
    with (
        mock.patch(
            f"{STANDARDS_CLI}._core.get_project_root",
            return_value=mock_project,
        ),
        mock.patch(
            f"{STANDARDS_CLI}._core.get_git_toplevel",
            return_value=mock_project,
        ),
    ):
        exit_code, lines = _run_init(make_cli_context, capsys)

    assert exit_code == ExitCode.EX_FAILURE
    assert lines[2] == (
        "  FAIL    configure pre-commit hooks  user config directory not found"
    )
    assert lines[3] == (
        "        `PKGDX_CONFIG_DIR` is not an existing directory: "
        f"{tmp_path / 'nope'}"
    )
    assert lines[-1] == "pkgdx init: failed at step 3/6 (3 steps not run)"
    assert not any("Traceback" in line for line in lines)


def test_init_runs_real_steps_on_configured_project(
    mock_project: Path,
    plain_stderr: mock.MagicMock,
    mock_subprocess_run: mock.MagicMock,
    make_cli_context: ContextFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The real steps report what they changed on a configured project.

    NOTE: The fixture's `prek.toml` has an inline `hooks = []`, which must
    be converted before hooks are added, or the written file is invalid.
    """
    prek_toml = mock_project / "prek.toml"
    template = tomlkit.parse(standards.PREK_CONFIG.read_text())
    hooks = sum(len(repo.get("hooks", [])) for repo in template["repos"])
    with (
        mock.patch(
            f"{STANDARDS_CLI}._core.get_project_root",
            return_value=mock_project,
        ),
        mock.patch(
            f"{STANDARDS_CLI}._core.get_git_toplevel",
            return_value=mock_project,
        ),
    ):
        exit_code, lines = _run_init(make_cli_context, capsys)

    assert exit_code == ExitCode.EX_OK
    assert lines[1:-1] == [
        "  ok      identify Git top-level      same as project root",
        (
            "  ok      configure pre-commit hooks  updated    "
            f"prek.toml ({hooks} hooks added)"
        ),
        "  ok      prek install                unchanged  Git shims",
        "  ok      prek update --check         hook revisions up to date",
        "  ok      detect-secrets scan         unchanged  .secrets.baseline",
    ]
    assert lines[-1].endswith("(1 changed, 2 unchanged)")
    tomlkit.parse(prek_toml.read_text())


def test_init_keyboard_interrupt_prints_stop_row(
    plain_stderr: mock.MagicMock,
    steps: dict[str, mock.MagicMock],
    make_cli_context: ContextFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Ctrl-C names the interrupted step & exits with code 130."""
    steps["install_prek_hooks"].side_effect = KeyboardInterrupt

    exit_code, lines = _run_init(make_cli_context, capsys)

    assert exit_code == ExitCode.EX_INTERRUPT == 130
    assert lines[-2:] == [
        "  stop    prek install                interrupted",
        "pkgdx init: interrupted, no cleanup performed",
    ]
    steps["update_prek_hooks"].assert_not_called()
    steps["create_secrets_baseline"].assert_not_called()


def test_init_shows_spinner_per_step_in_tty(
    tty_stderr_enable: None,
    steps: dict[str, mock.MagicMock],
    make_cli_context: ContextFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Each step shows a transient spinner when STDERR is a TTY."""
    with mock.patch.object(GLOBAL_CONSOLE, "status") as mstatus:
        _run_init(make_cli_context, capsys)

    assert mstatus.call_args_list == [
        mock.call(f"{label} ...", spinner="dots")
        for label in [
            "identify project root",
            "identify Git top-level",
            "configure pre-commit hooks",
            "prek install",
            "prek update --check",
            "detect-secrets scan",
        ]
    ]


def test_init_no_spinner_in_non_tty(
    plain_stderr: mock.MagicMock,
    steps: dict[str, mock.MagicMock],
    make_cli_context: ContextFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A piped STDERR gets no spinner & no ANSI escape codes."""
    _, lines = _run_init(make_cli_context, capsys)

    plain_stderr.assert_not_called()
    assert not any("\x1b" in line for line in lines)


def test_init_closing_line_not_highlighted(
    tty_stderr_enable: None,
    steps: dict[str, mock.MagicMock],
    make_cli_context: ContextFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The closing line is plain text, even with colour enabled."""
    with (
        mock.patch.object(GLOBAL_CONSOLE, "status"),
        mock.patch.object(GLOBAL_CONSOLE, "_width", 80),
        mock.patch.object(
            GLOBAL_CONSOLE, "_color_system", ColorSystem.TRUECOLOR
        ),
    ):
        _, lines = _run_init(make_cli_context, capsys)

    assert any("\x1b" in line for line in lines[:-1])
    assert lines[-1] == "pkgdx init: done in 2.9s (2 changed, 1 unchanged)"


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


@pytest.fixture
def plain_stdout() -> Iterator[None]:
    """Render `CLI_CONSOLE` (STDOUT) without colour, even under `pytest -s`."""
    with mock.patch.object(CLI_CONSOLE, "_color_system", None):
        yield


@pytest.fixture
def export_clock(plain_stderr: mock.MagicMock) -> Iterator[None]:
    """Render the `--export` ledger as a pipe, taking 2.9s."""
    with mock.patch(f"{STANDARDS_CLI}.time") as mtime:
        mtime.monotonic.side_effect = [0.0, 2.9]
        yield


@pytest.fixture
def platform_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Unset `PKGDX_CONFIG_DIR` & point the platform dir under `tmp_path`."""
    monkeypatch.delenv("PKGDX_CONFIG_DIR")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    return tmp_path / "pkgdx"


def _run_config(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> tuple[int, list[str], list[str]]:
    """Run `pkgdx config` & return the exit code, STDOUT & STDERR lines."""
    exit_code = _run_main(["config", *argv])
    out, err = capsys.readouterr()
    return exit_code, out.splitlines(), err.splitlines()


def _source_row(bundled: Path, source: str, resolved: Path) -> str:
    """Build the expected plain-run row for a config file."""
    return f"  {bundled.name:<15}  {source:<11}{resolved}"


def _export_row(user_dir: Path, name: str, change: str) -> str:
    """Build the expected `--export` ledger line for a config file."""
    return f"  ok      {name:<15}  {change:<11}{user_dir / name}"


def test_config_lists_bundled_sources(
    isolated_user_config: Path,
    plain_stderr: mock.MagicMock,
    plain_stdout: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """With an empty user dir every row is bundled & STDOUT holds only rows."""
    exit_code, out, err = _run_config([], capsys)

    assert exit_code == ExitCode.EX_OK
    assert out == [
        _source_row(bundled, "bundled", bundled)
        for bundled in standards.BUNDLED_CONFIGS
    ]
    assert err == [
        (
            f"pkgdx config: user config dir {isolated_user_config}, "
            "from PKGDX_CONFIG_DIR (0 user, 4 bundled)"
        )
    ]


def test_config_lists_user_override(
    isolated_user_config: Path,
    plain_stderr: mock.MagicMock,
    plain_stdout: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A user file is listed as `user`, with its own path."""
    user_ruff = isolated_user_config / "ruff.toml"
    user_ruff.write_text("")

    exit_code, out, err = _run_config([], capsys)

    assert exit_code == ExitCode.EX_OK
    assert out == [
        _source_row(standards.MYPY_CONFIG, "bundled", standards.MYPY_CONFIG),
        _source_row(standards.PREK_CONFIG, "bundled", standards.PREK_CONFIG),
        _source_row(
            standards.PYMARKDOWN_CONFIG,
            "bundled",
            standards.PYMARKDOWN_CONFIG,
        ),
        _source_row(standards.RUFF_CONFIG, "user", user_ruff),
    ]
    assert err[-1].endswith("from PKGDX_CONFIG_DIR (1 user, 3 bundled)")


def test_config_names_platform_dir_when_env_unset(
    platform_dir: Path,
    plain_stderr: mock.MagicMock,
    plain_stdout: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The closing line says when `PKGDX_CONFIG_DIR` is not set."""
    exit_code, _, err = _run_config([], capsys)

    assert exit_code == ExitCode.EX_OK
    assert err == [
        (
            f"pkgdx config: user config dir {platform_dir}, "
            "PKGDX_CONFIG_DIR not set (0 user, 4 bundled)"
        )
    ]


def test_config_export_creates_files(
    isolated_user_config: Path,
    export_clock: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--export` prints a ledger line per file on STDERR & no rows."""
    exit_code, out, err = _run_config(["--export"], capsys)

    assert exit_code == ExitCode.EX_OK
    assert out == []
    assert err == [
        *(
            _export_row(isolated_user_config, bundled.name, "created")
            for bundled in standards.BUNDLED_CONFIGS
        ),
        "pkgdx config: done in 2.9s (4 changed, 0 unchanged)",
    ]
    for bundled in standards.BUNDLED_CONFIGS:
        target = isolated_user_config / bundled.name
        assert target.read_bytes() == bundled.read_bytes()


def test_config_export_never_overwrites(
    isolated_user_config: Path,
    export_clock: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--export` reports an existing user file unchanged & leaves it."""
    existing = isolated_user_config / "ruff.toml"
    existing.write_text("# mine")

    exit_code, _, err = _run_config(["--export"], capsys)

    assert exit_code == ExitCode.EX_OK
    assert err[-2:] == [
        _export_row(isolated_user_config, "ruff.toml", "unchanged"),
        "pkgdx config: done in 2.9s (3 changed, 1 unchanged)",
    ]
    assert existing.read_text() == "# mine"


def test_config_export_creates_platform_dir(
    platform_dir: Path,
    export_clock: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--export` creates a missing platform config dir."""
    exit_code, _, err = _run_config(["--export"], capsys)

    assert exit_code == ExitCode.EX_OK
    assert err[0] == _export_row(platform_dir, "mypy.ini", "created")
    assert sorted(p.name for p in platform_dir.iterdir()) == sorted(
        bundled.name for bundled in standards.BUNDLED_CONFIGS
    )


def test_config_export_stops_at_copy_error(
    isolated_user_config: Path,
    export_clock: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A failed copy is a FAIL line naming the files not run, with exit 1."""
    denied = PermissionError(13, "Permission denied", "x")
    with mock.patch("pkgdx._core.shutil.copyfile", side_effect=[None, denied]):
        exit_code, out, err = _run_config(["--export"], capsys)

    assert exit_code == ExitCode.EX_FAILURE
    assert out == []
    assert err == [
        _export_row(isolated_user_config, "mypy.ini", "created"),
        "  FAIL    hooks.toml       could not be copied",
        "        Permission denied: x",
        "        -> Fix the cause, then re-run `pkgdx config --export`",
        "        not run: pymarkdown.toml, ruff.toml",
        "pkgdx config: failed at step 2/4 (2 steps not run)",
    ]


@pytest.mark.parametrize("argv", [[], ["--export"]], ids=["plain", "export"])
def test_config_bad_env_dir_fails_without_traceback(
    argv: list[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    plain_stderr: mock.MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An invalid `PKGDX_CONFIG_DIR` is a FAIL line, exit 1 & no rows."""
    missing = tmp_path / "nope"
    monkeypatch.setenv("PKGDX_CONFIG_DIR", str(missing))

    exit_code, out, err = _run_config(argv, capsys)

    assert exit_code == ExitCode.EX_FAILURE
    assert out == []
    assert err == [
        "  FAIL    PKGDX_CONFIG_DIR  user config directory not found",
        (
            "        `PKGDX_CONFIG_DIR` is not an existing directory: "
            f"{missing}"
        ),
        "        -> Create it, or unset `PKGDX_CONFIG_DIR`",
        "pkgdx config: failed",
    ]
    assert not missing.exists()
