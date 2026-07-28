---
context-hierarchy: Layer 1
context-hierarchy-role: Workspace task routing
maximum-context-tokens: 300
---

# Workspace Routing

## Routing

Each task category heading details necessary context and locations.

### Create Feature

- **Navigate to**: `ICM/create-feature`
- **Read**: `CONTEXT.md`
- **Exclude**: * in `.gitignore`

### Create Documentation

- **Navigate to**: `ICM/create-documentation`
- **Read**: `CONTEXT.md`
- **Exclude**: * in `.gitignore`

### Create Unit Test

- **Navigate to**: `ICM/create-unit-test`
- **Read**: `CONTEXT.md`
- **Exclude**: * in `.gitignore`

### Code Refactor

- **Navigate to**: `ICM/create-feature`
- **Read**: `CONTEXT.md`
- **Exclude**: * in `.gitignore`

### Code Review

- **Navigate to**:
  - `src/`
    **Read**: `pkgdx/*`
  - `tests/`
    **Read**: `*`
  - `ICM/_config/`
    - **Read**:
      - `reference-toolchain-logging`
      - `reference-toolchain-mypy`
      - `reference-toolchain-ruff`
- **Exclude**: * in `.gitignore`
