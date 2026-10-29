"""Core logic and file-system operations for the `pkgdx init` command."""

import argparse
import dataclasses
import logging
import os
import re
import subprocess
import sys
from collections.abc import Iterable
from enum import IntEnum, StrEnum
from itertools import chain, pairwise
from pathlib import Path
from typing import Any

import tomlkit
from rich.console import Console
from tomlkit import TOMLDocument
from tomlkit.exceptions import TOMLKitError
from tomlkit.items import AoT, Table

from pkgdx import exceptions, standards
from pkgdx._types import HookBuiltin, HookLocal, HookRemote

logger = logging.getLogger(__package__)

_PREK_FIX_HINT = "Fix prek.toml, or regenerate it with `pkgdx init --reset`"
_WOULD_UPDATE = re.compile(
    r"would update rev `(?P<old>[^`]+)` -> `(?P<new>[^`]+)`"
)


class ExitCode(IntEnum):
    """Exit codes for the CLI commands.

    NOTE: Members can be passed to `sys.exit` as `int` type checks pass
    due to `IntEnum` inheritance.
    """

    EX_OK = 0
    EX_FAILURE = 1
    EX_SYNTAX = 2
    EX_USAGE = 64
    EX_INTERRUPT = 130


class Outcome(StrEnum):
    """The state of a finished `pkgdx init` step."""

    OK = "ok"
    WARN = "warn"
    FAIL = "fail"


class Change(StrEnum):
    """The change a state-changing `pkgdx init` step made on disk."""

    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"


@dataclasses.dataclass(frozen=True, slots=True)
class StepResult:
    """The result of one `pkgdx init` step, for the CLI to render.

    Attributes:
        outcome: Whether the step succeeded, warned or failed.
        detail: The step summary, shown when `change` is None.
        message: The cause, shown under a WARN or FAIL row when non-empty.
        hint: The suggested fix, shown under a WARN or FAIL row.
        change: What a state-changing step did, else None.
        subject: What was changed, plus any qualifier that adds information.
    """

    outcome: Outcome
    detail: str = ""
    message: str = ""
    hint: str = ""
    change: Change | None = None
    subject: str = ""


@dataclasses.dataclass(frozen=True, slots=True)
class CLIContext:
    """Centralized state for the CLI commands.

    Attributes:
        args: The parsed command-line arguments from argparse.
        console: The Rich console instance used for terminal output.
        is_debug: Flag indicating if the CLI is running in debug mode.
    """

    args: argparse.Namespace
    console: Console
    is_debug: bool = False


class CLIGFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom formatter for the CLI help output.

    NOTE: Based on CLI guidance from https://clig.dev/.
    """

    def add_usage(
        self,
        usage: str | None,
        actions: Iterable[argparse.Action],
        groups: Iterable[argparse._MutuallyExclusiveGroup],
        prefix: str | None = None,
    ) -> None:
        """Add a custom usage message to the CLI help output.

        Args:
            usage: The usage string to display.
            actions: The list of actions for the parser.
            groups: The list of mutually exclusive groups for the parser.
            prefix: The prefix for the usage message.
        """

        super().add_usage(usage, actions, groups, prefix=prefix or "")


def get_git_toplevel() -> Path:
    """Get the root path of the consuming Git repository.

    Returns:
        The Git top-level directory path.

    Raises:
        exceptions.GitTopLevelError: If the working directory is not inside
            a Git repository.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            text=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        logger.debug("git rev-parse failed: %s", e.stderr)
        msg = "Failed `git rev-parse --show-toplevel`"
        raise exceptions.GitTopLevelError(msg) from e
    else:
        return Path(result.stdout.strip())


def get_project_root() -> Path:
    """Get the root path of the consuming repo.

    Returns:
        The root path of the consuming repo.

    Raises:
        exceptions.ProjectRootNotFoundError: If no `pyproject.toml` is found
            in the working directory, its parents or the venv parent.
    """
    cwd = Path.cwd().resolve()
    for directory in chain([cwd], cwd.parents):
        if (directory / "pyproject.toml").exists():
            return directory

    venv_parent = Path(sys.prefix).parent
    if (venv_parent / "pyproject.toml").exists():
        return venv_parent

    msg = f"No pyproject.toml in {cwd}, its parents or {venv_parent}"
    raise exceptions.ProjectRootNotFoundError(msg)


