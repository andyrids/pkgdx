"""Type definitions for Pre-commit hooks and repositories in the TOML config.

This module defines `TypedDict` classes for representing remote, local and
builtin hooks and repositories as they appear in the Pre-commit configuration.
"""

from typing import Literal, NotRequired, TypedDict


class HookRemote(TypedDict):
    """Represents a Pre-commit remote hook entry in the TOML config.

    Attributes:
        id: The unique identifier for the remote hook.
        name: The name of the remote hook.
        entry: The entry point for the remote hook.
        args: The list of arguments for the remote hook.
        language: The programming language of the remote hook.
        types_or: The list of file types the hook applies to.
        exclude: The pattern for files to exclude from the hook.
        require_serial: Flag indicating if the hook requires serial execution.
        pass_filenames: Flag indicating if filenames should be passed to the
            hook.
    """

    id: str
    name: NotRequired[str]
    entry: NotRequired[str]
    args: NotRequired[list[str]]
    language: NotRequired[str]
    types_or: NotRequired[list[str]]
    exclude: NotRequired[str]
    require_serial: NotRequired[bool]
    pass_filenames: NotRequired[bool]


class RepoRemote(TypedDict):
    """Represents a Pre-commit remote repo entry in the TOML config.

    Attributes:
        repo: The URL of the remote repository.
        rev: The revision of the remote repository.
        hooks: A list of remote hooks associated with the repository.
    """

    repo: str
    rev: NotRequired[str]
    hooks: list[HookRemote]


class HookLocal(TypedDict):
    """Represents a Pre-commit local hook entry in the TOML config.

    Attributes:
        id: The unique identifier for the local hook.
        name: The name of the local hook.
        entry: The entry point for the local hook.
        args: The list of arguments for the local hook.
        language: The programming language of the local hook.
        types_or: The list of file types the hook applies to.
        exclude: The pattern for files to exclude from the hook.
        require_serial: Flag indicating if the hook requires serial execution.
        pass_filenames: Flag indicating if filenames should be passed to the
            hook.
    """

    id: str
    name: str
    entry: str
    args: NotRequired[list[str]]
    language: str
    types_or: NotRequired[list[str]]
    exclude: NotRequired[str]
    require_serial: NotRequired[bool]
    pass_filenames: NotRequired[bool]


class RepoLocal(TypedDict):
    """Represents a Pre-commit local repo entry in the TOML config.

    Attributes:
        repo: The literal string "local" indicating a local repository.
        rev: The revision of the local repository.
        hooks: A list of local hooks associated with the repository.
    """

    repo: Literal["local"]
    rev: NotRequired[str]
    hooks: list[HookLocal]


class HookBuiltin(TypedDict):
    """Represents a Pre-commit builtin hook entry in the TOML config.

    Attributes:
        id: The unique identifier for the builtin hook.
    """

    id: str


class RepoBuiltin(TypedDict):
    """Represents a Pre-commit builtin repo entry in the TOML config.

    Attributes:
        repo: The literal string "builtin" indicating a builtin repository.
        hooks: A list of builtin hooks associated with the repository.
    """

    repo: Literal["builtin"]
    hooks: list[HookBuiltin]
