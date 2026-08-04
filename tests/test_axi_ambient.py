"""Unit tests for `pkgdx.axi._ambient`."""

import json
from pathlib import Path
from unittest import mock

from pkgdx.axi._ambient import (
    _update_mcp_json,
    inject_agents_md,
    setup_ambient_context,
)

AMBIENT = "pkgdx.axi._ambient"


def test_inject_agents_md_creates_file(tmp_path: Path) -> None:
    """A missing `AGENTS.md` is created with the axi block."""
    changed = inject_agents_md(tmp_path)
    text = (tmp_path / "AGENTS.md").read_text()
    assert changed is True
    assert "<!-- pkgdx:axi:begin -->" in text
    assert "<!-- pkgdx:axi:end -->" in text
    assert "axi" in text
    assert "pkgdx axi find" in text
    assert "pkgdx axi inspect" in text
    assert "pkgdx axi tree" in text
    assert "pkgdx axi serve" in text
    assert "pkgdx axi setup" in text


def test_inject_agents_md_appends_to_existing_file(tmp_path: Path) -> None:
    """An existing `AGENTS.md` without markers gets the block appended."""
    path = tmp_path / "AGENTS.md"
    path.write_text("# My project\n")
    changed = inject_agents_md(tmp_path)
    text = path.read_text()
    assert changed is True
    assert "# My project" in text
    assert "<!-- pkgdx:axi:begin -->" in text


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
        "<!-- pkgdx:axi:begin -->\nstale content\n"
        "<!-- pkgdx:axi:end -->\n"
    )
    changed = inject_agents_md(tmp_path)
    text = path.read_text()
    assert changed is True
    assert "stale content" not in text
    assert "axi" in text


def test_inject_agents_md_migrates_venv_axi_block(tmp_path: Path) -> None:
    """A pre-rename `venv-axi` block is removed and the new block
    installed, preserving surrounding prose."""
    path = tmp_path / "AGENTS.md"
    path.write_text(
        "# My project\n\n"
        "<!-- pkgdx:venv-axi:begin -->\nold content\n"
        "<!-- pkgdx:venv-axi:end -->\n"
    )
    changed = inject_agents_md(tmp_path)
    text = path.read_text()
    assert changed is True
    assert "venv-axi" not in text
    assert "old content" not in text
    assert text.count("<!-- pkgdx:axi:begin -->") == 1
    assert "# My project" in text


def test_inject_agents_md_removes_old_block_when_new_present(
    tmp_path: Path,
) -> None:
    """A duplicated old+new state drops the old block, keeping one new
    block."""
    path = tmp_path / "AGENTS.md"
    inject_agents_md(tmp_path)
    path.write_text(
        "<!-- pkgdx:venv-axi:begin -->\nold content\n"
        "<!-- pkgdx:venv-axi:end -->\n\n" + path.read_text()
    )
    changed = inject_agents_md(tmp_path)
    text = path.read_text()
    assert changed is True
    assert "old content" not in text
    assert text.count("<!-- pkgdx:axi:begin -->") == 1


def test_update_mcp_json_creates_file(tmp_path: Path) -> None:
    """A missing MCP config file is created with a axi entry."""
    path = tmp_path / ".vscode" / "mcp.json"
    with mock.patch(f"{AMBIENT}._axi_command", return_value="/bin/pkgdx"):
        changed = _update_mcp_json(path, "servers", available=True)

    data = json.loads(path.read_text())
    assert changed is True
    assert data["servers"]["axi"]["command"] == "/bin/pkgdx"
    assert data["servers"]["axi"]["args"] == ["axi", "serve"]


def test_update_mcp_json_idempotent(tmp_path: Path) -> None:
    """Running the update twice makes no further changes."""
    path = tmp_path / "mcp.json"
    with mock.patch(f"{AMBIENT}._axi_command", return_value="/bin/pkgdx"):
        _update_mcp_json(path, "mcpServers", available=True)
        changed = _update_mcp_json(path, "mcpServers", available=True)
    assert changed is False


