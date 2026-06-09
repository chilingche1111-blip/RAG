---
topic: python-asyncio
source_name: Python Coroutines and Tasks
source_url: https://docs.python.org/3/library/asyncio-task.html
---

# asyncio Tasks

## Await versus create_task

Using `await` pauses the current coroutine until the awaited operation finishes. `asyncio.create_task` schedules a coroutine to run concurrently as a task and immediately gives control back to the caller, so other work can continue before the result is awaited later.

## Why tasks matter

Tasks are useful when you need multiple asynchronous operations to make progress at the same time, such as calling several remote APIs or performing multiple IO steps concurrently. They are not a shortcut for CPU-bound parallelism.

## Structured concurrency

Modern asyncio also encourages structured concurrency patterns such as `TaskGroup`, which help ensure tasks are awaited and failures are surfaced in a controlled way instead of being silently lost.
