---
context-hierarchy: Layer 1
context-hierarchy-role: Workspace task routing
maximum-context-tokens: 300
---

# Create Documentation

## Overview

This workspace is used to create new project documentation.

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
create-documentation/
├── CONTEXT.md
└── stages/                  <-- 3-stage pipeline
    ├── 01-specification/    <-- Documentation specification
    │   ├── CONTEXT.md       <-- Stage routing & reference material
    │   └── output/          <-- Documentation plan
    │
    ├── 02-implementation/   <-- Documentation implementation
    │   ├── CONTEXT.md       <-- Stage routing & reference material
    │   └── output/          <-- Drafted documentation
    │
    └── 03-verification/     <-- Documentation verification
        ├── CONTEXT.md       <-- Stage routing & reference material
        └── output/          <-- Verification report
```

## Acceptance Criteria

- Artifact creation in accordance with stage guidance
- Stage checkpoint review
  - User review & acceptance of each output artifact
  - User review & acceptance of modified/created documentation
  - User review & acceptance must be explicit before continuation
    - "approved" or "continue" response
