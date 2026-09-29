---
context-hierarchy: Layer 3
context-hierarchy-role: Reference material
immutable: true
recommended-context-tokens: 2500
tags: [specs, invariants, protocol]
---

# Specifications (spec)

`specification/` declares what MUST be true of the project and is the primary source of truth for
behaviour.

This is not documentation of what was built - it is specification of what should exist. The codebase
implementation is brought into conformance with these files, not the other way round.

| Layer         | Answers                    | Location           | Lifetime                     |
| ------------- | -------------------------- | ------------------ | ---------------------------- |
| Specification | What MUST be true, forever | `specification/**` | Permanent, changed by review |

A spec with no implementation is a known gap and on the default branch a known gap MUST carry a plan
and epic/issue/task.

## Example layout

```text
specification/
├── README.md         <- This file
├── commands/         <- One file per CLI verb, if the project has a CLI
└── behaviors/        <- Cross-cutting invariants spanning several commands
```

Subdirectories are created as the project needs them, not up front. The names above are
illustrative - a project without a CLI has no `commands/`, and one that serves no MCP has no
`mcp/`. Group by the shape of the thing being specified, one file per unit.

## Frontmatter

```yaml
---
context-hierarchy: Layer 3
context-hierarchy-role: Reference material
immutable: false
tags: [keyword, ...]   # what this spec is about, for retrieval
---
```

Every file under `specification/**` carries it and the block is what makes the file routable by
layer. There is no `recommended-context-tokens` key - specs are unbudgeted by design, because a
spec is as long as the behaviour it declares. `immutable: false` is what separates a spec from the
factory configuration sharing this layer - plans and implementation exist to amend specs.

## What specs cover

Invocation and inputs, data requirements, outputs, failure modes, out of scope and principles.

## What specs do NOT cover

Module decomposition, function and variable names, file paths inside the implementation and test
cases. Those are implementation decisions that change freely; a spec that pins them rots on the
first refactor. Authoring guidance and templates are in `docs/reference-standard-spec.md`.

## Specification authority

How much authority the spec holds over the code is a chosen position, not a given. Three exist:

- **Spec-first** - the spec is written and reviewed, implementation follows, and the document is
  thereafter history.
- **Spec-anchored** - the spec evolves with the software, and automated tests bridge the two.
- **Spec-as-source** - the spec is the only hand-written artifact; code is regenerated from it.

This tree is **spec-anchored**. That commits the project to three things: the spec is amended
whenever desired behaviour moves and tests are the bridge. Invariant 2 below is this stance stated
as a rule, not a house preference.

> [!IMPORTANT]
> A project wanting a different position edits this section. The pipeline does not change.

## Invariants

1. Every spec on the default branch is either implemented or owned by an epic/issue/task.
2. Spec/code divergence is a bug, not debt. Fix the code, or amend the spec - never work around a
   spec in code. This is the spec-anchored stance above, applied one divergence at a time.
3. A spec whose desired state is still being negotiated stays off the default branch, on a
   feature branch, until its epic/issue/task rides along with it. Absence is the only unambiguous
   marker.
4. Where the project exposes a CLI, `<cli> <cmd> --help` is authoritative for invocation. If a
   command spec disagrees with it, `--help` wins and the spec needs updating.

## Changing a spec

A spec edit can strand work already planned against the old desired state. After editing, find
the epic/issue/task chasing it and offer to update them:
