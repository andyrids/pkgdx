"""Logging configuration for `pkgdx`.

NOTE: All logging handlers are on the `pkgdx` logger.
"""

import logging.config
import pathlib

import tomllib
from rich import get_console

CONFIG_PATH = pathlib.Path(__file__).parent / "config.toml"
CONFIG_STR = CONFIG_PATH.read_text(encoding="utf-8")
GLOBAL_CONSOLE = get_console()


def configure_cli_logging(level: int = logging.WARNING) -> None:
    """Configure CLI logging using the `config.toml` settings."""
    logging.config.dictConfig(tomllib.loads(CONFIG_STR))

    package = __package__.split(".")[0] if __package__ else "pkgdx"

    logger = logging.getLogger(package)
    logger.setLevel(level)

    # Prevent CLI logs from propagating & being duplicated
    logger.propagate = False


def configure_pkg_logging() -> None:
    """Configure package logging using a `NullHandler`."""
    package = __package__.split(".")[0] if __package__ else "pkgdx"
    logging.getLogger(package).addHandler(logging.NullHandler())
