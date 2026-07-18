"""Unit tests for `pytack.venvaxi._cli`."""

import argparse
from pathlib import Path
from unittest import mock

import pytest

from pytack import exceptions
from pytack.venvaxi import _cli
from pytack.venvaxi._introspect import SymbolInfo
from pytack.venvaxi._packages import PackageInfo

CLI = "pytack.venvaxi._cli"


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


def test_command_home_prints_status(
    capsys: pytest.CaptureFixture,
) -> None:
    """The home view prints description, bin, venv and status fields."""
    exit_code = _cli.command_home(argparse.Namespace())
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "description:" in out
    assert "bin:" in out
    assert "status:" in out
    assert "help[2]:" in out


def test_command_home_status_active_when_prefixes_differ(
    capsys: pytest.CaptureFixture,
) -> None:
    """Status is `active` when `sys.prefix != sys.base_prefix`."""
    with (
        mock.patch(f"{CLI}.sys.prefix", "/repo/.venv"),
        mock.patch(f"{CLI}.sys.base_prefix", "/usr"),
    ):
        _cli.command_home(argparse.Namespace())
    out = capsys.readouterr().out
    assert "status: active" in out


def test_command_home_status_inactive_when_prefixes_match(
    capsys: pytest.CaptureFixture,
) -> None:
    """Status is `inactive` when `sys.prefix == sys.base_prefix`."""
    with (
        mock.patch(f"{CLI}.sys.prefix", "/usr"),
        mock.patch(f"{CLI}.sys.base_prefix", "/usr"),
    ):
        _cli.command_home(argparse.Namespace())
    out = capsys.readouterr().out
    assert "status: inactive" in out


def test_command_list_empty(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """A repo with no resolvable dependencies prints the empty state."""
    args = argparse.Namespace(all=False, fields="name,version")
    with (
        mock.patch(f"{CLI}.get_project_root", return_value=tmp_path),
        mock.patch(f"{CLI}.list_packages", return_value=[]),
    ):
        exit_code = _cli.command_list(args)
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "count: 0" in out


def test_command_list_with_packages(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Resolved packages are printed as a TOON table."""
    packages = [
        PackageInfo(name="rich", version="15.0.0", location="/venv"),
    ]
    args = argparse.Namespace(all=False, fields="name,version")
    with (
        mock.patch(f"{CLI}.get_project_root", return_value=tmp_path),
        mock.patch(f"{CLI}.list_packages", return_value=packages),
    ):
        exit_code = _cli.command_list(args)
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "count: 1" in out
    assert "rich,15.0.0" in out


def test_command_show_metadata(capsys: pytest.CaptureFixture) -> None:
    """Package metadata is printed for a plain `show` invocation."""
    package = PackageInfo(name="rich", version="15.0.0", location="/venv")
    args = argparse.Namespace(
        package="rich", fields="name,version", api=False, full=False
    )
    with mock.patch(f"{CLI}.resolve_package", return_value=package):
        exit_code = _cli.command_show(args)
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "name: rich" in out
    assert "version: 15.0.0" in out


def test_command_show_api(capsys: pytest.CaptureFixture) -> None:
    """Public API symbols are printed when `--api` is passed."""
    symbols = [
        SymbolInfo(name="foo", kind="function", signature="()", doc="Foo."),
    ]
    args = argparse.Namespace(package="rich", api=True, full=False)
    with mock.patch(f"{CLI}.get_public_api", return_value=symbols):
        exit_code = _cli.command_show(args)
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "count: 1" in out
    assert "foo,function" in out


def test_command_show_api_empty(capsys: pytest.CaptureFixture) -> None:
    """A package with no public symbols prints the empty state."""
    args = argparse.Namespace(package="rich", api=True, full=False)
    with mock.patch(f"{CLI}.get_public_api", return_value=[]):
        exit_code = _cli.command_show(args)
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "count: 0" in out


def test_command_serve_reports_missing_extra() -> None:
    """A missing `fastmcp` extra is reported as a handled error."""
    with mock.patch("pytack.venvaxi._mcp.serve", side_effect=ImportError):
        exit_code = _cli.command_serve(argparse.Namespace())
    assert exit_code == 1


def test_command_setup(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """The setup command reports which artifacts changed."""
    changed = {"agents_md": True, "vscode_mcp": False, "repo_mcp": False}
    with (
        mock.patch(f"{CLI}.get_project_root", return_value=tmp_path),
        mock.patch(f"{CLI}.setup_ambient_context", return_value=changed),
    ):
        exit_code = _cli.command_setup(argparse.Namespace())
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "agents_md: true" in out


def test_main_maps_handled_error_to_exit_1(
    capsys: pytest.CaptureFixture,
) -> None:
    """A `pytack.exceptions.Error` maps to exit code 1."""
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
