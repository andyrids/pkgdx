# Consuming Repository For `pkgdevx`

This package is a workspace member for the main `pkgdevx` project and is used to
test `pkgdevx` setup logic in a consuming repository.

## Testing

>[!warning]
>The commands below should be run from the `pkgdevx` root.

The `pkgdevx/Justfile` contains a recipe for running pkgdevx against the
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
uv run --directory consumers/testing pkgdevx -v setup
```

To run a full reset and setup, add the `--reset` option:

```sh
uv run --directory consumers/testing pkgdevx -v setup --reset
```

>[!tip]
>The pkgdevx `--verbose` or `-v` or option enables verbose logging.
