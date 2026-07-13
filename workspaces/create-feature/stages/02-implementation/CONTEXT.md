---
context-hierarchy: Layer 2
---

# Implementation

Write Python code for the technical specification from the planning stage.

## Inputs

- `01-planning/output/[slug]-spec.md`
- `02-implementation/references/*` (any relevant reference material)
- `workspaces/_config/*` (any relevant reference material)

## Process

1. Read the specification in `01-planning/output/[slug]-spec.md`
2. Implement the required logic within `src/pytack/`
3. Adhere to the workspace toolchain
   - Astral uv dependency management
   - Check typing, linting & formatting rules
4. Draft the implimentation report
5. CHECKPOINT - await user review in accordance with acceptance criteria

## Outputs

Summary of code added, files changed, reasoning, and a diff report.

- [slug]-code.md -> `02-implementation/output/`
