"""Lazy FastMCP server exposing `venv-axi` data as MCP tools."""

import logging
from dataclasses import asdict
from typing import Any

from pytack.__main__ import get_project_root
from pytack.venvaxi._introspect import get_public_api
from pytack.venvaxi._packages import list_packages, resolve_package
from pytack.venvaxi._toon import encode_object, encode_table

logger = logging.getLogger(__package__)


def build_server() -> Any:
    """Builds the `venv-axi` FastMCP server instance.

    Raises:
        ImportError: If `fastmcp` is not installed (requires the
            `pytack[venv-axi]` extra).

    Returns:
        A configured `FastMCP` server exposing package listing,
        metadata and public-API tools.
    """
    from fastmcp import FastMCP

    server = FastMCP("venv-axi")

    @server.tool
    def list_packages_tool(include_dev: bool = False) -> str:
        """Lists the consuming repo's venv packages in TOON format."""
        root = get_project_root()
        packages = list_packages(root, include_dev=include_dev)
        if not packages:
            return "count: 0"
        rows = [asdict(package) for package in packages]
        table = encode_table("packages", rows, ["name", "version"])
        return f"count: {len(packages)}\n{table}"

    @server.tool
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

    @server.tool
    def show_package_api_tool(name: str, full: bool = False) -> str:
        """Shows a package's public, top-level API symbols in TOON."""
        symbols = get_public_api(name, full=full)
        if not symbols:
            return "count: 0"
        rows = [asdict(symbol) for symbol in symbols]
        table = encode_table(
            "symbols", rows, ["name", "kind", "signature", "doc"]
        )
        return f"count: {len(symbols)}\n{table}"

    return server


def serve() -> None:
    """Starts the `venv-axi` MCP server over stdio."""
    build_server().run()
