---
context-hierarchy: Layer 3
context-hierarchy-role: Rules, conventions and guidelines
---

# Toolchain - `PyMarkdown`

PyMarkdown is used to implement Markdown linting standards.

## Commands

- `uv run pymarkdown --config src/pkgdx/standards/pymarkdown.toml scan <file>` - Lint a file
- `uv run prek run --all-files` - Run the `markdown` hook alongside all other hooks

## Configuration

The PyMarkdown config is located at `src/pkgdx/standards/pymarkdown.toml`.
