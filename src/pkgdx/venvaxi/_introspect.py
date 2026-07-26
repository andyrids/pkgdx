"""Agent eXperience Interface (AXI) API and symbol-graph introspection.

Attribution:
    The recursive AST walking patterns used in this module are heavily
    inspired by `code-review-graph`.

    Repository: https://github.com/tirth8205/code-review-graph
    License: MIT License - Copyright (c) 2026 Tirth Kanani
"""

import importlib
import inspect
import logging
import pkgutil
import re
from dataclasses import dataclass
from importlib import metadata
from types import ModuleType
from typing import Any

from pkgdx.exceptions import (
    PackageImportError,
    PackageNotFoundError,
    SymbolNotFoundError,
)
from pkgdx.venvaxi._store import (
    EdgeKind,
    NodeKind,
    SymbolEdge,
    SymbolNode,
    SymbolStore,
    qualify,
)

logger = logging.getLogger(__package__)

_VALID_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
DEFAULT_TRUNCATE_LIMIT = 200
DEFAULT_MAX_DEPTH = 2


@dataclass(frozen=True, slots=True)
class SymbolInfo:
    """A single public, top-level API symbol."""

    name: str
    kind: str
    signature: str
    doc: str


def truncate(text: str, limit: int = DEFAULT_TRUNCATE_LIMIT) -> str:
    """Truncates text to a set number of characters determined by `limit`.

    NOTE: AXI principle 3 (content truncation with size hints).

    Args:
        text: The text to truncate.
        limit: Maximum number of characters to keep. Defaults to 200.

    Returns:
        `text` unchanged or truncated with an appended size hint.
    """
    if len(text) <= limit:
        return text

    return (
        f"{text[:limit]}... truncated, {len(text)} chars total"
        " - use --full to see complete body"
    )


def _resolve_import_name(name: str) -> str:
    """Resolves import slugs from distribution names.

    Args:
        name: The distribution (package) name.

    Returns:
        The best-effort importable top-level module name.
    """
    normalized = name.lower().replace("-", "_")
    mapping = metadata.packages_distributions()
    for import_name, dist_names in mapping.items():
        for dist_name in dist_names:
            if dist_name.lower().replace("-", "_") == normalized:
                return import_name
    return normalized


def _signature_of(obj: Any) -> str:
    """Best-effort `inspect.signature` string for a callable.

    Args:
        obj: The object to inspect.

    Returns:
        The signature string, or `"(...)"` if it cannot be determined.
    """
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "(...)"


def _classify(obj: Any) -> NodeKind:
    """Classifies a module-level member as a class/function/attribute.

    Args:
        obj: The object to classify.

    Returns:
        The matching `NodeKind`.
    """
    if inspect.isclass(obj):
        return NodeKind.CLASS
    if inspect.isroutine(obj):
        return NodeKind.FUNCTION
    return NodeKind.ATTRIBUTE


def _walk_class_members(
    cls: type, *, store: SymbolStore, package: str, version: str
) -> None:
    """Walks a class's public members into `CONTAINS`/`INHERITS` edges.

    Args:
        cls: The class to walk.
        store: The `SymbolStore` to populate.
        package: The owning package (distribution/import) name.
        version: The owning package's installed version.
    """
    class_qualified_name = qualify(cls.__module__, cls.__name__)
    for member_name, member in inspect.getmembers(cls):
        if member_name.startswith("_"):
            continue
        kind = (
            NodeKind.METHOD
            if inspect.isroutine(member)
            else NodeKind.ATTRIBUTE
        )
        member_qualified_name = qualify(
            cls.__module__, cls.__name__, member_name
        )
        store.upsert_node(
            SymbolNode(
                qualified_name=member_qualified_name,
                kind=kind,
                name=member_name,
                module=cls.__module__,
                signature=_signature_of(member)
                if kind is NodeKind.METHOD
                else "",
                doc=inspect.getdoc(member) or "",
                package=package,
                version=version,
            )
        )
        store.upsert_edge(
            SymbolEdge(
                src=class_qualified_name,
                dst=member_qualified_name,
                kind=EdgeKind.CONTAINS,
            )
        )
    for base in cls.__bases__:
        if base is object:
            continue
        base_qualified_name = qualify(base.__module__, base.__name__)
        store.upsert_edge(
            SymbolEdge(
                src=class_qualified_name,
                dst=base_qualified_name,
                kind=EdgeKind.INHERITS,
            )
        )


