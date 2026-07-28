from typing import Literal, NotRequired, TypedDict


class HookRemote(TypedDict):
    """Represents a Prek remote hook entry in the TOML config."""

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
    """Represents a Prek remote repo entry in the TOML config."""

    repo: str
    rev: NotRequired[str]
    hooks: list[HookRemote]


class HookLocal(TypedDict):
    """Represents a Prek local hook entry in the TOML config."""

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
    """Represents a Prek local repo entry in the TOML config."""

    repo: Literal["local"]
    rev: NotRequired[str]
    hooks: list[HookLocal]


class HookBuiltin(TypedDict):
    """Represents a Prek builtin hook entry in the TOML config."""

    id: str


class RepoBuiltin(TypedDict):
    """Represents a Prek builtin repo entry in the TOML config."""

    repo: Literal["builtin"]
    hooks: list[HookBuiltin]
