---
context-hierarchy: Layer 2
context-hierarchy-role: Stage control point
maximum-context-tokens: 500
---

# Verification

Validate code changes through existing unit tests, consumer testing and standard compliance checks.

## Inputs

- `02-implementation/output/[slug]-code.md`

## Reference Material

- Read:
  - `ICM/_config/reference-toolchain-prek.md`
  - `ICM/_config/reference-toolchain-pytest.md`
  - `ICM/_config/reference-toolchain-coverage.md`
  - `ICM/_config/reference-toolchain-uv.md`
  - `Justfile`

## Process

1. Review the changes listed in `02-implementation/output/[slug]-code.md`
2. Run existing unit tests
3. CHECKPOINT - await user review in accordance with acceptance criteria
4. Ensure Prek hooks still pass
5. CHECKPOINT - await user review in accordance with acceptance criteria
6. Execute consumer package testing against `consumers/testing/` package
7. CHECKPOINT - await user review in accordance with acceptance criteria
8. Draft a verification report
   - List requirement identifiers accounted for
   - List requirement identifiers not covered by existing testing & compliance checks
   - List unit test coverage (if existing tests pass)
9. CHECKPOINT - await user review in accordance with acceptance criteria

## Outputs

- [slug]-test.md -> `03-verification/output/`
