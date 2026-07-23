"""Lazy FastMCP server exposing `venv-axi` data as MCP tools."""

import logging
from dataclasses import asdict
from typing import Any

from pytack._core import get_project_root
from pytack.venvaxi._introspect import (
    find_symbol,
    get_inheritors,
    get_module_tree,
    get_public_api,
    get_symbol,
    show_module,
)
from pytack.venvaxi._packages import list_packages, resolve_package
from pytack.venvaxi._toon import encode_object, encode_table

logger = logging.getLogger(__package__)


def list_packages_tool(include_dev: bool = False) -> str:
    """Lists the consuming repo's venv packages in TOON format."""
    root = get_project_root()
    packages = list_packages(root, include_dev=include_dev)
    if not packages:
        return "count: 0"
    rows = [asdict(package) for package in packages]
    table = encode_table("packages", rows, ["name", "version"])
    return f"count: {len(packages)}\n{table}"


def show_package_tool(name: str) -> str:
    """Shows a single package's metadata in TOON format."""
    package = resolve_package(name)
    return encode_object(
        {
            "name": package.name,
            "version": package.version,
            "location": package.location,
        }
    )


def show_package_api_tool(name: str, full: bool = False) -> str:
    """Shows a package's public, top-level API symbols in TOON."""
    symbols = get_public_api(name, docstring=full)
    if not symbols:
        return "count: 0"
    rows = [asdict(symbol) for symbol in symbols]
    table = encode_table("symbols", rows, ["name", "kind", "signature", "doc"])
    return f"count: {len(symbols)}\n{table}"


def show_module_tool(name: str) -> str:
    """Shows a module/package node and its direct children in TOON."""
    node, children = show_module(name)
    header = encode_object(
        {
            "qualified_name": node.qualified_name,
            "kind": str(node.kind),
            "doc": node.doc,
        }
    )
    if not children:
        return f"{header}\nchildren count: 0"
    rows = [child.as_row() for child in children]
    table = encode_table(
        "children", rows, ["name", "kind", "signature", "doc"]
    )
    return f"{header}\nchildren count: {len(children)}\n{table}"


def get_symbol_tool(qualified_name: str) -> str:
    """Shows a single symbol's full detail in TOON format."""
    node = get_symbol(qualified_name)
    return encode_object(
        {
            "qualified_name": node.qualified_name,
            "kind": str(node.kind),
            "signature": node.signature,
            "doc": node.doc,
        }
    )


def find_symbol_tool(query: str, limit: int = 20) -> str:
    """Searches cached symbols by name/doc text, returned as TOON."""
    nodes = find_symbol(query, limit)
    if not nodes:
        return "count: 0"
    rows = [node.as_row() for node in nodes]
    table = encode_table("symbols", rows, ["name", "kind", "qualified_name"])
    return f"count: {len(nodes)}\n{table}"


def get_inheritors_tool(qualified_name: str) -> str:
    """Shows classes that directly inherit from a class, in TOON."""
    nodes = get_inheritors(qualified_name)
    if not nodes:
        return "count: 0"
    rows = [node.as_row() for node in nodes]
    table = encode_table(
        "inheritors", rows, ["name", "kind", "qualified_name"]
    )
    return f"count: {len(nodes)}\n{table}"


def get_module_tree_tool(name: str, max_depth: int = 2) -> str:
    """Shows a module/package's nested module tree, in TOON."""
    pairs = get_module_tree(name, max_depth)
    if not pairs:
        return "count: 0"
    rows = [{"depth": depth, **node.as_row()} for depth, node in pairs]
    table = encode_table("tree", rows, ["depth", "qualified_name", "kind"])
    return f"count: {len(pairs)}\n{table}"


_TOOLS = (
    list_packages_tool,
    show_package_tool,
    show_package_api_tool,
    show_module_tool,
    get_symbol_tool,
    find_symbol_tool,
    get_inheritors_tool,
    get_module_tree_tool,
)


def build_server() -> Any:
    """Builds the `venv-axi` FastMCP server instance.

    Raises:
        ImportError: If `fastmcp` is not installed (requires the
            `pytack[venv-axi]` extra).

    Returns:
        A configured `FastMCP` server exposing package listing,
        metadata, symbol-graph and public-API tools.
    """
    from fastmcp import FastMCP

    server = FastMCP("venv-axi")
    for tool_fn in _TOOLS:
        server.tool(tool_fn)
    return server


def serve() -> None:
    """Starts the `venv-axi` MCP server over stdio."""
    build_server().run()
