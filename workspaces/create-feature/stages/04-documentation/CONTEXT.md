---
context-hierarchy: Layer 2
---

# Documentation

Finalise the workflow by updating project documentation to reflect the new feature and changes.

## Inputs

- `01-specification/output/[slug]-spec.md`
- `02-implementation/output/[slug]-code.md`
- `03-verification/output/[slug]-test.md`
- `04-documentation/references/*` (any relevant reference material)
- `workspaces/_config/*` (any relevant reference material)

## Process

1. Review the output from previous stages
2. Create a documentation report
   - List relevant documentation updates
     - `README.md`, `CHANGELOG` etc.
     - Provide sufficient detail for a `create-documentation` specification
   - List unit test & compliance check updates
     - Provide sufficient detail for a `create-unit-test` specification
3. CHECKPOINT - await user review in accordance with acceptance criteria

## Outputs

- [slug]-docs.md -> `04-documentation/output/`