def _last_line(text: str) -> str:
    """Get the last non-blank line of captured subprocess output.

    Args:
        text: The captured output.

    Returns:
        The last non-blank line, stripped, or an empty string.
    """
    lines = text.strip().splitlines()
    return lines[-1].strip() if lines else ""


def install_prek_hooks(root: Path, git_toplevel: Path | None) -> StepResult:
    """Install the pre-commit Git shims if not installed.

    Args:
        root: The root path of the consuming repo.
        git_toplevel: The Git top-level directory, or None to install at
            the project root.

    Returns:
        An OK result (created or unchanged), or WARN if `prek install`
        fails.
    """
    target = git_toplevel or root
    subject = "Git shims" if git_toplevel else "Git shims (at project root)"
    if (target / ".git" / "hooks" / "pre-commit").exists():
        logger.debug("Git shims already installed at `.git/hooks/pre-commit`")
        return StepResult(Outcome.OK, change=Change.UNCHANGED, subject=subject)

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "prek", "install"],
            cwd=target,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError as e:
        reason = str(e)
    else:
        logger.debug(
            "prek install exited %d: %s", proc.returncode, proc.stderr
        )
        if proc.returncode == 0:
            return StepResult(
                Outcome.OK, change=Change.CREATED, subject=subject
            )
        reason = (
            _last_line(proc.stderr)
            or f"prek exited with code {proc.returncode}"
        )
    return StepResult(
        Outcome.WARN,
        "Git shims not installed",
        reason,
        "Fix the error, then run `prek install`",
    )


def update_prek_hooks(root: Path) -> StepResult:
    """Check for remote pre-commit hook revision updates.

    NOTE: Runs `prek update --check`, which compares each remote repo `rev`
    with its latest tag (e.g. the remote `pkgdx` repo) without updating.

    Args:
        root: The root path of the consuming repo.

    Returns:
        An OK result if revisions are up to date, else a WARN result naming
        the available updates or why the check failed.
    """
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "prek", "update", "--check"],
            cwd=root,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError as e:
        reason = str(e)
    else:
        logger.debug(
            "prek update --check exited %d:\n%s%s",
            proc.returncode,
            proc.stdout,
            proc.stderr,
        )
        if proc.returncode == 0:
            return StepResult(Outcome.OK, "hook revisions up to date")

        # STDOUT lists a repo URL, then `would update rev `a` -> `b`` lines
        repo, updates = "", []
        for line in proc.stdout.splitlines():
            if match := _WOULD_UPDATE.search(line):
                update = f"{repo} {match['old']} -> {match['new']}"
                updates.append(update.lstrip())
            elif line.strip() and "`" not in line:
                name = line.strip().rstrip("/").rsplit("/", 1)[-1]
                repo = name.removesuffix(".git")

        # A failed fetch prints the repo URL, then an `update failed:` line
        unfetched = [
            url.strip()
            for url, line in pairwise(proc.stderr.splitlines())
            if "update failed:" in line
        ]
        failed = f"fetch failed: {', '.join(unfetched)}" if unfetched else ""

        if proc.returncode == 1 and (updates or not proc.stderr.strip()):
            available = ", ".join(updates) or "hook revision updates"
            return StepResult(
                Outcome.WARN,
                f"{available} available",
                failed,
                "Update remote hook revisions - `prek update`",
            )
        reason = (
            failed
            or _last_line(proc.stderr)
            or f"prek exited with code {proc.returncode}"
        )
    return StepResult(
        Outcome.WARN,
        "could not check hook revisions",
        reason,
        "Run `prek update --check` to see the full output",
    )


def _create_repo_table(
    doc: TOMLDocument, name: str, revision: str | None = None
) -> Table:
    """Create a new repository table in the pre-commit configuration.

    Args:
        doc: The TOMLDocument to parse.
        name: The name of the repository.
        revision: The revision of the repository.
    """
    new_repo = tomlkit.table()
    new_repo["repo"] = name
    if revision:
        new_repo["rev"] = revision

    new_repo.add(tomlkit.nl())

    new_repo["hooks"] = tomlkit.aot()
    doc["repos"].append(new_repo)

    logger.debug("Created `[repo]` - %s | %s", name, revision)
    return new_repo


