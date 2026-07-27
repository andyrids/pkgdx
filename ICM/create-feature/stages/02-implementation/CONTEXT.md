---
context-hierarchy: Layer 2
context-hierarchy-role: Stage control point
maximum-context-tokens: 500
---

# Implementation

Write Python code for the technical specification from the Specification stage.

## Inputs

- `01-specification/output/[slug]-spec.md`

## Reference Material

- Read:
  - `ICM/_config/reference-toolchain-logging.md`
  - `ICM/_config/reference-toolchain-mypy.md`
  - `ICM/_config/reference-toolchain-prek.md`
  - `ICM/_config/reference-toolchain-pytest.md`
  - `ICM/_config/reference-toolchain-ruff.md`
  - `ICM/_config/reference-toolchain-uv.md`
  - `ICM/_config/reference-cookbook-rich.md`
  - `ICM/_config/reference-standard-attribution.md`

## Process

1. Read the specification
2. Implement the required logic within `src/pkgdx/`
3. Adhere to the workspace toolchain
4. Draft the implementation report
   - List Git command to generate a diff report
   - List changes in accordance with specification
     - List each file modified
     - Explain decisions
5. CHECKPOINT - await user review in accordance with acceptance criteria

## Outputs

- [slug]-code.md -> `02-implementation/output/`
