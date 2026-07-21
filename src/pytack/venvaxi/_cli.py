"""Argparse CLI for `venv-axi`."""

import argparse
import logging
import sys
from dataclasses import asdict
from pathlib import Path

from rich.console import Console

from pytack import exceptions
from pytack._core import get_project_root, CLIContext, ExitCode
from pytack.logging import configure_venv_axi_logging
from pytack.venvaxi._ambient import setup_ambient_context
from pytack.venvaxi._introspect import get_public_api
from pytack.venvaxi._packages import list_packages, resolve_package
from pytack.venvaxi._toon import encode_object, encode_table, format_help

logger = logging.getLogger(__package__)


def _emit(text: str) -> None:
    """Writes a line of structured output to STDOUT.

    NOTE: Uses `sys.stdout.write` (instead of `print`) so structural
    TOON output is never subject to Rich console line-wrapping and to
    avoid the `T201` (flake8-print) lint rule.

    Args:
        text: The text to write, without a trailing newline.
    """
    sys.stdout.write(f"{text}\n")


def _format_path(path: Path) -> str:
    """Formats a path relative to the user's home directory.

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
    """Formats a structured TOON error object and help footer.

    Args:
        message: The human-readable error message.

    Returns:
        The TOON-encoded error object, followed by a help footer.
    """
    body = encode_object({"error": True, "message": message})
    footer = format_help(["Run `venv-axi --help` for available commands"])
    return f"{body}\n{footer}"


def command_home(_: CLIContext) -> int:
    """Prints live status and next-step hints (the content-first home view).

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
                "Run `venv-axi show <package>` for package info",
            ]
        )
    )
    return ExitCode.EX_OK


def command_list(ctx: CLIContext) -> int:
    """Lists the consuming repo's declared, installed venv packages.

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
                    "Run `venv-axi list --all` to include"
                    " dev/optional dependencies",
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
    """Shows a package's public, top-level API symbols.

    Args:
        ctx: The CLI context.

    Returns:
        The process exit code.
    """
    symbols = get_public_api(ctx.args.package, full=ctx.args.full)
    if not symbols:
        _emit("count: 0")
        return ExitCode.EX_OK

    rows = [asdict(symbol) for symbol in symbols]
    _emit(f"count: {len(symbols)}")
    _emit(encode_table("symbols", rows, ["name", "kind", "signature", "doc"]))
    if not ctx.args.full:
        _emit(
            format_help(
                [
                    f"Run `venv-axi show {ctx.args.package} --api --full`"
                    " for complete docstrings"
                ]
            )
        )
    return ExitCode.EX_OK


def _command_show_metadata(ctx: CLIContext) -> int:
    """Shows a package's installed metadata.

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
    """Shows a package's metadata or public API (dispatches on `--api`).

    Args:
        ctx: The CLI context.

    Returns:
        The process exit code.
    """
    if ctx.args.api:
        return _command_show_api(ctx)
    return _command_show_metadata(ctx)


def command_serve(_: CLIContext) -> int:
    """Runs the `venv-axi` MCP server over stdio.

    Args:
        _: The CLI context.

    Returns:
        The process exit code.
    """
    from pytack.venvaxi import _mcp

    try:
        _mcp.serve()
    except ImportError:
        logger.error("`venv-axi serve` requires the `pytack[venv-axi]` extra")
        return ExitCode.EX_FAILURE
    return ExitCode.EX_OK


def command_setup(_: CLIContext) -> int:
    """Installs `venv-axi` ambient context into the consuming repo.

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
    """Builds the `venv-axi` argument parser.

    Returns:
        The configured `ArgumentParser`, with non-required subcommands
        so a bare `venv-axi` invocation falls through to the home view.
    """
    parser = argparse.ArgumentParser(
        prog="venv-axi",
        description="Fetch dependency API info from a project's venv",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging on STDERR",
    )
    parser.set_defaults(func=command_home)

    subparsers = parser.add_subparsers(title="commands", dest="command")

    parser_list = subparsers.add_parser("list", help="List venv packages")
    parser_list.add_argument(
        "--all",
        action="store_true",
        help="Include dev/optional dependency groups",
    )
    parser_list.add_argument(
        "--fields",
        default="name,version",
        help="Comma-separated fields to display",
    )
    parser_list.set_defaults(func=command_list)

    parser_show = subparsers.add_parser(
        "show", help="Show package metadata or API"
    )
    parser_show.add_argument("package", help="Package (distribution) name")
    parser_show.add_argument(
        "--fields",
        default="name,version,location",
        help="Comma-separated fields to display",
    )
    parser_show.add_argument(
        "--api",
        action="store_true",
        help="Show public API symbols instead of metadata",
    )
    parser_show.add_argument(
        "--full",
        action="store_true",
        help="Show complete docstrings (no truncation)",
    )
    parser_show.set_defaults(func=command_show)

    parser_serve = subparsers.add_parser(
        "serve", help="Run the venv-axi MCP server"
    )
    parser_serve.set_defaults(func=command_serve)

    parser_setup = subparsers.add_parser(
        "setup", help="Install venv-axi ambient context"
    )
    parser_setup.set_defaults(func=command_setup)

    return parser


def main() -> int:
    """Parses arguments and dispatches to the selected command.

    Returns:
        The process exit code: 0 on success, 1 on a handled
        `pytack.exceptions.Error`, 2 on an unexpected exception.
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