def _get_repo_table(
    doc: TOMLDocument, name: str, revision: str | None = None
) -> tuple[Table, bool]:
    """Get an existing or create a new repository table.

    Args:
        doc: The TOMLDocument to parse.
        name: The name of the repository.
        revision: The revision of the repository.

    Returns:
        A tuple containing the table and a boolean indicating any changes.
    """
    for repo in doc["repos"]:
        if repo.get("repo") == name:
            if "hooks" not in repo:
                repo["hooks"] = tomlkit.aot()
                return repo, True
            return repo, False
    return _create_repo_table(doc, name, revision), True


def _inject_missing_hooks(
    table: dict[str, Any],
    expected_hooks: list[HookBuiltin | HookLocal | HookRemote],
) -> int:
    """Inject missing hooks into the repository table.

    NOTE: An inline `hooks = [...]` array cannot hold tables, so it is
    converted to `[[repos.hooks]]` tables, keeping its hooks, before any
    missing hook is added.

    Args:
        table: The repository table.
        expected_hooks: The expected hooks to be present in the table.

    Returns:
        The number of hooks added to the table.
    """
    existing_id_set = {hook.get("id") for hook in table.get("hooks", [])}
    missing = [h for h in expected_hooks if h["id"] not in existing_id_set]

    if missing and not isinstance(table["hooks"], AoT):
        hooks = tomlkit.aot()
        for hook in table.pop("hooks"):
            hooks.append(hook.unwrap())
        table["hooks"] = hooks

    for expected in missing:
        logger.debug("Detected missing hook `%s`", expected["id"])
        hook_table = tomlkit.table()
        for key, value in expected.items():
            if isinstance(value, list):
                array = tomlkit.array()
                for item in value:
                    array.append(item)
                hook_table[key] = array
            else:
                hook_table[key] = value

        hook_table.add(tomlkit.nl())
        table["hooks"].append(hook_table)
    return len(missing)


def _merge_template(
    doc: TOMLDocument, template: TOMLDocument
) -> tuple[bool, int]:
    """Merge the template repos & hooks missing from a consumer document.

    Args:
        doc: The parsed consumer `prek.toml` document, modified in place.
        template: The parsed template (`hooks.toml`) document.

    Returns:
        A tuple containing a boolean indicating any changes and the number
        of hooks added.
    """
    changed, added = False, 0
    if "repos" not in doc or not doc.get("repos", []):
        logger.debug("Existing `prek.toml` missing or has empty `[repos]`")
        doc["repos"] = tomlkit.aot()
        changed = True

    for table in template.get("repos", []):
        name, rev = table.get("repo"), table.get("rev")
        table_consumer, tchanged = _get_repo_table(doc, name, rev)
        added += _inject_missing_hooks(table_consumer, table.get("hooks", []))
        changed = changed or tchanged

    return changed or added > 0, added


def _validate_prek_repos(doc: TOMLDocument) -> None:
    """Validate the consumer `prek.toml` `[[repos]]` shape.

    NOTE: A missing or empty `repos` key stays valid - the template
    injection path in `setup_prek_config` creates it.

    Args:
        doc: The parsed consumer `prek.toml` document.

    Raises:
        exceptions.PrekConfigError: On a malformed repo/hook entry.
    """
    repos = doc.get("repos")
    if repos is None:
        return
    if not isinstance(repos, list):
        msg = "`repos` must be an array of tables"
        raise exceptions.PrekConfigError(msg)

    for index, repo in enumerate(repos):
        is_table = isinstance(repo, dict)
        if not is_table or not isinstance(repo.get("repo"), str):
            msg = f"`repos[{index}]` missing string `repo` key"
            raise exceptions.PrekConfigError(msg)

        hooks = repo.get("hooks", [])
        if not isinstance(hooks, list):
            msg = f"`repos[{index}].hooks` must be an array of tables"
            raise exceptions.PrekConfigError(msg)

        for hook_index, hook in enumerate(hooks):
            is_table = isinstance(hook, dict)
            if not is_table or not isinstance(hook.get("id"), str):
                msg = (
                    f"`repos[{index}].hooks[{hook_index}]`"
                    " missing string `id` key"
                )
                raise exceptions.PrekConfigError(msg)


