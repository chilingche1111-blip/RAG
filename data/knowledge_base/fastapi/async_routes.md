---
topic: fastapi
source_name: FastAPI Async
source_url: https://fastapi.tiangolo.com/async/
---

# FastAPI Async Routes

## Choosing async def

In FastAPI, `async def` is appropriate when the route handler awaits asynchronous operations such as network IO, async database drivers, or async SDK calls. This lets the server work on other requests while waiting for the IO to complete.

## Choosing def

If a route uses blocking libraries and does not await anything, a normal `def` can still be fine. FastAPI can run standard sync path operations without requiring the whole codebase to become asynchronous.

## Practical rule

The key question is not whether async looks modern, but whether the work inside the route actually benefits from non-blocking IO. CPU-heavy work still needs different treatment, such as background workers or process-level parallelism.
