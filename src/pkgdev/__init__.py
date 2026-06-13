"""__init__ for pkgdev."""

import contextlib
from importlib import metadata
from pathlib import Path
from pkgdev import exceptions, standards

__all__: list[str] = ["exceptions", "standards"]

PKGDEV_ROOT: Path = Path(__file__).parent

with contextlib.suppress(metadata.PackageNotFoundError):
    __version__: str = metadata.version("pkgdev")
