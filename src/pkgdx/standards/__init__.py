"""__init__ for `pkgdx.standards` module.

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
    """Load Prek config.

    Returns:
        The Prek hooks TOML as a dict."""
    import tomllib

    with PREK_CONFIG.open("rb") as f:
        return tomllib.load(f)


@lru_cache(maxsize=1)
def get_pkgdx_repository() -> str:
    """Get repository URL from pkgdx metadata.

    Raises:
        ProjectRepoURLMissingError: On missing repository URL in metadata.

    Returns:
        Repository URL.
    """
    import urllib.parse
    from importlib.metadata import metadata

    from pkgdx.exceptions import ProjectRepoURLMissingError

    pkgdx_metadata = metadata("pkgdx")

    entry: str
    for entry in pkgdx_metadata.get_all("Project-URL", failobj=[]):
        if entry.lower().startswith("repository"):
            _, URL = entry.split(", ", 1)
            parsed = urllib.parse.urlparse(URL)
            if parsed.scheme and parsed.netloc:
                return URL
    msg = "Missing repository URL in `pkgdx` metadata (`pyproject.toml`)"
    raise ProjectRepoURLMissingError(msg)


@lru_cache(maxsize=1)
def get_config_revision() -> str:
    """Get repo revision from Prek config.

    Raises:
        PrekRepoRevisionError: On missing revision value.

    Returns:
        Revision tag.
    """
    from pkgdx.exceptions import PrekRepoRevisionError

    config = _load_prek_config()
    REPO_URL: str = get_pkgdx_repository()

    for repo in config.get("repos", []):
        if repo.get("repo") == REPO_URL:
            revision: str | None = repo.get("rev", None)
            if revision:
                return revision
            msg = "Missing `rev` key in Prek config"
            raise PrekRepoRevisionError(msg)
    msg = "`pkgdx` metadata URL missing/mismatch for Prek config"
    raise PrekRepoRevisionError(msg)


@lru_cache(maxsize=1)
def get_config_repository() -> str:
    """Get repo URL from Prek config.

    Raises:
        ProjectRepoURLMissingError: On missing repository URL.

    Returns:
        Repository URL.
    """
    from pkgdx.exceptions import ProjectRepoURLMissingError

    config = _load_prek_config()
    REPO_URL = get_pkgdx_repository()

    for repo in config.get("repos", []):
        if repo.get("repo") == REPO_URL:
            return REPO_URL

    msg = "`pkgdx` repository URL from metadata not found in Prek config"
    raise ProjectRepoURLMissingError(msg)


__all__: list[str] = [
    "MYPY_CONFIG",
    "PREK_CONFIG",
    "PYMARKDOWN_CONFIG",
    "RUFF_CONFIG",
]
