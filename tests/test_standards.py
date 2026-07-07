"""Unit tests for validating the hook manifest."""

import os
import re
import subprocess
import sys
from pathlib import Path
import pytest
from pkgdevx import exceptions, standards


def test_validate_manifest() -> None:
    """Validates the hook manifest."""

    project_root = Path(__file__).resolve().parent.parent
    manifest = project_root / ".pre-commit-hooks.yaml"

    assert manifest.exists(), "Missing `.pre-commit-hooks.yaml`"

    result = subprocess.run(
        [sys.executable, "-m", "prek", "validate-manifest", str(manifest)],
        capture_output=True,
        check=False,
        text=True,
    )

    stderr = re.sub(r"\n", "", result.stderr)
    assert result.returncode == 0, stderr


@pytest.mark.skipif(
    os.environ.get("CI_COMMIT_TAG") is not None,
    reason="Avoid CI/CD race condition on tag event",
)
def test_prek_revision_update() -> None:
    """Ensures the Prek config has the latest revision version."""
    import shutil
    from pkgdevx.standards import PREK_CONFIG

    prek = shutil.which("prek")
    assert prek is not None

    result = subprocess.run(
        [prek, "auto-update", "--check", "--config", str(PREK_CONFIG)],
        capture_output=True,
        check=False,
        text=True,
    )

    stderr = re.sub(r"\n", "", result.stderr)
    stdout = re.sub(r"\n", "", result.stdout)
    assert result.returncode == 0, stdout or stderr


def test_prek_repo_revision() -> None:
    """Tests Prek config `repo` revision value."""
    try:
        standards.get_config_revision()
    except exceptions.PrekRepoRevisionError as e:
        pytest.fail(str(e))


def test_prek_repo_url() -> None:
    """Tests Prek config `repo` URL value."""
    try:
        config_repository = standards.get_config_repository()
    except exceptions.PrekRepoRevisionError as e:
        pytest.fail(str(e))

    try:
        pkgdevx_repository = standards.get_pkgdevx_repository()
    except exceptions.PrekRepoURLMissingError as e:
        pytest.fail(str(e))

    assert config_repository == pkgdevx_repository
