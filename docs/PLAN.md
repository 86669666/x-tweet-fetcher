# Plan

Single-stream work on `work/main`. One writer, this checkout. No live X/Twitter calls in tests.

## Done in this slice

- Nitter HTTP paths percent-encode each username and status id, matching the browser backend. A slash or question mark in those values cannot retarget the request.

## Next

- `--monitor` still does not use the same leading-`@` / surrounding-space strip as `--user`.
- Abbreviated Nitter stat text (`12.3K`) stays out until a captured page actually uses it. Do not add a synthetic fixture for that.
- Do not add network fetches, session cookies, or an upstream pull request.

## Out of scope

Upstream `main`, release tags, production deploy, and any checkout outside this fork's `work/main`.
