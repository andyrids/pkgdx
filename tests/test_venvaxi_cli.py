"""Unit tests for `pkgdx.venvaxi._cli`."""

import argparse
from collections.abc import Callable
from pathlib import Path
from unittest import mock

import pytest

from pkgdx import exceptions
from pkgdx._core import CLIContext
from pkgdx.venvaxi import _cli
from pkgdx.venvaxi._introspect import SYMBOL_INFO_FIELDS, SymbolInfo
from pkgdx.venvaxi._packages import PackageInfo
from pkgdx.venvaxi._store import NodeKind, SymbolNode

CLI = "pkgdx.venvaxi._cli"

ContextFactory = Callable[..., CLIContext]
NodeFactory = Callable[..., SymbolNode]
PackageFactory = Callable[..., PackageInfo]


def test_build_parser_defaults_to_home() -> None:
    """A bare invocation dispatches to `command_home`."""
    parser = _cli._build_parser()
    args = parser.parse_args([])
    assert args.func is _cli.command_home
    assert args.verbose is False


def test_build_parser_list_defaults() -> None:
    """The `list` subcommand has the documented default flags."""
    parser = _cli._build_parser()
    args = parser.parse_args(["list"])
    assert args.func is _cli.command_list
    assert args.all is False
    assert args.fields == "name,version"


def test_build_parser_show_requires_package() -> None:
    """The `show` subcommand requires a positional package name."""
    parser = _cli._build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["show"])


def test_build_parser_find_defaults() -> None:
    """The `find` subcommand has the documented default flags."""
    parser = _cli._build_parser()
    args = parser.parse_args(["find", "Console"])
    assert args.func is _cli.command_find
    assert args.query == "Console"
    assert args.limit == 20


def test_build_parser_tree_defaults() -> None:
    """The `tree` subcommand has the documented default flags."""
    parser = _cli._build_parser()
    args = parser.parse_args(["tree", "rich"])
    assert args.func is _cli.command_tree
    assert args.package == "rich"
    assert args.max_depth == 2


def test_build_parser_inspect_requires_qualified_name() -> None:
    """The `inspect` subcommand requires a positional qualified name."""
    parser = _cli._build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["inspect"])
    args = parser.parse_args(["inspect", "rich::Console"])
    assert args.func is _cli.command_inspect
    assert args.qualified_name == "rich::Console"


def test_command_home_prints_status(
    capsys: pytest.CaptureFixture, make_cli_context: ContextFactory
) -> None:
    """The home view prints description, bin, venv and status fields."""
    exit_code = _cli.command_home(make_cli_context())
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "description:" in out
    assert "bin:" in out
    assert "status:" in out
    assert "help[7]:" in out


def test_command_home_status_active_when_prefixes_differ(
    capsys: pytest.CaptureFixture, make_cli_context: ContextFactory
) -> None:
    """Status is `active` when `sys.prefix != sys.base_prefix`."""
    with (
        mock.patch(f"{CLI}.sys.prefix", "/repo/.venv"),
        mock.patch(f"{CLI}.sys.base_prefix", "/usr"),
    ):
        _cli.command_home(make_cli_context())
    out = capsys.readouterr().out
    assert "status: active" in out


def test_command_home_status_inactive_when_prefixes_match(
    capsys: pytest.CaptureFixture, make_cli_context: ContextFactory
) -> None:
    """Status is `inactive` when `sys.prefix == sys.base_prefix`."""
    with (
        mock.patch(f"{CLI}.sys.prefix", "/usr"),
        mock.patch(f"{CLI}.sys.base_prefix", "/usr"),
    ):
        _cli.command_home(make_cli_context())
    out = capsys.readouterr().out
    assert "status: inactive" in out


def test_command_list_empty(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
    make_cli_context: ContextFactory,
) -> None:
    """A repo with no resolvable dependencies prints the empty state."""
    ctx = make_cli_context(
        args=argparse.Namespace(all=False, fields="name,version")
    )
    with (
        mock.patch(f"{CLI}.get_project_root", return_value=tmp_path),
        mock.patch(f"{CLI}.list_packages", return_value=[]),
    ):
        exit_code = _cli.command_list(ctx)
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "count: 0" in out


