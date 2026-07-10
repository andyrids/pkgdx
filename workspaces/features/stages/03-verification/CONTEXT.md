---
context-hierarchy: Layer 2
---

# Verification

Validate the newly implemented code through unit testing, consumer testing, and standard compliance checks.

## Inputs

- `02-implementation/output/[slug]-code.md`
- `03-verification/references/*` (any relevant reference material)
- `workspaces/_config/*` (any relevant reference material)

## Process

1. Review the code in `02-implementation/output/[slug]-code.md`
2. Write unit tests in `tests/` to cover new feature logic
3. CHECKPOINT - await user review in accordance with acceptance criteria
4. Execute consumer package testing against `consumers/testing/` package
5. Ensure unit tests are robust for GitLab CI/CD environments
6. Ensure Prek hooks still pass

## Outputs

Create a unit test and verification report.

- [slug]-test.md -> `03-verification/output/`
