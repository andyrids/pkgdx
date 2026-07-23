"""Unit tests for `pytack.venvaxi._ambient`."""

import json
from pathlib import Path
from unittest import mock

from pytack.venvaxi._ambient import (
    _update_mcp_json,
    inject_agents_md,
    setup_ambient_context,
)

AMBIENT = "pytack.venvaxi._ambient"


def test_inject_agents_md_creates_file(tmp_path: Path) -> None:
    """A missing `AGENTS.md` is created with the venv-axi block."""
    changed = inject_agents_md(tmp_path)
    text = (tmp_path / "AGENTS.md").read_text()
    assert changed is True
    assert "<!-- pytack:venv-axi:begin -->" in text
    assert "<!-- pytack:venv-axi:end -->" in text
    assert "venv-axi" in text
    assert "venv-axi find" in text
    assert "venv-axi inspect" in text
    assert "venv-axi tree" in text
    assert "venv-axi serve" in text
    assert "venv-axi setup" in text


def test_inject_agents_md_appends_to_existing_file(tmp_path: Path) -> None:
    """An existing `AGENTS.md` without markers gets the block appended."""
    path = tmp_path / "AGENTS.md"
    path.write_text("# My project\n")
    changed = inject_agents_md(tmp_path)
    text = path.read_text()
    assert changed is True
    assert "# My project" in text
    assert "<!-- pytack:venv-axi:begin -->" in text


def test_inject_agents_md_idempotent(tmp_path: Path) -> None:
    """Running injection twice makes no further changes."""
    inject_agents_md(tmp_path)
    changed = inject_agents_md(tmp_path)
    assert changed is False


def test_inject_agents_md_replaces_stale_block(tmp_path: Path) -> None:
    """An outdated block between markers is replaced in-place."""
    path = tmp_path / "AGENTS.md"
    path.write_text(
        "# My project\n\n"
        "<!-- pytack:venv-axi:begin -->\nstale content\n"
        "<!-- pytack:venv-axi:end -->\n"
    )
    changed = inject_agents_md(tmp_path)
    text = path.read_text()
    assert changed is True
    assert "stale content" not in text
    assert "venv-axi" in text


def test_update_mcp_json_creates_file(tmp_path: Path) -> None:
    """A missing MCP config file is created with a venv-axi entry."""
    path = tmp_path / ".vscode" / "mcp.json"
    with mock.patch(
        f"{AMBIENT}._venv_axi_command", return_value="/bin/venv-axi"
    ):
        changed = _update_mcp_json(path, "servers")

    data = json.loads(path.read_text())
    assert changed is True
    assert data["servers"]["venv-axi"]["command"] == "/bin/venv-axi"
    assert data["servers"]["venv-axi"]["args"] == ["serve"]


def test_update_mcp_json_idempotent(tmp_path: Path) -> None:
    """Running the update twice makes no further changes."""
    path = tmp_path / "mcp.json"
    with mock.patch(
        f"{AMBIENT}._venv_axi_command", return_value="/bin/venv-axi"
    ):
        _update_mcp_json(path, "mcpServers")
        changed = _update_mcp_json(path, "mcpServers")
    assert changed is False


def test_update_mcp_json_preserves_other_keys(tmp_path: Path) -> None:
    """Existing unrelated servers/keys are preserved."""
    path = tmp_path / "mcp.json"
    path.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}}))
    with mock.patch(
        f"{AMBIENT}._venv_axi_command", return_value="/bin/venv-axi"
    ):
        _update_mcp_json(path, "mcpServers")

    data = json.loads(path.read_text())
    assert "other" in data["mcpServers"]
    assert "venv-axi" in data["mcpServers"]


def test_update_mcp_json_recovers_from_malformed_json(
    tmp_path: Path,
) -> None:
    """Malformed existing JSON is replaced rather than raising."""
    path = tmp_path / "mcp.json"
    path.write_text("{not valid json")
    with mock.patch(
        f"{AMBIENT}._venv_axi_command", return_value="/bin/venv-axi"
    ):
        changed = _update_mcp_json(path, "mcpServers")

    data = json.loads(path.read_text())
    assert changed is True
    assert "venv-axi" in data["mcpServers"]


def test_setup_ambient_context_reports_all_artifacts(
    tmp_path: Path,
) -> None:
    """`setup_ambient_context` reports all three artifact statuses."""
    with mock.patch(
        f"{AMBIENT}._venv_axi_command", return_value="/bin/venv-axi"
    ):
        changed = setup_ambient_context(tmp_path)

    assert set(changed) == {"AGENTS.md", ".vscode", ".mcp.json"}
    assert all(changed.values())
