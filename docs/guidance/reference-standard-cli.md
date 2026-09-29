---
context-hierarchy: Layer 3
context-hierarchy-role: Reference material
immutable: true
recommended-context-tokens: 2500
tags: [CLI, argparse]
---

# Standard - CLI

This standard is based on the [Command Line Interface Guidelines](https://clig.dev/).

## (1) Basic rules

These basic rules make a CLI easy to use and act as a solid foundation.

### Exit codes

Return zero exit code on success and non-zero on failure. Map the non-zero exit codes to the most
important failure modes.

### Output

Send output to STDOUT, including anything that is machine readable.

### Messaging

Send messaging to STDERR, including log messages, errors and exceptions. When commands are piped
together, these messages are displayed to the user and not fed into the next command.

## (2) Help

Display extensive help text when asked. Display help when passed `-h` or `--help` flags.

Display concise help text by default. When `pkgdx` or `pkgdx subcommand` requires arguments to
function and is run with no arguments, display concise help text.

NOTE: You can ignore this guideline if your program is interactive by default (e.g. `npm init`).

Concise help text:

- A description of what your program does.
- One or two example invocations.
- Descriptions of flags, unless there are lots of them.
- An instruction to pass the `--help` flag for more information.

## (2) Documentation

The purpose of help text is to give a brief, immediate sense of what your tool is, what options are
available and how to perform the most common tasks. Documentation, on the other hand, is where you
go into full detail.
