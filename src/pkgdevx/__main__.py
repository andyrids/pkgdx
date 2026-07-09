"""Main entry point for pkgdevx pre-commit hooks."""

import argparse
import logging
import re
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from itertools import chain
from pathlib import Path
from typing import NoReturn

import tomlkit
import tomlkit.exceptions
from pkgdevx import exceptions, standards
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, TaskID
from tomlkit import TOMLDocument
from tomlkit.items import Table


logger = logging.getLogger(__package__)


@contextmanager
def _setup_progress() -> Iterator[Progress]:
    """Create a TTY-aware Rich progress bar for the setup command.

    The progress bar shares a Console with any RichHandler attached to the
    ``pkgdevx`` logger so that log messages render above the live progress
    display. In non-TTY environments the progress bar is disabled and output
    falls back to plain logging.
    """

    handlers = [h for h in logger.handlers if isinstance(h, RichHandler)]
    if not handlers:
        logger.error("Failed to find logging handlers")
        raise exceptions.RichHandlerNotFound

    is_tty = sys.stdout.isatty()
    console = Console(force_terminal=is_tty)

    original_consoles = {h: h.console for h in handlers}

    for h in handlers:
        h.console = console

    progress = Progress(
        *Progress.get_default_columns(),
        console=console,
        disable=not is_tty,
    )

    try:
        with progress:
            yield progress
    finally:
        for handler, original_console in original_consoles.items():
            handler.console = original_console


def _advance_progress(
    progress: Progress,
    task_id: TaskID,
    description: str,
) -> None:
    """Update the description & advance a progress task by one step."""
    progress.update(task_id, description=description, advance=1)


