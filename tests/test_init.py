"""Unit tests for the `pkgdx` package - import side effects & version."""

import importlib
import json
import subprocess
import sys
from importlib import metadata

import pytest

import pkgdx

_PROBE = """
import json, logging, sys
import rich
import pkgdx, pkgdx.__main__
handlers = logging.getLogger("pkgdx").handlers
print(json.dumps({
    "rich_console": rich._console is not None,
    "handlers": [type(h).__name__ for h in handlers],
    "logging_module": "pkgdx.logging" in sys.modules,
}))
"""


def test_import_has_no_side_effects() -> None:
    """`import pkgdx` leaves Rich's global console & logging alone (#8)."""
    result = subprocess.run(
        [sys.executable, "-c", _PROBE],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout) == {
        "rich_console": False,
        "handlers": ["NullHandler"],
        "logging_module": False,
    }


def test_version_fallback_without_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`__version__` falls back when package metadata is unavailable (#12)."""

    def missing(name: str) -> str:
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(metadata, "version", missing)
    try:
        assert importlib.reload(pkgdx).__version__ == "0.0.0+unknown"
        assert importlib.import_module("pkgdx.__main__").cli.name == "pkgdx"
    finally:
        monkeypatch.undo()
        importlib.reload(pkgdx)
