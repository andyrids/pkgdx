"""Unit tests for canonical standards hook command builders."""

import os
import pathlib
from collections.abc import Callable
from unittest import mock

import pytest

from pkgdx import __main__, exceptions, standards
from pkgdx.standards import _hooks


@pytest.mark.parametrize(
    ("hook", "prefix", "args"),
    [
        (
            _hooks.core_ruff_format,
            ["ruff", "format", "--config", standards.RUFF_CONFIG.as_posix()],
            ["--exit-non-zero-on-format"],
        ),
        (
            _hooks.core_ruff_lint,
            ["ruff", "check", "--config", standards.RUFF_CONFIG.as_posix()],
            ["--fix", "--exit-non-zero-on-fix"],
        ),
        (
            _hooks.core_mypy_typing,
            ["mypy", "--config-file", standards.MYPY_CONFIG.as_posix()],
            [],
        ),
        (
            _hooks.core_pymarkdown_lint,
            [
                "pymarkdown",
                "--config",
                standards.PYMARKDOWN_CONFIG.as_posix(),
                "--continue-on-error",
                "scan",
            ],
            ["README.md"],
        ),
    ],
    ids=["ruff-format", "ruff-lint", "mypy-typing", "pymarkdown-lint"],
)
def test_config_hook_builds_command_and_forwards_returncode(
    hook: Callable[[list[str]], int],
    prefix: list[str],
    args: list[str],
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """Config hooks prepend bundled config and forward the tool returncode."""
    mock_subprocess_run.return_value.returncode = 1

    returncode = hook(args)

    mock_subprocess_run.assert_called_once_with(prefix + args)
    assert returncode == 1


def test_detect_secrets_injects_default_baseline_when_missing(
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """Check detect-secrets gets or creates a baseline when none is given."""
    returncode = _hooks.core_detect_secrets(["--no-verify"])

    mock_subprocess_run.assert_called_once_with(
        [
            "detect-secrets-hook",
            "--baseline",
            ".secrets.baseline",
            "--no-verify",
        ],
        env=mock.ANY,
    )
    assert returncode == 0


def test_detect_secrets_preserves_explicit_baseline(
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """An explicit `--baseline` is not prepended a second time."""
    args = ["--baseline", ".secrets.baseline", "--no-verify"]

    returncode = _hooks.core_detect_secrets(args)

    mock_subprocess_run.assert_called_once_with(
        ["detect-secrets-hook", *args], env=mock.ANY
    )
    assert returncode == 0


def test_detect_secrets_forces_utf8_mode_and_preserves_environment(
    mock_subprocess_run: mock.MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UTF-8 mode is forced on top of the caller's environment."""
    monkeypatch.setenv("PYTHONUTF8", "0")
    monkeypatch.setenv("PKGDX_SENTINEL", "kept")

    _hooks.core_detect_secrets([])

    env = mock_subprocess_run.call_args.kwargs["env"]
    assert env["PYTHONUTF8"] == "1"
    assert env["PKGDX_SENTINEL"] == "kept"
    assert env["PATH"] == os.environ["PATH"]


def test_mypy_typing_defaults_to_project_and_excludes_tests(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No-args mypy checks the cwd project and excludes tests (issue #1)."""
    monkeypatch.chdir(tmp_path)

    demo_package = tmp_path / "src" / "demo"
    demo_package.mkdir(parents=True)
    (demo_package / "__init__.py").write_text(
        "def add(a: int, b: int) -> int:\n    return a + b\n"
    )

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_demo.py").write_text("def test_x(a):\n    return a\n")

    assert _hooks.core_mypy_typing([]) == 0

    (demo_package / "__init__.py").write_text('x: int = "a"\n')

    assert _hooks.core_mypy_typing([]) == 1


def test_pymarkdown_lint_continues_past_a_crashing_document(
    tmp_path: pathlib.Path,
    capfd: pytest.CaptureFixture[str],
) -> None:
    """A `BadTokenizationError` on one file does not abort the scan (issue #2).

    With `markdown-tables` enabled, pymarkdownlnt 0.9.40 crashes tokenizing a
    quoted list containing a pipe (`|`) character. `--continue-on-error`
    keeps the scan going so later files are still linted and named alongside
    the crashing one.
    """
    crash = tmp_path / "crash.md"
    crash.write_text("> quote\n>\n> - `A | B` first item\n> - second item\n")

    lint = tmp_path / "lint.md"
    lint.write_text("# Lint\n\nText.\n* item\n")

    returncode = _hooks.core_pymarkdown_lint([str(crash), str(lint)])

    captured = capfd.readouterr()
    output = captured.out + captured.err

    assert returncode == 1
    assert str(lint) in output
    assert "MD032" in output
    assert str(crash) in output


@pytest.mark.parametrize(
    ("args", "options", "scan_args"),
    [
        (["--stack-trace", "a.md"], ["--stack-trace"], ["a.md"]),
        (["-d", "md013", "a.md"], ["-d", "md013"], ["a.md"]),
        (["--set=x=y", "a.md"], ["--set=x=y"], ["a.md"]),
        (
            ["a.md", "-r", "--log-level", "DEBUG", "-e", "x.md", "--no-json5"],
            ["--log-level", "DEBUG", "--no-json5"],
            ["a.md", "-r", "-e", "x.md"],
        ),
    ],
    ids=["stack-trace", "disable-rule", "set-equals", "mixed"],
)
def test_pymarkdown_lint_moves_global_options_before_scan(
    args: list[str],
    options: list[str],
    scan_args: list[str],
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """Global options move before `scan`, in order (#2, part b)."""
    _hooks.core_pymarkdown_lint(args)

    mock_subprocess_run.assert_called_once_with(
        [
            "pymarkdown",
            "--config",
            standards.PYMARKDOWN_CONFIG.as_posix(),
            "--continue-on-error",
            *options,
            "scan",
            *scan_args,
        ]
    )


@pytest.mark.parametrize(
    "args",
    [
        ["a.md", "b.md"],
        ["-r", "docs"],
        ["--recurse", "--list-files", "docs"],
        ["-e", "x.md", "a.md"],
        ["--exclude=x.md", "a.md"],
        ["-ae", ".md,.mdx", "--respect-gitignore", "docs"],
    ],
    ids=["files", "recurse", "long-flags", "exclude", "exclude-equals", "mix"],
)
def test_pymarkdown_lint_keeps_scan_args_after_scan(
    args: list[str],
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """Paths & `scan` options build the same command as before the fix."""
    _hooks.core_pymarkdown_lint(args)

    mock_subprocess_run.assert_called_once_with(
        [
            "pymarkdown",
            "--config",
            standards.PYMARKDOWN_CONFIG.as_posix(),
            "--continue-on-error",
            "scan",
            *args,
        ]
    )


@pytest.mark.parametrize(
    ("hook", "name"),
    [
        (_hooks.core_ruff_format, "ruff.toml"),
        (_hooks.core_ruff_lint, "ruff.toml"),
        (_hooks.core_mypy_typing, "mypy.ini"),
        (_hooks.core_pymarkdown_lint, "pymarkdown.toml"),
    ],
    ids=["ruff-format", "ruff-lint", "mypy-typing", "pymarkdown-lint"],
)
def test_config_hook_uses_user_config(
    hook: Callable[[list[str]], int],
    name: str,
    isolated_user_config: pathlib.Path,
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """Config hooks pass the user config path when one exists."""
    user_file = isolated_user_config / name
    user_file.write_text("")

    hook([])

    assert user_file.as_posix() in mock_subprocess_run.call_args.args[0]


def test_hook_entry_point_bad_env_dir_exits_1(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A bad `PKGDX_CONFIG_DIR` exits 1 with a one-line error."""
    monkeypatch.setenv("PKGDX_CONFIG_DIR", str(tmp_path / "nope"))
    monkeypatch.setattr("sys.argv", ["pkgdx-lint-hook"])
    with pytest.raises(SystemExit) as exc_info:
        __main__.ruff_lint()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert err.startswith("error: ")
    assert "pkgdx: " not in err
    assert "Traceback" not in err


@pytest.mark.parametrize(
    "shim",
    [
        __main__.ruff_format,
        __main__.ruff_lint,
        __main__.mypy_typing,
        __main__.pymarkdown_lint,
        __main__.detect_secrets,
    ],
    ids=["format", "lint", "typing", "markdown", "secrets"],
)
def test_hook_entry_point_interrupt_exits_130(
    shim: Callable[[], None],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Ctrl-C in any hook shim prints one warning line & exits 130."""
    monkeypatch.setattr("sys.argv", ["pkgdx-hook"])
    with (
        mock.patch("subprocess.run", side_effect=KeyboardInterrupt),
        pytest.raises(SystemExit) as exc_info,
    ):
        shim()
    assert exc_info.value.code == 130
    assert capsys.readouterr().err == "warning: interrupted\n"


def test_run_tool_missing_executable_raises_tool_not_found(
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """A tool missing from `PATH` raises an error naming it & the fix."""
    error = FileNotFoundError(2, "The system cannot find the file specified")
    mock_subprocess_run.side_effect = error

    with pytest.raises(exceptions.ToolNotFoundError) as exc_info:
        _hooks._run_tool(["ruff", "check"])

    assert str(exc_info.value) == (
        "`ruff` not found on PATH - run the hook in the environment pkgdx is"
        " installed in, e.g. via `uv run`"
    )
    assert exc_info.value.__cause__ is error


@pytest.mark.parametrize(
    ("shim", "tool"),
    [
        (__main__.ruff_format, "ruff"),
        (__main__.ruff_lint, "ruff"),
        (__main__.mypy_typing, "mypy"),
        (__main__.pymarkdown_lint, "pymarkdown"),
        (__main__.detect_secrets, "detect-secrets-hook"),
    ],
    ids=["format", "lint", "typing", "markdown", "secrets"],
)
def test_hook_entry_point_missing_tool_exits_1(
    shim: Callable[[], None],
    tool: str,
    mock_subprocess_run: mock.MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A hook tool missing from `PATH` exits 1 with a one-line error."""
    mock_subprocess_run.side_effect = FileNotFoundError(2, "not found")
    monkeypatch.setattr("sys.argv", ["pkgdx-hook"])
    with pytest.raises(SystemExit) as exc_info:
        shim()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert err.startswith(f"error: `{tool}` not found on PATH - ")
    assert len(err.splitlines()) == 1
    assert "Traceback" not in err
    assert "unexpected" not in err


def test_hook_entry_point_passes_tool_exit_code(
    mock_subprocess_run: mock.MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A shim exits with the wrapped tool's return code."""
    mock_subprocess_run.return_value.returncode = 3
    monkeypatch.setattr("sys.argv", ["pkgdx-secrets-hook"])
    with pytest.raises(SystemExit) as exc_info:
        __main__.detect_secrets()
    assert exc_info.value.code == 3
