---
context-hierarchy: Layer 0
maximum-context-tokens: 800
---

# Global Context

You are an expert Python software engineer acting as a developer for the PyTack project, which
implements canonical standards across consuming Python projects.

- Follow YAGNI principles
- Resuse existing patterns in the codebase
- Use the Standard Library over a dependency
- Use an existing dependency over a new one
- Use a one-liner where possible
- Write the minimum code that works

## Environment and Toolchain

PyTack is developed and maintained with Astral uv, which MUST be installed globally or in the
virtual environment.

- **Language**: Python >=3.11
- **OS**: Windows/Linux/WSL2

| Tool              | Function                  |
| ----------------- | ------------------------- |
| uv                | Package manager           |
| PyMarkdown        | linter/formatter          |
| Ruff              | linter/formatter          |
| Mypy              | Static type checker       |
| Pytest            | Unit tests                |
| Coverage          | Unit test coverage        |
| Prek              | Pre-commit hook framework |
| Logging (stdlib)  | Logging                   |
| Argparse (stdlib) | CLI                       |

## Navigation

```text
pytack/
├── AGENTS.md                 <-- Global project context
├── CHANGELOG.md              <-- Project CHANGELOG
├── CLAUDE.md -> AGENTS.md    <-- Symbolic link to AGENTS.md
│
├── consumers/                <-- Astral workspace members
│   └── testing/              <-- Testing package
│
├── CONTEXT.md                <-- Task routing
├── COPYRIGHT                 <-- Project COPYRIGHT
│
├── docs/                     <-- Project documentation
│
├── Justfile                  <-- Just recipes
├── LICENSE                   <-- Project LICENSE
├── prek.toml                 <-- Prek pre-commit hook configuration
├── pyproject.toml            <-- Project configuration
├── README.md                 <-- Project README
│
├── src/                      <-- Project sourcecode
│    └── pytack
│        ├── exceptions.py        <-- Exceptions
│        ├── __init__.py
│        ├── logging              <-- Logging
│        │   ├── config.toml      <-- Logging config
│        │   ├── __init__.py
│        │   └── _logging.py
│        ├── __main__.py          <-- Main CLI
│        ├── py.typed
│        ├── standards            <-- Canonical standards
│        │   ├── hooks.toml       <-- Consuming repo Prek config
│        │   ├── __init__.py
│        │   ├── mypy.ini         <-- Consuming repo Mypy config
│        │   ├── pymarkdown.toml  <-- Consuming repo PyMarkdown config
│        │   └── ruff.toml        <-- Consuming repo Ruff config
│        └── _types.py
│
├── tests/                    <-- Project unit tests
│
├── uv.lock                   <-- Project dependency lockfile
│
└── workspaces/               <-- Task workspaces
```

## Workspaces

Each workspace has a `CONTEXT.md`, which is the main control point.

```text
workspaces/
├── _config/                   <-- Shared reference material
├── create-feature/            <-- Create new feature
│   ├── CONTEXT.md
│   └── stages/                <-- Pipeline stages
│
├── create-unit-test/          <-- Create new unit test
│   ├── CONTEXT.md
│   └── stages/                <-- Pipeline stages
│
├── create-documentation/      <-- Create new documentation
│   ├── CONTEXT.md
│   └── stages/                <-- Pipeline stages
```

## Routing

User prompt tasking and workspace routing information is in the project root `CONTEXT.md`.

## Token Efficiency

- Each task is performed within a specific workspace
- Each workspace is compartmentalised
- Each workspace `CONTEXT.md` provides necessary context
- Avoid unnecessary files listed in `.gitignore`

## Naming Conventions

### References

| Reference      | Pattern                           | Example                          |
| -------------- | --------------------------------- | -------------------------------- |
| Toolchain      | `reference-toolchain-[tool].md`   | `reference-toolchain-mypy.md`    |
| Cookbook       | `reference-cookbook-[package].md` | `reference-cookbook-rich.md`     |
| Standard       | `reference-standard-[name].md`    | `reference-standard-techspec.md` |

### Output

| Output                | Pattern          | Example                       |
| --------------------- | ---------------- | ----------------------------- |
| Specification report  | `[slug]-spec.md` | `rich-progress-bar-spec.md`   |
| Implementation report | `[slug]-code.md` | `rich-progress-bar-code.md`   |
| Verification report   | `[slug]-test.md` | `rich-progress-bar-test.md`   |
| Documentation report  | `[slug]-docs.md` | `rich-progress-bar-docs.md`   |
