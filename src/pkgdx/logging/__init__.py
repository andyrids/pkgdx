"""__init__ for pkgdx logging module."""

from ._logging import (
    CLI_CONSOLE,
    GLOBAL_CONSOLE,
    configure_cli_logging,
    configure_pkg_logging,
)

__all__: list[str] = [
    "CLI_CONSOLE",
    "GLOBAL_CONSOLE",
    "configure_cli_logging",
    "configure_pkg_logging",
]
