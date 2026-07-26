-- schema.sql
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS nodes (
    qualified_name TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    name TEXT NOT NULL,
    module TEXT NOT NULL,
    signature TEXT NOT NULL,
    doc TEXT NOT NULL,
    package TEXT NOT NULL,
    version TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS edges (
    src TEXT NOT NULL,
    dst TEXT NOT NULL,
    kind TEXT NOT NULL,
    PRIMARY KEY (src, dst, kind)
);

CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst);
CREATE INDEX IF NOT EXISTS idx_nodes_package ON nodes(package);