def test_command_list_with_packages(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
    make_cli_context: ContextFactory,
    make_package_info: PackageFactory,
) -> None:
    """Resolved packages are printed as a TOON table."""
    packages = [make_package_info()]
    ctx = make_cli_context(
        args=argparse.Namespace(all=False, fields="name,version")
    )
    with (
        mock.patch(f"{CLI}.get_project_root", return_value=tmp_path),
        mock.patch(f"{CLI}.list_packages", return_value=packages),
    ):
        exit_code = _cli.command_list(ctx)
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "count: 1" in out
    assert "rich|15.0.0" in out


def test_command_show_metadata(
    capsys: pytest.CaptureFixture,
    make_cli_context: ContextFactory,
    make_package_info: PackageFactory,
) -> None:
    """Package metadata is printed for a plain `show` invocation."""
    ctx = make_cli_context(
        args=argparse.Namespace(
            package="rich", fields="name,version", api=False, full=False
        )
    )
    with mock.patch(
        f"{CLI}.resolve_package", return_value=make_package_info()
    ):
        exit_code = _cli.command_show(ctx)
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "name: rich" in out
    assert "version: 15.0.0" in out


def test_command_show_api(
    capsys: pytest.CaptureFixture, make_cli_context: ContextFactory
) -> None:
    """Public API symbols are printed when `--api` is passed."""
    symbols = [
        SymbolInfo(name="foo", kind="function", signature="()", doc="Foo."),
    ]
    ctx = make_cli_context(
        args=argparse.Namespace(package="rich", api=True, docstring=False)
    )
    with mock.patch(f"{CLI}.get_public_api", return_value=symbols):
        exit_code = _cli.command_show(ctx)
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "count: 1" in out
    assert "foo|function" in out


def test_command_show_api_header_matches_symbol_info_fields(
    capsys: pytest.CaptureFixture, make_cli_context: ContextFactory
) -> None:
    """The `--api` TOON table header tracks `SymbolInfo` field order."""
    symbols = [
        SymbolInfo(name="foo", kind="function", signature="()", doc="Foo."),
    ]
    ctx = make_cli_context(
        args=argparse.Namespace(package="rich", api=True, docstring=False)
    )
    with mock.patch(f"{CLI}.get_public_api", return_value=symbols):
        _cli.command_show(ctx)
    out = capsys.readouterr().out
    assert f"{{{'|'.join(SYMBOL_INFO_FIELDS)}}}" in out


def test_command_show_api_empty(
    capsys: pytest.CaptureFixture, make_cli_context: ContextFactory
) -> None:
    """A package with no public symbols prints the empty state."""
    ctx = make_cli_context(
        args=argparse.Namespace(package="rich", api=True, docstring=False)
    )
    with mock.patch(f"{CLI}.get_public_api", return_value=[]):
        exit_code = _cli.command_show(ctx)
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "count: 0" in out


def test_command_serve_reports_missing_extra(
    make_cli_context: ContextFactory,
) -> None:
    """A missing `fastmcp` extra is reported as a handled error."""
    with mock.patch("pkgdx.venvaxi._mcp.serve", side_effect=ImportError):
        exit_code = _cli.command_serve(make_cli_context())
    assert exit_code == 1


def test_command_find_with_results(
    capsys: pytest.CaptureFixture,
    make_cli_context: ContextFactory,
    make_symbol_node: NodeFactory,
) -> None:
    """Search matches are printed as a TOON table with a help footer."""
    nodes = [make_symbol_node(qualified_name="rich::Console", name="Console")]
    ctx = make_cli_context(args=argparse.Namespace(query="Console", limit=20))
    with mock.patch(f"{CLI}.find_symbol", return_value=nodes):
        exit_code = _cli.command_find(ctx)
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "count: 1" in out
    assert "Console|class" in out
    assert "help[1]:" in out


def test_command_find_empty(
    capsys: pytest.CaptureFixture, make_cli_context: ContextFactory
) -> None:
    """No matches prints the empty state."""
    ctx = make_cli_context(args=argparse.Namespace(query="nope", limit=20))
    with mock.patch(f"{CLI}.find_symbol", return_value=[]):
        exit_code = _cli.command_find(ctx)
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "count: 0" in out


