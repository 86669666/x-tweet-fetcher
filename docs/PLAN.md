# Plan

Single-stream work on `work/main`. One writer, this checkout. No live X/Twitter calls in tests.

## Done in this slice

- Upstream bodies over 10 MiB raise `upstream_down`. A body at or under the cap is unchanged. The oversized read is not retried.

## Next

- Strip trailing punctuation from URLs copied out of tweet text into the ledger, without changing URLs that already have no trailing mark.
- Do not add network fetches, session cookies, or an upstream pull request.

## Out of scope

Upstream `main`, release tags, production deploy, and any checkout outside this fork's `work/main`.
Abbreviated Nitter stat text (`12.3K`) stays out until a captured fixture uses it.
