"""Minimal TOON (Token-Oriented Object Notation) encoder for `venv-axi`.

Implements a narrow, spec-compliant subset of the TOON specification
(https://github.com/toon-format/spec), which is sufficient for flat
key-value objects and uniform tabular arrays.

NOTE: Nesting, folding and alternate delimiters have not been implemented.
"""

import re
from collections.abc import Mapping, Sequence
from typing import Any

_NUMERIC_RE = re.compile(r"^-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$")
_CONTROL_RE = re.compile(r"[\x00-\x1f]")
_QUOTE_CHARS = ',:"\\[]{}'
_ESCAPES = {
    "\\": "\\\\",
    '"': '\\"',
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}


def _needs_quoting(value: str) -> bool:
    """Determines whether a string value must be quoted.

    Args:
        value: The raw string value.

    Returns:
        True if `value` must be wrapped in double quotes.
    """
    if value == "" or value != value.strip():
        return True
    if value in ("true", "false", "null"):
        return True
    if _NUMERIC_RE.match(value):
        return True
    if any(ch in value for ch in _QUOTE_CHARS):
        return True
    if _CONTROL_RE.search(value):
        return True
    return value == "-" or value.startswith("-")


def _escape(value: str) -> str:
    """Escapes a string value for use inside TOON double quotes.

    Args:
        value: The raw string value.

    Returns:
        The escaped string, without surrounding quotes.
    """

    def match_char(ch: str) -> str:
        """Matches & escapes a single character for TOON."""
        match ch:
            case ch if ch in _ESCAPES:
                return _ESCAPES[ch]
            case _ if ord(ch) < 0x20:
                return f"\\u{ord(ch):04x}"
            case _:
                return ch

    chars = [match_char(ch) for ch in value]
    return "".join(chars)


def encode_primitive(value: Any) -> str:
    """Encodes a single primitive value as a TOON token.

    Args:
        value: A string, number, boolean or None value.

    Returns:
        The TOON-encoded token.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)

    text = str(value)
    if _needs_quoting(text):
        return f'"{_escape(text)}"'
    return text


def encode_object(fields: Mapping[str, Any]) -> str:
    """Encodes a flat mapping as TOON `key: value` lines.

    Args:
        fields: An ordered mapping of field names to primitive values.

    Returns:
        The TOON-encoded object, one field per line.
    """
    return "\n".join(f"{k}: {encode_primitive(v)}" for k, v in fields.items())


def encode_table(
    key: str,
    rows: Sequence[Mapping[str, Any]],
    fields: Sequence[str],
) -> str:
    """Encodes a uniform list of objects as a TOON tabular array.

    Args:
        key: The array field name.
        rows: The row objects for each item in `fields`.
        fields: The ordered field names forming the tabular header.

    Returns:
        A TOON-encoded tabular array, with a header and indented, comma-joined
        rows per field item.
    """
    header = f"{key}[{len(rows)}]{{{','.join(fields)}}}:"
    lines = [header]
    for row in rows:
        cells = ",".join(encode_primitive(row.get(field)) for field in fields)
        lines.append(f"  {cells}")
    return "\n".join(lines)


def format_help(lines: Sequence[str]) -> str:
    """Formats the contextual-disclosure `help[]` footer.

    NOTE: AXI principle 9 (contextual disclosure): concrete
    next-step commands are surfaced instead of a static usage summary.

    Args:
        lines: Concrete next-step command suggestions.

    Returns:
        A `help[N]:` block, with indented lines for each suggestion.

        ```
        help[2]:
            Run `venv-axi list` for the venv package list
            Run `venv-axi show <package>` for package info
        ```
    """
    body = "\n".join(f"  {line}" for line in lines)
    return f"help[{len(lines)}]:\n{body}"