def test_command_tree_with_results(
    capsys: pytest.CaptureFixture,
    make_cli_context: ContextFactory,
    make_symbol_node: NodeFactory,
) -> None:
    """The module tree is printed as a depth-annotated TOON table."""
    pairs = [
        (
            0,
            make_symbol_node(
                qualified_name="rich", kind=NodeKind.PACKAGE, name="rich"
            ),
        ),
        (
            1,
            make_symbol_node(
                qualified_name="rich.table",
                kind=NodeKind.MODULE,
                name="table",
            ),
        ),
    ]
    ctx = make_cli_context(
        args=argparse.Namespace(package="rich", max_depth=2)
    )
    with mock.patch(f"{CLI}.get_module_tree", return_value=pairs):
        exit_code = _cli.command_tree(ctx)
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "count: 2" in out
    assert "1|rich.table|module" in out


def test_command_tree_empty(
    capsys: pytest.CaptureFixture, make_cli_context: ContextFactory
) -> None:
    """An empty tree prints the empty state."""
    ctx = make_cli_context(
        args=argparse.Namespace(package="rich", max_depth=2)
    )
    with mock.patch(f"{CLI}.get_module_tree", return_value=[]):
        exit_code = _cli.command_tree(ctx)
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "count: 0" in out


def test_command_inspect_prints_symbol_detail(
    capsys: pytest.CaptureFixture,
    make_cli_context: ContextFactory,
    make_symbol_node: NodeFactory,
) -> None:
    """A single symbol's full detail is printed as a TOON object."""
    node = make_symbol_node(qualified_name="rich::Console", name="Console")
    ctx = make_cli_context(
        args=argparse.Namespace(qualified_name="rich::Console")
    )
    with mock.patch(f"{CLI}.get_symbol", return_value=node):
        exit_code = _cli.command_inspect(ctx)
    out = capsys.readouterr().out
    assert exit_code == 0
    assert 'qualified_name: "rich::Console"' in out
    assert "kind: class" in out


def test_command_inspect_propagates_not_found(
    capsys: pytest.CaptureFixture, make_cli_context: ContextFactory
) -> None:
    """A missing symbol propagates `SymbolNotFoundError`."""
    ctx = make_cli_context(
        args=argparse.Namespace(qualified_name="rich::Nope")
    )
    with (
        mock.patch(
            f"{CLI}.get_symbol",
            side_effect=exceptions.SymbolNotFoundError("not found"),
        ),
        pytest.raises(exceptions.SymbolNotFoundError),
    ):
        _cli.command_inspect(ctx)


def test_command_setup(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
    make_cli_context: ContextFactory,
) -> None:
    """The setup command reports which artifacts changed."""
    changed = {"agents_md": True, "vscode_mcp": False, "repo_mcp": False}
    with (
        mock.patch(f"{CLI}.get_project_root", return_value=tmp_path),
        mock.patch(f"{CLI}.setup_ambient_context", return_value=changed),
    ):
        exit_code = _cli.command_setup(make_cli_context())
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "agents_md: true" in out


def test_main_maps_handled_error_to_exit_1(
    capsys: pytest.CaptureFixture,
) -> None:
    """A `pkgdx.exceptions.Error` maps to exit code 1."""
    parsed_args = argparse.Namespace(
        verbose=False,
        func=mock.MagicMock(
            side_effect=exceptions.PackageNotFoundError("boom")
        ),
    )
    with (
        mock.patch(f"{CLI}._build_parser") as mock_build_parser,
        mock.patch(f"{CLI}.configure_venv_axi_logging"),
    ):
        mock_build_parser.return_value.parse_args.return_value = parsed_args
        exit_code = _cli.main()
    out = capsys.readouterr().out
    assert exit_code == 1
    assert "error: true" in out
    assert "boom" in out


def test_main_maps_unexpected_error_to_exit_2(
    capsys: pytest.CaptureFixture,
) -> None:
    """An unexpected exception maps to exit code 2."""
    parsed_args = argparse.Namespace(
        verbose=False,
        func=mock.MagicMock(side_effect=RuntimeError("oops")),
    )
    with (
        mock.patch(f"{CLI}._build_parser") as mock_build_parser,
        mock.patch(f"{CLI}.configure_venv_axi_logging"),
    ):
        mock_build_parser.return_value.parse_args.return_value = parsed_args
        exit_code = _cli.main()
    out = capsys.readouterr().out
    assert exit_code == 2
    assert "Unexpected error" in out
