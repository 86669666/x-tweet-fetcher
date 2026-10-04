# Plan

Single-stream work on `work/main`. One writer, this checkout. No live X/Twitter calls in tests.

## Done in this slice

- FxTwitter fetch treats a non-object body, a null `tweet`, or a non-object `user` as a typed error. View supplementation skips that payload instead of raising.

## Next

- Quote Nitter HTTP path segments the same way the browser backend already does, so a slash or question mark in a username cannot change the request path.
- Abbreviated Nitter stat text (`12.3K`) stays out until a captured page actually uses it. Do not add a synthetic fixture for that.
- Do not add network fetches, session cookies, or an upstream pull request.

## Out of scope

Upstream `main`, release tags, production deploy, and any checkout outside this fork's `work/main`.
