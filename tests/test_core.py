"""Tests for router fallback logic, models, HTTP retry, and monitor cache."""
import json

import pytest

from xtf.backends.base import Backend
from xtf.exceptions import (
    AllBackendsFailed,
    BackendUnavailable,
    NotFound,
    NotSupported,
    RateLimited,
    UpstreamDown,
)
from xtf.models import Reply, Tweet
from xtf.router import Router


# ── models ────────────────────────────────────────────────────────────────
def test_tweet_to_dict_omits_empty_optionals():
    d = Tweet(author="@a", author_name="A", text="hi").to_dict()
    assert "media" not in d and "retweeted_by" not in d and "quoted_tweet" not in d
    assert d["likes"] == 0


def test_tweet_roundtrip_from_snapshot():
    entry = {
        "author": "@a", "author_name": "A", "text": "t", "time_ago": "3h",
        "likes": 1, "retweets": 2, "replies": 3, "views": 4,
        "tweet_id": "9", "media": ["u"], "retweeted_by": "B",
        "quoted_tweet": {"author": "@q", "text": "qt"},
    }
    d = Tweet.from_snapshot_entry(entry).to_dict()
    assert d["retweeted_by"] == "B"
    assert d["quoted_tweet"]["author"] == "@q"
    assert d["media"] == ["u"]


def test_tweet_from_nitter_entry_normalizes_handle():
    tw = Tweet.from_nitter_entry({"username": "alice", "display_name": "Alice",
                                  "text": "x", "time": "3h", "likes": 5,
                                  "media_urls": ["m1"]})
    assert tw.author == "@alice"
    assert tw.time_ago == "3h"
    assert tw.media == ["m1"]


def test_nitter_entry_id_comes_from_status_url():
    tw = Tweet.from_nitter_entry({
        "username": "alice",
        "display_name": "Alice",
        "text": "from the permalink",
        "time": "1h",
        "views": 1,
        "url": "https://x.com/alice/status/555#m",
    })
    assert tw.tweet_id == "555"
    assert tw.to_dict()["tweet_id"] == "555"
    # An explicit id wins, and a lookalike host does not invent one.
    kept = Tweet.from_nitter_entry({
        "username": "alice", "text": "x", "tweet_id": "1",
        "url": "https://x.com/alice/status/555",
    })
    assert kept.tweet_id == "1"
    rejected = Tweet.from_nitter_entry({
        "username": "alice", "text": "x",
        "url": "https://nottwitter.com/alice/status/99",
    })
    assert rejected.tweet_id == ""


def test_snapshot_reply_id_comes_from_status_url():
    reply = Reply.from_snapshot_entry({
        "author": "@bob", "author_name": "Bob", "text": "reply",
        "url": "https://fxtwitter.com/bob/status/777",
    })
    assert reply.to_dict()["tweet_id"] == "777"


def test_reply_to_dict_v1_shape():
    d = Reply(author="@a", author_name="A", text="t", time_ago="1h",
              likes=1, replies=0, views=2).to_dict()
    # v1 reply envelope always has these keys
    for key in ("author", "author_name", "text", "time_ago", "likes", "replies", "views"):
        assert key in d
    assert "retweets" not in d  # omitted when zero, matching v1


# ── router fallback ───────────────────────────────────────────────────────
class _Failing(Backend):
    name = "failing"

    def __init__(self, exc):
        self._exc = exc

    def available(self):
        return True

    def fetch_timeline(self, username, limit=20):
        raise self._exc


class _Working(Backend):
    name = "working"

    def available(self):
        return True

    def fetch_timeline(self, username, limit=20):
        return [Tweet(author="@ok", author_name="OK", text="served")]


def _router_with_chain(*backends):
    r = Router(backend="auto")
    r._chain = lambda: list(backends)  # type: ignore
    return r


@pytest.mark.parametrize("exc", [
    NotSupported("nope"), BackendUnavailable("down"),
    RateLimited("429"), UpstreamDown("503"),
])
def test_router_falls_through_on_transient(exc):
    r = _router_with_chain(_Failing(exc), _Working())
    tweets = r.fetch_timeline("alice")
    assert tweets[0].text == "served"
    assert r.last_backend == "working"


def test_router_all_failed_carries_causes():
    r = _router_with_chain(_Failing(RateLimited("429 a")), _Failing(UpstreamDown("503 b")))
    with pytest.raises(AllBackendsFailed) as ei:
        r.fetch_timeline("alice")
    causes = ei.value.causes
    assert set(causes) == {"failing"} or len(causes) >= 1
    assert ei.value.to_dict()["code"] == "all_backends_failed"


