"""__init__ for pkgdx."""

import logging
from importlib import metadata
from pathlib import Path

from pkgdx import exceptions, standards

__all__: list[str] = ["exceptions", "standards"]

PKGDX_ROOT: Path = Path(__file__).parent

# Mypy-recommended method to mitigate `[no-redef]` issues
__version__: str
try:
    __version__ = metadata.version("pkgdx")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0+unknown"

# Library use stays silent; the CLI configures logging per run (pyclig)
logging.getLogger(__name__).addHandler(logging.NullHandler())
