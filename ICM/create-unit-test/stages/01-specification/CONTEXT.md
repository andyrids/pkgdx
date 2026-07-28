---
context-hierarchy: Layer 2
context-hierarchy-role: Stage control point
maximum-context-tokens: 500
---

# Specification

Analyse the incoming task and generate a comprehensive test specification.

## Inputs

- User unit test request prompt

## Reference Material

- Read:
  - `ICM/_config/reference-toolchain-mypy.md`
  - `ICM/_config/reference-toolchain-ruff.md`
  - `ICM/_config/reference-toolchain-prek.md`
  - `ICM/_config/reference-toolchain-pytest.md`

## Process

1. Read the provided test request
2. Consult relevant reference material for additional context
3. Identify the source code under test within `src/`
4. Draft the test specification
   - Follow IEEE 830 standard
5. CHECKPOINT - await user review in accordance with acceptance criteria

## Outputs

- [slug]-spec.md -> `01-specification/output/`
