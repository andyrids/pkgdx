"""Initialise the standards package."""

from pathlib import Path

PKG_ROOT: Path = Path(__file__).parent
MYPY_CONFIG: Path = PKG_ROOT / "mypy.ini"
PYMARKDOWN_CONFIG: Path = PKG_ROOT / "pymarkdown.toml"
RUFF_CONFIG: Path = PKG_ROOT / "ruff.toml"

__all__: list[str] = ["MYPY_CONFIG", "PYMARKDOWN_CONFIG", "RUFF_CONFIG"]