def ruff_format() -> NoReturn:
    """Runs ruff formatting with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdevx-format`, with
    entry point `pkgdevx-format-hook`.
    """
    config = standards.RUFF_CONFIG.as_posix()
    cmd = ["ruff", "format", "--config", config] + sys.argv[1:]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def ruff_lint() -> NoReturn:
    """Runs ruff linting with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdevx-lint`, with
    entry point `pkgdevx-lint-hook`.
    """
    config = standards.RUFF_CONFIG.as_posix()
    cmd = ["ruff", "check", "--config", config] + sys.argv[1:]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def mypy_typing() -> NoReturn:
    """Runs mypy type checking with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdevx-typing`, with
    entry point `pkgdevx-typing-hook`.
    """
    config = standards.MYPY_CONFIG.as_posix()
    cmd = ["mypy", "--config-file", config] + sys.argv[1:]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def detect_secrets() -> NoReturn:
    """Runs detect-secrets with the provided arguments.

    NOTE: Relates to pre-commit hook ID `pkgdevx-secrets`, with
    entry point `pkgdevx-secrets-hook`.
    """
    args = sys.argv[1:]
    if "--baseline" not in args:
        args = ["--baseline", ".secrets.baseline"] + args
    cmd = ["detect-secrets-hook"] + args
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def pymarkdown_lint() -> NoReturn:
    """Runs pymarkdown linting with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdevx-markdown`, with
    entry point `pkgdevx-markdown-hook`.
    """
    config = standards.PYMARKDOWN_CONFIG.as_posix()
    cmd = ["pymarkdown", "--config", config, "scan"] + sys.argv[1:]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


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
            ["uv", "run", "prek", "install"],
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
    the remote `pkgdevx` repo.

    Args:
        root: The root path of the consuming repo.
    """
    try:
        subprocess.run(
            ["uv", "run", "prek", "update", "--check"],
            cwd=root,
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        if e.stdout:
            logger.warning(re.sub("\n", "", e.stdout))
            logger.warning("Run `uv run prek update`")
        if e.stderr:
            logger.exception("Failed to check for hook updates")
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

    logger.debug(f"Created `[repo]` - {name=} | {revision=}")
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
    table: dict, expected_hooks: tuple[dict[str, str], ...]
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
            logger.debug(f"Detected missing hook `{expected['id']=}`")
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

    tomlkit.exceptions.TOMLKitError
    if "repos" not in doc_consumer:
        logger.debug("Existing `prek.toml` missing `[repos]`")
        doc_consumer["repos"] = tomlkit.aot()
        changed = True

    # `pkgdevx` template `prek.toml`
    doc_pkgdevx: TOMLDocument = tomlkit.parse(config_template.read_text())
    for table in doc_pkgdevx.get("repos", []):
        name, rev = table.get("repo"), table.get("rev")
        table_consumer, tchanged = _get_repo_table(doc_consumer, name, rev)

        table_pkgdevx = table.get("hooks", [])
        hchanged = _inject_missing_hooks(table_consumer, table_pkgdevx)

        changed = changed or tchanged or hchanged

    if changed:
        config_text = tomlkit.dumps(doc_consumer)
        # Normalise spacing between tables
        config_text = re.sub(r"\n+\[\[repos", "\n\n[[repos", config_text)

        config_existing.write_text(config_text)
        logger.debug(f"Added missing pre-commit hooks to `prek.toml`")
    else:
        logger.info(f"Existing `prek.toml` correct & unchanged")


def command_setup(args: argparse.Namespace) -> None:
    """Configures a consuming repo with `pkgdevx` standards.

    Attempts to identify the root of the consuming repo and ensures that
    `Prek` is configured with the expected `pkgdevx` hooks.

    Args:
        args: Namespace object with command-line arguments as attributes.
    """
    with _setup_progress() as progress:
        task = progress.add_task("[cyan]pkgdev setup", total=6)

        _advance_progress(progress, task, "[cyan]Find project root")
        try:
            root = get_project_root()
        except exceptions.ProjectRootNotFoundError:
            progress.update(
                task,
                description="[red]Failed to find project root",
            )
            logger.exception("Failed to find project root")
            sys.exit(1)

        _advance_progress(progress, task, "[cyan]Find Git top-level")
        git_toplevel = None
        try:
            git_toplevel = get_git_toplevel()
        except exceptions.GitTopLevelError as e:
            logger.warning(str(e))

        _advance_progress(progress, task, "[cyan]Configure pre-commit hooks")
        try:
            setup_prek_config(root, reset=args.reset)
        except tomlkit.exceptions.TOMLKitError:
            progress.update(
                task,
                description="[red][strike]Configure pre-commit hooks",
            )
            logger.exception("Failed to configure pre-commit hooks")
            sys.exit(1)

        _advance_progress(
            progress, task, "[cyan]Prek install pre-commit hooks"
        )
        install_prek_hooks(git_toplevel or root)

        _advance_progress(progress, task, "[cyan]Prek check updates")
        update_prek_hooks(root)

        _advance_progress(progress, task, "[cyan]Create `.secrets.baseline`")
        secrets_baseline = root / ".secrets.baseline"
        if not secrets_baseline.exists():
            logger.info("Creating `.secrets.baseline` at %s" % root)
            try:
                # Open `.secrets.baseline` for stdout redirect
                with open(secrets_baseline, "w") as f:
                    subprocess.run(
                        [
                            "uv",
                            "run",
                            "detect-secrets",
                            "scan",
                            "--exclude-files",
                            r"(.*\.lock)",
                        ],
                        cwd=root,
                        stdout=f,
                        check=True,
                    )
            except (subprocess.CalledProcessError, FileNotFoundError):
                progress.update(
                    task,
                    description="[red][strike]Create `.secrets.baseline`",
                )
                logger.exception("Error creating `.secrets.baseline`")
                secrets_baseline.unlink(missing_ok=True)
                sys.exit(1)
        else:
            logger.debug("Using existing `.secrets.baseline`")

        progress.update(
            task,
            description="[green]pkgdevx complete",
        )


def main() -> None:
    """Provides CLI entrypoint for `pkgdevx`."""
    parser = argparse.ArgumentParser(
        description="`pkgdevx` - Canonical standards management"
    )

    # Require a subcommand ('setup')
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=True,
        help="Available commands",
    )

    parser_setup = subparsers.add_parser(
        "setup", help="Setup pre-commit hooks"
    )

    parser_setup.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging [DEBUG]",
    )

    parser_setup.add_argument(
        "--reset", action="store_true", help="Reset existing pre-commit hooks"
    )

    parser_setup.set_defaults(func=command_setup)

    args = parser.parse_args()
    logger.setLevel(logging.DEBUG if args.verbose else logging.WARNING)

    args.func(args)
    sys.exit(0)


if __name__ == "__main__":
    main()
