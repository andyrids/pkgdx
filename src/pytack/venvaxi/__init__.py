"""`venv-axi` - Agent eXperience Interface for a consuming repo's venv.

Provides package metadata and public API introspection for packages installed
in the venv of a pytack-consuming repo. Outputs are in Token-Optimized
Object Notation (TOON) format, which is a token-efficient, human-readable, and
machine-parseable format for structured data.

TOON Documentation: https://toonformat.dev/
AXI Documentation: https://axi.md/
"""

from pytack.venvaxi._cli import main

__all__: list[str] = ["main"]
