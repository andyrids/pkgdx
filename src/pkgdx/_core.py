"""Core logic and file-system operations for the `pkgdx init` command."""

import argparse
import dataclasses
import logging
import re
import subprocess
import sys
from collections.abc import Iterable
from itertools import chain
from pathlib import Path
from typing import Any

import tomlkit
import tomlkit.exceptions
from rich.console import Console
from tomlkit import TOMLDocument
from tomlkit.items import Table

from pkgdx import exceptions, standards
from pkgdx._types import HookBuiltin, HookLocal, HookRemote

logger = logging.getLogger(__package__)


class ExitCode:
    """Exit codes for the CLI commands."""

    EX_OK = 0
    EX_FAILURE = 1
    EX_SYNTAX = 2
    EX_USAGE = 64


@dataclasses.dataclass(frozen=True, slots=True)
class CLIContext:
    """Centralized state for the CLI commands."""

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
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            text=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        msg = "Failed `git rev-parse --show-toplevel`"
        raise exceptions.GitTopLevelError(msg) from e
    else:
        return Path(result.stdout.strip())


def get_project_root() -> Path:
    """Get the root path of the consuming repo.

    Returns:
        The root path of the consuming repo.
    """
    cwd = Path.cwd().resolve()
    for directory in chain([cwd], cwd.parents):
        if (directory / "pyproject.toml").exists():
            return directory

    venv_parent = Path(sys.prefix).parent
    if (venv_parent / "pyproject.toml").exists():
        return venv_parent

    msg = f"Cannot identify project root:- `{sys.prefix=}` | `{cwd=}`."
    raise exceptions.ProjectRootNotFoundError(msg)


def install_prek_hooks(root: Path) -> None:
    """Install pre-commit hooks if not installed.

    Args:
        root: The root path of the consuming repo.
    """
    precommit_config = root / ".git" / "hooks" / "pre-commit"
    if precommit_config.exists():
        logger.debug("Prek pre-commit hooks already installed")
        return
    try:
        subprocess.run(
            [sys.executable, "-m", "prek", "install"],
            cwd=root,
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.exception("Failed to install pre-commit hooks")
    else:
        logger.debug("Prek pre-commit hooks installed")


def update_prek_hooks(root: Path) -> None:
    """Check for pre-commit hook updates.

    NOTE: Updates the pre-commit hooks based on available tagged versions in
    the remote `pkgdx` repo.

    Args:
        root: The root path of the consuming repo.
    """
    try:
        subprocess.run(
            [sys.executable, "-m", "prek", "update", "--check", "-v"],
            cwd=root,
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        msg = re.sub(r"\n\s|\n", "", e.stdout or e.stderr or "Unknown error")
        match e.returncode:
            case 1:
                logger.warning(msg)
                logger.warning("Update `pkgdx` hooks with `prek update`")
            case 2:
                logger.error(msg)
            case _:
                logger.exception(msg)
    except FileNotFoundError:
        logger.exception("Check `prek.toml` exists")
    else:
        logger.info("Prek pre-commit hooks are up-to-date")


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
) -> bool:
    """Inject missing hooks into the repository table.

    Args:
        table: The repository table.
        expected_hooks: The expected hooks to be present in the table.

    Returns:
        A boolean indicating if the table was modified.
    """
    changed = False
    existing_id_set = {hook.get("id") for hook in table.get("hooks", [])}

    for expected in expected_hooks:
        if expected["id"] not in existing_id_set:
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
            changed = True
    return changed


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


def setup_prek_config(root: Path, reset: bool = False) -> None:
    """Configure pre-commit hooks in the consuming repo.

    Args:
        root: The root path of the consuming repo.
        reset: Clean installation flag. Defaults to False.
    """
    changed = False
    config_existing = root / "prek.toml"
    config_template = standards.PREK_CONFIG

    if reset or not config_existing.exists():
        logger.info("Creating `prek.toml` from template")
        config_existing.write_text(config_template.read_text())
        return

    # Consuming project `prek.toml`
    doc_consumer: TOMLDocument = tomlkit.parse(config_existing.read_text())
    _validate_prek_repos(doc_consumer)

    if "repos" not in doc_consumer or not doc_consumer.get("repos", []):
        logger.debug("Existing `prek.toml` missing or has empty `[repos]`")
        doc_consumer["repos"] = tomlkit.aot()
        changed = True

    # `pkgdx` template `prek.toml`
    doc_pkgdx: TOMLDocument = tomlkit.parse(config_template.read_text())
    for table in doc_pkgdx.get("repos", []):
        name, rev = table.get("repo"), table.get("rev")
        table_consumer, tchanged = _get_repo_table(doc_consumer, name, rev)

        table_pkgdx = table.get("hooks", [])
        hchanged = _inject_missing_hooks(table_consumer, table_pkgdx)

        changed = changed or tchanged or hchanged

    if changed:
        config_text = tomlkit.dumps(doc_consumer)
        # Normalise spacing between tables
        config_text = re.sub(r"\n+\[\[repos", "\n\n[[repos", config_text)

        config_existing.write_text(config_text)
        logger.debug("Added missing pre-commit hooks to `prek.toml`")
    else:
        logger.info("Existing `prek.toml` correct & unchanged")


def create_secrets_baseline(root: Path) -> None:
    """Run detect-secrets to create a `.secrets.baseline` file."""
    secrets_baseline = root / ".secrets.baseline"
    if secrets_baseline.exists():
        logger.debug("Using existing `.secrets.baseline`")
        return

    logger.info("Creating `.secrets.baseline` at %s", root)
    try:
        with open(secrets_baseline, "w") as f:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "detect_secrets",
                    "scan",
                    "--exclude-files",
                    r"(.*\.lock)",
                ],
                cwd=root,
                stdout=f,
                check=True,
            )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        secrets_baseline.unlink(missing_ok=True)
        msg = "Error creating `.secrets.baseline`"
        raise exceptions.Error(msg) from e
