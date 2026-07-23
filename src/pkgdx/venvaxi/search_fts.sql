-- search_fts.sql
SELECT nodes.* FROM symbols_fts
JOIN nodes ON nodes.rowid = symbols_fts.rowid
WHERE symbols_fts MATCH ?
LIMIT ?;