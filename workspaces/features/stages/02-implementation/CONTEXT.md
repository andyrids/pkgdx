---
context-hierarchy: Layer 2
---

# Implementation

Write Python code for the technical specification from the planning stage.

## Inputs

- `01-planning/output/[slug]-spec.md`

## Process

1. Read the specification in `01-planning/output/[slug]-spec.md`
2. Implement the required logic within `src/pkgdevx/`
3. Adhere to the workspace toolchain
   - Astral uv dependency management
   - Check typing, linting & formatting rules

## Outputs

Summary of code added, files changed, reasoning, and a diff report.

- [slug]-code.md -> `02-implementation/output/`
