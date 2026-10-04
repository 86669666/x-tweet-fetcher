# Plan

Single-stream work on `work/main`. One writer, this checkout. No live X/Twitter calls in tests.

## Done in this slice

- A negative `--limit` on fetch and ledger query is the documented default of 50. Explicit `0` still means no rows.

## Next

- Accept a leading `@` on `--user` and `--user-info`, matching `--monitor`, so `@alice` is not sent upstream as a different handle.
- Do not add network fetches, session cookies, or an upstream pull request.

## Out of scope

Upstream `main`, release tags, production deploy, and any checkout outside this fork's `work/main`.
Abbreviated Nitter stat text (`12.3K`) stays out until a captured fixture uses it.
