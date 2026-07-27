---
context-hierarchy: Layer 2
context-hierarchy-role: Stage control point
maximum-context-tokens: 500
---

# Verification

Validate newly implemented tests through execution and standard compliance checks.

## Inputs

- `02-implementation/output/[slug]-code.md`

## Reference Material

- Read:
  - `ICM/_config/reference-toolchain-mypy.md`
  - `ICM/_config/reference-toolchain-ruff.md`
  - `ICM/_config/reference-toolchain-prek.md`
  - `ICM/_config/reference-toolchain-pytest.md`
  - `ICM/_config/reference-toolchain-uv.md`

## Process

1. Review the changes listed in `02-implementation/output/[slug]-code.md`
2. Execute the new unit tests
3. Execute the full test suite to detect regressions
4. CHECKPOINT - await user review in accordance with acceptance criteria
5. Ensure Prek hooks still pass

## Outputs

Create a verification report.

- [slug]-test.md -> `03-verification/output/`
