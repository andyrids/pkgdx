---
context-hierarchy: Layer 1
context-hierarchy-role: Workspace task routing
maximum-context-tokens: 300
---

# Create Unit Test

## Overview

This workspace is used to create new unit tests for this project.

## Routing

### Specification Stage

- **Navigate to**: stages/01-specification
- **Read**: CONTEXT.md

### Implementation Stage

- **Navigate to**: stages/02-implementation
- **Read**: CONTEXT.md

### Verification Stage

- **Navigate to**: stages/03-verification
- **Read**: CONTEXT.md

## Navigation

```text
create-unit-test/
├── CONTEXT.md
└── stages/                  <-- 3-stage pipeline
    ├── 01-specification/    <-- Test specification
    │   ├── CONTEXT.md       <-- Stage routing & reference material
    │   └── output/          <-- Technical specification
    │
    ├── 02-implementation/   <-- Test implementation
    │   ├── CONTEXT.md       <-- Stage routing & reference material
    │   └── output/          <-- Implemented tests
    │
    └── 03-verification/     <-- Test verification
        ├── CONTEXT.md       <-- Stage routing & reference material
        └── output/          <-- Verification report
```

## Acceptance Criteria

- Artifact creation in accordance with stage guidance
- Stage checkpoint review
  - User review & acceptance of each output artifact
  - User review & acceptance of modified/created sourcecode
  - User review & acceptance must be explicit before continuation
    - "approved" or "continue" response
