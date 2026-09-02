"""Fetch a single public X post by URL/ID via the public syndication endpoint.

This uses ``cdn.syndication.twimg.com`` — the same no-auth endpoint X's own
embedded-tweet widgets use — so it needs no API token. It is handy for demoing
the pipeline on a specific link. The authenticated following-timeline feature
still uses the X API v2 (:mod:`xdigest.sources.x_api`).

X **Articles** (long-form posts) carry their headline in ``article.title`` and
a summary in ``article.preview_text`` while the tweet ``text`` is just a link;
this module folds the article title/preview into the post so keyword matching
and the digest work on the real content.
"""

from __future__ import annotations

import math
import re

import httpx

from xdigest.models import Author, Post

SYNDICATION_URL = "https://cdn.syndication.twimg.com/tweet-result"
_STATUS_RE = re.compile(r"(?:status(?:es)?/)(\d+)")
_ID_RE = re.compile(r"^\d+$")


class SyndicationError(RuntimeError):
    """Raised when a post cannot be fetched or parsed from syndication."""


def extract_tweet_id(url_or_id: str) -> str:
    value = url_or_id.strip()
    if _ID_RE.match(value):
        return value
    m = _STATUS_RE.search(value)
    if not m:
        raise SyndicationError(f"Could not find a tweet id in: {url_or_id!r}")
    return m.group(1)


def _syndication_token(tweet_id: str) -> str:
    """Replicate the token X's embed widgets derive from the tweet id."""
    # (id / 1e15 * pi) rendered in base-36, with zeros and the dot stripped.
    value = (int(tweet_id) / 1e15) * math.pi
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    intpart = int(value)
    frac = value - intpart

    if intpart == 0:
        ip = "0"
    else:
        ip = ""
        n = intpart
        while n > 0:
            ip = digits[n % 36] + ip
            n //= 36

    fp = ""
    count = 0
    while frac > 1e-12 and count < 24:
        frac *= 36
        d = int(frac)
        fp += digits[d]
        frac -= d
        count += 1

    return re.sub(r"(0+|\.)", "", f"{ip}.{fp}") or "0"


def parse_syndication(payload: dict, tweet_id: str | None = None) -> Post:
    user = payload.get("user", {})
    author = Author(
        username=user.get("screen_name", "unknown"),
        name=user.get("name", ""),
    )
    tid = str(payload.get("id_str") or tweet_id or "")

    article = payload.get("article")
    is_article = isinstance(article, dict)
    if is_article:
        title = article.get("title")
        preview = article.get("preview_text", "")
        # Fold the headline + preview into the searchable text.
        text = f"{title}\n\n{preview}".strip() if title else preview
    else:
        title = None
        text = payload.get("text", "")

    return Post(
        id=tid,
        author=author,
        text=text,
        created_at=payload.get("created_at", ""),
        url=f"https://x.com/{author.username}/status/{tid}",
        like_count=int(payload.get("favorite_count", 0) or 0),
        retweet_count=int(payload.get("retweet_count", 0) or 0),
        reply_count=int(payload.get("conversation_count", 0) or 0),
        is_article=is_article,
        title=title,
    )


def fetch_post(url_or_id: str, *, timeout: float = 15.0) -> Post:
    tweet_id = extract_tweet_id(url_or_id)
    params = {
        "id": tweet_id,
        "lang": "en",
        "token": _syndication_token(tweet_id),
    }
    headers = {"User-Agent": "Mozilla/5.0 (compatible; xdigest/0.1)"}
    with httpx.Client(timeout=timeout, headers=headers) as client:
        response = client.get(SYNDICATION_URL, params=params)
    if response.is_error:
        raise SyndicationError(
            f"Syndication request for tweet {tweet_id} failed with HTTP "
            f"{response.status_code}."
        )
    try:
        payload = response.json()
    except ValueError as exc:  # pragma: no cover - defensive
        raise SyndicationError("Syndication response was not valid JSON.") from exc
    if not payload or "__typename" not in payload:
        raise SyndicationError(
            f"Tweet {tweet_id} not found or not public via syndication."
        )
    return parse_syndication(payload, tweet_id)


class XSyndicationSource:
    """A source backed by one or more explicit X post URLs/IDs."""

    def __init__(self, urls: list[str]) -> None:
        self.urls = urls

    def fetch_following_posts(self, limit: int = 100) -> list[Post]:
        posts = []
        for url in self.urls[:limit]:
            posts.append(fetch_post(url))
        return posts
