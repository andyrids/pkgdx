# Technical Specification: `venvaxi` Sub-Package Refactor

## 1. Summary

Code review of the `venvaxi` sub-package on the `develop` branch, focused on
`_store.py` (`SymbolStore`) and its integration with `_cache.py`,
`_introspect.py`, `_cli.py`, `_mcp.py`, `_ambient.py`, and the broader
`pytack` core. This spec catalogues bugs, design issues, and performance
problems with concrete refactoring steps.

---

## 2. Architecture Context

```text
venvaxi/
├── _store.py          SQLite graph store (nodes + edges + FTS5)
├── _cache.py          Version-keyed on-disk cache management
├── _introspect.py     Recursive inspect-based module walking
├── _cli.py            Argparse CLI with TOON output
├── _ambient.py        MCP config injection (AGENTS.md, .vscode/mcp.json)
├── _mcp.py            FastMCP server wrapping introspection functions
├── _packages.py       Dependency discovery via importlib.metadata
├── _toon.py           Token-Oriented Object Notation encoder
├── _toon_constants.py TOON format constants
├── schema.sql         Core nodes/edges DDL
├── schema_fts5.sql    FTS5 virtual table DDL
└── *.sql              Parameterized query files
```

**Data flow:**
CLI / MCP → `_introspect.py` walks modules → `_store.py` persists graph →
`_cache.py` manages invalidation → `_toon.py` encodes output.

---

## 3. Critical Issues

### 3.1 Per-Operation Commits — `_store.py` (Performance, P0)

**Lines:** 188, 200, 370

Every `upsert_node()` and `upsert_edge()` ends with
`self._connection.commit()`, forcing an `fsync` per operation. Introspecting a
medium package (e.g. `rich`, 500+ symbols) produces hundreds of commits —
approximately 10–20× slower than a single batched commit.

**Fix:** Remove per-operation commits. Add a `flush()` method. Call `flush()`
once in `_cache.get_or_build_store()` after the full walk completes. Retain the
commit in `clear_package()` since it is a standalone destructive operation.

### 3.2 Resource Leak on Schema Error — `_store.py` (P0)

**Lines:** 119–128

If `_ensure_schema()` raises (corrupt DB, permissions), the `sqlite3`
connection opened on line 125 is never closed — no `try/finally` guard.

**Fix:** Wrap `_ensure_schema()` in `try/except` inside `__init__`, close the
connection on failure, then re-raise.

### 3.3 Shell Redirect Bug — `_core.py` (P0)

**Location:** `_core.py`, detect-secrets baseline creation

`">"` is passed as a literal argument to `subprocess.run()` (no shell). The
redirect never executes. The `.secrets.baseline` file is silently never
created.

**Fix:** Capture `stdout` via `subprocess.run(..., capture_output=True)` and
write it to the file with `Path.write_bytes()`.

### 3.4 Partial-Build Cache Poisoning — `_cache.py` (P0)

**Lines:** 124–151

If `_walk_module()` raises a non-`DatabaseError` (e.g. `AttributeError`,
`TypeError`), the store is returned partially populated. The `PACKAGE` root
node was already upserted, so `is_cache_valid()` returns `True` on subsequent
calls — partial data is treated as valid indefinitely.

**Fix:** Catch all exceptions (not just `DatabaseError`), clear the package,
and re-raise.

---

## 4. High-Priority Issues

### 4.1 Missing Database Indexes — `schema.sql` (P1)

No index on `edges.dst` (needed by `get_inheritors()`). No index on
`nodes.package` (needed by `clear_package()`). Both require full table scans.

**Fix:** Add to `schema.sql`:

```sql
CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst);
CREATE INDEX IF NOT EXISTS idx_nodes_package ON nodes(package);
```

### 4.2 FTS5 Manual Sync — `_store.py` (P1)

**Lines:** 178–187

The FTS5 index is manually synced with explicit `DELETE` + `INSERT` after each
`upsert_node()`. If the upsert succeeds but the FTS operation fails, the index
diverges from the main table.

**Fix:** Use SQLite triggers in `schema_fts5.sql` to keep FTS5 in sync
automatically, or use FTS5 content-sync tables (`content=nodes`).

### 4.3 Bare `except Exception` — `_introspect.py` (P1)

**Line:** 282

`_walk_submodules()` catches `except Exception` on submodule import,
swallowing `SyntaxError`, `PermissionError`, `RuntimeError`, etc.

