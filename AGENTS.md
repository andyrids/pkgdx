---
context-hierarchy: Layer 0
---

# Global Context

You are an expert Python software engineer acting as an autonomous developer for the PyTack project,
which implements canonical standards across consuming Python projects.

## Environment & Toolchain

PyTack is developed and maintained with Astral uv, which MUST be installed globally or in the
virtual environment.

- **Language**: Python >=3.11
- **OS**: Windows/Linux/WSL2

| Tool         | Function                  |
| ------------ | ------------------------- |
| uv           | Package manager           |
| PyMarkdown   | linter/formatter          |
| Ruff         | linter/formatter          |
| Mypy         | Static type checker       |
| Pytest       | Unit tests                |
| Prek         | Pre-commit hook framework |

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
├── _config/                   <-- Shared constraints & reference material
├── create-feature/            <-- Create new feature
│   ├── CONTEXT.md
│   └── stages/                <-- 4-stage pipeline
│       ├── 01-specification/  <-- Feature specification
│       ├── 02-implementation/ <-- Feature implementation
│       ├── 03-verification/   <-- Feature evaluation
│       └── 04-documentation/  <-- Feature documentation
│
├── create-unit-test/          <-- Create new unit test
│   ├── CONTEXT.md
│   └── stages/                <-- 4-stage pipeline
│
├── create-documentation/      <-- Create new documentation
│   ├── CONTEXT.md
│   └── stages/                <-- 4-stage pipeline
```

## Routing

| Task                 | Navigate to                      | Read        | Skill   |
| -------------------- | -------------------------------- | ----------- | ------- |
| Create feature       | workspaces/create-feature/       | CONTEXT.md  | -       |
| Create unit test     | workspaces/create-unit-test/     | CONTEXT.md  | -       |
| Create documentation | workspaces/create-documentation/ | CONTEXT.md  | -       |
| Code review          | src/                             | *           | -       |

## Token Efficiency

- Each task is performed within a specific workspace
- Each workspace is compartmentalised
- Each workspace `CONTEXT.md` provides all necessary context
- Avoid unnecessary files in `__pycache__`

## Naming Conventions

### References

| Reference      | Pattern                           | Example                        |
| -------------- | --------------------------------- | ------------------------------ |
| Toolchain      | `reference-toolchain-[tool].md`   | `reference-tool-mypy.md`       |
| Code snippets  | `reference-cookbook-[package].md` | `reference-cookbook-rich.md`   |

### Output

| Output                | Pattern                  | Example                       |
| --------------------- | ------------------------ | ----------------------------- |
| Feature specification | `[feature-slug]-spec.md` | `rich-progress-bar-spec.md`   |
| Implementation report | `[feature-slug]-code.md` | `rich-progress-bar-code.md`   |
| Verification report   | `[feature-slug]-test.md` | `rich-progress-bar-test.md`   |
| Documentation report  | `[feature-slug]-docs.md` | `rich-progress-bar-docs.md`   |
