---
context-hierarchy: Layer 1
---

# Create Feature

## Overview

This workspace is used to create new features for the PyTack Python package.

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
features/
├── CONTEXT.md
└── stages/                  <-- 4-stage pipeline
    ├── 01-planning/         <-- Feature specification
    │   ├── CONTEXT.md       <-- Stage routing
    │   ├── output/          <-- Technical specification
    │   └── references/      <-- Reference material
    │
    ├── 02-implementation/   <-- Feature implementation
    │   ├── CONTEXT.md       <-- Stage routing
    │   ├── output/          <-- Implemented specification
    │   └── references/      <-- Reference material
    │
    ├── 03-verification/     <-- Feature testing
    │   ├── CONTEXT.md       <-- Stage routing
    │   ├── output/          <-- Verification report
    │   └── references/      <-- Reference material
    │
    └── 04-documentation/    <-- Feature documentation
        ├── CONTEXT.md       <-- Stage routing
        ├── output/          <-- Documentation report
        └── references/      <-- Reference material
```

## Acceptance Criteria

- Artifact creation in accordance with stage guidance
- Stage checkpoint review
  - User review & acceptance of each output artifact
  - User review & acceptance of modified/created sourcecode
  - User review & acceptance must be explicit before continuation
    - "approved" or "continue" response
    - "Keep" changes button click
