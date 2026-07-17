---
context-hierarchy: Layer 3
---

# Toolchain - `Mypy`

Mypy is used to enforce standards for typing.

## Configuration

The Mypy config is located at `src/pytack/standards/mypy.ini`. Enforce the usage of the type hints
for all function/method args and return values.

```ini
disallow_untyped_defs = true
```

Protect developers from falsely trusting that dependencies are typed correctly.

```ini
disallow_any_unimported = true
```

When something is imported from a dependency, it's resolved to `Any` if Mypy can't resolve the import.

- Missing stubs can sometimes be found at [typeshed/stubs](https://github.com/python/typeshed/tree/main/stubs)
- A type ignore (`# type: ignore[no-any-unimported]`) can be used when stubs are unavailable

```python
from requests import Request

def my_function(request: Request) -> None:  # type: ignore[no-any-unimported]
    ...
```

Explicit is better than implicit - `arg: Optional[str] = None` over `arg: str = None`.

```ini
no_implicit_optional = true
```

Check body of a function/method.

```ini
check_untyped_defs = true
```

Check for Any return when declared return type is different.

```ini
warn_return_any = true
```

It is better to ignore only the specific type of an error. Prefer `# type: ignore[<error-code>]`
over `# type: ignore`.

```ini
show_error_codes = true
warn_unused_ignores = true
```