def _record_symbol(
    module: ModuleType,
    symbol_name: str,
    obj: Any,
    *,
    store: SymbolStore,
    package: str,
    version: str,
) -> NodeKind:
    """Upserts a single module-level symbol node plus its edges.

    Args:
        module: The owning module.
        symbol_name: The symbol's bare name within `module`.
        obj: The symbol object.
        store: The `SymbolStore` to populate.
        package: The owning package (distribution/import) name.
        version: The owning package's installed version.

    Returns:
        The symbol's classified `NodeKind` (so callers can decide
        whether to recurse into class members).
    """
    kind = _classify(obj)
    symbol_qualified_name = qualify(module.__name__, symbol_name)
    signature = (
        _signature_of(obj)
        if kind in (NodeKind.CLASS, NodeKind.FUNCTION)
        else ""
    )
    store.upsert_node(
        SymbolNode(
            qualified_name=symbol_qualified_name,
            kind=kind,
            name=symbol_name,
            module=module.__name__,
            signature=signature,
            doc=inspect.getdoc(obj) or "",
            package=package,
            version=version,
        )
    )
    store.upsert_edge(
        SymbolEdge(
            src=module.__name__,
            dst=symbol_qualified_name,
            kind=EdgeKind.CONTAINS,
        )
    )

    obj_home_module = getattr(obj, "__module__", None) or module.__name__
    if obj_home_module != module.__name__:
        store.upsert_edge(
            SymbolEdge(
                src=module.__name__,
                dst=symbol_qualified_name,
                kind=EdgeKind.EXPORTS,
            )
        )
        store.upsert_edge(
            SymbolEdge(
                src=module.__name__,
                dst=obj_home_module,
                kind=EdgeKind.IMPORTS_FROM,
            )
        )
    return kind


def _walk_submodules(
    module: ModuleType,
    *,
    package_root: str,
    depth: int,
    max_depth: int,
    visited: set[str],
    store: SymbolStore,
    package: str,
    version: str,
) -> None:
    """Discovers and recursively walks a package's direct submodules.

    Args:
        module: The parent package module.
        package_root: The top-level import name recursion must stay
            within (prevents escaping into unrelated re-exported deps).
        depth: The current recursion depth.
        max_depth: The maximum recursion depth.
        visited: Module names already visited (cycle/re-import guard).
        store: The `SymbolStore` to populate.
        package: The owning package (distribution/import) name.
        version: The owning package's installed version.
    """
    if not hasattr(module, "__path__") or depth >= max_depth:
        return

    for _, subname, _ in pkgutil.iter_modules(
        module.__path__, prefix=f"{module.__name__}."
    ):
        if subname.rsplit(".", 1)[-1].startswith("_") or subname in visited:
            continue
        try:
            submodule = importlib.import_module(subname)
        except Exception as err:
            # NOTE: Broad on purpose - importing third-party submodules
            # runs arbitrary module-level code, which can raise anything
            # (RuntimeError, OSError, ...); one bad submodule must not
            # abort the whole walk.
            logger.warning(
                "Skipping submodule `%s` (import failed: %s)", subname, err
            )
            continue
        if not submodule.__name__.startswith(package_root):
            continue

        visited.add(subname)
        store.upsert_node(
            SymbolNode(
                qualified_name=submodule.__name__,
                kind=NodeKind.MODULE,
                name=submodule.__name__.rsplit(".", 1)[-1],
                module=module.__name__,
                signature="",
                doc=inspect.getdoc(submodule) or "",
                package=package,
                version=version,
            )
        )
        store.upsert_edge(
            SymbolEdge(
                src=module.__name__,
                dst=submodule.__name__,
                kind=EdgeKind.CONTAINS,
            )
        )
        _walk_module(
            submodule,
            package_root=package_root,
            depth=depth + 1,
            max_depth=max_depth,
            visited=visited,
            store=store,
            package=package,
            version=version,
        )


def _walk_module(
    module: ModuleType,
    *,
    package_root: str,
    depth: int,
    max_depth: int,
    visited: set[str],
    store: SymbolStore,
    package: str,
    version: str,
) -> None:
    """Recursively walks a module's public API into the symbol store.

    Args:
        module: The module to walk.
        package_root: The top-level import name recursion must stay
            within (prevents escaping into unrelated re-exported deps).
        depth: The current recursion depth.
        max_depth: The maximum recursion depth for submodules.
        visited: Module names already visited (cycle/re-import guard).
        store: The `SymbolStore` to populate.
        package: The owning package (distribution/import) name.
        version: The owning package's installed version.
    """
    public_names = list(
        getattr(module, "__all__", None)
        or [n for n in dir(module) if not n.startswith("_")]
    )
    for symbol_name in sorted(public_names):
        obj: Any = getattr(module, symbol_name, None)
        kind = _record_symbol(
            module,
            symbol_name,
            obj,
            store=store,
            package=package,
            version=version,
        )
        if kind is NodeKind.CLASS:
            _walk_class_members(
                obj, store=store, package=package, version=version
            )

    _walk_submodules(
        module,
        package_root=package_root,
        depth=depth,
        max_depth=max_depth,
        visited=visited,
        store=store,
        package=package,
        version=version,
    )


def _top_level_root(name: str) -> str:
    """Extracts the top-level package/module name from any identifier.

    Args:
        name: A bare module name (`"rich"`), dotted module name
            (`"rich.table"`), or fully qualified symbol name
            (`"rich.table::Table.add_row"`).

    Returns:
        The top-level (first dotted) component, e.g. `"rich"`.
    """
    module_part = name.split("::", 1)[0]
    return module_part.split(".", 1)[0]


