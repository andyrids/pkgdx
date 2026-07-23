-- search_fts.sql
SELECT nodes.* FROM symbols_fts
JOIN nodes ON nodes.qualified_name = symbols_fts.qualified_name
WHERE symbols_fts MATCH ?
LIMIT ?;