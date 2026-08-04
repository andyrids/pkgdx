---
context-hierarchy: Layer 3
context-hierarchy-role: Rules, conventions and guidelines
---

# Toolchain - `uv`

Astral uv is used to manage this project.

## Commands

The `uv run` command should be used to interface with any installed Python dependency or CLI as this
will activate the project virtual environment if necessary.

The project dependencies can be listed with the `uv pip list` command.

## Scripts

Scripts can be read from `stdin`:

```bash
uv run - << 'EOF'
print("hello world!")
EOF
```

When using `uv run` in this project, uv will install Pkgdx before running the script. If the
script does not depend on Pkgdx, use the `--no-project` option.

Example script with dependencies added into an inline metadata format:

```bash
uv run - << 'EOF'
# /// script
# dependencies = [
#   "requests",
#   "rich",
# ]
# ///

import requests
from rich.pretty import pprint

resp = requests.get("https://peps.python.org/api/peps.json")
data = resp.json()
pprint([(k, v["title"]) for k, v in data.items()][:10])
EOF
```

NOTE: Any dependencies not included with Pkgdx must be declared in the script.

## Workspaces

This project uses Astral uv workspaces, which are in `consumers/*`. When testing Pkgdx commands
in workspace members with uv, the `--directory` option should be used to generate output in the
workspace member root.

```bash
uv run --directory consumers/testing pkgdx init
```

NOTE: Only run Pkgdx commands in workspace members, which have a `pkgdx` dependency in their
`pyproject.toml`.
