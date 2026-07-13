---
context-hierarchy: Layer 2
---

# Planning

Analyse the incoming task and generate a comprehensive technical specification.

## Inputs

- User feature request prompt
- `01-specification/references/*` (any relevant reference material)
- `workspaces/_config/*` (any relevant reference material)

## Process

1. Read the provided feature request
2. Consult relevant reference material for additional context
3. Define the architecture changes required within `src/`
4. Draft the specification
   - Focus on robust design
   - Reuse existing patterns in the codebase
   - Prefer the standard library over additional dependencies
   - Prefer existing dependencies over adding a new one
5. CHECKPOINT - await user review in accordance with acceptance criteria

## Outputs

- [slug]-spec.md -> `01-planning/output/`
