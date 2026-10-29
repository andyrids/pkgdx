[unix]
set shell := ["bash", "-euo", "pipefail", "-c"]

[windows]
set shell := ["pwsh.exe", "-c"]

set dotenv-load := true

[default]
@_:
    just --list

[doc("Generate a `detect-secrets` baseline for the repository")]
[group("DEV")]
secrets-baseline:
    echo "NOTE: Run this once after initial setup & re-run after intentionally adding secrets to the codebase (e.g. test fixtures)."
    uv run detect-secrets scan --exclude-files "(\.venv|\.secrets\.baseline|.*\.lock)" > .secrets.baseline

[doc("Setup development environment")]
[group("DEV")]
setup: && secrets-baseline
    uv sync
    uv run -m prek install

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

[env("PKGDX_CONFIG_DIR", ".pkgdx")]
[doc("Test `pkgdx init` command in workspace member `consumers/testing`")]
[group("TEST")]
consumer-init *FLAGS:
    uv run --directory consumers/testing pkgdx init {{FLAGS}}

[env("PKGDX_CONFIG_DIR", ".pkgdx")]
[doc("Test `pkgdx config` command in workspace member `consumers/testing`")]
[group("TEST")]
consumer-config *FLAGS:
    uv run --directory consumers/testing pkgdx config {{FLAGS}}


[env("PKGDX_CONFIG_DIR", ".pkgdx")]
[doc("Demonstrate `pkgdx` features in workspace member `consumers/testing`")]
[group("TEST")]
consumer-demo *FLAGS:
    @echo '{{CLEAR}}'
    @echo '{{ BOLD + CYAN + INVERT + "--- pkgdx demo in workspace member `consumers/testing` ---" + NORMAL }}'
    @rm ./consumers/testing/.pkgdx/*
    @-rm ./consumers/testing/prek.toml
    @-rm ./consumers/testing/.secrets.baseline
    @ls ./consumers/testing/
    @sleep 1.5

    @echo '{{ BOLD + CYAN + "SETUP canonical standards\n" + NORMAL }}'
    @echo '{{ GREEN + ITALIC + "$ pkgdx init" + NORMAL }}'
    @sleep 1
    @uv run --directory consumers/testing pkgdx {{FLAGS}} init
    @sleep 2
    @ls ./consumers/testing/
    @sleep 2

    @echo ""
    @echo '{{ BOLD + CYAN + "INIT is idempotent (without --reset)\n" + NORMAL }}'
    @echo '{{ GREEN + ITALIC + "$ pkgdx init" + NORMAL }}'
    @sleep 1
    @uv run --directory consumers/testing pkgdx {{FLAGS}} init
    @sleep 2

    @echo ""
    @echo '{{ BOLD + CYAN + "CHECK toolchain config (default is bundled)\n" + NORMAL }}'
    @echo '{{ GREEN + ITALIC + "$ pkgdx config" + NORMAL }}'
    @sleep 1
    @uv run --directory consumers/testing pkgdx {{FLAGS}} config
    @sleep 2

    @echo ""
    @echo '{{ BOLD + CYAN + "EXPORT toolchain config (demo uses PKGDX_CONFIG_DIR)\n" + NORMAL }}'
    @echo '{{ GREEN + ITALIC + "$ pkgdx config --export" + NORMAL }}'
    @sleep 1
    @uv run --directory consumers/testing pkgdx {{FLAGS}} config --export
    @sleep 2

    @echo ""
    @echo '{{ BOLD + CYAN + "MODIFY toolchain config(s) as desired (demo edits pymarkdown.toml)\n" + NORMAL }}'
    @echo '{{ GREEN + ITALIC + "$ vim ./consumers/testing/.pkgdx/pymarkdown.toml" + NORMAL }}'
    @sleep 1
    @uv run --directory consumers/testing python -c "import pathlib; \
        p = pathlib.Path('.pkgdx/pymarkdown.toml'); \
        p.write_text( \
            p.read_text().replace( \
                'line-length.line_length = 100', 'line-length.line_length = 30', 1 \
            ) \
        )"
    @uv run --directory consumers/testing python -m  rich.syntax -l -t github-dark --highlight-line=7 .pkgdx/pymarkdown.toml
    @sleep 2

    @echo ""
    @echo '{{ BOLD + CYAN + "HOOKS reflect config changes\n" + NORMAL }}'
    @echo '{{ GREEN + ITALIC + "$ prek run --all-files" + NORMAL }}'
    @sleep 1
    @-uv run --directory consumers/testing prek run --all-files
    @sleep 3

    @echo ""
    @echo '{{ BOLD + CYAN + "REMOVE toolchain config(s) as desired (pymarkdown.toml reverts to bundled)\n" + NORMAL }}'
    @echo '{{ GREEN + ITALIC + "$ rm .pkgdx/pymarkdown.toml && pkgdx config" + NORMAL }}'
    @sleep 1
    @rm ./consumers/testing/.pkgdx/pymarkdown.toml
    @uv run --directory consumers/testing pkgdx {{FLAGS}} config
    @sleep 2

    @echo ""
    @echo '{{ BOLD + CYAN + "HOOKS reflect config changes\n" + NORMAL }}'
    @echo '{{ GREEN + ITALIC + "$ prek run --all-files" + NORMAL }}'
    @sleep 1
    @-uv run --directory consumers/testing prek run --all-files
    @sleep 3
