"""__init__ for pkgdev.standards.

Provides access to configuration files for supported tools such as; `mypy`,
`prek`, `pymarkdown`, and `ruff`.
"""

from pathlib import Path

MODULE_ROOT: Path = Path(__file__).parent
MYPY_CONFIG: Path = MODULE_ROOT / "mypy.ini"
PREK_CONFIG: Path = MODULE_ROOT / "_prek.toml"
PYMARKDOWN_CONFIG: Path = MODULE_ROOT / "pymarkdown.toml"
RUFF_CONFIG: Path = MODULE_ROOT / "ruff.toml"


__all__: list[str] = [
    "MYPY_CONFIG",
    "PREK_CONFIG",
    "PYMARKDOWN_CONFIG",
    "RUFF_CONFIG",
]
