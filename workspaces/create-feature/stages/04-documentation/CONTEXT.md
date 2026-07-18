---
context-hierarchy: Layer 2
context-hierarchy-role: Stage control point
maximum-context-tokens: 500
---

# Documentation

Finalise the workflow by updating project documentation to reflect the new feature and changes.

## Inputs

- `01-specification/output/[slug]-spec.md`
- `02-implementation/output/[slug]-code.md`
- `03-verification/output/[slug]-test.md`
- `REFERENCE.md`

## Process

1. Review the output from previous stages
2. Create a documentation report
   - List relevant documentation updates
     - `README.md`, `CHANGELOG.md` etc.
     - Provide sufficient detail for a `create-documentation` specification
   - List unit test & compliance check updates
     - Provide sufficient detail for a `create-unit-test` specification
   - List any new reusable design pattern introduced during implementation (e.g. a new Rich/CLI
     UX pattern) to be appended to the relevant `workspaces/_config/reference-*.md` file, so it
     becomes the canonical reference for future features
3. CHECKPOINT - await user review in accordance with acceptance criteria

## Outputs

- [slug]-docs.md -> `04-documentation/output/`
