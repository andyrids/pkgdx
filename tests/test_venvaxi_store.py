"""Unit tests for `pytack.venvaxi._store`."""

from pathlib import Path

from pytack.venvaxi._store import (
    EdgeKind,
    NodeKind,
    SymbolEdge,
    SymbolNode,
    SymbolStore,
    qualify,
)


def _node(
    qualified_name: str,
    kind: NodeKind,
    name: str,
    *,
    module: str = "pkg",
    package: str = "pkg",
    version: str = "1.0.0",
) -> SymbolNode:
    """Builds a `SymbolNode` with sensible test defaults."""
    return SymbolNode(
        qualified_name=qualified_name,
        kind=kind,
        name=name,
        module=module,
        signature="",
        doc="",
        package=package,
        version=version,
    )


def test_qualify_module_only() -> None:
    """A bare module name is returned unchanged when no parts given."""
    assert qualify("pkg.mod") == "pkg.mod"


def test_qualify_with_parts() -> None:
    """Extra parts are dot-joined after a `::` separator."""
    assert qualify("pkg.mod", "Foo", "bar") == "pkg.mod::Foo.bar"


def test_upsert_and_get_node(tmp_path: Path) -> None:
    """A node can be inserted and fetched back by qualified name."""
    with SymbolStore(tmp_path / "store.db") as store:
        store.upsert_node(_node("pkg", NodeKind.PACKAGE, "pkg"))
        node = store.get_node("pkg")
    assert node is not None
    assert node.kind is NodeKind.PACKAGE


def test_get_node_missing_returns_none(tmp_path: Path) -> None:
    """A missing qualified name returns `None`."""
    with SymbolStore(tmp_path / "store.db") as store:
        assert store.get_node("does.not.exist") is None


def test_upsert_node_overwrites_existing(tmp_path: Path) -> None:
    """Re-upserting the same qualified name updates the stored fields."""
    with SymbolStore(tmp_path / "store.db") as store:
        store.upsert_node(
            _node("pkg", NodeKind.PACKAGE, "pkg", version="1.0.0")
        )
        store.upsert_node(
            _node("pkg", NodeKind.PACKAGE, "pkg", version="2.0.0")
        )
        node = store.get_node("pkg")
    assert node is not None
    assert node.version == "2.0.0"


def test_get_children_returns_contains_edges_only(tmp_path: Path) -> None:
    """Only `CONTAINS`-linked nodes are returned as children."""
    with SymbolStore(tmp_path / "store.db") as store:
        store.upsert_node(_node("pkg", NodeKind.PACKAGE, "pkg"))
        store.upsert_node(_node("pkg::Foo", NodeKind.CLASS, "Foo"))
        store.upsert_node(_node("pkg::Bar", NodeKind.FUNCTION, "Bar"))
        store.upsert_edge(
            SymbolEdge(src="pkg", dst="pkg::Foo", kind=EdgeKind.CONTAINS)
        )
        store.upsert_edge(
            SymbolEdge(src="pkg", dst="pkg::Bar", kind=EdgeKind.CONTAINS)
        )
        store.upsert_edge(
            SymbolEdge(src="pkg", dst="pkg::Bar", kind=EdgeKind.EXPORTS)
        )
        children = store.get_children("pkg")
    assert [node.name for node in children] == ["Bar", "Foo"]


def test_get_inheritors(tmp_path: Path) -> None:
    """Direct subclasses are found via `INHERITS` edges."""
    with SymbolStore(tmp_path / "store.db") as store:
        store.upsert_node(_node("pkg::Animal", NodeKind.CLASS, "Animal"))
        store.upsert_node(_node("pkg::Dog", NodeKind.CLASS, "Dog"))
        store.upsert_edge(
            SymbolEdge(
                src="pkg::Dog", dst="pkg::Animal", kind=EdgeKind.INHERITS
            )
        )
        inheritors = store.get_inheritors("pkg::Animal")
    assert [node.name for node in inheritors] == ["Dog"]


def test_get_module_tree(tmp_path: Path) -> None:
    """The module tree walks `CONTAINS` edges restricted to modules."""
    with SymbolStore(tmp_path / "store.db") as store:
        store.upsert_node(_node("pkg", NodeKind.PACKAGE, "pkg"))
        store.upsert_node(
            _node("pkg.sub", NodeKind.MODULE, "sub", module="pkg")
        )
        store.upsert_node(_node("pkg::Foo", NodeKind.CLASS, "Foo"))
        store.upsert_edge(
            SymbolEdge(src="pkg", dst="pkg.sub", kind=EdgeKind.CONTAINS)
        )
        store.upsert_edge(
            SymbolEdge(src="pkg", dst="pkg::Foo", kind=EdgeKind.CONTAINS)
        )
        pairs = store.get_module_tree("pkg")
    assert [(depth, node.name) for depth, node in pairs] == [
        (0, "pkg"),
        (1, "sub"),
    ]


def test_get_module_tree_missing_root_returns_empty(tmp_path: Path) -> None:
    """An unknown root module returns an empty tree."""
    with SymbolStore(tmp_path / "store.db") as store:
        assert store.get_module_tree("does.not.exist") == []


def test_search_symbols_matches_name(tmp_path: Path) -> None:
    """`search_symbols` finds nodes by name/doc substring."""
    with SymbolStore(tmp_path / "store.db") as store:
        store.upsert_node(_node("pkg::Dog", NodeKind.CLASS, "Dog"))
        store.upsert_node(_node("pkg::Cat", NodeKind.CLASS, "Cat"))
        results = store.search_symbols("Dog")
    assert [node.name for node in results] == ["Dog"]


def test_search_symbols_respects_limit(tmp_path: Path) -> None:
    """`search_symbols` never returns more than `limit` results."""
    with SymbolStore(tmp_path / "store.db") as store:
        for index in range(5):
            store.upsert_node(
                _node(f"pkg::Sym{index}", NodeKind.FUNCTION, f"Sym{index}")
            )
        results = store.search_symbols("Sym", limit=2)
    assert len(results) == 2


def test_search_symbols_like_fallback_when_fts_disabled(
    tmp_path: Path,
) -> None:
    """When FTS5 is unavailable, `search_symbols` still finds matches
    via the `LIKE` fallback path."""
    with SymbolStore(tmp_path / "store.db") as store:
        store._fts_enabled = False
        store.upsert_node(_node("pkg::Dog", NodeKind.CLASS, "Dog"))
        store.upsert_node(_node("pkg::Cat", NodeKind.CLASS, "Cat"))
        results = store.search_symbols("Dog")
    assert [node.name for node in results] == ["Dog"]


def test_clear_package_removes_nodes_and_edges(tmp_path: Path) -> None:
    """`clear_package` deletes all of a package's nodes and edges."""
    with SymbolStore(tmp_path / "store.db") as store:
        store.upsert_node(_node("pkg", NodeKind.PACKAGE, "pkg"))
        store.upsert_node(_node("pkg::Foo", NodeKind.CLASS, "Foo"))
        store.upsert_edge(
            SymbolEdge(src="pkg", dst="pkg::Foo", kind=EdgeKind.CONTAINS)
        )
        store.clear_package("pkg")
        assert store.get_node("pkg") is None
        assert store.get_children("pkg") == []


def test_as_row_contains_all_fields() -> None:
    """`SymbolNode.as_row` exposes every field as a plain string."""
    node = _node("pkg::Foo", NodeKind.CLASS, "Foo")
    row = node.as_row()
    assert row["qualified_name"] == "pkg::Foo"
    assert row["kind"] == "class"
    assert row["name"] == "Foo"
