---
context-hierarchy: Layer 2
context-hierarchy-role: Stage control point
maximum-context-tokens: 500
---

# Verification

Validate the newly implemented documentation through review and standard compliance checks.

## Inputs

- `02-implementation/output/[doc-slug]-code.md`
- `03-verification/references/*` (any relevant reference material)
- `workspaces/_config/*` (any relevant reference material)

## Process

1. Review the changes listed in `02-implementation/output/[doc-slug]-code.md`
2. Verify documentation renders correctly
3. CHECKPOINT - await user review in accordance with acceptance criteria
4. Ensure Prek hooks still pass

## Outputs

Create a verification report.

- [doc-slug]-test.md -> `03-verification/output/`
