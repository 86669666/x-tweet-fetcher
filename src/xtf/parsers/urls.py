"""URL / ID parsing helpers. Pure functions."""
from __future__ import annotations

import re
import urllib.parse

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


_X_HOST_RE = (
    r"(?<![A-Za-z0-9])(?:https?://)?"
    r"(?:(?:www|mobile|m)\.)?"
    r"(?:x\.com|twitter\.com)"
)
_LIST_URL_RE = re.compile(_X_HOST_RE + r"/i/lists/(?P<id>\d+)", re.IGNORECASE)
_ARTICLE_URL_RE = re.compile(
    _X_HOST_RE + r"/i/article/(?P<id>\d{10,25})",
    re.IGNORECASE,
)
_X_URL_HOSTS = frozenset({
    "x.com",
    "twitter.com",
    "www.x.com",
    "www.twitter.com",
    "mobile.x.com",
    "mobile.twitter.com",
    "m.x.com",
    "m.twitter.com",
})


def is_x_url(value: object) -> bool:
    """True when the URL host is X or Twitter.

    A lookalike such as ``notx.com``, or a page that only mentions ``x.com``
    in the query string, is not an X URL.
    """
    if not isinstance(value, str):
        return False
    text = value.strip()
    if not text:
        return False
    if "://" not in text:
        text = "https://" + text
    try:
        host = urllib.parse.urlparse(text).hostname
    except ValueError:
        return False
    if not host:
        return False
    return host.lower() in _X_URL_HOSTS


def extract_list_id(input_str: str) -> str | None:
    """Extract list ID from a bare id or an x.com / twitter.com list URL.

    Other hosts are rejected, including lookalikes that merely contain
    ``/i/lists/<id>``.
    """
    input_str = input_str.strip()
    if re.fullmatch(r"\d+", input_str):
        return input_str
    match = _LIST_URL_RE.search(input_str)
    if match:
        return match.group("id")
    return None


def parse_article_id(input_str: str) -> str | None:
    """Extract an article id from a bare id or an x.com / twitter.com article URL.

    Other hosts are rejected. A status URL is not an article URL; pass the
    article id itself in that case.
    """
    input_str = input_str.strip()
    if re.fullmatch(r"\d{10,25}", input_str):
        return input_str
    match = _ARTICLE_URL_RE.search(input_str)
    if match:
        return match.group("id")
    return None
