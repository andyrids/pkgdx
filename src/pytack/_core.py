"""Core logic and file-system operations for pytack setup."""

import argparse
import dataclasses
from rich.console import Console
import logging
import re
import subprocess
import sys
from itertools import chain
from pathlib import Path
from typing import Any

import tomlkit
import tomlkit.exceptions
from tomlkit import TOMLDocument
from tomlkit.items import Table

from pytack import exceptions, standards
from pytack._types import HookBuiltin, HookLocal, HookRemote

logger = logging.getLogger(__package__)


class ExitCode:
    """Exit codes for the CLI commands."""

    EX_OK = 0
    EX_FAILURE = 1
    EX_SYNTAX = 2


@dataclasses.dataclass
class CLIContext:
    """Centralized state for the CLI commands."""

    args: argparse.Namespace
    console: Console
    is_verbose: bool


def get_git_toplevel() -> Path:
    """Gets the root path of the consuming Git repository.

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
    """Gets the root path of the consuming repo.

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
    """Checks for pre-commit hook updates.

    NOTE: Updates the pre-commit hooks based on available tagged versions in
    the remote `pytack` repo.

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
                logger.warning("Update `pytack` hooks with `prek update`")
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
    """Creates a new repository table in the pre-commit configuration.

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
    """Gets an existing or creates a new repository table.

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
    """Injects missing hooks into the repository table.

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


def setup_prek_config(root: Path, reset: bool = False) -> None:
    """Configures pre-commit hooks in the consuming repo.

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

    if "repos" not in doc_consumer or not doc_consumer.get("repos", []):
        logger.debug("Existing `prek.toml` missing or has empty `[repos]`")
        doc_consumer["repos"] = tomlkit.aot()
        changed = True

    # `pytack` template `prek.toml`
    doc_pytack: TOMLDocument = tomlkit.parse(config_template.read_text())
    for table in doc_pytack.get("repos", []):
        name, rev = table.get("repo"), table.get("rev")
        table_consumer, tchanged = _get_repo_table(doc_consumer, name, rev)

        table_pytack = table.get("hooks", [])
        hchanged = _inject_missing_hooks(table_consumer, table_pytack)

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
    """Runs detect-secrets to create a .secrets.baseline file."""
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
