"""__init__ for pkgdx."""

import contextlib
from importlib import metadata
from pathlib import Path
from pkgdx import exceptions, standards
from pkgdx.logging import configure_pkg_logging

__all__: list[str] = ["exceptions", "standards"]

PKGDX_ROOT: Path = Path(__file__).parent

configure_pkg_logging()

with contextlib.suppress(metadata.PackageNotFoundError):
    __version__: str = metadata.version("pkgdx")
