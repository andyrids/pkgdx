"""Main entry point for pkgdev pre-commit hooks."""

import logging
import sys
import subprocess
from itertools import chain
from pathlib import Path
from typing import NoReturn

import tomlkit
from pkgdev import exceptions, standards
from tomlkit import TOMLDocument
from tomlkit.items import Table


logger = logging.getLogger(__name__)


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


def get_project_root() -> Path:
    """Gets the root path of the consuming repo.

    Returns:
        The root path of the consuming repo.
    """
    venv_parent = Path(sys.prefix).parent
    if (venv_parent / "pyproject.toml").exists():
        return venv_parent

    cwd = Path.cwd().resolve()
    for directory in chain([cwd], cwd.parents):
        if (directory / "pyproject.toml").exists():
            return directory

    msg = f"Cannot identify project root:- `{sys.prefix=}` | `{cwd=}`."
    raise exceptions.ProjectRootNotFoundError(msg)


def install_prek_hooks(root: Path) -> None:
    """Install pre-commit hooks if not installed.

    Args:
        root: The root path of the consuming repo.
    """
    precommit_config = root / ".git" / "hooks" / "pre-commit"
    if precommit_config.exists():
        logger.info("Pre-commit hooks already installed.")
        return
    try:
        subprocess.run(
            ["uv", "run", "prek", "install"], cwd=root, capture_output=True, check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error(e, exc_info=True)
    except FileNotFoundError as e:
        logger.error(e, exc_info=True)


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
        )
    except subprocess.CalledProcessError as e:
        logger.error(e, exc_info=True)
    except FileNotFoundError as e:
        logger.error(e, exc_info=True)


def setup_prek_config(root: Path) -> None:
    """Configures pre-commit hooks in the consuming repo.

    Args:
        root: The root path of the consuming repo.
    """
    changed = False
    config_existing = root / "prek.toml"
    config_template = standards.PREK_CONFIG

    if not config_existing.exists():
        config_existing.write_text(config_template.read_text())
        return

    doc: TOMLDocument = tomlkit.parse(config_existing.read_text())

    if "repos" not in doc:
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
        new_repo["hooks"] = tomlkit.aot()
        doc["repos"].append(new_repo)
        changed = True
        return new_repo

    def get_repo_table(name: str, revision: str | None = None) -> Table:
        """Gets an existing or creates a new repository table.

        Args:
            name: The name of the repository.
            revision: The revision of the repository.
        """
        nonlocal changed

        for repo in doc["repos"]:
            print(type(repo), end="\n\n")
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
                hook_table = tomlkit.table()
                for key, value in expected.items():
                    if isinstance(value, list):
                        array = tomlkit.array()
                        for item in value:
                            array.append(item)
                        hook_table[key] = array
                    else:
                        hook_table[key] = value

                table["hooks"].append(hook_table)
                changed = True

    doc_pkgdev: TOMLDocument = tomlkit.parse(config_template.read_text())
    for table in doc_pkgdev.get("repos", []):
        name = table.get("repo")
        revision = table.get("rev")

        existing_table = get_repo_table(name, revision)
        inject_missing_hooks(existing_table, table.get("hooks", []))

    if changed:
        logger.info(f"Updating pre-commit hooks (`{config_existing}`).")
        config_existing.write_text(tomlkit.dumps(doc))


def main() -> None:
    """Configures a consuming repo with `pkgdev` standards.

    Attempts to identify the root of the consuming repo and ensures that
    `Prek` is configured with the expected `pkgdev` hooks.
    """
    try:
        root = get_project_root()
    except exceptions.ProjectRootNotFoundError as e:
        logger.error(e, exc_info=True)
        sys.exit(1)

    setup_prek_config(root)
    install_prek_hooks(root)
    update_prek_hooks(root)

    secrets_baseline = root / ".secrets.baseline"
    if not secrets_baseline.exists():
        logger.info("Creating `.secrets.baseline`.")
        try:
            subprocess.run(
                [
                    "uv",
                    "run",
                    "detect-secrets",
                    "scan",
                    "--exclude-files",
                    r"(.*\.lock)",
                    ">",
                    ".secrets.baseline",
                ],
                cwd=root,
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error(e, exc_info=True)
            sys.exit(1)
        except FileNotFoundError as e:
            logger.error(e, exc_info=True)
            sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
