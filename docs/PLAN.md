# Plan

Single-stream work on `work/main`. One writer, this checkout. No live X/Twitter calls in tests.

## Done in this slice

- Mentions cache load ignores a non-list `seen`, drops non-string entries, and does not treat a cache that already has URLs as a first run when `is_baseline` is missing.

## Next

- No further local slice is queued. Abbreviated Nitter stat text (`12.3K`) stays out until a captured page actually uses it. Do not add a synthetic fixture for that.
- Do not add network fetches, session cookies, or an upstream pull request.

## Out of scope

Upstream `main`, release tags, production deploy, and any checkout outside this fork's `work/main`.
