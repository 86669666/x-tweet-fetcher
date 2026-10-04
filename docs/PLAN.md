# Plan

Single-stream work on `work/main`. One writer, this checkout. No live X/Twitter calls in tests.

## Done in this slice

- `--user @alice` and `--user-info @alice` are fetched as `alice`. A lone `@` is not turned into an empty handle.

## Next

- Percent-encode read-only SQLite URIs. A `?` in the ledger path is parsed as the URI query, so query/stats can open the wrong file and even create an empty sibling.
- Do not add network fetches, session cookies, or an upstream pull request.

## Out of scope

Upstream `main`, release tags, production deploy, and any checkout outside this fork's `work/main`.
Abbreviated Nitter stat text (`12.3K`) stays out until a captured fixture uses it.
