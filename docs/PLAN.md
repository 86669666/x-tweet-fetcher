# Plan

Single-stream work on `work/main`. One writer, this checkout. No live X/Twitter calls in tests.

## Done in this slice

URL identity only. Bare numeric list and article ids stay valid.

- `--list` and `--article` accept `x.com` and `twitter.com` (including www/mobile) and reject other hosts.
- Browser mention search keeps a result only when the host is X or Twitter. `notx.com` and `example.com/?q=x.com` are dropped.

## Next

- Clamp a negative fetch `--limit` the same way ledger query already does, so it is not a silent empty result.
- Do not add network fetches, session cookies, or an upstream pull request.

## Out of scope

Upstream `main`, release tags, production deploy, and any checkout outside this fork's `work/main`.
Abbreviated Nitter stat text (`12.3K`) stays out until a captured fixture uses it.
