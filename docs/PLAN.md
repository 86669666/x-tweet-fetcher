# Plan

Single-stream work on `work/main`. One writer, this checkout. No live X/Twitter calls in tests.

## Done in this slice

Local correctness only. Happy-path JSON field names stay the same.

- Browser pages use the configured Nitter base URL, scheme included.
- Nitter 404 is `not_found` and does not fail over.
- Tweet URL parsing accepts `/i/web/status/<id>` and common embed hosts, and rejects lookalike hosts.
- Monitor cache files cannot leave `XTF_CACHE_DIR`.
- FxTwitter `author: null` no longer crashes normalization.
- Ledger query no longer treats a negative limit as unlimited. Counting ids in a foreign database without a `tweets` table returns 0.

## Next

- Keep archive and fetch envelopes aligned when a backend omits `tweet_id` outside the single-tweet path.
- Add a pure fixture for Nitter abbreviated stat text (`12.3K`) only if a captured page actually uses it.
- Do not add network fetches, session cookies, or an upstream pull request.

## Out of scope

Upstream `main`, release tags, production deploy, and any checkout outside this fork's `work/main`.
