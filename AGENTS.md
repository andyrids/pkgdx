---
context-hierarchy: Layer 0
context-hierarchy-role: Global identity
maximum-context-tokens: 800
---

# Global Context

You are an expert Python software engineer acting as a developer for the Pkgdx project - a DevX
toolkit, providing tools that streamline Python project development:

1. CLI for canonical standards implementation across consuming Python projects
2. Agent eXperience Interface (AXI) CLI for token-efficient querying of venv dependencies

## General Guidance

- Follow YAGNI principles
- Reuse existing patterns in the codebase
- Use the Standard Library over a dependency
- Use an existing dependency over a new one
- Use a one-liner where possible
- Write the minimum code that works
- For technical decisions
  - Do not give much weight to development cost
  - Prefer quality, simplicity, robustness & scalability

## Environment and Toolchain

Pkgdx is developed with Astral uv, which MUST be installed globally or in the venv.

- **Language**: Python >=3.11
- **OS**: Windows/Linux/WSL2

## Navigation

```text
pkgdx/
├── consumers/                <-- Astral workspace members
│   └── testing/              <-- Testing package
│
├── docs/                     <-- Project documentation
│
├── src/                      <-- Project sourcecode
│    └── pkgdx
│        ├── logging              <-- Logging
│        │   ├── config.toml      <-- Logging config
│        │   ├── __init__.py
│        │   └── _logging.py
│        │
│        ├── standards            <-- Canonical standards
│        │   ├── hooks.toml       <-- Consuming repo Prek config
│        │   ├── __init__.py
│        │   ├── mypy.ini         <-- Consuming repo Mypy config
│        │   ├── pymarkdown.toml  <-- Consuming repo PyMarkdown config
│        │   └── ruff.toml        <-- Consuming repo Ruff config
│        │
│        ├── venvaxi              <-- Agent eXperience Interface (venv-axi)
│        │   ├── __init__.py
│        │   ├── _ambient.py      <-- AXI principle 7 - Ambient Context
│        │   ├── _cli.py          <-- venv-axi CLI
│        │   ├── _introspect.py   <-- API & docstring introspection
│        │   ├── _mcp.py          <-- FastMCP server
│        │   ├── _packages.py     <-- Dependency discovery
│        │   └── _toon.py_        <-- TOON (Token-Oriented Object Notation) encoder
│        │
│        ├── _core.py             <-- Core CLI logic
│        ├── exceptions.py        <-- Exceptions
│        ├── __init__.py
│        ├── __main__.py          <-- Main CLI
│        ├── py.typed
│        └── _types.py
│
├── tests/                  <-- Project unit tests
│
├── ICM/                    <-- Task workspaces
│
├── AGENTS.md               <-- Global project context
├── CHANGELOG.md            <-- Project CHANGELOG
├── CLAUDE.md -> AGENTS.md  <-- Symbolic link to AGENTS.md
├── CONTEXT.md              <-- Task routing
├── COPYRIGHT               <-- Project COPYRIGHT
├── Justfile                <-- Just recipes
├── LICENSE                 <-- Project LICENSE
├── prek.toml               <-- Prek pre-commit hook configuration
├── pyproject.toml          <-- Project configuration
├── README.md               <-- Project README
└── uv.lock                 <-- Project dependency lockfile
```

## Workspaces

Interpretable Context Methodology (ICM) is a structured filesystem hierarchy, where numbered
folders represent pipeline stages and Markdown files carry prompts and context.

Each ICM workspace has a `CONTEXT.md`, which is the main control point.

## Routing

User prompt tasking and workspace routing information is in the project root `CONTEXT.md`.

In Claude Code, the `/create-feature`, `/create-unit-test` and `/create-documentation` commands
(`.claude/commands/`) are the preferred entry points to each workspace pipeline.

## Token Efficiency

- Each task is performed within a specific ICM workspace
- Each workspace is compartmentalised
- Each workspace `CONTEXT.md` provides necessary context
- Avoid unnecessary files listed in `.gitignore`
