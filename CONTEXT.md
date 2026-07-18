---
context-hierarchy: Layer 1
context-hierarchy-role: Workspace task routing
maximum-context-tokens: 300
---

# Workspace Routing

## Routing

Each task category heading details necessary context and locations.

### Create Feature

- **Navigate to**: `workspaces/create-feature`
- **Read**: `CONTEXT.md`
- **Exclude**: * in `.gitignore`

### Create Documentation

- **Navigate to**: `workspaces/create-documentation`
- **Read**: `CONTEXT.md`

### Create Unit Test

- **Navigate to**: `workspaces/create-unit-test`
- **Read**: `CONTEXT.md`

### Code Refactor

- **Navigate to**: `workspaces/create-feature`
- **Read**: `CONTEXT.md`
- **Exclude**: * in `.gitignore`

### Code Review

- **Navigate to**:
  - `src/`
    **Read**: `pytack/*`
  - `tests/`
    **Read**: `*`
  - `workspaces/_config/`
    - **Read**:
      - `reference-toolchain-logging`
      - `reference-toolchain-mypy`
      - `reference-toolchain-ruff`
- **Exclude**: * in `.gitignore`
