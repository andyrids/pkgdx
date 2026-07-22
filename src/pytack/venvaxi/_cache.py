"""Project-scoped, version-keyed on-disk cache for `venv-axi`'s store.

Cache invalidation is version-hash based (compare the stored `PACKAGE`
node's version against the currently installed distribution version) -
NOT file-hash/incremental-parse based, since `venv-axi` never parses the
consuming repo's own source files, only already-installed package
metadata.
"""

import hashlib
import importlib
import inspect
import logging
import sqlite3
from importlib import metadata
from pathlib import Path

from pytack import exceptions
from pytack.venvaxi import _introspect
from pytack.venvaxi._store import NodeKind, SymbolNode, SymbolStore

logger = logging.getLogger(__package__)


def get_cache_dir() -> Path:
    """Returns (creating if needed) the `venv-axi` cache directory.

    Returns:
        `~/.pytack/venv-axi/`.
    """
    cache_dir = Path.home() / ".pytack" / "venv-axi"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _project_hash(root: Path) -> str:
    """Computes a short, stable hash for a project root path.

    Args:
        root: The project root directory.

    Returns:
        A 16-character hex digest of the resolved root path.
    """
    return hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:16]


def get_cache_db_path(root: Path) -> Path:
    """Returns the cache database path for a given project root.

    Args:
        root: The project root directory.

    Returns:
        The project-scoped `SymbolStore` SQLite database path.
    """
    return get_cache_dir() / f"{_project_hash(root)}.db"


def _installed_version(package_name: str) -> str:
    """Resolves an installed distribution's version, if any.

    Args:
        package_name: The import (or distribution) name to resolve.

    Returns:
        The installed version string, or `""` if it cannot be
        determined (e.g. not an installed distribution).
    """
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return ""


def is_cache_valid(
    store: SymbolStore, package: str, installed_version: str
) -> bool:
    """Checks whether a package's cached symbols are still current.

    Args:
        store: The `SymbolStore` to check.
        package: The package (import) name.
        installed_version: The currently installed version string.

    Returns:
        True if a `PACKAGE` node exists for `package` and its stored
        version matches `installed_version`.
    """
    node = store.get_node(package)
    return node is not None and node.version == installed_version


def get_or_build_store(
    root: Path,
    package_name: str,
    *,
    max_depth: int = _introspect.DEFAULT_MAX_DEPTH,
    force_refresh: bool = False,
) -> SymbolStore:
    """Fetches (rebuilding if stale) a project's cached `SymbolStore`.

    Args:
        root: The consuming project's root directory.
        package_name: The import name of the package to introspect.
        max_depth: The maximum submodule recursion depth. Defaults to
            `_introspect.DEFAULT_MAX_DEPTH`.
        force_refresh: Rebuild even if the cache is still valid.
            Defaults to False.

    Returns:
        A `SymbolStore` open on the project's cache database, populated
        with `package_name`'s symbol graph. Callers are responsible for
        calling `.close()` (or using it as a context manager).
    """
    store = SymbolStore(get_cache_db_path(root))
    installed_version = _installed_version(package_name)
    if not force_refresh and is_cache_valid(
        store, package_name, installed_version
    ):
        return store

    module = importlib.import_module(package_name)
    store.clear_package(package_name)
    try:
        store.upsert_node(
            SymbolNode(
                qualified_name=package_name,
                kind=NodeKind.PACKAGE,
                name=package_name,
                module=package_name,
                signature="",
                doc=inspect.getdoc(module) or "",
                package=package_name,
                version=installed_version,
            )
        )
        _introspect._walk_module(
            module,
            package_root=package_name,
            depth=0,
            max_depth=max_depth,
            visited=set(),
            store=store,
            package=package_name,
            version=installed_version,
        )
    except sqlite3.DatabaseError as err:
        store.clear_package(package_name)
        msg = f"Failed to build symbol store for {package_name!r}"
        raise exceptions.StoreError(msg) from err
    return store
