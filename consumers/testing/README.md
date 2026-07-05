# Consuming Repository For `pkgdev`

This package is a workspace member for the main `pkgdev` project and is used to
test `pkgdev` setup logic in a consuming repository.

## Testing

>[!warning]
>The commands below should be run from the `pkgdev` root.

The `pkgdev/Justfile` contains a recipe for running pkgdev against the
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
uv run --directory consumers/testing pkgdev -v setup
```

To run a full reset and setup, add the `--reset` option:

```sh
uv run --directory consumers/testing pkgdev -v setup --reset
```

>[!tip]
>The pkgdev `--verbose` or `-v` or option enables verbose logging.
