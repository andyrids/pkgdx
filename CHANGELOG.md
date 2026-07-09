<!-- pyml disable MD024 -->
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> [!NOTE]
> Types of changes:
>
> - `Added` for new features.
> - `Changed` for changes in existing functionality.
> - `Deprecated` for soon-to-be removed features.
> - `Removed` for now removed features.
> - `Fixed` for any bug fixes.
> - `Security` in case of vulnerabilities.

## [Unreleased]

### Added

- Rich progress bar to the `setup` command, tracking the setup stages.
- Automatic disabling of the progress bar in non-TTY environments.
- Render log messages above the live progress display.

## [0.1.0] - 2026-07-05

### Added

- CLI setup script for automated project configuration.
- `--reset` option for CLI setup script.
- Detect missing hooks based on pkgdevx config.
- Build & publish to GitLab package registry.
- Unit tests.

### Fixed

- Updated with correct Prek `update` command.
