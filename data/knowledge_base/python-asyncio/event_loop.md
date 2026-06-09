---
topic: python-asyncio
source_name: Python asyncio
source_url: https://docs.python.org/3/library/asyncio.html
---

# asyncio Event Loop

## Role of the event loop

The event loop is the core runtime that schedules coroutines, manages callbacks, and coordinates IO readiness. It allows many IO-bound operations to make progress without creating one operating system thread per task.

## What can go wrong

If code inside the event loop blocks for too long, other coroutines are delayed because the loop cannot switch work while blocked. That is why blocking calls should be avoided or delegated to executors when necessary.

## Suitable workload

asyncio works best for high-concurrency IO-bound applications such as web servers, clients, and orchestration services. It does not automatically speed up CPU-bound code.
