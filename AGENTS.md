---
context-hierarchy: Layer 0
context-hierarchy-role: Global identity
immutable: false
recommended-context-tokens: 900
---

# Package Developer Experience (DX) Toolkit [`Pkgdx`]

The pkgdx project provides a DX toolkit, which centralises the maintenance and implementation of
canonical standards for consuming projects.

This project adheres to [YAGNI](docs/guidance/standard-yagni.md) principles.

## Release workflow

Project pre-commit hooks are versioned and referenced by the `src/pkgdx/standards/hooks.toml`, in
the `rev = "v0.5.0"`, which means on release or realease candidate:

- `src/pkgdx/standards/hooks.toml` must reflect the new release version (repo tag).
- The project must be tagged with this same version.

## Context hierarchy

Markdown files declare their layer in frontmatter - read
[standard-context-hierarchy.md](docs/guidance/standard-context-hierarchy.md) before creating or
editing one. Files marked `immutable: true` are never edited in passing: propose the change and
wait for approval.

## Reference

Standards and references live in `docs/guidance/` as `standard-*.md` and `toolchain-*.md` files
(Layer 3). Load a file when its subject is in play, which can be determined by the frontmatter.
