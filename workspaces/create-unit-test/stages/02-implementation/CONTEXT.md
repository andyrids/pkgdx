---
context-hierarchy: Layer 2
context-hierarchy-role: Stage control point
maximum-context-tokens: 500
---

# Implementation

Write unit tests for the test specification from the Specification stage.

## Inputs

- `01-specification/output/[slug]-spec.md`
- `02-implementation/references/*` (any relevant reference material)
- `workspaces/_config/*` (any relevant reference material)

## Process

1. Read the specification
2. Implement the required tests within `tests/`
3. Adhere to the workspace toolchain
   - Astral uv dependency management
   - Check typing, linting & formatting rules
4. Draft the implementation report
   - List a command to generate a diff report
   - List each file modified
   - Explain reasoning behind each modification
5. CHECKPOINT - await user review in accordance with acceptance criteria

## Outputs

- [slug]-code.md -> `02-implementation/output/`
