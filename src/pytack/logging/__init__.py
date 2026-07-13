"""__init__ for pytack logging module."""

from ._logging import configure_cli_logging, configure_pkg_logging

__all__: list[str] = ["configure_cli_logging", "configure_pkg_logging"]
