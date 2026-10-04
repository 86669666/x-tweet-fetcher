# Plan

Single-stream work on `work/main`. One writer, this checkout. No live X/Twitter calls in tests.

## Done in this slice

- Read-only ledger opens encode the path. A `?` in the database path no longer drops `mode=ro` or creates an empty sibling file.

## Next

- Reject upstream HTTP bodies larger than the existing 10 MiB cap instead of parsing a truncated payload as success.
- Do not add network fetches, session cookies, or an upstream pull request.

## Out of scope

Upstream `main`, release tags, production deploy, and any checkout outside this fork's `work/main`.
Abbreviated Nitter stat text (`12.3K`) stays out until a captured fixture uses it.
