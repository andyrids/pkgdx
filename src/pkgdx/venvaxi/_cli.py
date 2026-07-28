"""Argparse CLI for `venv-axi`."""

import argparse
import logging
import sys
from dataclasses import asdict
from enum import StrEnum
from pathlib import Path

from rich.console import Console

from pkgdx import exceptions
from pkgdx._core import CLIContext, ExitCode, get_project_root
from pkgdx.logging import configure_venv_axi_logging
from pkgdx.venvaxi._ambient import setup_ambient_context
from pkgdx.venvaxi._introspect import (
    SYMBOL_INFO_FIELDS,
    find_symbol,
    get_module_tree,
    get_public_api,
    get_symbol,
)
from pkgdx.venvaxi._packages import list_packages, resolve_package
from pkgdx.venvaxi._toon import encode_object, encode_table, format_help

logger = logging.getLogger(__package__)


def _emit(text: str) -> None:
    """Write a line of structured output to STDOUT.

    NOTE: Uses `sys.stdout.write` (instead of `print`) so structural
    TOON output is never subject to Rich console line-wrapping.

    Args:
        text: The text to write, without a trailing newline.
    """
    sys.stdout.write(f"{text}\n")


def _format_path(path: Path) -> str:
    """Format a path relative to $HOME.

    Args:
        path: The absolute path to format.

    Returns:
        A `~/`-prefixed path when under the home directory, else the
        unmodified absolute path.
    """
    try:
        return f"~/{path.relative_to(Path.home())}"
    except ValueError:
        return str(path)


def _error_output(message: str) -> str:
    """Format a structured TOON error object and help footer.

    Args:
        message: The human-readable error message.

    Returns:
        The TOON-encoded error object, followed by a help footer.
    """
    body = encode_object({"error": True, "message": message})
    footer = format_help(["Run `venv-axi --help` for available commands"])
    return f"{body}\n{footer}"


def command_home(_: CLIContext) -> int:
    """Print live status and next-step hints (the content-first home view).

    Args:
        _: The CLI context.

    Returns:
        The process exit code.
    """
    bin_path = Path(sys.argv[0]).resolve()
    venv_path = Path(sys.prefix).resolve()
    active = sys.prefix != sys.base_prefix

    fields = {
        "description": "Fetch dependency API info from a project's venv",
        "bin": _format_path(bin_path),
        "venv": _format_path(venv_path),
        "status": "active" if active else "inactive",
    }
    _emit(encode_object(fields))
    _emit(
        format_help(
            [
                "Run `venv-axi list` for the venv package list",
                "Run `venv-axi show <package>` for metadata information",
                "Run `venv-axi show <package> --api` for public API symbols",
                "Run `venv-axi find <query>` to search cached symbols",
                "Run `venv-axi tree <package>` for a nested module tree",
                "Run `venv-axi inspect <qualified_name>` for symbol detail",
                "Run `venv-axi setup` to install ambient context",
            ]
        )
    )
    return ExitCode.EX_OK


def command_list(ctx: CLIContext) -> int:
    """List the consuming repo's declared, installed venv packages.

    Args:
        ctx: The CLI context.

    Returns:
        The process exit code.
    """
    root = get_project_root()
    packages = list_packages(root, include_dev=ctx.args.all)

    if not packages:
        _emit("count: 0")
        _emit(
            format_help(
                [
                    (
                        "Run `venv-axi list --all` to include dev/optional "
                        "dependencies"
                    )
                ]
            )
        )
        return ExitCode.EX_OK

    fields = [field.strip() for field in ctx.args.fields.split(",") if field]
    rows = [asdict(package) for package in packages]

    _emit(f"count: {len(packages)}")
    _emit(encode_table("packages", rows, fields))
    _emit(format_help(["Run `venv-axi show <package>` for package info"]))
    return ExitCode.EX_OK


