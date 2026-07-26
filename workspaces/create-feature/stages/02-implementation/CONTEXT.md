---
context-hierarchy: Layer 2
context-hierarchy-role: Stage control point
maximum-context-tokens: 500
---

# Implementation

Write Python code for the technical specification from the Specification stage.

## Inputs

- `01-specification/output/[slug]-spec.md`
- `REFERENCE.md`

## Process

1. Read the specification
2. Implement the required logic within `src/pkgdx/`
3. Adhere to the workspace toolchain
4. Draft the implimentation report
   - List Git command to generate a diff report
   - List changes in accordance with specification
     - List each file modified
     - Explain decisions
5. CHECKPOINT - await user review in accordance with acceptance criteria

## Outputs

- [slug]-code.md -> `02-implementation/output/`
