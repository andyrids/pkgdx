---
context-hierarchy: Layer 2
---

# Specification

Analyse the incoming task and generate a comprehensive documentation specification.

## Inputs

- User documentation request prompt
- `ICM/_config/*` (any relevant reference material)

## Process

1. Read the provided documentation request
2. Consult relevant reference material for additional context
3. Identify the target documentation files (e.g., `README.md`, `docs/`, `CHANGELOG.md`)
4. Draft the documentation specification
   - Focus on clarity and consistency
   - Reuse existing documentation patterns in the codebase
5. CHECKPOINT - await user review in accordance with acceptance criteria

## Outputs

- [doc-slug]-spec.md -> `01-specification/output/`
