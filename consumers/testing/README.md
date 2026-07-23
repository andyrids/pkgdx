# Consuming Repository For `pkgdx`

This package is a workspace member for the main `pkgdx` project and is used to
test `pkgdx` setup logic in a consuming repository.

## Testing

>[!warning]
>The commands below should be run from the `pkgdx` root.

The `pkgdx/Justfile` contains a recipe for running pkgdx against the
`testing` package:

```sh
just test
```

To run a full reset and setup, add the `--reset` option:

```sh
just test --reset
```

This test could be run manually with the following command:

```sh
uv run --directory consumers/testing pkgdx setup -v
```

To run a full reset and setup, add the `--reset` option:

```sh
uv run --directory consumers/testing pkgdx setup -v --reset
```

>[!tip]
>The pkgdx `--verbose` or `-v` or option enables verbose logging.
