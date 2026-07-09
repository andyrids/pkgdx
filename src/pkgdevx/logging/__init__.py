"""__init__ for pkgdevx logging module."""

from ._logging import GLOBAL_CONSOLE, configure_logging

__all__: list[str] = ["GLOBAL_CONSOLE", "configure_logging"]
