"""Unit tests for canonical standards hook command builders."""

from collections.abc import Callable
from unittest import mock

import pytest

from pkgdx import standards
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
        ]
    )
    assert returncode == 0


def test_detect_secrets_preserves_explicit_baseline(
    mock_subprocess_run: mock.MagicMock,
) -> None:
    """An explicit `--baseline` is not prepended a second time."""
    args = ["--baseline", ".secrets.baseline", "--no-verify"]

    returncode = _hooks.core_detect_secrets(args)

    mock_subprocess_run.assert_called_once_with(["detect-secrets-hook", *args])
    assert returncode == 0