**Fix:** Narrow to `except (ImportError, ModuleNotFoundError, AttributeError)`.

---

## 5. Design Issues

### 5.1 `asdict()` Enum Serialization — `_mcp.py` (P2)

`dataclasses.asdict()` on `SymbolNode` serializes `kind` as a `NodeKind` enum
instance, not a plain string. `SymbolNode.as_row()` already exists and returns
`dict[str, str]` — use it instead.

### 5.2 No Schema Versioning — `_store.py` (P2)

No mechanism to detect or migrate stale database schemas. If the schema changes
in a release, existing cached databases silently use the old schema.

**Fix:** Use SQLite `PRAGMA user_version` to track schema version. On open,
compare and re-create if stale.

### 5.3 Non-Atomic File Writes — `_ambient.py` (P2)

`path.write_text(updated)` is not atomic. Process interruption mid-write
corrupts the file.

**Fix:** Write to a temporary file in the same directory, then
`os.replace()`.

### 5.4 Store Lifecycle Churn — `_introspect.py` (P2)

Every public function (`show_module`, `get_symbol`, `get_inheritors`, etc.)
opens a new SQLite connection, potentially rebuilds the store, then closes it.
The `SymbolStore` supports context management but it's never used.

**Fix:** Use `with _build_store_for(name) as store:` consistently.

---

## 6. Code Quality Issues

### 6.1 Debug `print()` in Production — `_core.py`

`print(type(repo), end="\n\n")` left in `get_repo_table()`. Delete it.

### 6.2 Inconsistent `NoReturn` Annotations — `_core.py`

All hook functions (`ruff_format`, `mypy_typing`, `detect_secrets`,
`pymarkdown_lint`) call `sys.exit()` unconditionally but are annotated
`-> None`. Only `ruff_lint` correctly uses `-> NoReturn`.

### 6.3 No Metadata Caching — `_packages.py`

`resolve_package()` calls `metadata.distribution()` per invocation (filesystem
lookup). Add `@lru_cache`.

### 6.4 Short Hash Truncation — `_cache.py`

`_project_hash()` truncates SHA-256 to 16 hex chars (64 bits). Use 32 chars
for negligible collision risk.

---

## 7. Test Coverage Gaps

| Area | Status | Gap |
|------|--------|-----|
| `_toon.py` encoding | ✅ Covered | — |
| `_store.py` CRUD | ✅ Covered | No batch/performance tests |
| `_cli.py` dispatch | ✅ Covered | — |
| `_cache.py` validation | ✅ Covered | No partial-build recovery tests |
| Error recovery | ❌ Missing | Corrupt DB, schema mismatch |
| Concurrency | ❌ Missing | Thread safety verification |
| `_mcp.py` tools | ❌ Missing | Only import-guard test exists |
| `_ambient.py` | ❌ Missing | No tests for config injection |
| `_introspect.py` edge cases | ❌ Missing | C extensions, circular imports |

---

## 8. Refactoring Phases

### Phase 1 — Critical Fixes

1. Remove per-operation commits from `_store.py`; add `flush()` method
2. Add `try/finally` resource cleanup in `SymbolStore.__init__`
3. Fix cache poisoning: catch all exceptions in `_cache.get_or_build_store()`
4. Fix shell redirect bug in `_core.py`
5. Remove debug `print()` from `_core.py`

### Phase 2 — Schema & Query Improvements

6. Add `idx_edges_dst` and `idx_nodes_package` indexes to `schema.sql`
7. Implement FTS5 content-sync or triggers instead of manual sync
8. Add schema versioning via `PRAGMA user_version`

### Phase 3 — API & Code Quality

9. Use `node.as_row()` instead of `asdict()` in `_mcp.py`
10. Narrow exception handling in `_introspect._walk_submodules()`
11. Use context managers consistently in `_introspect.py` public functions
12. Fix `NoReturn` annotations on hook functions in `_core.py`
13. Add `@lru_cache` to `_packages.resolve_package()`

### Phase 4 — Hardening & Testing

14. Add atomic file writes in `_ambient.py`
15. Increase hash length in `_cache._project_hash()` to 32 characters
16. Add batch/performance tests for `_store.py`
17. Add error recovery tests for corrupt databases and partial builds
18. Add MCP integration tests for `_mcp.py`