def test_router_mode_chains():
    r = Router(backend="nitter")
    assert [b.name for b in r._chain()] == ["nitter"]
    r = Router(backend="browser")
    assert [b.name for b in r._chain()] == ["browser"]
    r = Router(backend="auto")
    assert [b.name for b in r._chain()] == ["nitter", "browser"]


# ── http retry ────────────────────────────────────────────────────────────
def test_http_get_text_retries_then_raises(monkeypatch):
    import urllib.error

    from xtf import http

    calls = {"n": 0}

    def fake_urlopen(req, timeout=0):
        calls["n"] += 1
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(http.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(http.time, "sleep", lambda s: None)

    with pytest.raises(UpstreamDown):
        http.get_text("http://127.0.0.1:1/x", retries=2)
    assert calls["n"] == 3  # 1 initial + 2 retries


def test_http_404_no_retry(monkeypatch):
    import urllib.error

    from xtf import http
    from xtf.exceptions import NotFound

    calls = {"n": 0}

    def fake_urlopen(req, timeout=0):
        calls["n"] += 1
        raise urllib.error.HTTPError("u", 404, "nf", {}, None)

    monkeypatch.setattr(http.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(NotFound):
        http.get_text("http://x/y", retries=3)
    assert calls["n"] == 1


# ── config ────────────────────────────────────────────────────────────────
def test_nitter_instances_env(monkeypatch):
    from xtf import config
    monkeypatch.setenv("XTF_NITTER", "nitter.example.com, http://127.0.0.1:8788,")
    insts = config.nitter_instances()
    assert insts == ["https://nitter.example.com", "http://127.0.0.1:8788"]


def test_nitter_instances_default(monkeypatch):
    from xtf import config
    monkeypatch.delenv("XTF_NITTER", raising=False)
    monkeypatch.delenv("NITTER_URL", raising=False)
    assert config.nitter_instances() == [config.DEFAULT_NITTER]


# ── monitor cache ─────────────────────────────────────────────────────────
def test_monitor_baseline_then_increment(tmp_path, monkeypatch):
    monkeypatch.setenv("XTF_CACHE_DIR", str(tmp_path))

    from xtf import monitor

    class FakeBrowser:
        port = 9377

        def available(self):
            return True

        def search_mentions(self, username, limit=10):
            return self._results

    class FakeRouter:
        browser = FakeBrowser()
        nitter = None

    router = FakeRouter()
    router.browser._results = [
        {"url": "https://x.com/a/status/1", "title": "t1", "snippet": ""},
    ]

    # First run: baseline, nothing reported
    r1 = monitor.monitor_mentions(router, "@alice", use_nitter=False)
    assert r1["is_baseline"] is True
    assert r1["new_mentions"] == []

    # Second run with one new URL: only the new one reported
    router.browser._results = [
        {"url": "https://x.com/a/status/1", "title": "t1", "snippet": ""},
        {"url": "https://x.com/b/status/2", "title": "t2", "snippet": ""},
    ]
    r2 = monitor.monitor_mentions(router, "@alice", use_nitter=False)
    assert r2["is_baseline"] is False
    assert [m["url"] for m in r2["new_mentions"]] == ["https://x.com/b/status/2"]

    # Cache file uses v2 dict format
    cache_file = tmp_path / "mentions-cache-alice.json"
    data = json.loads(cache_file.read_text())
    assert set(data["seen"]) == {"https://x.com/a/status/1", "https://x.com/b/status/2"}


def test_monitor_legacy_list_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("XTF_CACHE_DIR", str(tmp_path))
    from xtf import monitor

    # v1 stored a bare list — must be read as non-baseline
    (tmp_path / "mentions-cache-bob.json").write_text('["https://x.com/x/status/9"]')
    cache = monitor._load_cache("@Bob")
    assert cache["is_baseline"] is False
    assert cache["seen"] == ["https://x.com/x/status/9"]


def test_search_mentions_rejects_lookalike_hosts():
    from xtf.backends.browser import BrowserBackend

    backend = BrowserBackend(nitter_instance="http://127.0.0.1:9")

    class _Drv:
        def camofox_search(self, query, num=10, port=0):
            return [
                {"url": "https://x.com/alice/status/1", "title": "ok", "snippet": ""},
                {"url": "https://twitter.com/bob", "title": "ok", "snippet": ""},
                {"url": "https://notx.com/alice/status/1", "title": "bad", "snippet": ""},
                {"url": "https://example.com/?q=x.com", "title": "bad", "snippet": ""},
                {"url": "https://x.com.evil.com/alice", "title": "bad", "snippet": ""},
            ]

    backend._drv = _Drv()
    urls = [item["url"] for item in backend.search_mentions("alice")]
    assert urls == ["https://x.com/alice/status/1", "https://twitter.com/bob"]


def test_browser_preserves_nitter_scheme(monkeypatch):
    monkeypatch.setenv("XTF_NITTER", "http://127.0.0.1:8788")
    monkeypatch.delenv("NITTER_URL", raising=False)
    from xtf.backends.browser import BrowserBackend

    local = BrowserBackend()
    assert local.nitter_base == "http://127.0.0.1:8788"
    assert local._page_url("alice", "status", "20") == "http://127.0.0.1:8788/alice/status/20"
    assert local._page_url("i", "lists", "99") == "http://127.0.0.1:8788/i/lists/99"

    remote = BrowserBackend(nitter_instance="nitter.example")
    assert remote._page_url("bob") == "https://nitter.example/bob"

    explicit = BrowserBackend(nitter_instance="https://nitter.example/base/")
    assert explicit.nitter_base == "https://nitter.example/base"
    assert explicit._page_url("a b") == "https://nitter.example/base/a%20b"


def test_nitter_not_found_does_not_failover(monkeypatch):
    from xtf.backends import nitter as nitter_mod

    calls = []

    def fake_get_text(url, headers=None, timeout=15, retries=2):
        calls.append(url)
        raise NotFound(f"HTTP 404 — {url}")

    monkeypatch.setattr(nitter_mod.http, "probe", lambda url, timeout=3: False)
    monkeypatch.setattr(nitter_mod.http, "get_text", fake_get_text)
    backend = nitter_mod.NitterBackend(
        instances=["http://one.example", "http://two.example"]
    )
    with pytest.raises(NotFound):
        backend._get_html("/alice")
    assert calls == ["http://one.example/alice"]


def test_nitter_failsover_on_upstream_down(monkeypatch):
    from xtf.backends import nitter as nitter_mod

    calls = []

    def fake_get_text(url, headers=None, timeout=15, retries=2):
        calls.append(url)
        if url.startswith("http://dead.example"):
            raise UpstreamDown(f"down {url}")
        return "<html>ok</html>"

    monkeypatch.setattr(nitter_mod.http, "probe", lambda url, timeout=3: False)
    monkeypatch.setattr(nitter_mod.http, "get_text", fake_get_text)
    backend = nitter_mod.NitterBackend(
        instances=["http://dead.example", "http://ok.example"]
    )
    assert backend._get_html("/alice") == "<html>ok</html>"
    assert calls == ["http://dead.example/alice", "http://ok.example/alice"]
    assert backend._live == "http://ok.example"


def test_monitor_cache_cannot_escape_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("XTF_CACHE_DIR", str(tmp_path))
    from xtf import monitor

    path = monitor._get_cache_path("../../etc/passwd")
    assert path.parent == tmp_path
    assert ".." not in path.name
    assert "/" not in path.name

    monitor._save_cache("../../etc/passwd", {"seen": ["https://x.com/a/status/1"], "is_baseline": False})
    written = list(tmp_path.iterdir())
    assert len(written) == 1
    assert written[0].parent == tmp_path
    loaded = monitor._load_cache("../../etc/passwd")
    assert loaded["seen"] == ["https://x.com/a/status/1"]



def test_nitter_replies_use_status_url_id(monkeypatch):
    from xtf.backends.nitter import NitterBackend

    backend = NitterBackend(instances=["http://127.0.0.1:9"])
    monkeypatch.setattr(backend, "_get_html", lambda path: "<html></html>")
    monkeypatch.setattr(
        "xtf.backends.nitter.parse_tweet_detail_html",
        lambda html, username, tweet_id: {
            "replies_list": [{
                "username": "bob",
                "display_name": "Bob",
                "text": "reply body",
                "time": "2h",
                "likes": 1,
                "views": 1,
                "url": "https://x.com/bob/status/777",
                "tweet_id": "",
            }]
        },
    )
    replies = backend.fetch_replies("alice", "1")
    assert replies[0].to_dict()["tweet_id"] == "777"
