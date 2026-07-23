"""__init__ for pytack.standards.

Provides access to configuration files for supported tools such as; `mypy`,
`prek`, `pymarkdown` and `ruff`.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any


MODULE_ROOT: Path = Path(__file__).parent
MYPY_CONFIG: Path = MODULE_ROOT / "mypy.ini"
PREK_CONFIG: Path = MODULE_ROOT / "hooks.toml"
PYMARKDOWN_CONFIG: Path = MODULE_ROOT / "pymarkdown.toml"
RUFF_CONFIG: Path = MODULE_ROOT / "ruff.toml"


@lru_cache(maxsize=1)
def _load_prek_config() -> dict[str, Any]:
    """Loads Prek config.

    Returns:
        The Prek hooks TOML as a dict."""
    import tomllib

    with PREK_CONFIG.open("rb") as f:
        return tomllib.load(f)


@lru_cache(maxsize=1)
def get_pytack_repository() -> str:
    """Get repository URL from pytack metadata.

    Raises:
        ProjectRepoURLMissingError: On missing repository URL in metadata.

    Returns:
        Repository URL.
    """
    import urllib.parse
    from importlib.metadata import metadata
    from pytack.exceptions import ProjectRepoURLMissingError

    pytack_metadata = metadata("pytack")

    entry: str
    for entry in pytack_metadata.get_all("Project-URL", failobj=[]):
        if entry.lower().startswith("repository"):
            _, URL = entry.split(", ", 1)
            parsed = urllib.parse.urlparse(URL)
            if parsed.scheme and parsed.netloc:
                return URL
    msg = "Missing repository URL in `pytack` metadata (`pyproject.toml`)"
    raise ProjectRepoURLMissingError(msg)


@lru_cache(maxsize=1)
def get_config_revision() -> str:
    """Gets repo revision from Prek config.

    Raises:
        PrekRepoRevisionError: On missing revision value.

    Returns:
        Revision tag.
    """
    from pytack.exceptions import PrekRepoRevisionError

    config = _load_prek_config()
    REPO_URL: str = get_pytack_repository()

    for repo in config.get("repos", []):
        if repo.get("repo") == REPO_URL:
            revision: str | None = repo.get("rev", None)
            if revision:
                return revision
            msg = "Missing `rev` key in Prek config"
            raise PrekRepoRevisionError(msg)
    msg = "`pytack` metadata URL missing/mismatch for Prek config"
    raise PrekRepoRevisionError(msg)


@lru_cache(maxsize=1)
def get_config_repository() -> str:
    """Gets repo URL from Prek config.

    Raises:
        PrekRepoRevisionError: On missing revision value.

    Returns:
        Repository URL.
    """
    from pytack.exceptions import PrekRepoRevisionError

    config = _load_prek_config()
    REPO_URL = get_pytack_repository()

    for repo in config.get("repos", []):
        if repo.get("repo") == REPO_URL:
            return REPO_URL

    msg = "`pytack` repository URL from metadata not found in Prek config"
    raise PrekRepoRevisionError(msg)


__all__: list[str] = [
    "MYPY_CONFIG",
    "PREK_CONFIG",
    "PYMARKDOWN_CONFIG",
    "RUFF_CONFIG",
]