def _command_show_api(ctx: CLIContext) -> int:
    """Show public, top-level API symbols for a package.

    Args:
        ctx: The CLI context.

    Returns:
        The process exit code.
    """
    symbols = get_public_api(ctx.args.package, docstring=ctx.args.docstring)
    if not symbols:
        _emit("count: 0")
        return ExitCode.EX_OK

    rows = [asdict(symbol) for symbol in symbols]
    _emit(f"count: {len(symbols)}")
    _emit(encode_table("symbols", rows, SYMBOL_INFO_FIELDS))
    if not ctx.args.docstring:
        package = ctx.args.package
        options = "--api --docstring"

        _emit(
            format_help(
                [
                    f"Run `venv-axi show {package} {options}` for docstrings",
                ]
            )
        )
    return ExitCode.EX_OK


def _command_show_metadata(ctx: CLIContext) -> int:
    """Show a package's installed metadata.

    Args:
        ctx: The CLI context.

    Returns:
        The process exit code.
    """
    package = resolve_package(ctx.args.package)
    fields = [field.strip() for field in ctx.args.fields.split(",") if field]
    data = asdict(package)
    selected = {field: data[field] for field in fields if field in data}

    _emit(encode_object(selected))
    _emit(
        format_help(
            [f"Run `venv-axi show {ctx.args.package} --api` for public API"]
        )
    )
    return ExitCode.EX_OK


def command_show(ctx: CLIContext) -> int:
    """Show a package's metadata or public API (dispatches on `--api`).

    Args:
        ctx: The CLI context.

    Returns:
        The process exit code.
    """
    if ctx.args.api:
        return _command_show_api(ctx)
    return _command_show_metadata(ctx)


def command_find(ctx: CLIContext) -> int:
    """Search cached symbols by name/doc text.

    Args:
        ctx: The CLI context.

    Returns:
        The process exit code.
    """
    nodes = find_symbol(ctx.args.query, ctx.args.limit)
    if not nodes:
        _emit("count: 0")
        return ExitCode.EX_OK

    rows = [node.as_row() for node in nodes]
    _emit(f"count: {len(nodes)}")
    _emit(encode_table("symbols", rows, ["name", "kind", "qualified_name"]))
    _emit(
        format_help(
            ["Run `venv-axi inspect <qualified_name>` for complete metadata"]
        )
    )
    return ExitCode.EX_OK


class TreeField(StrEnum):
    """The fields for the `venv-axi tree` tabular output."""

    DEPTH = "depth"
    QUALIFIED_NAME = "qualified_name"
    KIND = "kind"


def command_tree(ctx: CLIContext) -> int:
    """Show a package's nested module tree.

    Args:
        ctx: The CLI context.

    Returns:
        The process exit code.
    """
    pairs = get_module_tree(ctx.args.package, ctx.args.max_depth)
    if not pairs:
        _emit("count: 0")
        return ExitCode.EX_OK

    rows = [{"depth": depth, **node.as_row()} for depth, node in pairs]
    _emit(f"count: {len(pairs)}")
    _emit(encode_table("tree", rows, [item.value for item in TreeField]))
    return ExitCode.EX_OK


def command_inspect(ctx: CLIContext) -> int:
    """Show complete information for a qualified symbol name.

    Args:
        ctx: The CLI context.

    Returns:
        The process exit code.
    """
    node = get_symbol(ctx.args.qualified_name)
    _emit(
        encode_object(
            {
                "qualified_name": node.qualified_name,
                "kind": str(node.kind),
                "signature": node.signature,
                "doc": node.doc,
            }
        )
    )
    return ExitCode.EX_OK


def command_serve(_: CLIContext) -> int:
    """Serve a dedicated AXI MCP server over STDIO.

    Args:
        _: The CLI context.

    Returns:
        The process exit code.
    """
    from pkgdx.venvaxi import _mcp

    try:
        _mcp.serve()
    except ImportError:
        logger.error("`venv-axi serve` requires the `pkgdx[venv-axi]` extra")
        return ExitCode.EX_FAILURE
    return ExitCode.EX_OK


