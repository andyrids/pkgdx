"""Custom exceptions for `pkgdev`."""


class Error(Exception):
    """Base-class for all exceptions raised by `pkgdev`."""


class ProjectRootNotFoundError(Error):
    """Raised when the project root cannot be determined."""
