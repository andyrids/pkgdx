"""Agent eXperience Interface (AXI) CLI init.

Provides package metadata and public API introspection for packages installed
in the venv of a pkgdx-consuming repo. Output uses Token-Oriented Object
Notation (TOON) format, which is a token-efficient, human-readable, and
machine-parseable format for structured data.

TOON Documentation: https://toonformat.dev/
AXI Documentation: https://axi.md/
"""

from pkgdx.axi._cli import add_subparser

__all__: list[str] = ["add_subparser"]
