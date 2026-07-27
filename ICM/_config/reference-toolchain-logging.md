---
context-hierarchy: Layer 3
context-hierarchy-role: Rules, conventions and guidelines
---

# Toolchain - logging

All logging is handled through the primary package logger. To ensure logs are routed correctly,
always instantiate loggers using the package name:

```python
import logging

logger = logging.getLogger(__package__)
```

## Configuration

Logging configuration is separated into two distinct contexts to prevent interference with
consuming applications:

### (1) Package Logging (Library)

By default, the package is configured with a `NullHandler`. This prevents the library from
polluting STDOUT when imported as a dependency.

- Setup: `configure_pkg_logging()` is called in `src/pkgdx/__init__.py`.

### (2) CLI Logging (Application)

When executed as a CLI, logging is configured using the settings defined in
`src/pkgdx/logging/config.toml`.

- Setup: `configure_cli_logging(level)` is called in `src/pkgdx/__main__.py` after argument
parsing.
- Handlers: Uses `rich.logging.RichHandler` for STDOUT and a standard `StreamHandler` for STDERR.

## Rich Progress Bar Integration

When building CLI features that use `rich.progress.Progress`, the progress bar MUST share the
`RichHandler` console — see "Sharing the Logging Console" in `reference-cookbook-rich.md`.
