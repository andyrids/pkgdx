"""Logging configuration for `pkgdevx`.

NOTE: All logging handlers are on the `pkgdevx` logger.
"""

import logging.config
import pathlib
import tomllib


CONFIG_PATH = pathlib.Path(__file__).parent / "config.toml"
CONFIG_STR = CONFIG_PATH.read_text(encoding="utf-8")


def configure_logging() -> None:
    """Configures logging using the `config.toml` settings."""
    logging.config.dictConfig(tomllib.loads(CONFIG_STR))
