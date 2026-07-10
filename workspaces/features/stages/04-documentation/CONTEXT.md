---
context-hierarchy: Layer 2
---

# Documentation

Finalise the workflow by updating project documentation to reflect the new feature and changes.

## Inputs

- `01-planning/output/[slug]-spec.md`
- `02-implementation/output/[slug]-code.md`
- `03-verification/output/[slug]-test.md`
- `04-documentation/references/*` (any relevant reference material)
- `workspaces/_config/*` (any relevant reference material)

## Process

1. Review the output from previous stages
2. Update `CHANGELOG.md`
   - Adhere to 'Keep a Changelog' format
   - Categorise changes appropriately
3. Update `README.md` if necessary
4. CHECKPOINT - await user review in accordance with acceptance criteria

## Outputs

Create a final documentation update report.

- [slug]-docs.md -> `04-documentation/output/`
