---
context-hierarchy: Layer 2
---

# Verification

Validate code changes through unit testing, consumer testing and standard compliance checks.

## Inputs

- `02-implementation/output/[slug]-code.md`
- `03-verification/references/*` (any relevant reference material)
- `workspaces/_config/*` (any relevant reference material)

## Process

1. Review the changes listed in `02-implementation/output/[slug]-code.md`
2. Ensure unit tests pass
3. CHECKPOINT - await user review in accordance with acceptance criteria
4. Ensure Prek hooks still pass
5. CHECKPOINT - await user review in accordance with acceptance criteria
6. Execute consumer package testing against `consumers/testing/` package
7. CHECKPOINT - await user review in accordance with acceptance criteria
8. Draft a verification report
   - List requirement identifiers accounted for
   - List requirement identifiers not covered by existing testing & compliance checks
   - List unit test coverage
9. CHECKPOINT - await user review in accordance with acceptance criteria

## Outputs

- [slug]-test.md -> `03-verification/output/`
