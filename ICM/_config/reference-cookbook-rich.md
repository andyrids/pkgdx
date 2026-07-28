---
context-hierarchy: Layer 3
context-hierarchy-role: Rules, conventions and guidelines
---

# Cookbook - `Rich`

## Progress Bars

The Progress class handles live-updating progress bars, supporting multiple tasks and custom
columns like spinners or text.

### Basic Example

```python
import time
from rich.progress import track

for i in track(range(20), description="Processing..."):
    time.sleep(1)  # Simulate work being done
```

### Advanced Example

```python
import time
from rich.progress import Progress

with Progress() as progress:
    task1 = progress.add_task("[red]Downloading...", total=1000)
    task2 = progress.add_task("[green]Processing...", total=1000)
    task3 = progress.add_task("[cyan]Cooking...", total=1000)

    while not progress.finished:
        progress.update(task1, advance=0.5)
        progress.update(task2, advance=0.3)
        progress.update(task3, advance=0.9)
        time.sleep(0.02)
```

### Persisting Per-Step Example

Unlike the concurrent example above, sequential CLI steps are better represented by adding a
*new* task per step rather than reusing a single task ID with `advance`. `Progress` keeps
finished task rows visible by default (`transient=False`), so each completed step's bar remains
on screen while the next step's bar is created below it.

```python
import time
from rich.progress import Progress

steps = ["Find project root", "Configure pre-commit hooks", "Install hooks"]

with Progress() as progress:
    for step in steps:
        task_id = progress.add_task(f"[cyan]{step}", total=1)
        # ... perform the step's work ...
        time.sleep(0.5)
        progress.update(task_id, completed=1, description=f"[green]{step}")
```

- Reusing one task ID and calling `advance=1` on it (e.g. a single 0-6 counter) produces a
  single row whose description changes — prior steps are NOT individually persisted.
- Adding one task per step and marking it `completed=<total>` when done persists a distinct,
  finished row per step instead.
- Combine with a shared `RichHandler` console (see below) when the CLI also logs during the same
  command.

## Sharing the Logging Console

Progress bars MUST share the same `Console` instance as the configured `RichHandler` (see
`reference-toolchain-logging.md`). When logging and progress consoles are not shared, log
messages break the live progress display.

```python
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress

handlers = [h for h in logger.handlers if isinstance(h, RichHandler)]
console = handlers[0].console if handlers else Console()
progress = Progress(console=console)
```
