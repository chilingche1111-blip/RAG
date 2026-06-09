---
topic: postgresql
source_name: PostgreSQL B-Tree Indexes
source_url: https://www.postgresql.org/docs/current/btree.html
---

# PostgreSQL B-Tree Indexes

## Why B-Tree is the default

PostgreSQL uses B-Tree indexes by default because they work well for common comparison operators such as less than, less than or equal, equal, greater than or equal, and greater than. They support exact lookups, range queries, and ordered scans on sortable data types.

## Query patterns

B-Tree indexes are a strong fit when a query filters or sorts by values that follow a clear ordering. That makes them useful for IDs, timestamps, and many business attributes used in filtering or pagination.

## Tradeoffs

Indexes speed up reads for matching patterns, but they add write cost because inserts, updates, and deletes must maintain the tree structure. That is why indexes should be designed around real query patterns instead of being added blindly.
