"""Centralized constants for the `venv-axi` TOON encoder.

Trimmed, encode-only subset of `toon-format/toon-python`'s `constants.py`.
`pytack` only ever encodes TOON, never decodes it, so decode-side
constants (e.g. header-length parsing patterns) are omitted.

Attribution:
    The regex patterns, structural tokens and constant-extraction patterns
    in this file are directly adapted from the official `toon-python`
    reference implementation.

    Repository: https://github.com/toon-format/toon-python
    License: MIT License - Copyright (c) 2025 TOON Format Organization
"""

COMMA = ","
PIPE = "|"
TAB = "\t"

DELIMITERS = {"comma": COMMA, "tab": TAB, "pipe": PIPE}
DEFAULT_DELIMITER = PIPE

NULL_LITERAL = "null"
TRUE_LITERAL = "true"
FALSE_LITERAL = "false"

NUMERIC_REGEX = r"^-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$"
VALID_KEY_REGEX = r"^[A-Za-z_][\w.]*$"

ESCAPES = {
    "\\": "\\\\",
    '"': '\\"',
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}
