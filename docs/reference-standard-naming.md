---
context-hierarchy: Layer 3
context-hierarchy-role: Reference material
immutable: true
recommended-context-tokens: 2500
tags: []
---

# Standard - naming conventions

## References

| Reference      | Pattern                           | Example                          |
| -------------- | --------------------------------- | --------------------------------- |
| Toolchain      | `reference-toolchain-[tool].md`   | `reference-toolchain-mypy.md`    |
| Standard       | `reference-standard-[name].md`    | `reference-standard-techspec.md` |

## Tracked artifacts

Permanent, version-controlled. See `specs/README.md` for the state vs motion split.

| Artifact  | Pattern                      | Example                       |
| --------- | ---------------------------- | ----------------------------- |
| Command   | `specs/commands/[verb].md`   | `specs/commands/find.md`      |
| Behavior  | `specs/behaviors/[name].md`  | `specs/behaviors/cache-refresh.md` |
| Plan      | `plans/[slug].md`            | `plans/rich-progress-bar.md`  |
