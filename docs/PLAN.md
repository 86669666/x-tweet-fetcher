# Plan

Single-stream work on `work/main`. One writer, this checkout. No live X/Twitter calls in tests.

## Done in this slice

Local identity only. Happy-path JSON field names stay the same when an id is already present.

- Timeline, search, list, and reply records that omit `tweet_id` but carry a status URL (`url`, `tweet_url`, or `status_url`) use that id on both the fetch envelope and the ledger row.
- Explicit ids still win. `conversation_id`, links that only appear in the text, and lookalike hosts do not become the id.
- Captured Nitter pages in `tests/fixtures` do not use abbreviated stat text (`12.3K`), so that parser change stays out.

## Next

- Reject list and article ids that are embedded in a non-X host, the same way tweet URLs already reject lookalikes. Bare numeric ids stay valid.
- Clamp a negative fetch `--limit` the same way ledger query already does, so it is not a silent empty result.
- Do not add network fetches, session cookies, or an upstream pull request.

## Out of scope

Upstream `main`, release tags, production deploy, and any checkout outside this fork's `work/main`.
