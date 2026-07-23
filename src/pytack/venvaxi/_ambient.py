"""Agent eXperience Interface (AXI) ambient-context installation.

AXI principle 7 (ambient context): Make visible to an agent from an
explicit setup command so that every conversation starts with relevant state
already visible - before the agent takes any action.

- Inject a marked block into the `AGENTS.md` of a consuming repo
- Register an MCP server entry in `.vscode/mcp.json`
- Register an MCP server entry in a `.mcp.json`

NOTE: The above steps are idempotent - running `venv-axi setup` multiple times
has no adverse effect.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__package__)

_BEGIN = "<!-- pytack:venv-axi:begin -->"
_END = "<!-- pytack:venv-axi:end -->"

_BLOCK_BODY = """## venv-axi

Agent-ergonomic venv package & API information is available via
`venv-axi`.

- Run `venv-axi` for live status and next-step hints.
- Run `venv-axi list` for the installed dependency list.
- Run `venv-axi show <package>` for package metadata.
- Run `venv-axi show <package> --api` for a package's public API.
- Run `venv-axi find <query>` to search cached symbols by name or doc.
- Run `venv-axi inspect <qualified_name>` for full detail on one symbol
  (qualified names use `module::Symbol` or `module::Class.method`).
- Run `venv-axi tree <package>` to explore a package's module tree.
- Run `venv-axi serve` to start the MCP server over stdio.
- Run `venv-axi setup` to register the MCP server in `.vscode/mcp.json`
  and `.mcp.json` and keep this block up to date."""


def _venv_axi_command() -> str:
    """Resolves the absolute path to the running `venv-axi` executable.

    Returns:
        The absolute path of the invoked `venv-axi`/`pytack-venv-axi`
        script.
    """
    return str(Path(sys.argv[0]).resolve())


def inject_agents_md(root: Path) -> bool:
    """Idempotently injects the ambient-context block into `AGENTS.md`.

    Args:
        root: The consuming repo's root path.

    Returns:
        True if `AGENTS.md` was created or modified.
    """
    path = root / "AGENTS.md"
    block = f"{_BEGIN}\n{_BLOCK_BODY}\n{_END}"

    if not path.exists():
        path.write_text(f"{block}\n", encoding="utf-8")
        logger.debug("Created `AGENTS.md` with venv-axi block")
        return True

    text = path.read_text(encoding="utf-8")
    if _BEGIN in text and _END in text:
        start = text.index(_BEGIN)
        end = text.index(_END) + len(_END)
        updated = text[:start] + block + text[end:]
        if updated == text:
            logger.debug("`AGENTS.md` venv-axi block is up-to-date")
            return False
        path.write_text(updated, encoding="utf-8")
        logger.debug("Updated `AGENTS.md` venv-axi block")
        return True

    separator = "\n\n" if text and not text.endswith("\n\n") else ""
    path.write_text(f"{text}{separator}{block}\n", encoding="utf-8")
    logger.debug("Appended venv-axi block to `AGENTS.md`")
    return True


def _update_mcp_json(path: Path, servers_key: str) -> bool:
    """Idempotently registers the venv-axi server in an MCP config file.

    Args:
        path: The MCP config JSON file path.
        servers_key: The top-level key holding server entries
            (`"servers"` for VS Code, `"mcpServers"` elsewhere).

    Returns:
        True if `path` was created or modified.
    """
    data: dict[str, Any] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("Ignoring malformed `%s`", path)
            data = {}

    servers = data.setdefault(servers_key, {})
    entry = {
        "type": "stdio",
        "command": _venv_axi_command(),
        "args": ["serve"],
    }

    if servers.get("venv-axi") == entry:
        return False

    servers["venv-axi"] = entry
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def setup_ambient_context(root: Path) -> dict[str, bool]:
    """Installs `venv-axi` ambient context into the consuming repo.

    Args:
        root: The consuming repo's root path.

    Returns:
        A mapping of which artifacts were created or modified:
        `agents_md`, `vscode_mcp` and `repo_mcp`.
    """
    return {
        "AGENTS.md": inject_agents_md(root),
        ".vscode": _update_mcp_json(root / ".vscode" / "mcp.json", "servers"),
        ".mcp.json": _update_mcp_json(root / ".mcp.json", "mcpServers"),
    }