def command_setup(_: CLIContext) -> int:
    """Install `venv-axi` ambient context into the consuming repo.

    Args:
        _: The CLI context.

    Returns:
        The process exit code.
    """
    root = get_project_root()
    changed = setup_ambient_context(root)

    _emit(encode_object(changed))
    _emit(format_help(["Run `venv-axi` to confirm ambient context is live"]))
    return ExitCode.EX_OK


def _build_parser() -> argparse.ArgumentParser:
    """Build the `venv-axi` argument parser.

    Returns:
        The configured `ArgumentParser`, with non-required subcommands
        so a bare `venv-axi` invocation falls through to the home view.
    """
    parser = argparse.ArgumentParser(
        prog="venv-axi",
        description="Fetch dependency metadata & API information from a venv",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging on STDERR",
    )
    parser.set_defaults(func=command_home)

    subparsers = parser.add_subparsers(title="commands", dest="command")

    parser_list = subparsers.add_parser(
        "list", help="Show installed venv packages"
    )
    parser_list.add_argument(
        "--all",
        action="store_true",
        help="Include dev|optional dependency groups",
    )
    parser_list.add_argument(
        "--fields",
        default="name,version",
        help="Comma-separated fields to display",
    )
    parser_list.set_defaults(func=command_list)

    parser_show = subparsers.add_parser(
        "show", help="Show package metadata|API information"
    )
    parser_show.add_argument("package", help="Package (distribution) name")
    parser_show.add_argument(
        "--fields",
        default="name,version,location",
        help="Comma-separated display fields",
    )
    parser_show.add_argument(
        "--api",
        action="store_true",
        help="Show public API symbols instead of metadata",
    )
    parser_show.add_argument(
        "--docstring",
        action="store_true",
        help="Show complete docstrings (with --api)",
    )
    parser_show.set_defaults(func=command_show)

    parser_find = subparsers.add_parser(
        "find",
        help="Search cached symbols by name|docstring text",
    )
    parser_find.add_argument(
        "query",
        help="Free-text search query",
    )
    parser_find.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of results",
    )
    parser_find.set_defaults(func=command_find)

    parser_tree = subparsers.add_parser(
        "tree", help="Show nested module tree for a package"
    )
    parser_tree.add_argument("package", help="Package (distribution) name")
    parser_tree.add_argument(
        "--max-depth",
        type=int,
        default=2,
        dest="max_depth",
        help="Maximum submodule recursion depth",
    )
    parser_tree.set_defaults(func=command_tree)

    parser_inspect = subparsers.add_parser(
        "inspect", help="Show complete details for a qualified symbol name"
    )
    parser_inspect.add_argument(
        "qualified_name",
        help="Qualified symbol name (module::Symbol | module::Class.method)",
    )
    parser_inspect.set_defaults(func=command_inspect)

    parser_serve = subparsers.add_parser(
        "serve",
        help="Run a dedicated AXI MCP server (requires pkgdx[venv-axi])",
    )
    parser_serve.set_defaults(func=command_serve)

    parser_setup = subparsers.add_parser(
        "setup",
        help=" ".join(
            [
                "Install AXI ambient context into the repo",
                "(AGENTS.md & MCP config)",
            ]
        ),
    )
    parser_setup.set_defaults(func=command_setup)

    return parser


def main() -> int:
    """Parse arguments & dispatch to the selected command.

    Returns:
        The process exit code; 0 on success, 1 on a handled
        `pkgdx.exceptions.Error`, 2 on an unexpected exception.
    """
    parser = _build_parser()
    args = parser.parse_args()

    is_verbose = args.verbose
    level = logging.DEBUG if is_verbose else logging.WARNING
    configure_venv_axi_logging(level)

    console = Console(stderr=True)
    ctx = CLIContext(args=args, console=console, is_verbose=is_verbose)

    try:
        return int(args.func(ctx))
    except exceptions.Error as err:
        _emit(_error_output(str(err)))
        logger.error(str(err))
        return ExitCode.EX_FAILURE
    except Exception:
        _emit(_error_output("Unexpected error"))
        logger.exception("Unexpected error in venv-axi")
        return ExitCode.EX_SYNTAX
