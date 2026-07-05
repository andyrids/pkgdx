"""__init__ for pkgdev.standards.

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
def get_pkgdev_repository() -> str:
    """Get repository URL from pkgdev metadata.

    Raises:
        ProjectRepoURLMissingError: On missing repository URL in metadata.

    Returns:
        Repository URL.
    """
    import urllib.parse
    from importlib.metadata import metadata
    from pkgdev.exceptions import ProjectRepoURLMissingError

    pkgdev_metadata = metadata("pkgdev")

    for entry in pkgdev_metadata.get_all("Project-URL", failobj=[]):
        if entry.lower().startswith("repository"):
            _, URL = entry.split()
            parsed = urllib.parse.urlparse(URL)
            if parsed.scheme and parsed.netloc:
                return URL
    msg = "Missing repository URL in `pkgdev` metadata (`pyproject.toml`)"
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
    from pkgdev.exceptions import PrekRepoRevisionError

    with PREK_CONFIG.open("rb") as f:
        config = tomllib.load(f)

    REPO_URL = get_pkgdev_repository()

    for repo in config.get("repos", []):
        if repo.get("repo") == REPO_URL:
            revision = repo.get("rev")
            if revision:
                return revision
            else:
                msg = "Missing `rev` key in Prek config"
                raise PrekRepoRevisionError(msg)
    msg = "`pkgdev` metadata URL missing/mismatch for Prek config"
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
    from pkgdev.exceptions import PrekRepoRevisionError

    with PREK_CONFIG.open("rb") as f:
        config = tomllib.load(f)

    REPO_URL = get_pkgdev_repository()

    for repo in config.get("repos", []):
        if repo.get("repo") == REPO_URL:
            return REPO_URL

    msg = "`pkgdev` repository URL from metadata not found in Prek config"
    raise PrekRepoRevisionError(msg)


__all__: list[str] = [
    "MYPY_CONFIG",
    "PREK_CONFIG",
    "PYMARKDOWN_CONFIG",
    "RUFF_CONFIG",
]
