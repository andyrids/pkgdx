"""Custom exceptions for `pkgdx`."""


class Error(Exception):
    """Base-class for all exceptions raised by `pkgdx`."""


class AXIError(Error):
    """Base for AXI CLI errors, surfaced as a TOON error block on STDOUT."""


class ProjectRootNotFoundError(AXIError):
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


class RichHandlerNotFound(Error):
    """Raised on missing Rich logging handler."""


class InvalidArgumentError(AXIError):
    """Raised on an invalid CLI/tool argument value."""


class PackageNotFoundError(AXIError):
    """Raised when a requested package is not installed in the venv."""


class PackageImportError(AXIError):
    """Raised when a package cannot be imported for API introspection."""


class AmbientContextError(AXIError):
    """Raised when `axi` ambient context cannot be installed."""


class SymbolNotFoundError(AXIError):
    """Raised when a qualified symbol name cannot be found in the store."""


class StoreError(AXIError):
    """Raised on `SymbolStore`-level failures."""
