---
context-hierarchy: Layer 3
context-hierarchy-role: Rules, conventions and guidelines
---

# Toolchain - `Prek`

Prek is used as a pre-commit hook manager and is installed as a dependency. Running Prek through
`uv run` ensures that the project virtual environment is activated and utilised.

## Commands

- `uv run prek install` - Install Git shims
- `uv run prek run` - Run hooks for files staged in Git
- `uv run prek run -vvv` - Run hooks with verbose output
- `uv run prek run --all-files` - Run hooks for all files
- `uv run prek validate-config prek.toml` - Validate a Prek config

## Configuration

- Project config: `prek.toml`
  - Root Prek config for the PyTack package
  - MUST not be changed
- Bundled config: `src/pytack/standards/hooks.toml`
  - Used by repositories that consume PyTack
