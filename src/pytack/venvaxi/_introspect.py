"""Public API and docstring introspection for `venv-axi`."""

import importlib
import inspect
import logging
import re
from dataclasses import dataclass
from importlib import metadata
from typing import Any

from pytack.exceptions import PackageImportError, PackageNotFoundError

logger = logging.getLogger(__package__)

_VALID_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
DEFAULT_TRUNCATE_LIMIT = 200


@dataclass(frozen=True, slots=True)
class SymbolInfo:
    """A single public, top-level API symbol."""

    name: str
    kind: str
    signature: str
    doc: str


def truncate(text: str, limit: int = DEFAULT_TRUNCATE_LIMIT) -> str:
    """Truncates text to a set number of characters determined by `limit`.

    NOTE: AXI principle 3 (content truncation with size hints).

    Args:
        text: The text to truncate.
        limit: Maximum number of characters to keep. Defaults to 200.

    Returns:
        `text` unchanged or truncated with an appended size hint.
    """
    if len(text) <= limit:
        return text

    return (
        f"{text[:limit]}... truncated, {len(text)} chars total"
        " - use --full to see complete body"
    )


def _resolve_import_name(name: str) -> str:
    """Resolves import slugs from distribution names.

    Args:
        name: The distribution (package) name.

    Returns:
        The best-effort importable top-level module name.
    """
    normalized = name.lower().replace("-", "_")
    mapping = metadata.packages_distributions()
    for import_name, dist_names in mapping.items():
        for dist_name in dist_names:
            if dist_name.lower().replace("-", "_") == normalized:
                return import_name
    return normalized


def get_public_api(
    name: str,
    *,
    full: bool = False,
    limit: int = DEFAULT_TRUNCATE_LIMIT,
) -> list[SymbolInfo]:
    """Extracts top-level public functions & classes from a package.

    Args:
        name: The package (distribution) name.
        full: Return complete docstrings instead of the truncated
            first line. Defaults to False.
        limit: The docstring truncation limit. Defaults to 200.

    Raises:
        PackageNotFoundError: On `name` containing invalid characters.
        PackageImportError: On resolved module import error.

    Returns:
        Public top-level symbols, with their kind, signature and
        docstring.
    """
    if not _VALID_NAME_RE.match(name):
        msg = f"Invalid package name `{name}`"
        raise PackageNotFoundError(msg)

    import_name = _resolve_import_name(name)
    try:
        module = importlib.import_module(import_name)
    except ImportError as err:
        msg = f"Failed to import `{import_name}` (from `{name}`)"
        raise PackageImportError(msg) from err

    public_names = list(
        getattr(module, "__all__", None)
        or [n for n in dir(module) if not n.startswith("_")]
    )

    symbols: list[SymbolInfo] = []
    for symbol_name in sorted(public_names):
        obj: Any = getattr(module, symbol_name, None)
        if inspect.isclass(obj):
            kind = "class"
        elif inspect.isroutine(obj):
            kind = "function"
        else:
            continue

        try:
            signature = str(inspect.signature(obj))
        except (TypeError, ValueError):
            signature = "(...)"

        doc = inspect.getdoc(obj) or ""
        if full:
            doc_field = doc
        else:
            first_line = doc.splitlines()[0] if doc else ""
            doc_field = truncate(first_line, limit)

        symbols.append(
            SymbolInfo(
                name=symbol_name,
                kind=kind,
                signature=signature,
                doc=doc_field,
            )
        )
    return symbols
