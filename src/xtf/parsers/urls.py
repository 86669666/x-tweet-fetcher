"""URL / ID parsing helpers. Pure functions."""
from __future__ import annotations

import re

# Left boundary stops ``twitter.com`` matching inside lookalike hosts
# such as ``nottwitter.com``. Embed hosts are included because users paste
# fxtwitter / vxtwitter / fixupx / fixvx links.
_TWEET_URL_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:https?://)?"
    r"(?:(?:www|mobile|m)\.)?"
    r"(?:x\.com|twitter\.com|fxtwitter\.com|vxtwitter\.com|fixupx\.com|fixvx\.com)"
    r"/(?:i/web/status/(?P<web_id>\d+)|(?P<user>[A-Za-z0-9_]{1,15})/status/(?P<id>\d+))",
    re.IGNORECASE,
)


def parse_tweet_url(url: str) -> tuple:
    """Extract username and tweet_id from an X/Twitter or embed URL.

    ``/i/web/status/<id>`` carries no author. The username is returned as
    ``i`` so callers hit FxTwitter's username-less ``/i/status/<id>`` route.
    ``/i/status/<id>`` already parses as username ``i`` for the same reason.
    """
    match = _TWEET_URL_RE.search(url.strip())
    if not match:
        raise ValueError(f"Cannot parse tweet URL: {url}")
    tweet_id = match.group("web_id") or match.group("id")
    username = "i" if match.group("web_id") else match.group("user")
    if not username or not re.fullmatch(r"[A-Za-z0-9_]{1,15}", username):
        raise ValueError(f"Invalid username format: {username}")
    if not tweet_id or not tweet_id.isdigit():
        raise ValueError(f"Invalid tweet ID format: {tweet_id}")
    return username, tweet_id


def status_id_from_url(value: object) -> str | None:
    """Return a status id from an X/Twitter or embed URL, else None.

    Lookalike hosts are rejected. This does not scan free text; callers pass
    a dedicated URL field so a mentioned status is not treated as this item.
    """
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        _username, tweet_id = parse_tweet_url(text)
    except ValueError:
        return None
    return tweet_id


def resolve_tweet_id(record: dict) -> str:
    """Prefer an explicit id, otherwise a status URL stored on the record.

    ``conversation_id`` is intentionally not an id field. A URL that only
    appears in the tweet text is ignored.
    """
    for key in ("tweet_id", "id_str", "id"):
        value = record.get(key)
        if value not in (None, ""):
            return str(value)
    for key in ("url", "tweet_url", "status_url"):
        found = status_id_from_url(record.get(key))
        if found:
            return found
    return ""


def extract_list_id(input_str: str) -> str | None:
    """Extract list ID from a URL or raw ID string.

    Accepts:
      - Pure numeric ID:           "123456789"
      - List URL:                 "https://x.com/i/lists/123456789"
      - List URL (twitter.com):  "https://twitter.com/i/lists/123456789"
      - List URL (no scheme):    "x.com/i/lists/123456789"

    Returns the list ID string (digits only), or None if unparseable.
    """
    input_str = input_str.strip()

    # Pure numeric ID
    if re.match(r'^\d+$', input_str):
        return input_str

    # URL containing /i/lists/<id>
    m = re.search(r'/i/lists/(\d+)', input_str)
    if m:
        return m.group(1)

    return None

def parse_article_id(input_str: str) -> str | None:
    """Extract article ID from a URL or raw ID string.

    Accepts:
      - Pure numeric ID:           "2011779830157557760"
      - Article URL:               "https://x.com/i/article/2011779830157557760"
      - Article URL (no scheme):   "x.com/i/article/2011779830157557760"
      - Tweet URL whose text links to an article (pass the ID directly in that case)

    Returns the article ID string, or None if unparseable.
    """
    input_str = input_str.strip()

    # Pure numeric ID
    if re.match(r'^\d{10,25}$', input_str):
        return input_str

    # URL containing /i/article/<id>
    m = re.search(r'/i/article/(\d{10,25})', input_str)
    if m:
        return m.group(1)

    return None