def test_update_mcp_json_preserves_other_keys(tmp_path: Path) -> None:
    """Existing unrelated servers/keys are preserved."""
    path = tmp_path / "mcp.json"
    path.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}}))
    with mock.patch(f"{AMBIENT}._axi_command", return_value="/bin/pkgdx"):
        _update_mcp_json(path, "mcpServers", available=True)

    data = json.loads(path.read_text())
    assert "other" in data["mcpServers"]
    assert "axi" in data["mcpServers"]


def test_update_mcp_json_removes_stale_venv_axi_entry(tmp_path: Path) -> None:
    """A stale `venv-axi` entry is removed, `axi` added, others kept."""
    path = tmp_path / "mcp.json"
    path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "venv-axi": {"command": "x"},
                    "other": {"command": "y"},
                }
            }
        )
    )
    with mock.patch(f"{AMBIENT}._axi_command", return_value="/bin/pkgdx"):
        changed = _update_mcp_json(path, "mcpServers", available=True)

    data = json.loads(path.read_text())
    assert changed is True
    assert "venv-axi" not in data["mcpServers"]
    assert "axi" in data["mcpServers"]
    assert "other" in data["mcpServers"]


def test_update_mcp_json_recovers_from_malformed_json(
    tmp_path: Path,
) -> None:
    """Malformed existing JSON is replaced rather than raising."""
    path = tmp_path / "mcp.json"
    path.write_text("{not valid json")
    with mock.patch(f"{AMBIENT}._axi_command", return_value="/bin/pkgdx"):
        changed = _update_mcp_json(path, "mcpServers", available=True)

    data = json.loads(path.read_text())
    assert changed is True
    assert "axi" in data["mcpServers"]


def test_update_mcp_json_unavailable_skips_creation(tmp_path: Path) -> None:
    """Without `fastmcp`, a missing MCP config file is not created."""
    path = tmp_path / ".vscode" / "mcp.json"
    changed = _update_mcp_json(path, "servers", available=False)
    assert changed is False
    assert not path.exists()


def test_update_mcp_json_unavailable_removes_entries(tmp_path: Path) -> None:
    """Without `fastmcp`, `axi` & `venv-axi` entries are removed and
    other entries are preserved."""
    path = tmp_path / "mcp.json"
    path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "axi": {"command": "x"},
                    "venv-axi": {"command": "x"},
                    "other": {"command": "y"},
                }
            }
        )
    )
    changed = _update_mcp_json(path, "mcpServers", available=False)

    data = json.loads(path.read_text())
    assert changed is True
    assert "axi" not in data["mcpServers"]
    assert "venv-axi" not in data["mcpServers"]
    assert "other" in data["mcpServers"]


def test_update_mcp_json_unavailable_idempotent(tmp_path: Path) -> None:
    """Without `fastmcp`, an already-clean config is left untouched."""
    path = tmp_path / "mcp.json"
    path.write_text(json.dumps({"mcpServers": {"other": {"command": "y"}}}))
    changed = _update_mcp_json(path, "mcpServers", available=False)
    assert changed is False
    assert "other" in json.loads(path.read_text())["mcpServers"]


def test_setup_ambient_context_reports_all_artifacts(
    tmp_path: Path,
) -> None:
    """`setup_ambient_context` reports all three artifact statuses."""
    # NOTE: `mcp_available` is patched so the suite passes with or
    # without the `axi` extra installed
    with (
        mock.patch(f"{AMBIENT}._axi_command", return_value="/bin/pkgdx"),
        mock.patch(f"{AMBIENT}.mcp_available", return_value=True),
    ):
        changed = setup_ambient_context(tmp_path)

    assert set(changed) == {"AGENTS.md", ".vscode", ".mcp.json"}
    assert all(changed.values())


def test_setup_ambient_context_skips_mcp_when_unavailable(
    tmp_path: Path,
) -> None:
    """Without `fastmcp`, `AGENTS.md` is still injected but no MCP
    config file is registered."""
    with mock.patch(f"{AMBIENT}.mcp_available", return_value=False):
        changed = setup_ambient_context(tmp_path)

    assert changed == {"AGENTS.md": True, ".vscode": False, ".mcp.json": False}
    assert (tmp_path / "AGENTS.md").exists()
    assert not (tmp_path / ".vscode" / "mcp.json").exists()
    assert not (tmp_path / ".mcp.json").exists()
