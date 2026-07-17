---
context-hierarchy: Layer 2
---

# Implementation

Write documentation for the specification from the Specification stage.

## Inputs

- `01-specification/output/[doc-slug]-spec.md`
- `02-implementation/references/*` (any relevant reference material)
- `workspaces/_config/*` (any relevant reference material)

## Process

1. Read the documentation specification
2. Implement the required documentation changes
3. Adhere to the workspace toolchain
   - Astral uv dependency management
   - Check Markdown linting rules
4. Draft the implementation report
   - List each file modified
   - Explain the reasoning behind each modification
5. CHECKPOINT - await user review in accordance with acceptance criteria

## Outputs

Summary of documentation added, files changed, reasoning, and a diff report.

- [doc-slug]-code.md -> `02-implementation/output/`
