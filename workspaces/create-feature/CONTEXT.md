---
context-hierarchy: Layer 1
context-hierarchy-role: Workspace task routing
maximum-context-tokens: 300
---

# Create Feature

## Overview

This workspace is used to create new features or refactor existing ones.

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

### Documentation Stage

- **Navigate to**: stages/04-documentation
- **Read**: CONTEXT.md

## Navigation

```text
create-feature/
├── CONTEXT.md
└── stages/                  <-- 4-stage pipeline
    ├── 01-specification/    <-- Feature specification
    │   ├── CONTEXT.md       <-- Stage routing
    │   ├── output/          <-- Technical specification
    │   └── REFERENCE.md     <-- Stage reference material
    │
    ├── 02-implementation/   <-- Feature implementation
    │   ├── CONTEXT.md       <-- Stage routing
    │   ├── output/          <-- Implemented specification
    │   └── REFERENCE.md     <-- Stage reference material
    │
    ├── 03-verification/     <-- Feature testing
    │   ├── CONTEXT.md       <-- Stage routing
    │   ├── output/          <-- Verification report
    │   └── REFERENCE.md     <-- Stage reference material
    │
    └── 04-documentation/    <-- Feature documentation
        ├── CONTEXT.md       <-- Stage routing
        ├── output/          <-- Documentation report
        └── REFERENCE.md     <-- Stage reference material
```

## Acceptance Criteria

- Artifact creation in accordance with stage guidance
- Stage checkpoint review
  - User review & acceptance of each output artifact
  - User review & acceptance of modified/created sourcecode
  - User review & acceptance must be explicit before continuation
    - "approved" or "continue" response
