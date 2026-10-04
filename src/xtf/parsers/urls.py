"""URL / ID parsing helpers. Pure functions."""
from __future__ import annotations

import re
import urllib.parse

# Hosts are taken from the parsed URL. Searching for the text ``x.com`` would
# accept lookalikes (``nottwitter.com``) and other hosts that only mention
# ``x.com`` in a path or query (``https://evil.example/x.com/...``).
_HOST_PREFIXES = ("", "www.", "mobile.", "m.")


def _with_prefixes(*roots: str) -> frozenset[str]:
    return frozenset(prefix + root for root in roots for prefix in _HOST_PREFIXES)


_X_URL_HOSTS = _with_prefixes("x.com", "twitter.com")
# Embed hosts are included because users paste fxtwitter / vxtwitter /
# fixupx / fixvx links. Lists and articles stay on X and Twitter only.
_TWEET_HOSTS = _X_URL_HOSTS | _with_prefixes(
    "fxtwitter.com", "vxtwitter.com", "fixupx.com", "fixvx.com",
)

_STATUS_PATH_RE = re.compile(
    r"^/(?:i/web/status/(?P<web_id>\d+)"
    r"|(?P<user>[A-Za-z0-9_]{1,15})/status/(?P<id>\d+))(?:/|$)",
    re.IGNORECASE,
)
_LIST_PATH_RE = re.compile(r"^/i/lists/(?P<id>\d+)(?:/|$)", re.IGNORECASE)
_ARTICLE_PATH_RE = re.compile(
    r"^/i/article/(?P<id>\d{10,25})(?:/|$)",
    re.IGNORECASE,
)


def _http_parts(value: str) -> tuple[str, str] | None:
    """Return ``(hostname, path)`` for a URL, else None.

    A missing scheme is treated as https so ``x.com/...`` still parses.
    The hostname is lowercased; the path is not.
    """
    text = value.strip()
    if not text:
        return None
    if "://" not in text:
        text = "https://" + text
    try:
        parsed = urllib.parse.urlparse(text)
    except ValueError:
        return None
    host = parsed.hostname
    if not host:
        return None
    return host.lower(), parsed.path or ""


def parse_tweet_url(url: str) -> tuple:
    """Extract username and tweet_id from an X/Twitter or embed URL.

    ``/i/web/status/<id>`` carries no author. The username is returned as
    ``i`` so callers hit FxTwitter's username-less ``/i/status/<id>`` route.
    ``/i/status/<id>`` already parses as username ``i`` for the same reason.

    The URL's own host must be X, Twitter, or an embed host. A status path
    buried in another host's path or query is not a tweet URL.
    """
    parts = _http_parts(url)
    match = _STATUS_PATH_RE.match(parts[1]) if parts and parts[0] in _TWEET_HOSTS else None
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

    Lookalike hosts are rejected, as is a status path that only appears
    inside another host. This does not scan free text; callers pass a
    dedicated URL field so a mentioned status is not treated as this item.
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


def is_x_url(value: object) -> bool:
    """True when the URL host is X or Twitter.

    A lookalike such as ``notx.com``, or a page that only mentions ``x.com``
    in the path or query string, is not an X URL.
    """
    if not isinstance(value, str):
        return False
    parts = _http_parts(value)
    if not parts:
        return False
    return parts[0] in _X_URL_HOSTS


def extract_list_id(input_str: str) -> str | None:
    """Extract list ID from a bare id or an x.com / twitter.com list URL.

    Other hosts are rejected, including lookalikes and pages that only
    contain ``/i/lists/<id>`` in a path or query.
    """
    input_str = input_str.strip()
    if re.fullmatch(r"\d+", input_str):
        return input_str
    parts = _http_parts(input_str)
    if not parts or parts[0] not in _X_URL_HOSTS:
        return None
    match = _LIST_PATH_RE.match(parts[1])
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
    parts = _http_parts(input_str)
    if not parts or parts[0] not in _X_URL_HOSTS:
        return None
    match = _ARTICLE_PATH_RE.match(parts[1])
    if match:
        return match.group("id")
    return None
