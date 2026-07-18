"""Unit tests for `pytack.venvaxi._introspect`."""

import sys
import types
from collections.abc import Iterator

import pytest

from pytack.exceptions import PackageImportError, PackageNotFoundError
from pytack.venvaxi._introspect import get_public_api, truncate


@pytest.fixture
def fake_module() -> Iterator[types.ModuleType]:
    """Registers a throwaway module for API-introspection tests."""
    module = types.ModuleType("venvaxi_fixture_mod")

    def greet(name: str) -> str:
        """Greets someone.

        Returns a friendly greeting for the given name.
        """
        return f"hello {name}"

    class Greeter:
        """Greets people repeatedly."""

    module.greet = greet  # type: ignore[attr-defined]
    module.Greeter = Greeter  # type: ignore[attr-defined]
    module._hidden = object()  # type: ignore[attr-defined]
    sys.modules[module.__name__] = module
    try:
        yield module
    finally:
        del sys.modules[module.__name__]


def test_truncate_short_text_unchanged() -> None:
    """Text at or under the limit is returned unchanged."""
    assert truncate("short", limit=10) == "short"


def test_truncate_long_text_appends_hint() -> None:
    """Text over the limit is cut and a size hint is appended."""
    result = truncate("x" * 20, limit=5)
    assert result.startswith("xxxxx... truncated, 20 chars total")
    assert "use --full to see complete body" in result


def test_get_public_api_filters_private_and_non_callables(
    fake_module: types.ModuleType,
) -> None:
    """Only public functions/classes are surfaced, sorted by name."""
    symbols = get_public_api(fake_module.__name__)
    names = [symbol.name for symbol in symbols]
    assert names == ["Greeter", "greet"]


def test_get_public_api_truncates_doc_by_default(
    fake_module: types.ModuleType,
) -> None:
    """The docstring's first line is used, truncated by default."""
    symbols = get_public_api(fake_module.__name__)
    greet = next(symbol for symbol in symbols if symbol.name == "greet")
    assert greet.doc == "Greets someone."
    assert greet.kind == "function"
    assert greet.signature == "(name: str) -> str"


def test_get_public_api_full_returns_complete_docstring(
    fake_module: types.ModuleType,
) -> None:
    """`full=True` returns the complete, untruncated docstring."""
    symbols = get_public_api(fake_module.__name__, full=True)
    greet = next(symbol for symbol in symbols if symbol.name == "greet")
    assert "friendly greeting" in greet.doc


def test_get_public_api_invalid_name_raises() -> None:
    """An invalid package name raises `PackageNotFoundError`."""
    with pytest.raises(PackageNotFoundError):
        get_public_api("../etc/passwd")


def test_get_public_api_import_error_raises() -> None:
    """A non-importable package raises `PackageImportError`."""
    with pytest.raises(PackageImportError):
        get_public_api("this-package-does-not-exist-xyz")
