"""__init__ for `pkgdx.standards` module.

Provides access to configuration files for supported tools such as; `mypy`,
`prek`, `pymarkdown` and `ruff`.
"""

import logging
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__package__)

MODULE_ROOT: Path = Path(__file__).parent
MYPY_CONFIG: Path = MODULE_ROOT / "mypy.ini"
PREK_CONFIG: Path = MODULE_ROOT / "hooks.toml"
PYMARKDOWN_CONFIG: Path = MODULE_ROOT / "pymarkdown.toml"
RUFF_CONFIG: Path = MODULE_ROOT / "ruff.toml"

CONFIG_DIR_ENV: str = "PKGDX_CONFIG_DIR"
BUNDLED_CONFIGS: tuple[Path, ...] = (
    MYPY_CONFIG,
    PREK_CONFIG,
    PYMARKDOWN_CONFIG,
    RUFF_CONFIG,
)


def user_config_dir() -> Path:
    """Get the user config directory.

    The environment is read on every call; nothing is cached. The platform
    directory is returned even if it does not exist.

    Raises:
        ConfigDirError: If `PKGDX_CONFIG_DIR` is set but not a directory.

    Returns:
        The `PKGDX_CONFIG_DIR` path, else the platform config directory.
    """
    from pkgdx.exceptions import ConfigDirError

    env_value = os.environ.get(CONFIG_DIR_ENV)
    if env_value:
        env_dir = Path(env_value).expanduser()
        if not env_dir.is_dir():
            msg = f"`{CONFIG_DIR_ENV}` is not an existing directory: {env_dir}"
            raise ConfigDirError(msg)
        return env_dir

    appdata = os.environ.get("APPDATA")
    if sys.platform == "win32" and appdata:
        return Path(appdata) / "pkgdx"

    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg and Path(xdg).is_absolute():
        return Path(xdg) / "pkgdx"
    return Path.home() / ".config" / "pkgdx"


def resolve_config(bundled: Path) -> Path:
    """Resolve a config file, preferring a user override.

    Args:
        bundled: A bundled config path (for example `RUFF_CONFIG`).

    Raises:
        ConfigDirError: If `PKGDX_CONFIG_DIR` is set but not a directory.

    Returns:
        The user config file if it exists, else the bundled file.
    """
    user_file = user_config_dir() / bundled.name
    if user_file.is_file():
        logger.debug("Using user config %s", user_file)
        return user_file
    logger.debug("Using bundled config %s", bundled)
    return bundled


@lru_cache(maxsize=1)
def _load_prek_config() -> dict[str, Any]:
    """Load Prek config.

    Returns:
        The Prek hooks TOML as a dict."""
    import tomllib

    # Bundled only: validates the package's own template, never a user copy
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
    "BUNDLED_CONFIGS",
    "CONFIG_DIR_ENV",
    "MYPY_CONFIG",
    "PREK_CONFIG",
    "PYMARKDOWN_CONFIG",
    "RUFF_CONFIG",
    "resolve_config",
    "user_config_dir",
]
