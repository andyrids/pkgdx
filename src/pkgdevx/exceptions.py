"""Custom exceptions for `pkgdevx`."""


class Error(Exception):
    """Base-class for all exceptions raised by `pkgdevx`."""


class ProjectRootNotFoundError(Error):
    """Raised when the project root cannot be determined."""


class PrekRepoRevisionError(Error):
    """Raised on missing `rev` key in Prek config."""


class PrekRepoURLMissingError(Error):
    """Raised on missing `repo` key in Prek config."""


class ProjectRepoURLMissingError(Error):
    """Raised on missing `repository` key in `pkgdevx` metadata."""


class GitTopLevelError(Error):
    """Raised on failed `git rev-parse --show-toplevel` command."""
