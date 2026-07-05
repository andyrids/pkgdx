"""Logging configuration for `pkgdev`.

NOTE: All logging handlers are on the `pkgdev` logger.
"""

import json
import logging.config
import pathlib
import tomllib
from logging import Formatter, LogRecord
from typing import override


CONFIG_PATH = pathlib.Path(__file__).parent / "config.toml"
CONFIG_STR = CONFIG_PATH.read_text(encoding="utf-8")


class JSONFormatter(Formatter):
    """Custom JSON formatter for LogRecord objects."""

    def __init__(self, *, defaults: dict[str, str] | None = None) -> None:
        """Initialises the `JSONFormatter` class.

        Args:
            defaults: Optional default values to use in custom fields.
        """
        super().__init__(datefmt="%Y-%m-%dT%H:%M:%S%z", defaults=defaults)

    @override
    def format(self: "JSONFormatter", record: LogRecord) -> str:
        """Format the log record as a JSON string."""
        msg = self._record_to_dict(record)
        return json.dumps(msg, default=str)

    def _record_to_dict(self: "JSONFormatter", record: LogRecord) -> dict[str, str]:
        """Convert a log record to a dictionary."""

        logrecord_dict = {
            "message": record.getMessage(),
            "timestamp": self.formatTime(record, self.datefmt),
        }

        if record.exc_info is not None:
            logrecord_dict["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info is not None:
            logrecord_dict["stack_info"] = self.formatStack(record.stack_info)

        logrecord_dict.update(
            {
                k: v
                for k, v in record.__dict__.items()
                if k not in logrecord_dict and k is not None
            }
        )

        return logrecord_dict


def configure_logging() -> None:
    """Configures logging using the `config.toml` settings."""
    logging.config.dictConfig(tomllib.loads(CONFIG_STR))
