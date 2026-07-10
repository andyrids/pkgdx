---
context-hierarchy: Layer 0
---

# `pkgdevx` - Global Context

You are an expert Python software engineer acting as an autonomous developer for the `pkgdevx` project,
which implements canonical standards across consuming Python projects.

## Environment & Toolchain

- **Language**: Python >=3.10
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
pkgdevx/
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
└── features/                 <-- Create new feature
  ├── CONTEXT.md
  └── stages/                 <-- 4-stage pipeline
      ├── 01-planning/        <-- Feature specification
      ├── 02-implementation/  <-- Feature implementation
      ├── 03-verification/    <-- Feature testing
      └── 04-documentation/   <-- Feature documentation
```

## Routing

| Task                   | Navigate to          | Read        | Skill   |
| ---------------------- | -------------------- | ----------- | ------- |
| New feature            | workspaces/features/ | CONTEXT.md  | -       |
| Code review            | src/pkgdevx/         | *           | -       |

## Token Efficiency

- Each task is performed within a specific workspace
- Each workspace is compartmentalised
- Each workspace `CONTEXT.md` provides all necessary context

## Naming Conventions

### References

| Reference        | Pattern                    | Example                          |
| ---------------- | -------------------------- | -------------------------------- |
| Toolchain        | `reference-tool-[tool].md` | `reference-tool-mypy.md`         |
| Code snippets    | `cookbook-[package].md`    | `reference-cookbook-rich.md`     |

### Output

| Output                | Pattern                | Example                       |
| --------------------- | ---------------------- | ----------------------------- |
| Feature specification | `[slug]-spec.md`       | `rich-progress-bar-spec.md`   |
| Implementation report | `[slug]-code.md`       | `rich-progress-bar-code.md`   |
| Verification report   | `[slug]-test.md`       | `rich-progress-bar-test.md`   |
| Documentation report  | `[slug]-docs.md`       | `rich-progress-bar-docs.md`   |
