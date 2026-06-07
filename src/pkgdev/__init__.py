"""__init__ for pkgdev."""

import contextlib
from importlib import metadata
from pkgdev import standards

__all__: list[str] = ["standards"]

with contextlib.suppress(metadata.PackageNotFoundError):
    __version__: str = metadata.version("pkgdev")
