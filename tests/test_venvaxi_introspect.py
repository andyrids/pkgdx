"""Unit tests for `pytack.venvaxi._introspect`."""

import importlib
import sys
import types
from collections.abc import Iterator
from pathlib import Path

import pytest

from pytack.exceptions import (
    PackageImportError,
    PackageNotFoundError,
    SymbolNotFoundError,
)
from pytack.venvaxi._introspect import (
    _walk_module,
    find_symbol,
    get_inheritors,
    get_module_tree,
    get_public_api,
    get_symbol,
    show_module,
    truncate,
)
from pytack.venvaxi._store import NodeKind, SymbolStore


@pytest.fixture
def fake_module(
    isolated_venv_axi_cache: Path,
) -> Iterator[types.ModuleType]:
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
    module.VERSION = "1.2.3"  # type: ignore[attr-defined]
    module._hidden = object()  # type: ignore[attr-defined]
    sys.modules[module.__name__] = module
    try:
        yield module
    finally:
        del sys.modules[module.__name__]


@pytest.fixture
def fake_package(
    isolated_venv_axi_cache: Path, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[str]:
    """Registers a real on-disk package with a submodule and a subclass."""
    src_dir = tmp_path_factory.mktemp("venvaxi_fixture_pkg_src")
    package_dir = src_dir / "venvaxi_fixture_pkg"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text(
        '"""Fixture package."""\n\n'
        "class Animal:\n"
        '    """An animal."""\n\n'
        "    def speak(self) -> str:\n"
        '        """Makes a sound."""\n'
        '        return "..."\n\n\n'
        "class Dog(Animal):\n"
        '    """A dog."""\n\n'
        "    def speak(self) -> str:\n"
        '        """Barks."""\n'
        '        return "Woof!"\n'
    )
    (package_dir / "sub.py").write_text(
        '"""A submodule."""\n\n\n'
        "def util() -> str:\n"
        '    """A utility function."""\n'
        '    return "util"\n'
    )
    (package_dir / "broken.py").write_text(
        '"""A submodule that fails to import."""\n\n'
        'raise RuntimeError("Error")\n'
    )
    sys.path.insert(0, str(src_dir))
    try:
        yield "venvaxi_fixture_pkg"
    finally:
        sys.path.remove(str(src_dir))
        for name in list(sys.modules):
            if name.startswith("venvaxi_fixture_pkg"):
                del sys.modules[name]


@pytest.fixture
def fake_module_with_none_module_attr(
    isolated_venv_axi_cache: Path,
) -> Iterator[types.ModuleType]:
    """Registers a module containing a symbol whose `__module__` is `None`.

    NOTE: Sometimes seen with some C-extension/builtin objects.
    """
    module = types.ModuleType("venvaxi_fixture_none_module_mod")

    def unset() -> str:
        """A function whose `__module__` is explicitly unset."""
        return "ok"

    unset.__module__ = None  # type: ignore[assignment]
    module.unset = unset  # type: ignore[attr-defined]
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


def test_show_module_captures_attribute_kind(
    fake_module: types.ModuleType,
) -> None:
    """A public non-callable module member is captured as an
    `ATTRIBUTE` node (previously silently skipped)."""
    _, children = show_module(fake_module.__name__)
    version_node = next(child for child in children if child.name == "VERSION")
    assert version_node.kind is NodeKind.ATTRIBUTE


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
    """`docstring=True` returns the complete, untruncated docstring."""
    symbols = get_public_api(fake_module.__name__, docstring=True)
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


def test_show_module_returns_node_and_children(fake_package: str) -> None:
    """`show_module` returns the package node and its direct children."""
    node, children = show_module(fake_package)
    assert node.kind is NodeKind.PACKAGE
    names = [child.name for child in children]
    assert names == ["Animal", "Dog", "sub"]


def test_show_module_raises_for_unknown_symbol(fake_package: str) -> None:
    """An unknown module name raises `SymbolNotFoundError`."""
    show_module(fake_package)
    with pytest.raises(SymbolNotFoundError):
        show_module(f"{fake_package}.does_not_exist")


def test_walk_module_handles_none_module_attribute(
    fake_module_with_none_module_attr: types.ModuleType,
) -> None:
    """A symbol whose `__module__` is `None` does not crash the walk
    (regression: `SymbolEdge(dst=None, ...)` violated the store's
    NOT NULL constraint) and is not mistaken for a foreign symbol."""
    node, children = show_module(fake_module_with_none_module_attr.__name__)
    assert node.kind is NodeKind.PACKAGE
    assert [child.name for child in children] == ["unset"]


def test_get_symbol_returns_class_node(fake_package: str) -> None:
    """`get_symbol` resolves a fully qualified class name."""
    node = get_symbol(f"{fake_package}::Dog")
    assert node.name == "Dog"
    assert node.kind is NodeKind.CLASS


def test_get_symbol_raises_for_unknown_symbol(fake_package: str) -> None:
    """An unknown qualified name raises `SymbolNotFoundError`."""
    with pytest.raises(SymbolNotFoundError):
        get_symbol(f"{fake_package}::DoesNotExist")


def test_get_inheritors_returns_subclasses(fake_package: str) -> None:
    """`get_inheritors` finds direct subclasses of a base class."""
    inheritors = get_inheritors(f"{fake_package}::Animal")
    names = [node.name for node in inheritors]
    assert names == ["Dog"]


def test_get_module_tree_walks_submodules(fake_package: str) -> None:
    """`get_module_tree` walks the package's nested module hierarchy."""
    pairs = get_module_tree(fake_package)
    depths_and_names = [(depth, node.name) for depth, node in pairs]
    assert (0, fake_package) in depths_and_names
    assert (1, "sub") in depths_and_names


def test_find_symbol_searches_cached_symbols(fake_package: str) -> None:
    """`find_symbol` searches symbols already cached for the project."""
    show_module(fake_package)
    results = find_symbol("Dog")
    names = [node.name for node in results]
    assert "Dog" in names


def test_walk_submodules_skips_import_failure(fake_package: str) -> None:
    """A submodule that raises on import is logged and skipped, and the
    walk continues over the remaining submodules."""
    _, children = show_module(fake_package)
    names = [child.name for child in children]
    assert "sub" in names
    assert "broken" not in names


def test_walk_module_visited_set_prevents_revisit(
    fake_package: str, tmp_path: Path
) -> None:
    """A submodule name already present in `visited` is skipped, even
    though `pkgutil.iter_modules` would otherwise discover it."""
    module = importlib.import_module(fake_package)
    with SymbolStore(tmp_path / "revisit-store.db") as store:
        _walk_module(
            module,
            package_root=fake_package,
            depth=0,
            max_depth=2,
            visited={f"{fake_package}.sub"},
            store=store,
            package=fake_package,
            version="1.0.0",
        )
        children = store.get_children(fake_package)
    assert "sub" not in [child.name for child in children]
