"""Unit tests for `pytack.venvaxi._mcp`."""

import asyncio
from pathlib import Path
from unittest import mock

import pytest

pytest.importorskip("fastmcp")

from pytack.venvaxi._introspect import SymbolInfo  # noqa: E402
from pytack.venvaxi._mcp import build_server  # noqa: E402
from pytack.venvaxi._packages import PackageInfo  # noqa: E402

MCP = "pytack.venvaxi._mcp"


def test_build_server_registers_tools() -> None:
    """`build_server` registers the three expected MCP tools."""
    server = build_server()
    tools = asyncio.run(server.list_tools())
    names = {tool.name for tool in tools}
    assert names == {
        "list_packages_tool",
        "show_package_tool",
        "show_package_api_tool",
    }


def test_list_packages_tool_returns_toon(tmp_path: Path) -> None:
    """The list tool returns a TOON-encoded package table."""
    server = build_server()
    packages = [
        PackageInfo(name="rich", version="15.0.0", location="/venv"),
    ]
    with (
        mock.patch(f"{MCP}.get_project_root", return_value=tmp_path),
        mock.patch(f"{MCP}.list_packages", return_value=packages),
    ):
        tool = asyncio.run(server.get_tool("list_packages_tool"))
        result = tool.fn()
    assert "count: 1" in result
    assert "rich,15.0.0" in result


def test_show_package_tool_returns_toon() -> None:
    """The show tool returns TOON-encoded package metadata."""
    server = build_server()
    package = PackageInfo(name="rich", version="15.0.0", location="/venv")
    with mock.patch(f"{MCP}.resolve_package", return_value=package):
        tool = asyncio.run(server.get_tool("show_package_tool"))
        result = tool.fn(name="rich")
    assert "name: rich" in result


def test_show_package_api_tool_returns_toon() -> None:
    """The API tool returns TOON-encoded public symbols."""
    server = build_server()
    symbols = [
        SymbolInfo(name="foo", kind="function", signature="()", doc="Foo."),
    ]
    with mock.patch(f"{MCP}.get_public_api", return_value=symbols):
        tool = asyncio.run(server.get_tool("show_package_api_tool"))
        result = tool.fn(name="rich")
    assert "count: 1" in result
    assert "foo,function" in result
