[unix]
set shell := ["bash", "-euo", "pipefail", "-c"]

[windows]
set shell := ["cmd.exe", "/c"]

set dotenv-load := true

[default]
@_:
    just --list

[doc("Generate a `detect-secrets` baseline for the repository")]
[group("DEV")]
secrets-baseline:
    echo "NOTE: Run this once after initial setup & re-run after intentionally adding secrets to the codebase (e.g. test fixtures)."
    uv run detect-secrets scan --exclude-files "(\.venv\.secrets\.baseline|.*\.lock)" > .secrets.baseline

[doc("Setup development environment")]
[group("DEV")]
setup: && secrets-baseline
    uv sync
    uv run -m prek install

[doc("Test `pkgdx` CLI in workspace member `consumers/testing`")]
[group("DEV")]
test-consumer *FLAGS:
    uv run --directory consumers/testing pkgdx
    uv run --directory consumers/testing pkgdx --version
    uv run --directory consumers/testing pkgdx -debug init --help
    uv run --directory consumers/testing pkgdx --debug init {{FLAGS}}

[doc("Create `coverage` report")]
[group("DEV")]
coverage *FLAGS:
    @uv run coverage run -m pytest {{FLAGS}}
    @uv run coverage report --show-missing --skip-covered --fail-under=75
    @uv run coverage xml
    @uv run coverage html

[doc("Git prune (aggressive)")]
[group("DEV")]
git-prune:
    git gc --prune=now --aggressive

[doc("Symlink `AGENTS.md` -> `CLAUDE.md`")]
[group("DEV")]
symlink-agents:
    @uv run python -c "import pathlib; p=pathlib.Path('CLAUDE.md'); p.unlink(missing_ok=True); p.symlink_to('AGENTS.md')"
