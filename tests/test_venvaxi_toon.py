"""Unit tests for `pytack.venvaxi._toon`."""

from pytack.venvaxi._toon import (
    encode_object,
    encode_primitive,
    encode_table,
    format_help,
)


def test_encode_primitive_none() -> None:
    """None encodes as the `null` token."""
    assert encode_primitive(None) == "null"


def test_encode_primitive_bool() -> None:
    """Booleans encode as the `true`/`false` tokens."""
    assert encode_primitive(True) == "true"
    assert encode_primitive(False) == "false"


def test_encode_primitive_number() -> None:
    """Numbers encode as bare tokens."""
    assert encode_primitive(42) == "42"
    assert encode_primitive(3.14) == "3.14"


def test_encode_primitive_plain_string() -> None:
    """A plain string encodes without quotes."""
    assert encode_primitive("rich") == "rich"


def test_encode_primitive_quotes_empty_string() -> None:
    """An empty string is quoted."""
    assert encode_primitive("") == '""'


def test_encode_primitive_quotes_numeric_like_string() -> None:
    """A numeric-looking string is quoted to disambiguate it."""
    assert encode_primitive("123") == '"123"'


def test_encode_primitive_quotes_reserved_words() -> None:
    """Strings matching `true`/`false`/`null` are quoted."""
    assert encode_primitive("true") == '"true"'
    assert encode_primitive("null") == '"null"'


def test_encode_primitive_quotes_delimiter() -> None:
    """A string containing a comma is quoted."""
    assert encode_primitive("a,b") == '"a,b"'


def test_encode_primitive_quotes_leading_hyphen() -> None:
    """A string starting with a hyphen is quoted."""
    assert encode_primitive("-x") == '"-x"'


def test_encode_primitive_escapes_special_chars() -> None:
    """Backslashes, quotes and newlines are escaped inside quotes."""
    assert encode_primitive('a"b\\c\nd') == '"a\\"b\\\\c\\nd"'


def test_encode_object() -> None:
    """A flat mapping encodes as one `key: value` line per field."""
    result = encode_object({"name": "rich", "version": "15.0.0"})
    assert result == "name: rich\nversion: 15.0.0"


def test_encode_table() -> None:
    """A uniform row list encodes as a TOON tabular array."""
    rows = [{"name": "rich", "version": "15.0.0"}]
    result = encode_table("packages", rows, ["name", "version"])
    assert result == "packages[1]{name,version}:\n  rich,15.0.0"


def test_encode_table_empty() -> None:
    """An empty row list encodes a zero-length header with no rows."""
    result = encode_table("packages", [], ["name", "version"])
    assert result == "packages[0]{name,version}:"


def test_format_help() -> None:
    """The help footer numbers and indents each suggestion."""
    result = format_help(["do this", "do that"])
    assert result == "help[2]:\n  do this\n  do that"