def _build_store_for(
    name: str, *, max_depth: int = DEFAULT_MAX_DEPTH
) -> SymbolStore:
    """Builds/fetches the cached store owning `name`'s top-level package.

    Args:
        name: A bare module name, dotted module name, or fully
            qualified symbol name.
        max_depth: The maximum submodule recursion depth to build (if
            a rebuild is required). Defaults to `DEFAULT_MAX_DEPTH`.

    Returns:
        An open `SymbolStore`, populated with the resolved top-level
        package's symbol graph. Callers must `.close()` it.
    """
    from pkgdx._core import get_project_root
    from pkgdx.venvaxi import _cache

    root_package = _resolve_import_name(_top_level_root(name))
    return _cache.get_or_build_store(
        get_project_root(), root_package, max_depth=max_depth
    )


def show_module(name: str) -> tuple[SymbolNode, list[SymbolNode]]:
    """Shows a module/package node and its direct children.

    Args:
        name: The module's bare or dotted import name.

    Raises:
        SymbolNotFoundError: If `name` has no matching node.

    Returns:
        The module's `SymbolNode` and its direct `CONTAINS` children.
    """
    with _build_store_for(name) as store:
        node = store.get_node(name)
        if node is None:
            msg = f"Module `{name}` not found"
            raise SymbolNotFoundError(msg)
        return node, store.get_children(name)


def get_symbol(qualified_name: str) -> SymbolNode:
    """Fetches a single symbol node by its qualified name.

    Args:
        qualified_name: The fully qualified symbol name.

    Raises:
        SymbolNotFoundError: If no matching node exists.

    Returns:
        The matching `SymbolNode`.
    """
    with _build_store_for(qualified_name) as store:
        node = store.get_node(qualified_name)
        if node is None:
            msg = f"Symbol `{qualified_name}` not found"
            raise SymbolNotFoundError(msg)
        return node


def get_inheritors(qualified_name: str) -> list[SymbolNode]:
    """Fetches classes that directly inherit from a class.

    Args:
        qualified_name: The base class's qualified name.

    Returns:
        The inheriting `SymbolNode`s.
    """
    with _build_store_for(qualified_name) as store:
        return store.get_inheritors(qualified_name)


def get_module_tree(
    name: str, max_depth: int = DEFAULT_MAX_DEPTH
) -> list[tuple[int, SymbolNode]]:
    """Fetches a module/package's nested module tree.

    Args:
        name: The module's bare or dotted import name.
        max_depth: The maximum recursion depth. Defaults to
            `DEFAULT_MAX_DEPTH`.

    Returns:
        `(depth, node)` pairs in depth-first order.
    """
    with _build_store_for(name, max_depth=max_depth) as store:
        return store.get_module_tree(name, max_depth)


def find_symbol(query: str, limit: int = 20) -> list[SymbolNode]:
    """Searches the project's already-cached symbols by name/doc text.

    NOTE: Searches whatever has already been cached via prior
    `show_module`/`get_module_tree`/`get_public_api` calls for this
    project - it does not proactively introspect every installed
    dependency (that would be slow and import packages the caller
    never asked about).

    Args:
        query: The free-text search query.
        limit: The maximum number of results. Defaults to 20.

    Returns:
        Matching `SymbolNode`s.
    """
    from pkgdx._core import get_project_root
    from pkgdx.venvaxi._cache import get_cache_db_path

    with SymbolStore(get_cache_db_path(get_project_root())) as store:
        return store.search_symbols(query, limit)


def get_public_api(
    name: str,
    *,
    docstring: bool = False,
    limit: int = DEFAULT_TRUNCATE_LIMIT,
) -> list[SymbolInfo]:
    """Extracts top-level public functions & classes from a package.

    NOTE: Compatibility shim over the `SymbolStore`-backed introspection
    engine - preserves the original flat, class/function-only contract.

    Args:
        name: The package (distribution) name.
        docstring: Return complete docstrings instead of the truncated
            first line. Defaults to False.
        limit: The docstring truncation limit. Defaults to 200.

    Raises:
        PackageNotFoundError: On `name` containing invalid characters.
        PackageImportError: On resolved module import error.

    Returns:
        Public top-level symbols, with their kind, signature and
        docstring.
    """
    if not _VALID_NAME_RE.match(name):
        msg = f"Invalid package name `{name}`"
        raise PackageNotFoundError(msg)

    import_name = _resolve_import_name(name)
    try:
        importlib.import_module(import_name)
    except ImportError as err:
        msg = f"Failed to import `{import_name}` (from `{name}`)"
        raise PackageImportError(msg) from err

    with _build_store_for(name) as store:
        children = store.get_children(import_name)

    symbols: list[SymbolInfo] = []
    for node in children:
        if node.kind not in (NodeKind.CLASS, NodeKind.FUNCTION):
            continue
        doc = node.doc
        if docstring:
            doc_field = doc
        else:
            first_line = doc.splitlines()[0] if doc else ""
            doc_field = truncate(first_line, limit)
        symbols.append(
            SymbolInfo(
                name=node.name,
                kind=str(node.kind),
                signature=node.signature,
                doc=doc_field,
            )
        )
    return sorted(symbols, key=lambda symbol: symbol.name)
