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
    """A tool missing from `PATH` raises an error naming it, with a hint."""
    error = FileNotFoundError(2, "The system cannot find the file specified")
    mock_subprocess_run.side_effect = error

    with pytest.raises(exceptions.ToolNotFoundError) as exc_info:
        _hooks._run_tool(["ruff", "check"])

    assert str(exc_info.value) == "`ruff` not found on PATH"
    assert exc_info.value.hint.startswith("Run the hook in the environment")
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
    """A hook tool missing from `PATH` exits 1: the error, then the hint."""
    mock_subprocess_run.side_effect = FileNotFoundError(2, "not found")
    monkeypatch.setattr("sys.argv", ["pkgdx-hook"])
    with pytest.raises(SystemExit) as exc_info:
        shim()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert err.splitlines() == [
        f"error: `{tool}` not found on PATH",
        (
            "Run the hook in the environment pkgdx is installed in, "
            "e.g. via `uv run`"
        ),
    ]
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


@pytest.mark.parametrize(
    ("hook", "subcommand"),
    [(_hooks.core_ruff_format, "format"), (_hooks.core_ruff_lint, "check")],
    ids=["ruff-format", "ruff-lint"],
)
def test_ruff_hooks_pass_project_excludes_inline(
    hook: Callable[[list[str]], int],
    subcommand: str,
    excluded_project: Callable[..., pathlib.Path],
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """Ruff gets one inline `extend-exclude`, before the forwarded args."""
    excluded_project("third_party", "a/b.py")

    hook(["--flag"])

    mock_subprocess_run.assert_called_once_with(
        [
            "ruff",
            subcommand,
            "--config",
            standards.RUFF_CONFIG.as_posix(),
            "--config",
            'extend-exclude=["./third_party", "./a/b.py"]',
            "--flag",
        ]
    )


def test_ruff_exclude_keeps_non_ascii_literal(
    excluded_project: Callable[..., pathlib.Path],
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """A non-BMP path stays literal: Ruff's TOML rejects surrogate escapes."""
    excluded_project("vendor\U0001f600")

    _hooks.core_ruff_lint([])

    command = mock_subprocess_run.call_args.args[0]
    assert 'extend-exclude=["./vendor\U0001f600"]' in command


def test_mypy_typing_passes_anchored_excludes(
    excluded_project: Callable[..., pathlib.Path],
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """A whole-project run gets anchored patterns & silences excluded code."""
    excluded_project("third_party", "a/b.py")

    _hooks.core_mypy_typing([])

    mock_subprocess_run.assert_called_once_with(
        [
            "mypy",
            "--config-file",
            standards.MYPY_CONFIG.as_posix(),
            "--exclude",
            "^third_party(/|$)",
            "--exclude",
            r"^a/b\.py(/|$)",
            "--follow-imports=silent",
        ]
    )


def test_mypy_typing_with_args_leaves_import_following_alone(
    excluded_project: Callable[..., pathlib.Path],
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """Args may narrow the target, so the silencing flag stays off."""
    excluded_project("vendor")

    _hooks.core_mypy_typing(["entry.py"])

    mock_subprocess_run.assert_called_once_with(
        [
            "mypy",
            "--config-file",
            standards.MYPY_CONFIG.as_posix(),
            "--exclude",
            "^vendor(/|$)",
            "entry.py",
        ]
    )


def test_mypy_narrowed_run_still_reports_first_party_imports(
    excluded_project: Callable[..., pathlib.Path],
) -> None:
    """A list, even a stale one, never hides errors in project code."""
    root = excluded_project("nope")
    (root / "lib.py").write_text('x: int = "a"\n')
    (root / "entry.py").write_text("import lib\n\ny: int = lib.x\n")

    assert _hooks.core_mypy_typing(["entry.py"]) == 1


def test_project_excludes_layer_on_user_config(
    excluded_project: Callable[..., pathlib.Path],
    isolated_user_config: pathlib.Path,
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """A user-level override still receives the project list."""
    excluded_project("vendor")
    user_file = isolated_user_config / "ruff.toml"
    user_file.write_text("")

    _hooks.core_ruff_lint([])

    command = mock_subprocess_run.call_args.args[0]
    assert user_file.as_posix() in command
    assert 'extend-exclude=["./vendor"]' in command


def test_ruff_exclude_anchored_to_project_root(
    excluded_project: Callable[..., pathlib.Path],
    capfd: pytest.CaptureFixture[str],
) -> None:
    """`vendor` means `<root>/vendor`, never `src/vendor`."""
    root = excluded_project("vendor", "gen/one.py")
    for path in ("app.py", "vendor/a.py", "src/vendor/b.py", "gen/one.py"):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text("x = 1\n")
    (root / "gen" / "two.py").write_text("x = 1\n")

    assert _hooks.core_ruff_lint(["--show-files"]) == 0

    listed = capfd.readouterr().out.replace("\\", "/")
    assert "/app.py" in listed
    assert "/src/vendor/b.py" in listed
    assert "/gen/two.py" in listed
    assert "/gen/one.py" not in listed
    assert "/vendor/a.py" not in listed


def test_ruff_lint_fix_leaves_excluded_file_untouched(
    excluded_project: Callable[..., pathlib.Path],
) -> None:
    """`--fix` rewrites project code but never a listed path (issue #5)."""
    root = excluded_project("submodules/plugin")
    vendored = root / "submodules" / "plugin" / "a.py"
    vendored.parent.mkdir(parents=True)
    source = b"import os\n"
    vendored.write_bytes(source)
    (root / "app.py").write_bytes(source)

    _hooks.core_ruff_lint(["--fix"])

    assert vendored.read_bytes() == source
    assert (root / "app.py").read_bytes() != source


@pytest.mark.parametrize(
    ("paths", "returncode"),
    [((), 1), (("vendor",), 0)],
    ids=["unlisted", "listed"],
)
def test_ruff_format_honours_excludes(
    paths: tuple[str, ...],
    returncode: int,
    excluded_project: Callable[..., pathlib.Path],
) -> None:
    """`ruff format` skips a listed folder, as `ruff check` does."""
    root = excluded_project(*paths)
    (root / "app.py").write_text("x = 1\n")
    (root / "vendor").mkdir()
    (root / "vendor" / "a.py").write_text("x=1\n")

    assert _hooks.core_ruff_format(["--check"]) == returncode


def test_bundled_ruff_config_keeps_default_excludes(
    excluded_project: Callable[..., pathlib.Path],
    capfd: pytest.CaptureFixture[str],
) -> None:
    """The bundled config does not clear Ruff's default exclusions."""
    root = excluded_project()
    (root / "app.py").write_text("x = 1\n")
    (root / "dist").mkdir()
    (root / "dist" / "x.py").write_text("x = 1\n")

    assert _hooks.core_ruff_lint(["--show-files"]) == 0

    listed = capfd.readouterr().out.replace("\\", "/")
    assert "/app.py" in listed
    assert "/dist/x.py" not in listed


def test_mypy_exclude_prevents_invalid_package_abort(
    excluded_project: Callable[..., pathlib.Path],
    capfd: pytest.CaptureFixture[str],
) -> None:
    """A listed folder never reaches the package-name abort (issue #5)."""
    root = excluded_project()
    plugin = root / "submodules" / "qgis-cotraveler-plugin"
    plugin.mkdir(parents=True)
    (plugin / "__init__.py").write_text('x: int = "a"\n')
    (root / "app.py").write_text("x: int = 1\n")
    (root / "tests").mkdir()
    (root / "tests" / "test_app.py").write_text('y: int = "a"\n')

    assert _hooks.core_mypy_typing([]) == 2
    captured = capfd.readouterr()
    assert "is not a valid Python package name" in captured.out + captured.err

    excluded_project("submodules")

    assert _hooks.core_mypy_typing([]) == 0


def test_mypy_exclude_applies_from_a_subfolder(
    excluded_project: Callable[..., pathlib.Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A subfolder run keeps a listed path below it out (issue #5's abort)."""
    root = excluded_project("src/plugins")
    plugin = root / "src" / "plugins" / "qgis-plugin"
    plugin.mkdir(parents=True)
    (plugin / "__init__.py").write_text('x: int = "a"\n')
    (root / "src" / "app.py").write_text("x: int = 1\n")
    monkeypatch.chdir(root / "src")

    assert _hooks.core_mypy_typing([]) == 0


def test_mypy_exclude_anchored_to_project_root(
    excluded_project: Callable[..., pathlib.Path],
    capfd: pytest.CaptureFixture[str],
) -> None:
    """A package named like a listed folder is still checked."""
    root = excluded_project("submodules")
    package = root / "src" / "app" / "submodules"
    package.mkdir(parents=True)
    (package / "core.py").write_text('x: int = "a"\n')

    assert _hooks.core_mypy_typing([]) == 1
    assert "core.py" in capfd.readouterr().out


def test_mypy_exclude_covers_a_literal_file(
    excluded_project: Callable[..., pathlib.Path],
) -> None:
    """A file entry excludes that file and leaves its siblings checked."""
    root = excluded_project("gen.py")
    (root / "gen.py").write_text('x: int = "a"\n')
    (root / "app.py").write_text("x: int = 1\n")

    assert _hooks.core_mypy_typing([]) == 0

    (root / "app.py").write_text('x: int = "a"\n')

    assert _hooks.core_mypy_typing([]) == 1


def test_mypy_hides_errors_in_excluded_code_the_project_imports(
    excluded_project: Callable[..., pathlib.Path],
    capfd: pytest.CaptureFixture[str],
) -> None:
    """Imported excluded code stays silent while real targets are checked."""
    root = excluded_project("gen")
    (root / "gen").mkdir()
    (root / "gen" / "__init__.py").write_text('x: int = "a"\n')
    (root / "app.py").write_text("import gen\n\ny: int = gen.x\n")

    assert _hooks.core_mypy_typing([]) == 0

    (root / "app.py").write_text("import gen\n\ny: bytes = gen.x\n")

    assert _hooks.core_mypy_typing([]) == 1
    output = capfd.readouterr().out
    assert "app.py" in output
    assert "__init__.py" not in output


@pytest.mark.parametrize(
    "spelling",
    [
        "vendor/a.md",
        "./vendor/a.md",
        os.path.join("vendor", "a.md"),
        "ABSOLUTE",
    ],
    ids=["relative", "dot-relative", "native", "absolute"],
)
def test_pymarkdown_lint_drops_excluded_paths(
    spelling: str,
    excluded_project: Callable[..., pathlib.Path],
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """Only paths outside the list reach `scan`, however they are spelled."""
    root = excluded_project("vendor")
    if spelling == "ABSOLUTE":
        spelling = str(root / "vendor" / "a.md")

    _hooks.core_pymarkdown_lint([spelling, "b.md"])

    command = mock_subprocess_run.call_args.args[0]
    assert command[command.index("scan") + 1 :] == ["b.md"]


def test_pymarkdown_lint_drops_a_listed_file(
    excluded_project: Callable[..., pathlib.Path],
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """A file entry drops that file and leaves its siblings."""
    excluded_project("skip.md")

    _hooks.core_pymarkdown_lint(["skip.md", "b.md"])

    command = mock_subprocess_run.call_args.args[0]
    assert command[command.index("scan") + 1 :] == ["b.md"]


def test_pymarkdown_lint_match_is_case_sensitive(
    excluded_project: Callable[..., pathlib.Path],
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """Matching follows Ruff & Mypy on every platform: wrong case is kept."""
    excluded_project("vendor")

    _hooks.core_pymarkdown_lint(["VENDOR/a.md"])

    command = mock_subprocess_run.call_args.args[0]
    assert command[command.index("scan") + 1 :] == ["VENDOR/a.md"]


def test_pymarkdown_lint_drops_excluded_paths_from_a_subfolder(
    excluded_project: Callable[..., pathlib.Path],
    mock_subprocess_run: mock.MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A subfolder run drops a listed path below it."""
    root = excluded_project("docs/skip")
    (root / "docs").mkdir()
    monkeypatch.chdir(root / "docs")

    _hooks.core_pymarkdown_lint(["skip/a.md", "keep.md"])

    command = mock_subprocess_run.call_args.args[0]
    assert command[command.index("scan") + 1 :] == ["keep.md"]


def test_pymarkdown_lint_drops_a_listed_path_starting_with_a_dash(
    excluded_project: Callable[..., pathlib.Path],
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """A real path starting with `-`, as prek passes, is no `scan` option."""
    root = excluded_project("-x")
    (root / "-x").mkdir()
    (root / "-x" / "a.md").write_text("# A\n")

    _hooks.core_pymarkdown_lint(["-x/a.md", "b.md"])

    command = mock_subprocess_run.call_args.args[0]
    assert command[command.index("scan") + 1 :] == ["b.md"]


def test_pymarkdown_lint_matches_whole_path_segments(
    excluded_project: Callable[..., pathlib.Path],
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """`vendor` drops neither `vendor2/` nor `src/vendor/`."""
    excluded_project("vendor")
    kept = ["vendor2/a.md", "src/vendor/a.md"]

    _hooks.core_pymarkdown_lint(kept)

    command = mock_subprocess_run.call_args.args[0]
    assert command[command.index("scan") + 1 :] == kept


def test_pymarkdown_lint_from_inside_an_excluded_folder_keeps_paths(
    excluded_project: Callable[..., pathlib.Path],
    mock_subprocess_run: mock.MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nothing is dropped from inside: the folder & paths above are checked."""
    root = excluded_project("vendor")
    inside = root / "vendor" / "sub"
    inside.mkdir(parents=True)
    monkeypatch.chdir(inside)
    paths = ["../../outside.md", "i.md", "."]

    _hooks.core_pymarkdown_lint(paths)

    command = mock_subprocess_run.call_args.args[0]
    assert command[command.index("scan") + 1 :] == paths


@pytest.mark.parametrize(
    "args",
    [
        ["-e", "vendor/a.md", "b.md"],
        ["--exclude", "vendor", "a.md"],
        ["-r", "vendor"],
        ["-l", "vendor/a.md"],
    ],
    ids=["exclude-short", "exclude-long", "recurse", "list-files"],
)
def test_pymarkdown_lint_runs_scan_options_as_given(
    args: list[str],
    excluded_project: Callable[..., pathlib.Path],
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """An option's value is no path: dropping it could hide real findings."""
    excluded_project("vendor")

    _hooks.core_pymarkdown_lint(args)

    command = mock_subprocess_run.call_args.args[0]
    assert command[command.index("scan") + 1 :] == args


def test_pymarkdown_lint_skips_tool_when_all_excluded(
    excluded_project: Callable[..., pathlib.Path],
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """With nothing left to scan the hook passes without running the tool."""
    excluded_project("vendor")

    assert _hooks.core_pymarkdown_lint(["vendor/a.md"]) == 0

    mock_subprocess_run.assert_not_called()


def test_pymarkdown_lint_without_paths_still_runs_tool(
    excluded_project: Callable[..., pathlib.Path],
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """No paths at all is PyMarkdown's usage error, not an exclusion."""
    excluded_project("vendor")

    _hooks.core_pymarkdown_lint([])

    mock_subprocess_run.assert_called_once()


def test_is_excluded_keeps_a_path_on_another_drive() -> None:
    """`relpath` raises across Windows drives, so the path is kept."""
    with mock.patch("os.path.relpath", side_effect=ValueError):
        assert not _hooks._is_excluded("D:/vendor/a.md", ["vendor"])


def test_detect_secrets_ignores_project_excludes(
    excluded_project: Callable[..., pathlib.Path],
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """A listed path is still scanned: a leaked secret is still leaked."""
    excluded_project("vendor")

    _hooks.core_detect_secrets(["vendor/a.py"])

    assert "vendor/a.py" in mock_subprocess_run.call_args.args[0]


@pytest.mark.parametrize(
    "shim",
    [
        __main__.ruff_format,
        __main__.ruff_lint,
        __main__.mypy_typing,
        __main__.pymarkdown_lint,
    ],
    ids=["format", "lint", "typing", "markdown"],
)
def test_hook_entry_point_invalid_exclude_exits_1(
    shim: Callable[[], None],
    excluded_project: Callable[..., pathlib.Path],
    mock_subprocess_run: mock.MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A bad list stops the hook before any tool can touch vendored code."""
    excluded_project("a[1]")
    monkeypatch.setattr("sys.argv", ["pkgdx-hook", "app.md"])

    with pytest.raises(SystemExit) as exc_info:
        shim()

    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert err.startswith("error: ")
    assert len(err.splitlines()) == 1
    assert "a[1]" in err
    assert "Traceback" not in err
    mock_subprocess_run.assert_not_called()
