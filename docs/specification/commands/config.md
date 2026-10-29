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

Without `--export`, standard output holds only one row per recognised file: the file name, its
source (`user` or `bundled`) and the resolved path, as aligned columns with the path last. Standard
error then gets one closing line, naming the resolved user config directory, whether
`PKGDX_CONFIG_DIR` set it, and how many files are `user` and `bundled`.

Each row reflects the same selection the hooks make at the same moment, so a `user` row means the
hooks are using that file.

With `--export`, standard error gets one ledger line per file in the `pkgdx init` format (`created`,
or `unchanged` when a file of that name already exists), then a closing line. Nothing is written to
standard output.

- The user config directory is created when it does not exist.
- A bundled file is copied only when no file of that name exists in the user config directory.
- Existing files are never overwritten or modified.
- After a successful export, a plain run shows every exported file as `user`.

## Failure modes

- If `PKGDX_CONFIG_DIR` is set and does not name an existing directory, then the command shall
  exit with status 1 and write a single FAIL line, with its cause and a hint, to standard error,
  without a traceback, with no rows written. This applies with and without `--export`.
- If a file cannot be written during `--export`, then the command shall stop at that file and exit
  with status 1, without a traceback. Files already written are kept, and the remaining files are
  listed as not run. Running the export again is safe.

## Out of scope

- Editing the standard files. Users edit the exported copies with their own editor.
- Showing the contents of the files. The command reports where each file comes from, not what it
  contains.
- Validating the contents of user files. A malformed user file surfaces when the hook that reads it
  runs.
- Removing or resetting user files. Deleting a file restores the bundled behaviour for that file.
