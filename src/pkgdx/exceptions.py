"""Custom exceptions for `pkgdx`."""


class Error(Exception):
    """Base-class for all exceptions raised by `pkgdx`."""


class ProjectRootNotFoundError(Error):
    """Raised when the project root cannot be determined."""


class PrekConfigError(Error):
    """Raised on a malformed consumer `prek.toml` configuration."""


class PrekRepoRevisionError(Error):
    """Raised on missing `rev` key in Prek config."""


class PrekRepoURLMissingError(Error):
    """Raised on missing `repo` key in Prek config."""


class ProjectRepoURLMissingError(Error):
    """Raised on missing `repository` key in `pkgdx` metadata."""


class GitTopLevelError(Error):
    """Raised on failed `git rev-parse --show-toplevel` command."""


class GitNotFoundError(GitTopLevelError):
    """Raised when the `git` executable is not found on `PATH`."""


class RichHandlerNotFound(Error):
    """Raised on missing Rich logging handler."""


class ConfigDirError(Error):
    """Raised on an invalid `PKGDX_CONFIG_DIR`."""


class ProjectConfigError(Error):
    """Raised on an invalid `[tool.pkgdx]` table in `pyproject.toml`."""


class ToolNotFoundError(Error):
    """Raised when a hook tool executable is not found on `PATH`.

    Attributes:
        hint: The remedy, printed by the CLI after the error.
    """

    hint = (
        "Run the hook in the environment pkgdx is installed in, "
        "e.g. via `uv run`"
    )
