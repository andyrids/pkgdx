---
context-hierarchy: Layer 0
context-hierarchy-role: Global identity
immutable: false
recommended-context-tokens: 900
---

# Package Developer Experience (DX) Toolkit [`Pkgdx`]

The pkgdx project provides a DX toolkit, which centralises the maintenance and implementation of
canonical standards for consuming projects.

This project adheres to [YAGNI](docs\reference-standard-yagni.md) principles.

## Markdown frontmatter

Mardown files carry `context-hierarchy`, `context-hierarchy-role` and `immutable` keys, plus
`recommended-context-tokens` where a target is given. Beyond those:

- Budgets are a signal, not an enforced limit. A file that outgrows one is worth a look - it may have
  started doing another layer's job.
- Layer 3 carries tags: [keyword, ...]. immutable: true marks the factory configuration, amended
  deliberately, not in passing.

## Reference

Standards and references live in `docs/` as reference-*.md files (Layer 3). See the reference
`docs\reference-standard-naming.md` document for more information. Load a file when its subject
is in play, which can be determined by the frontmatter.
