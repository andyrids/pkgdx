"""Unit tests for the `pkgdx init` core logic (`pkgdx._core`)."""

import logging
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest
import tomlkit

from pkgdx import exceptions, standards
from pkgdx._core import (
    Change,
    Outcome,
    StepResult,
    _inject_missing_hooks,
    _validate_prek_repos,
    create_secrets_baseline,
    get_git_toplevel,
    get_project_root,
    install_prek_hooks,
    setup_prek_config,
    update_prek_hooks,
)

# Real `prek update --check` STDOUT (prek 0.4.14), with two stale revisions
PREK_WOULD_UPDATE = (
    "https://gitlab.com/andyrids/pkgdx\n"
    "  would update rev `v0.4.1` -> `v0.5.0rc1`\n"
    "\n"
    "https://github.com/pre-commit/pre-commit-hooks\n"
    "  would update rev `v4.0.0` -> `v6.0.0`\n"
)

# Real `prek update --check` STDERR for an unreachable repo (command abridged)
PREK_FETCH_FAILED = (
    "https://gitlab.com/andyrids/missing\n"
    "  update failed: Command `git.exe fetch origin HEAD --quiet` exited "
    "with an error:\n"
    "\n"
    "[status]\n"
    "exit code: 128\n"
)


def _completed(
    returncode: int, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    """Build a finished subprocess result for `subprocess.run` mocks."""
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


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


def test_get_project_root_message_names_searched_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing project root is reported in plain words, not reprs."""
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.chdir(empty)
    monkeypatch.setattr(sys, "prefix", str(tmp_path / "venv"))

    with pytest.raises(exceptions.ProjectRootNotFoundError) as exc_info:
        get_project_root()

    assert "No pyproject.toml" in str(exc_info.value)
    assert "sys.prefix=" not in str(exc_info.value)


def test_get_git_toplevel_raises_outside_git(
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """A failed `git rev-parse` raises `GitTopLevelError`."""
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(
        128, ["git"], stderr="fatal: not a git repository"
    )
    with pytest.raises(exceptions.GitTopLevelError):
        get_git_toplevel()


def test_inject_missing_hooks_returns_added_count() -> None:
    """The number of hooks added is returned, and 0 when none are missing."""
    table = {"hooks": tomlkit.aot()}
    expected = [{"id": "a"}, {"id": "b", "args": ["--x"]}]

    assert _inject_missing_hooks(table, expected) == 2  # type: ignore[arg-type]
    assert _inject_missing_hooks(table, expected) == 0  # type: ignore[arg-type]


def test_setup_prek_config_creates_missing_file(tmp_path: Path) -> None:
    """A missing `prek.toml` is created from the template."""
    result = setup_prek_config(tmp_path)

    assert result == StepResult(
        Outcome.OK, change=Change.CREATED, subject="prek.toml"
    )
    template_text = standards.PREK_CONFIG.read_text()
    assert (tmp_path / "prek.toml").read_text() == template_text


def test_setup_prek_config_reset_updates_differing_file(
    tmp_path: Path,
) -> None:
    """`--reset` overwrites a differing `prek.toml`, without a qualifier."""
    (tmp_path / "prek.toml").write_text('[[repos]]\nrepo = "local"\n')

    result = setup_prek_config(tmp_path, reset=True)

    assert result == StepResult(
        Outcome.OK, change=Change.UPDATED, subject="prek.toml"
    )
    template_text = standards.PREK_CONFIG.read_text()
    assert (tmp_path / "prek.toml").read_text() == template_text


def test_setup_prek_config_reset_keeps_identical_file(tmp_path: Path) -> None:
    """`--reset` leaves a `prek.toml` that already matches the template."""
    (tmp_path / "prek.toml").write_text(standards.PREK_CONFIG.read_text())

    with mock.patch("pathlib.Path.write_text") as mwrite_text:
        result = setup_prek_config(tmp_path, reset=True)

    assert result == StepResult(
        Outcome.OK, change=Change.UNCHANGED, subject="prek.toml"
    )
    mwrite_text.assert_not_called()


@pytest.mark.parametrize(
    ("hook_ids", "subject"),
    [
        (["a", "b"], "prek.toml (1 hook added)"),
        (["a", "b", "c"], "prek.toml (2 hooks added)"),
    ],
)
def test_setup_prek_config_counts_added_hooks(
    tmp_path: Path,
    isolated_user_config: Path,
    hook_ids: list[str],
    subject: str,
) -> None:
    """The subject counts the hooks added, with a singular `1 hook`."""
    hooks = "".join(f'\n[[repos.hooks]]\nid = "{i}"\n' for i in hook_ids)
    user_hooks = isolated_user_config / "hooks.toml"
    user_hooks.write_text(f'[[repos]]\nrepo = "local"\n{hooks}')
    prek = tmp_path / "prek.toml"
    prek.write_text('[[repos]]\nrepo = "local"\n\n[[repos.hooks]]\nid = "a"\n')

    result = setup_prek_config(tmp_path)

    assert result == StepResult(
        Outcome.OK, change=Change.UPDATED, subject=subject
    )
    assert "1 hooks" not in result.subject


def test_setup_prek_config_fills_empty_repos(
    tmp_path: Path, isolated_user_config: Path
) -> None:
    """A `prek.toml` without `[[repos]]` gets the template repos."""
    user_hooks = isolated_user_config / "hooks.toml"
    user_hooks.write_text(
        '[[repos]]\nrepo = "local"\n[[repos.hooks]]\nid = "a"'
    )
    (tmp_path / "prek.toml").write_text("# no repos\n")

    result = setup_prek_config(tmp_path)

    assert result == StepResult(
        Outcome.OK, change=Change.UPDATED, subject="prek.toml (1 hook added)"
    )


def test_setup_prek_config_second_run_is_unchanged(tmp_path: Path) -> None:
    """A second run after a merge leaves `prek.toml` unchanged."""
    prek = tmp_path / "prek.toml"
    prek.write_text('[[repos]]\nrepo = "local"\n')
    assert setup_prek_config(tmp_path).change is Change.UPDATED
    merged = prek.read_bytes()

    result = setup_prek_config(tmp_path)

    assert result == StepResult(
        Outcome.OK, change=Change.UNCHANGED, subject="prek.toml"
    )
    assert prek.read_bytes() == merged


@pytest.mark.parametrize(
    ("inline", "args"),
    [
        ("hooks = []", None),
        ('hooks = [{ id = "a", args = ["-x"] }]', ["-x"]),
    ],
)
def test_setup_prek_config_converts_inline_hooks(
    tmp_path: Path,
    isolated_user_config: Path,
    inline: str,
    args: list[str] | None,
) -> None:
    """Inline `hooks = [...]` becomes `[[repos.hooks]]`, keeping its hooks."""
    (isolated_user_config / "hooks.toml").write_text(
        '[[repos]]\nrepo = "local"\n\n'
        '[[repos.hooks]]\nid = "a"\n\n[[repos.hooks]]\nid = "b"\n'
    )
    prek = tmp_path / "prek.toml"
    prek.write_text(f'[[repos]]\n{inline}\nrepo = "local"\n')

    assert setup_prek_config(tmp_path).change is Change.UPDATED

    hooks = tomlkit.parse(prek.read_text())["repos"][0]["hooks"]
    assert [hook["id"] for hook in hooks] == ["a", "b"]
    assert hooks[0].get("args") == args
    assert setup_prek_config(tmp_path).change is Change.UNCHANGED


def test_setup_prek_config_keeps_complete_inline_hooks(
    tmp_path: Path, isolated_user_config: Path
) -> None:
    """Inline hooks with nothing missing are left as written."""
    (isolated_user_config / "hooks.toml").write_text(
        '[[repos]]\nrepo = "local"\n\n[[repos.hooks]]\nid = "a"\n'
    )
    prek = tmp_path / "prek.toml"
    prek.write_text('[[repos]]\nrepo = "local"\nhooks = [{ id = "a" }]\n')
    original = prek.read_bytes()

    result = setup_prek_config(tmp_path)

    assert result.change is Change.UNCHANGED
    assert prek.read_bytes() == original


def test_setup_prek_config_fails_on_unparsable_file(tmp_path: Path) -> None:
    """An unparsable `prek.toml` gives a FAIL result instead of raising."""
    (tmp_path / "prek.toml").write_text("[[repos]\n")

    result = setup_prek_config(tmp_path)

    assert result.outcome is Outcome.FAIL
    assert result.detail == "prek.toml could not be parsed"
    assert "--reset" in result.hint


def test_setup_prek_config_fails_on_malformed_consumer_file(
    tmp_path: Path,
) -> None:
    """A malformed consumer `prek.toml` gives a FAIL result."""
    (tmp_path / "prek.toml").write_text('[[repos]]\nrev = "1.0.0"')

    result = setup_prek_config(tmp_path)

    assert result.outcome is Outcome.FAIL
    assert result.detail == "prek.toml is invalid"
    assert "repos[0]" in result.message


def test_setup_prek_config_fails_on_bad_config_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An invalid `PKGDX_CONFIG_DIR` gives a FAIL result."""
    monkeypatch.setenv(standards.CONFIG_DIR_ENV, str(tmp_path / "nope"))

    result = setup_prek_config(tmp_path)

    assert result.outcome is Outcome.FAIL
    assert result.detail == "user config directory not found"
    assert standards.CONFIG_DIR_ENV in result.message


def test_setup_prek_config_fails_on_broken_user_hooks_toml(
    tmp_path: Path, isolated_user_config: Path
) -> None:
    """A broken user `hooks.toml` fails without suggesting `--reset`."""
    (isolated_user_config / "hooks.toml").write_text("[[repos]\n")
    (tmp_path / "prek.toml").write_text('[[repos]]\nrepo = "local"\n')

    result = setup_prek_config(tmp_path)

    assert result.outcome is Outcome.FAIL
    assert result.detail == "hooks.toml could not be parsed"
    assert "--reset" not in result.hint


def test_setup_prek_config_uses_user_hooks_toml(
    tmp_path: Path, isolated_user_config: Path
) -> None:
    """A user `hooks.toml` replaces the bundled template."""
    user_hooks = isolated_user_config / "hooks.toml"
    user_hooks.write_text('[[repos]]\nrepo = "local"\nhooks = []\n# user')
    project = tmp_path / "proj"
    project.mkdir()

    result = setup_prek_config(project)

    assert result.change is Change.CREATED
    assert (project / "prek.toml").read_text() == user_hooks.read_text()


def test_install_prek_hooks_skips_existing_shims(
    tmp_path: Path, mock_subprocess_run: mock.MagicMock
) -> None:
    """Existing Git shims are left as they are, without running prek."""
    shim = tmp_path / ".git" / "hooks" / "pre-commit"
    shim.parent.mkdir(parents=True)
    shim.write_text("#!/bin/sh")

    result = install_prek_hooks(tmp_path, tmp_path)

    assert result == StepResult(
        Outcome.OK, change=Change.UNCHANGED, subject="Git shims"
    )
    mock_subprocess_run.assert_not_called()


def test_install_prek_hooks_installs_at_git_toplevel(
    tmp_path: Path, mock_subprocess_run: mock.MagicMock
) -> None:
    """Git shims are installed from the Git top-level."""
    mock_subprocess_run.return_value = _completed(0)
    toplevel = tmp_path / "top"

    result = install_prek_hooks(tmp_path, toplevel)

    assert result == StepResult(
        Outcome.OK, change=Change.CREATED, subject="Git shims"
    )
    assert mock_subprocess_run.call_args.kwargs["cwd"] == toplevel


def test_install_prek_hooks_installs_at_project_root(
    tmp_path: Path, mock_subprocess_run: mock.MagicMock
) -> None:
    """Without a Git top-level, the shims are installed at the root."""
    mock_subprocess_run.return_value = _completed(0)

    result = install_prek_hooks(tmp_path, None)

    assert result.subject == "Git shims (at project root)"
    assert mock_subprocess_run.call_args.kwargs["cwd"] == tmp_path


def test_install_prek_hooks_warns_on_failure(
    tmp_path: Path,
    mock_subprocess_run: mock.MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A failed `prek install` warns with its last error line."""
    caplog.set_level(logging.DEBUG, logger="pkgdx")
    mock_subprocess_run.return_value = _completed(
        1, stderr="error: x\n  caused by: y\n"
    )

    result = install_prek_hooks(tmp_path, tmp_path)

    assert result.outcome is Outcome.WARN
    assert result.detail == "Git shims not installed"
    assert result.message == "caused by: y"
    assert {record.levelno for record in caplog.records} == {logging.DEBUG}


def test_install_prek_hooks_warns_on_missing_executable(
    tmp_path: Path, mock_subprocess_run: mock.MagicMock
) -> None:
    """A missing executable warns instead of raising."""
    mock_subprocess_run.side_effect = FileNotFoundError("no python")

    result = install_prek_hooks(tmp_path, tmp_path)

    assert result.outcome is Outcome.WARN
    assert result.message == "no python"


def test_update_prek_hooks_reports_up_to_date(
    tmp_path: Path, mock_subprocess_run: mock.MagicMock
) -> None:
    """Return code 0 means hook revisions are up to date."""
    mock_subprocess_run.return_value = _completed(0)

    result = update_prek_hooks(tmp_path)

    assert result == StepResult(Outcome.OK, "hook revisions up to date")
    assert "-v" not in mock_subprocess_run.call_args.args[0]


def test_update_prek_hooks_names_available_update(
    tmp_path: Path, mock_subprocess_run: mock.MagicMock
) -> None:
    """A stale revision is named with the repo and both versions."""
    mock_subprocess_run.return_value = _completed(
        1,
        "https://gitlab.com/andyrids/pkgdx\n"
        "  would update rev `v0.4.2` -> `v0.5.0`\n",
    )

    result = update_prek_hooks(tmp_path)

    assert result.outcome is Outcome.WARN
    assert result.detail == "pkgdx v0.4.2 -> v0.5.0 available"
    assert result.message == ""
    assert result.hint.endswith("`prek update`")


def test_update_prek_hooks_joins_several_updates(
    tmp_path: Path, mock_subprocess_run: mock.MagicMock
) -> None:
    """Several stale repos are joined with commas."""
    mock_subprocess_run.return_value = _completed(1, PREK_WOULD_UPDATE)

    result = update_prek_hooks(tmp_path)

    assert result.detail == (
        "pkgdx v0.4.1 -> v0.5.0rc1, "
        "pre-commit-hooks v4.0.0 -> v6.0.0 available"
    )


def test_update_prek_hooks_falls_back_on_unrecognised_output(
    tmp_path: Path, mock_subprocess_run: mock.MagicMock
) -> None:
    """Unrecognised update output gives a generic update warning."""
    mock_subprocess_run.return_value = _completed(1, "something new\n")

    result = update_prek_hooks(tmp_path)

    assert result.outcome is Outcome.WARN
    assert result.detail == "hook revision updates available"


@pytest.mark.parametrize(
    ("returncode", "stderr", "message"),
    [
        (
            1,
            PREK_FETCH_FAILED,
            "fetch failed: https://gitlab.com/andyrids/missing",
        ),
        (2, "error: bad\n", "error: bad"),
        (101, "", "prek exited with code 101"),
    ],
)
def test_update_prek_hooks_warns_when_check_fails(
    tmp_path: Path,
    mock_subprocess_run: mock.MagicMock,
    caplog: pytest.LogCaptureFixture,
    returncode: int,
    stderr: str,
    message: str,
) -> None:
    """A failed check warns with its last error line, without logging it."""
    caplog.set_level(logging.DEBUG, logger="pkgdx")
    mock_subprocess_run.return_value = _completed(returncode, stderr=stderr)

    result = update_prek_hooks(tmp_path)

    assert result.outcome is Outcome.WARN
    assert result.detail == "could not check hook revisions"
    assert result.message == message
    assert {record.levelno for record in caplog.records} == {logging.DEBUG}


def test_update_prek_hooks_names_fetch_failure_beside_updates(
    tmp_path: Path, mock_subprocess_run: mock.MagicMock
) -> None:
    """A repo that failed to fetch is named beside the available updates."""
    mock_subprocess_run.return_value = _completed(
        1, PREK_WOULD_UPDATE, PREK_FETCH_FAILED
    )

    result = update_prek_hooks(tmp_path)

    assert result.outcome is Outcome.WARN
    assert result.detail.startswith("pkgdx v0.4.1 -> v0.5.0rc1, ")
    assert result.message == (
        "fetch failed: https://gitlab.com/andyrids/missing"
    )


def test_update_prek_hooks_warns_on_missing_executable(
    tmp_path: Path, mock_subprocess_run: mock.MagicMock
) -> None:
    """A missing executable warns instead of raising."""
    mock_subprocess_run.side_effect = FileNotFoundError("no python")

    result = update_prek_hooks(tmp_path)

    assert result.outcome is Outcome.WARN
    assert result.detail == "could not check hook revisions"


def test_create_secrets_baseline_keeps_existing_file(
    tmp_path: Path, mock_subprocess_run: mock.MagicMock
) -> None:
    """An existing baseline is kept, without running a scan."""
    (tmp_path / ".secrets.baseline").write_text("{}")

    result = create_secrets_baseline(tmp_path)

    assert result == StepResult(
        Outcome.OK, change=Change.UNCHANGED, subject=".secrets.baseline"
    )
    mock_subprocess_run.assert_not_called()


def test_create_secrets_baseline_writes_scan_output(
    tmp_path: Path, mock_subprocess_run: mock.MagicMock
) -> None:
    """A successful scan's output is written as the baseline."""
    mock_subprocess_run.return_value.stdout = b'{"x": 1}'

    result = create_secrets_baseline(tmp_path)

    assert result == StepResult(
        Outcome.OK, change=Change.CREATED, subject=".secrets.baseline"
    )
    assert (tmp_path / ".secrets.baseline").read_bytes() == b'{"x": 1}'


def test_create_secrets_baseline_fails_without_partial_file(
    tmp_path: Path, mock_subprocess_run: mock.MagicMock
) -> None:
    """A failed scan gives FAIL with its last error line and no file."""
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(
        2, ["detect-secrets"], stderr=b"Traceback ...\nValueError: boom\n"
    )

    result = create_secrets_baseline(tmp_path)

    assert result.outcome is Outcome.FAIL
    assert result.detail == ".secrets.baseline not created"
    assert result.message == "ValueError: boom"
    assert not (tmp_path / ".secrets.baseline").exists()


def test_create_secrets_baseline_fails_on_missing_executable(
    tmp_path: Path, mock_subprocess_run: mock.MagicMock
) -> None:
    """A missing executable gives a FAIL result."""
    mock_subprocess_run.side_effect = FileNotFoundError("no python")

    result = create_secrets_baseline(tmp_path)

    assert result.outcome is Outcome.FAIL
    assert result.message == "no python"


def test_create_secrets_baseline_interrupt_leaves_no_file(
    tmp_path: Path, mock_subprocess_run: mock.MagicMock
) -> None:
    """Ctrl-C during a scan leaves no partial baseline."""
    mock_subprocess_run.side_effect = KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        create_secrets_baseline(tmp_path)

    assert not (tmp_path / ".secrets.baseline").exists()


def test_create_secrets_baseline_forces_utf8_mode(
    tmp_path: Path,
    mock_subprocess_run: mock.MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Baseline scans run in UTF-8 mode so non-cp1252 files are not skipped."""
    monkeypatch.setenv("PYTHONUTF8", "0")
    monkeypatch.setenv("PKGDX_SENTINEL", "kept")
    mock_subprocess_run.return_value.stdout = b"{}"

    create_secrets_baseline(tmp_path)

    env = mock_subprocess_run.call_args.kwargs["env"]
    assert env["PYTHONUTF8"] == "1"
    assert env["PKGDX_SENTINEL"] == "kept"
