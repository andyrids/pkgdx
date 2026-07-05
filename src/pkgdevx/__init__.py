"""__init__ for pkgdevx."""

import contextlib
from importlib import metadata
from pathlib import Path
from pkgdevx import exceptions, standards
from pkgdevx.logging import configure_logging

__all__: list[str] = ["exceptions", "standards"]

PKGDEV_ROOT: Path = Path(__file__).parent

configure_logging()

with contextlib.suppress(metadata.PackageNotFoundError):
    __version__: str = metadata.version("pkgdevx")
