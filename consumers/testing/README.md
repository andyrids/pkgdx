# Consuming Repository For `pytack`

This package is a workspace member for the main `pytack` project and is used to
test `pytack` setup logic in a consuming repository.

## Testing

>[!warning]
>The commands below should be run from the `pytack` root.

The `pytack/Justfile` contains a recipe for running pytack against the
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
uv run --directory consumers/testing pytack setup -v
```

To run a full reset and setup, add the `--reset` option:

```sh
uv run --directory consumers/testing pytack setup -v --reset
```

>[!tip]
>The pytack `--verbose` or `-v` or option enables verbose logging.
