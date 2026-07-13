"""Custom exceptions for `pytack`."""


class Error(Exception):
    """Base-class for all exceptions raised by `pytack`."""


class ProjectRootNotFoundError(Error):
    """Raised when the project root cannot be determined."""


class PrekRepoRevisionError(Error):
    """Raised on missing `rev` key in Prek config."""


class PrekRepoURLMissingError(Error):
    """Raised on missing `repo` key in Prek config."""


class ProjectRepoURLMissingError(Error):
    """Raised on missing `repository` key in `pytack` metadata."""


class GitTopLevelError(Error):
    """Raised on failed `git rev-parse --show-toplevel` command."""


class RichHandlerNotFound(Error):
    """Raised on missing Rich logging handler."""
