---
topic: fastapi
source_name: FastAPI Dependencies
source_url: https://fastapi.tiangolo.com/tutorial/dependencies/
---

# FastAPI Dependencies

## What dependencies solve

FastAPI dependencies let you declare shared logic once and reuse it across path operations. They work well for cross-cutting concerns such as authentication, database sessions, query parsing, and permission checks.

## How FastAPI resolves dependencies

When a request reaches a path operation, FastAPI builds a dependency graph, resolves each dependency, and injects the returned values into the endpoint function. Sub-dependencies can depend on other dependencies, which makes the system composable instead of forcing all setup code into middleware or route handlers.

## When to choose dependencies over middleware

Dependencies are best when the logic needs typed inputs, return values, or per-route customization. Middleware is better for request and response processing that should wrap every request regardless of which endpoint is called.
