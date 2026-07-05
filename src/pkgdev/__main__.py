"""Main entry point for pkgdev pre-commit hooks."""

import argparse
import logging
import re
import sys
import subprocess
from itertools import chain
from pathlib import Path
from typing import NoReturn

import tomlkit
from pkgdev import exceptions, standards
from tomlkit import TOMLDocument
from tomlkit.items import Table


logger = logging.getLogger(__package__)


def ruff_format() -> None:
    """Runs ruff formatting with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdev-format`, with
    entry point `pkgdev-format-hook`.
    """
    config = standards.RUFF_CONFIG.as_posix()
    cmd = ["ruff", "format", "--config", config] + sys.argv[1:]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def ruff_lint() -> NoReturn:
    """Runs ruff linting with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdev-lint`, with
    entry point `pkgdev-lint-hook`.
    """
    config = standards.RUFF_CONFIG.as_posix()
    cmd = ["ruff", "check", "--config", config] + sys.argv[1:]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def mypy_typing() -> None:
    """Runs mypy type checking with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdev-typing`, with
    entry point `pkgdev-typing-hook`.
    """
    config = standards.MYPY_CONFIG.as_posix()
    cmd = ["mypy", "--config-file", config] + sys.argv[1:]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def detect_secrets() -> None:
    """Runs detect-secrets with the provided arguments.

    NOTE: Relates to pre-commit hook ID `pkgdev-secrets`, with
    entry point `pkgdev-secrets-hook`.
    """
    args = sys.argv[1:]
    if "--baseline" not in args:
        args = ["--baseline", ".secrets.baseline"] + args
    cmd = ["detect-secrets-hook"] + args
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def pymarkdown_lint() -> None:
    """Runs pymarkdown linting with the configured settings.

    NOTE: Relates to pre-commit hook ID `pkgdev-markdown`, with
    entry point `pkgdev-markdown-hook`.
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
        return
    try:
        subprocess.run(
            ["uv", "run", "prek", "install"],
            cwd=root,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        logger.exception(e)
    except FileNotFoundError as e:
        logger.exception(e)
    else:
        logger.debug("Prek pre-commit hooks installed")


def update_prek_hooks(root: Path) -> None:
    """Auto-update pre-commit hooks.

    NOTE: Updates the pre-commit hooks based on available tagged versions in
    the remote `pkgdev` repo.

    Args:
        root: The root path of the consuming repo.
    """
    try:
        subprocess.run(
            ["uv", "run", "prek", "auto-update"],
            cwd=root,
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(e.stderr or e.stdout)
    except FileNotFoundError as e:
        logger.exception(e)
    else:
        logger.debug("Prek auto-update process completed")


def setup_prek_config(root: Path, reset: bool = False) -> None:
    """Configures pre-commit hooks in the consuming repo.

    Args:
        root: The root path of the consuming repo.
    """
    changed = False
    config_existing = root / "prek.toml"
    config_template = standards.PREK_CONFIG

    # Config file missing | empty | `--reset` option
    if reset or not config_existing.exists() or not config_existing.stat().st_size:
        logger.debug(f"Existing `./{config_existing.name}` not found")
        config_existing.write_text(config_template.read_text())
        return

    doc: TOMLDocument = tomlkit.parse(config_existing.read_text())

    if "repos" not in doc:
        logger.debug(f"Existing `./{config_existing.name}` is missing `[repos]` AoT")
        doc["repos"] = tomlkit.aot()
        changed = True

    def create_repo_table(name: str, revision: str | None = None) -> Table:
        """Creates a new repository table in the pre-commit configuration.

        Args:
            name: The name of the repository.
            revision: The revision of the repository.
        """
        nonlocal changed
        new_repo = tomlkit.table()
        new_repo["repo"] = name
        if revision:
            new_repo["rev"] = revision

        new_repo.add(tomlkit.nl())

        new_repo["hooks"] = tomlkit.aot()
        doc["repos"].append(new_repo)
        changed = True
        logger.debug(f"Created new `[repo]` table - {name=} | {revision=}")
        return new_repo

    def get_repo_table(name: str, revision: str | None = None) -> Table:
        """Gets an existing or creates a new repository table.

        Args:
            name: The name of the repository.
            revision: The revision of the repository.
        """
        nonlocal changed

        for repo in doc["repos"]:
            if repo.get("repo") == name:
                if "hooks" not in repo:
                    repo["hooks"] = tomlkit.aot()
                    changed = True
                return repo
        return create_repo_table(name, revision)

    def inject_missing_hooks(
        table: dict, expected_hooks: tuple[dict[str, str], ...]
    ) -> None:
        """Injects missing hooks into the repository table.

        Args:
            table: The repository table.
            expected_hooks: The expected hooks to be present in the table.
        """
        nonlocal changed
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

    doc_pkgdev: TOMLDocument = tomlkit.parse(config_template.read_text())
    for table in doc_pkgdev.get("repos", []):
        name = table.get("repo")
        revision = table.get("rev")

        existing_table = get_repo_table(name, revision)
        inject_missing_hooks(existing_table, table.get("hooks", []))

    if changed:
        config_text = tomlkit.dumps(doc)
        # Normalise spacing between tables
        config_text = re.sub(r"\n+\[\[repos", "\n\n[[repos", config_text)

        config_existing.write_text(config_text)
        logger.debug(
            f"Updated existing `./{config_existing.name}` with missing pre-commit hooks"
        )


def command_setup(args: argparse.Namespace) -> None:
    """Configures a consuming repo with `pkgdev` standards.

    Attempts to identify the root of the consuming repo and ensures that
    `Prek` is configured with the expected `pkgdev` hooks.

    Args:
        args: Namespace object with command-line arguments as attributes.
    """
    try:
        root = get_project_root()
    except exceptions.ProjectRootNotFoundError as e:
        logger.exception(e)
        sys.exit(1)

    git_toplevel = None
    try:
        git_toplevel = get_git_toplevel()
    except exceptions.GitTopLevelError as e:
        logger.warning(str(e))

    setup_prek_config(root, reset=args.reset)
    install_prek_hooks(git_toplevel or root)
    update_prek_hooks(root)

    secrets_baseline = root / ".secrets.baseline"
    if not secrets_baseline.exists():
        logger.info(f"Creating `.secrets.baseline` at {root}.")
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
        except subprocess.CalledProcessError as e:
            logger.exception(e)
            sys.exit(1)
        except FileNotFoundError as e:
            logger.exception(e)
            sys.exit(1)


def main() -> None:
    """Provides CLI entrypoint for `pkgdev`."""
    parser = argparse.ArgumentParser(
        description="`pkgdev` - Canonical standards management"
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging [INFO]",
    )

    # Require a subcommand ('setup')
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=True,
        help="Available commands",
    )

    parser_setup = subparsers.add_parser("setup", help="Setup pre-commit hooks")

    parser_setup.add_argument(
        "--reset", action="store_true", help="Reset existing pre-commit hooks"
    )

    parser_setup.set_defaults(func=command_setup)

    args = parser.parse_args()
    logger.setLevel(logging.DEBUG if args.verbose else logging.WARNING)

    args.func(args)
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
