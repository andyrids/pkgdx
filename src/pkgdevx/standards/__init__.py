"""__init__ for pkgdevx.standards.

Provides access to configuration files for supported tools such as; `mypy`,
`prek`, `pymarkdown`, and `ruff`.
"""

from functools import lru_cache
from pathlib import Path


MODULE_ROOT: Path = Path(__file__).parent
MYPY_CONFIG: Path = MODULE_ROOT / "mypy.ini"
PREK_CONFIG: Path = MODULE_ROOT / "hooks.toml"
PYMARKDOWN_CONFIG: Path = MODULE_ROOT / "pymarkdown.toml"
RUFF_CONFIG: Path = MODULE_ROOT / "ruff.toml"


@lru_cache(maxsize=1)
def get_pkgdevx_repository() -> str:
    """Get repository URL from pkgdevx metadata.

    Raises:
        ProjectRepoURLMissingError: On missing repository URL in metadata.

    Returns:
        Repository URL.
    """
    import urllib.parse
    from importlib.metadata import metadata
    from pkgdevx.exceptions import ProjectRepoURLMissingError

    pkgdevx_metadata = metadata("pkgdevx")

    for entry in pkgdevx_metadata.get_all("Project-URL", failobj=[]):
        if entry.lower().startswith("repository"):
            _, URL = entry.split()
            parsed = urllib.parse.urlparse(URL)
            if parsed.scheme and parsed.netloc:
                return URL
    msg = "Missing repository URL in `pkgdevx` metadata (`pyproject.toml`)"
    raise ProjectRepoURLMissingError(msg)


@lru_cache(maxsize=1)
def get_config_revision() -> str:
    """Gets repo revision from Prek config.

    Raises:
        PrekRepoRevisionError: On missing revision value.

    Returns:
        Revision tag.
    """
    import tomllib
    from pkgdevx.exceptions import PrekRepoRevisionError

    with PREK_CONFIG.open("rb") as f:
        config = tomllib.load(f)

    REPO_URL = get_pkgdevx_repository()

    for repo in config.get("repos", []):
        if repo.get("repo") == REPO_URL:
            revision = repo.get("rev")
            if revision:
                return revision
            else:
                msg = "Missing `rev` key in Prek config"
                raise PrekRepoRevisionError(msg)
    msg = "`pkgdevx` metadata URL missing/mismatch for Prek config"
    raise PrekRepoRevisionError(msg)


@lru_cache(maxsize=1)
def get_config_repository() -> str:
    """Gets repo URL from Prek config.

    Raises:
        PrekRepoRevisionError: On missing revision value.

    Returns:
        Repository URL.
    """
    import tomllib
    from pkgdevx.exceptions import PrekRepoRevisionError

    with PREK_CONFIG.open("rb") as f:
        config = tomllib.load(f)

    REPO_URL = get_pkgdevx_repository()

    for repo in config.get("repos", []):
        if repo.get("repo") == REPO_URL:
            return REPO_URL

    msg = "`pkgdevx` repository URL from metadata not found in Prek config"
    raise PrekRepoRevisionError(msg)


__all__: list[str] = [
    "MYPY_CONFIG",
    "PREK_CONFIG",
    "PYMARKDOWN_CONFIG",
    "RUFF_CONFIG",
]
