"""Agent eXperience Interface (AXI) Graph-Based Symbol Registry.

Stores a structural graph of introspected Python symbols including; packages,
modules, classes, functions, methods, attributes and their relationships,
into a project-scoped on-disk cache (`pytack.venvaxi._cache`).

NOTE: Adapted from `GraphStore` in `code-review-graph` package, but with a
simplified schema and API surface, since this AXI focuses on installed
packages within a project venv.

Attribution:
    The SQLite Node|Edge graph architecture and recursive AST walking patterns
    used in this module are heavily inspired by `code-review-graph`.

    Repository: https://github.com/tirth8205/code-review-graph
    License: MIT License - Copyright (c) 2026 Tirth Kanani
"""

import logging
import sqlite3
from dataclasses import dataclass
from enum import StrEnum
from importlib import resources
from functools import lru_cache
from pathlib import Path
from types import TracebackType

logger = logging.getLogger(__package__)


class NodeKind(StrEnum):
    """The kind of a `SymbolNode`."""

    PACKAGE = "package"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    ATTRIBUTE = "attribute"


class EdgeKind(StrEnum):
    """The kind of a `SymbolEdge`."""

    EXPORTS = "exports"
    INHERITS = "inherits"
    CONTAINS = "contains"
    IMPORTS_FROM = "imports_from"
    DEPENDS_ON = "depends_on"


@dataclass(frozen=True, slots=True)
class SymbolNode:
    """A single node in the symbol graph."""

    qualified_name: str
    kind: NodeKind
    name: str
    module: str
    signature: str
    doc: str
    package: str
    version: str

    def as_row(self) -> dict[str, str]:
        """Converts this node to a flat, string-valued TOON row.

        Returns:
            A dict keyed by every `SymbolNode` field, suitable for
            `pytack.venvaxi._toon.encode_table` | `encode_object`.
        """
        return {
            "qualified_name": self.qualified_name,
            "kind": str(self.kind),
            "name": self.name,
            "module": self.module,
            "signature": self.signature,
            "doc": self.doc,
            "package": self.package,
            "version": self.version,
        }


@dataclass(frozen=True, slots=True)
class SymbolEdge:
    """A directed edge between two symbol graph nodes."""

    src: str
    dst: str
    kind: EdgeKind


def qualify(module: str, *parts: str) -> str:
    """Builds a qualified symbol name.

    Args:
        module: The owning module's dotted name.
        parts: One or more dotted name components (e.g. class then
            method name).

    Returns:
        A `module::a.b.c` qualified name, or the bare `module` name
        when `parts` is empty (module/package node naming).
    """
    if not parts:
        return module
    return f"{module}::{'.'.join(parts)}"


@lru_cache(maxsize=None)
def _read_sql(filename: str) -> str:
    """Loads & caches SQL queries to prevent disk I/O on every execution."""
    return (resources.files(__package__) / filename).read_text("UTF-8")


