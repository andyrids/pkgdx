-- search_like.sql
SELECT * FROM nodes
WHERE name LIKE ? OR qualified_name LIKE ?
ORDER BY qualified_name
LIMIT ?;