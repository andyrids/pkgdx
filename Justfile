[default]
@_:
    just --list

[doc("Generate a `detect-secrets` baseline for the repository")]
[group("DEV")]
secrets-baseline:
    echo "NOTE: Run this once after initial setup & re-run after intentionally adding secrets to the codebase (e.g. test fixtures)."
    uv run detect-secrets scan --exclude-files '(\.secrets\.baseline|.*\.lock)' > .secrets.baseline

[doc("Setup development environment")]
[group("DEV")]
setup:
    uv sync
    uv run -m prek install
    {{ if path_exists(".secrets.baseline") == "false" { "just secrets-baseline" } else { "" } }}