class SymbolStore:
    """A SQLite-backed store for a project's introspected symbol graph."""

    def __init__(self, db_path: Path) -> None:
        """Opens (creating if needed) the symbol store database.

        Args:
            db_path: The path to the SQLite database file.
        """
        self._connection = sqlite3.connect(db_path)
        self._connection.row_factory = sqlite3.Row
        self._fts_enabled = True
        self._ensure_schema()

    def __enter__(self) -> "SymbolStore":
        """Returns `self` for use as a context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Closes the underlying database connection."""
        self.close()

    def close(self) -> None:
        """Closes the underlying database connection."""
        self._connection.close()

    def _ensure_schema(self) -> None:
        """Creates the `nodes`/`edges` tables and FTS5 index if missing."""

        self._connection.executescript(_read_sql("schema.sql"))

        try:
            self._connection.executescript(_read_sql("schema_fts5.sql"))
        except sqlite3.OperationalError:
            logger.debug("FTS5 unavailable, falling back to LIKE search")
            self._fts_enabled = False
        self._connection.commit()

    def upsert_node(self, node: SymbolNode) -> None:
        """Inserts or updates a symbol node.

        Args:
            node: The `SymbolNode` to persist.
        """
        self._connection.execute(
            _read_sql("upsert_node.sql"),
            (
                node.qualified_name,
                str(node.kind),
                node.name,
                node.module,
                node.signature,
                node.doc,
                node.package,
                node.version,
            ),
        )
        if self._fts_enabled:
            self._connection.execute(
                "DELETE FROM symbols_fts WHERE qualified_name = ?",
                (node.qualified_name,),
            )
            self._connection.execute(
                "INSERT INTO symbols_fts (qualified_name, name, doc)"
                " VALUES (?, ?, ?)",
                (node.qualified_name, node.name, node.doc),
            )
        self._connection.commit()

    def upsert_edge(self, edge: SymbolEdge) -> None:
        """Inserts an edge, ignoring it if already present.

        Args:
            edge: The `SymbolEdge` to persist.
        """
        self._connection.execute(
            _read_sql("upsert_edge.sql"),
            (edge.src, edge.dst, str(edge.kind)),
        )
        self._connection.commit()

    def _row_to_node(self, row: sqlite3.Row) -> SymbolNode:
        """Maps a raw `nodes` row to a typed `SymbolNode`.

        Args:
            row: A raw `sqlite3.Row` from the `nodes` table.

        Returns:
            The corresponding `SymbolNode`.
        """
        return SymbolNode(
            qualified_name=row["qualified_name"],
            kind=NodeKind(row["kind"]),
            name=row["name"],
            module=row["module"],
            signature=row["signature"],
            doc=row["doc"],
            package=row["package"],
            version=row["version"],
        )

    def get_node(self, qualified_name: str) -> SymbolNode | None:
        """Fetches a single node by qualified name.

        Args:
            qualified_name: The node's qualified name.

        Returns:
            The matching `SymbolNode`, or `None` if not found.
        """
        cursor = self._connection.execute(
            "SELECT * FROM nodes WHERE qualified_name = ?", (qualified_name,)
        )
        row = cursor.fetchone()
        return self._row_to_node(row) if row else None

    def get_children(self, qualified_name: str) -> list[SymbolNode]:
        """Fetches direct `CONTAINS` children of a node.

        Args:
            qualified_name: The parent node's qualified name.

        Returns:
            The child `SymbolNode`s, ordered by name.
        """
        cursor = self._connection.execute(
            _read_sql("get_children.sql"),
            (qualified_name, str(EdgeKind.CONTAINS)),
        )
        return [self._row_to_node(row) for row in cursor.fetchall()]

    def get_inheritors(self, qualified_name: str) -> list[SymbolNode]:
        """Fetches classes that directly inherit from a node.

        Args:
            qualified_name: The base class's qualified name.

        Returns:
            The inheriting `SymbolNode`s, ordered by name.
        """
        cursor = self._connection.execute(
            _read_sql("get_inheritors.sql"),
            (qualified_name, str(EdgeKind.INHERITS)),
        )
        return [self._row_to_node(row) for row in cursor.fetchall()]

    def _collect_module_tree(
        self,
        qualified_name: str,
        depth: int,
        max_depth: int,
        result: list[tuple[int, SymbolNode]],
    ) -> None:
        """Recursively appends `MODULE`/`PACKAGE` descendants to `result`.

        Args:
            qualified_name: The current node's qualified name.
            depth: The current recursion depth.
            max_depth: The maximum recursion depth.
            result: The accumulator list of `(depth, node)` pairs.
        """
        if depth > max_depth:
            return
        for child in self.get_children(qualified_name):
            if child.kind not in (NodeKind.MODULE, NodeKind.PACKAGE):
                continue
            result.append((depth, child))
            self._collect_module_tree(
                child.qualified_name, depth + 1, max_depth, result
            )

    def get_module_tree(
        self, module_name: str, max_depth: int = 2
    ) -> list[tuple[int, SymbolNode]]:
        """Walks the `CONTAINS` module/package hierarchy depth-first.

        Args:
            module_name: The root module's qualified (bare) name.
            max_depth: The maximum recursion depth. Defaults to 2.

        Returns:
            `(depth, node)` pairs in depth-first order, restricted to
            `MODULE`/`PACKAGE` kind nodes. Empty if `module_name` has
            no matching node.
        """
        root = self.get_node(module_name)
        if root is None:
            return []
        result: list[tuple[int, SymbolNode]] = [(0, root)]
        self._collect_module_tree(module_name, 1, max_depth, result)
        return result

    def search_symbols(self, query: str, limit: int = 20) -> list[SymbolNode]:
        """Searches symbols by name|docstring via FTS5 with a `LIKE` fallback.

        Args:
            query: The free-text search query.
            limit: The maximum number of results. Defaults to 20.

        Returns:
            Matching `SymbolNode`s, ranked by relevance (FTS5) or
            qualified name (`LIKE` fallback).
        """
        if self._fts_enabled:
            try:
                cursor = self._connection.execute(
                    _read_sql("search_fts.sql"),
                    (f"{query}*", limit),
                )
                return [self._row_to_node(row) for row in cursor.fetchall()]
            except sqlite3.OperationalError:
                logger.debug("FTS5 query failed (`%s`), using LIKE", query)

        LIKE = f"%{query}%"
        cursor = self._connection.execute(
            _read_sql("search_like.sql"),
            (LIKE, LIKE, limit),
        )
        return [self._row_to_node(row) for row in cursor.fetchall()]

    def clear_package(self, package: str) -> None:
        """Deletes all nodes|edges belonging to a package.

        NOTE: Avoids Python-to-C context switching and N+1 query problem with
        sub-queries.

        Args:
            package: The package (distribution|import) name to clear.
        """
        # Clear the FTS Index (if enabled)
        if self._fts_enabled:
            self._connection.execute(
                "DELETE FROM symbols_fts WHERE qualified_name IN "
                "(SELECT qualified_name FROM nodes WHERE package = ?)",
                (package,),
            )

        # Clear the Edges
        self._connection.execute(
            "DELETE FROM edges WHERE "
            "src IN (SELECT qualified_name FROM nodes WHERE package = ?) OR "
            "dst IN (SELECT qualified_name FROM nodes WHERE package = ?)",
            (package, package),
        )

        # Clear the Nodes (MUST occur last)
        self._connection.execute(
            "DELETE FROM nodes WHERE package = ?", (package,)
        )
        self._connection.commit()
