"""__init__ for pytack."""

import contextlib
from importlib import metadata
from pathlib import Path
from pytack import exceptions, standards
from pytack.logging import configure_pkg_logging

__all__: list[str] = ["exceptions", "standards"]

PKGDEV_ROOT: Path = Path(__file__).parent

configure_pkg_logging()

with contextlib.suppress(metadata.PackageNotFoundError):
    __version__: str = metadata.version("pytack")
