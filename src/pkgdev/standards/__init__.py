""""""

from pathlib import Path

PKG_ROOT: Path = Path(__file__).parent
MYPY_CONFIG: Path = PKG_ROOT / "mypy.ini"
PYMARKDOWN_CONFIG: Path = PKG_ROOT / "pymarkdown.ini"
RUFF_CONFIG: Path = PKG_ROOT / "ruff.ini"

__all__: list[str] = ["MYPY_CONFIG", "PYMARKDOWN_CONFIG", "RUFF_CONFIG"]
