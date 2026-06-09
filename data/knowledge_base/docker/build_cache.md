---
topic: docker
source_name: Docker Build Cache
source_url: https://docs.docker.com/build/cache/
---

# Docker Build Cache

## Cache by layer

Docker builds images layer by layer. If a layer can reuse a previous cached result, the build skips recomputing that step, which can greatly reduce build time.

## Why later layers rebuild

When a layer changes, later layers often need rebuilding because they depend on the filesystem state produced earlier in the Dockerfile. This is why Dockerfile order matters for efficient builds.

## Practical optimization

Stable steps such as installing dependencies are often moved earlier, while frequently changing application code is copied later. That layout helps preserve cache hits for expensive setup steps across repeated builds.
