"""Unit tests for validating the hook manifest."""

import re
import subprocess
import sys
from pathlib import Path


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
