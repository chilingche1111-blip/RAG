---
topic: redis
source_name: Redis Persistence
source_url: https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/
---

# Redis Persistence

## RDB snapshotting

RDB creates point-in-time snapshots of the dataset. It is compact, fast to restore, and well-suited for backups or disaster recovery, but recent writes may be lost between snapshots if the server fails.

## AOF append-only file

AOF logs write operations so Redis can rebuild state by replaying them. Because writes are recorded more continuously, AOF can provide better durability than periodic snapshots, though the file may grow larger and recovery can be slower depending on configuration.

## Choosing between RDB and AOF

RDB is often preferred when restart speed and compact backups matter. AOF is preferred when reducing data loss matters more. Many deployments enable both so they can trade off restore speed and durability.
