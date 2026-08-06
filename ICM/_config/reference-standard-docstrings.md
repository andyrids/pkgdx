---
context-hierarchy: Layer 3
context-hierarchy-role: Rules, conventions and guidelines
---

# Documentation

## Docstrings

Docstrings follow the Google style guide and PEP 257 guidelines.

### (1) Module-Level Docstrings

- MUST follow existing codebase style
- MUST include a summary line
- MUST include License section
- SHOULD have a summary line with enough information to understand the module purpose
- COULD add extra detail seperated from the summary by a blank line

```python
"""A one-line summary of the module or program, terminated by a period.

Leave one blank line. The rest of this docstring should contain an
overall description of the module or program.

License:
    SPDX-License-Identifier: Apache-2.0
"""
```

### (2) Functions and Methods

- MUST follow existing codebase style
- MUST use the imperative-style in the summary line
- MUST include Args section
- MUST include Returns (or Yields for generators) section
- MUST include Raises section (if relevant)
- SHOULD have a summary line with enough information to call a function without reading the code
- COULD add extra detail seperated from the summary by a blank line
- COULD provide example usage or detail where needed

```python
def install_prek_hooks(root: Path) -> None:
    """Install pre-commit hooks if not installed.

    NOTE: A pre-existing `.git/hooks/pre-commit` is left alone - `prek
    install` is only shelled out to on a repo that has none.

    Args:
        root: The root path of the consuming repo.
    """
    precommit_config = root / ".git" / "hooks" / "pre-commit"
    if precommit_config.exists():
        logger.debug("Prek pre-commit hooks already installed")
        return
    ...
```

### (3) Classes

- MUST follow existing codebase style
- MUST have a summary line that describes what the class instance represents
- SHOULD include Attributes section for public attributes (excluding properties)
