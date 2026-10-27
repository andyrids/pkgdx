---
context-hierarchy: Layer 3
context-hierarchy-role: Reference material
immutable: false
tags: [cli, config, user-config, export, overrides]
---

# Command: pkgdx config

## Invocation / inputs

| Argument   | Required | Default | Meaning                                                    |
| ---------- | -------- | ------- | ---------------------------------------------------------- |
| `--export` | no       | off     | Copy the bundled files into the user config directory.     |

Environment: `PKGDX_CONFIG_DIR`, as described in
[Behavior: user config directory](../behaviors/user-config.md).

## Data requirements

- The user config directory, resolved as the behavior spec defines.
- The four bundled standard files, which are always present in the installed package.

## Outputs

Without `--export`, standard output shows:

- the resolved user config directory;
- the environment variable that can override it;
- one row per recognised file, giving the file name, its source (`user` or `bundled`) and the
  resolved path.

Each row reflects the same selection the hooks make at the same moment, so a `user` row means the
hooks are using that file.

With `--export`, the per-file messages reporting whether each file was written or skipped go to
standard error, following the project's output convention.

- The user config directory is created when it does not exist.
- A bundled file is copied only when no file of that name exists in the user config directory.
- Existing files are never overwritten or modified.
- After a successful export, a plain run shows every exported file as `user`.

## Failure modes

- If `PKGDX_CONFIG_DIR` is set and does not name an existing directory, then the command shall
  exit with status 1 and write a single error message to standard error, without a traceback, with
  no table written. This applies with and without `--export`.

## Out of scope

- Editing the standard files. Users edit the exported copies with their own editor.
- Showing the contents of the files. The command reports where each file comes from, not what it
  contains.
- Validating the contents of user files. A malformed user file surfaces when the hook that reads it
  runs.
- Removing or resetting user files. Deleting a file restores the bundled behaviour for that file.
