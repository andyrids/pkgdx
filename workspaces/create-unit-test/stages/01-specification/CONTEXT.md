---
context-hierarchy: Layer 2
---

# Specification

Analyse the incoming task and generate a comprehensive test specification.

## Inputs

- User unit test request prompt
- `workspaces/create-feature/stages/04-documentation/output/*` (any reference material)
- `01-specification/references/*` (any relevant reference material)
- `workspaces/_config/*` (any relevant reference material)

## Process

1. Read the provided test request
2. Consult relevant reference material for additional context
3. Identify the source code under test within `src/`
4. Draft the test specification
   - Follow IEEE 830 standard
5. CHECKPOINT - await user review in accordance with acceptance criteria

## Outputs

- [slug]-spec.md -> `01-specification/output/`
