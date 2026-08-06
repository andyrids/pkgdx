---
context-hierarchy: Layer 3
context-hierarchy-role: Rules, conventions and guidelines
---

# Attribution

When blending direct code snippets with architectural concepts, open-source etiquette mandates
both legal compliance and community gratitude.

Assuming permissive licenses such as MIT and Apache 2.0, there are three ways attribution can be
implemented, which are detailed below.

## (1) Module-Level Docstrings

When a whole file or core concept is adapted, include a clear `Attribution` in the module
docstring.

Example (direct code porting):

```python
"""Bundled toolchain configuration for `pkgdx.standards`.

Attribution:
    The rule selection and per-file ignore patterns in this file are directly
    adapted from the upstream project's own configuration.

    Repository: https://github.com/example/upstream
    License: MIT License - Copyright (c) 2026 Upstream Authors
"""
```

Example (architectural inspiration):

```python
"""Pre-commit hook shims for `pkgdx.standards`.

Attribution:
    The console-script shim pattern - a thin entry point that injects a
    bundled config file before delegating to the underlying tool - is
    heavily inspired by `upstream-hooks`.

    Repository: https://github.com/example/upstream-hooks
    License: MIT License - Copyright (c) 2026 Upstream Authors
"""
```

## (2) Inline Comments (For Specific Functions)

If a new function is written, but the logic or algorithm is pulled directly from the other
projects, a comment above the function can be added.

## (3) Preserving Copyright Notices

A copy-paste of substantial chunks of actual source code results in adherence to permissive
licenses like MIT and Apache, which require you to preserve their copyright notice.

1. Pasting their short copyright header directly above the copied function/class in files.
2. Creating a `CREDITS.md` file in the project root:
   - Include full license text all projects
   - State which files use them

## (4) README Acknowledgements

Add an `Acknowledgements` section to the project `README`.