def setup_prek_config(root: Path, reset: bool = False) -> StepResult:
    """Configure pre-commit hooks in the consuming repo.

    NOTE: Expected errors (an invalid `PKGDX_CONFIG_DIR`, `prek.toml` or
    `hooks.toml`) are returned as FAIL results, not raised.

    Args:
        root: The root path of the consuming repo.
        reset: Clean installation flag. Defaults to False.

    Returns:
        An OK result (created, updated or unchanged `prek.toml`), or FAIL.
    """
    config_existing = root / "prek.toml"
    try:
        config_template = standards.resolve_config(standards.PREK_CONFIG)
    except exceptions.ConfigDirError as e:
        return StepResult(
            Outcome.FAIL,
            "user config directory not found",
            str(e),
            f"Create it, or unset `{standards.CONFIG_DIR_ENV}`",
        )
    template_text = config_template.read_text()

    if reset or not config_existing.exists():
        existed = config_existing.exists()
        if existed and config_existing.read_text() == template_text:
            logger.debug("Existing `prek.toml` matches the template")
            change = Change.UNCHANGED
        else:
            logger.debug("Creating `prek.toml` from template")
            config_existing.write_text(template_text)
            change = Change.UPDATED if existed else Change.CREATED
        return StepResult(Outcome.OK, change=change, subject="prek.toml")

    # Consuming project `prek.toml`
    try:
        doc_consumer = tomlkit.parse(config_existing.read_text())
        _validate_prek_repos(doc_consumer)
    except TOMLKitError as e:
        return StepResult(
            Outcome.FAIL,
            "prek.toml could not be parsed",
            str(e),
            _PREK_FIX_HINT,
        )
    except exceptions.PrekConfigError as e:
        return StepResult(
            Outcome.FAIL, "prek.toml is invalid", str(e), _PREK_FIX_HINT
        )

    # `pkgdx` template `prek.toml`
    try:
        doc_pkgdx = tomlkit.parse(template_text)
    except TOMLKitError as e:
        return StepResult(
            Outcome.FAIL,
            f"{config_template.name} could not be parsed",
            str(e),
            f"Fix {config_template}, or remove it to use the bundled template",
        )

    changed, added = _merge_template(doc_consumer, doc_pkgdx)
    if not changed:
        logger.debug("Existing `prek.toml` is correct & unchanged")
        return StepResult(
            Outcome.OK, change=Change.UNCHANGED, subject="prek.toml"
        )

    config_text = tomlkit.dumps(doc_consumer)
    # Normalise spacing between tables
    config_text = re.sub(r"\n+\[\[repos", "\n\n[[repos", config_text)

    config_existing.write_text(config_text)
    logger.debug("Added missing pre-commit hooks to `prek.toml`")
    hooks = f"{added} hook{'s' * (added != 1)}"
    subject = f"prek.toml ({hooks} added)" if added else "prek.toml"
    return StepResult(Outcome.OK, change=Change.UPDATED, subject=subject)


def create_secrets_baseline(root: Path) -> StepResult:
    """Run detect-secrets to create a `.secrets.baseline` file.

    NOTE: The scan output is written only on success, so a failed or
    interrupted scan leaves no partial baseline.

    Args:
        root: The root path of the consuming repo.

    Returns:
        An OK result (created or unchanged), or FAIL if the scan fails.
    """
    secrets_baseline = root / ".secrets.baseline"
    if secrets_baseline.exists():
        logger.debug("Using existing `.secrets.baseline`")
        return StepResult(
            Outcome.OK, change=Change.UNCHANGED, subject=".secrets.baseline"
        )

    logger.debug("Creating `.secrets.baseline` at %s", root)
    try:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "detect_secrets",
                "scan",
                "--exclude-files",
                r"(.*\.lock)",
            ],
            cwd=root,
            env=os.environ | {"PYTHONUTF8": "1"},
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode(errors="replace")
        logger.debug("detect-secrets scan failed: %s", stderr)
        reason = _last_line(stderr) or str(e)
    except FileNotFoundError as e:
        reason = str(e)
    else:
        secrets_baseline.write_bytes(proc.stdout)
        return StepResult(
            Outcome.OK, change=Change.CREATED, subject=".secrets.baseline"
        )
    return StepResult(
        Outcome.FAIL,
        ".secrets.baseline not created",
        reason,
        "Run `detect-secrets scan` to see the full error",
    )
