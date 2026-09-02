import pytest

from xdigest.sources.x_api import MissingCredentialsError, XApiSource


def test_requires_credentials(monkeypatch):
    monkeypatch.delenv("X_BEARER_TOKEN", raising=False)
    with pytest.raises(MissingCredentialsError):
        XApiSource()


def test_parse_timeline_maps_authors_and_metrics():
    payload = {
        "data": [
            {
                "id": "42",
                "author_id": "7",
                "text": "hello world",
                "created_at": "2026-01-01T00:00:00Z",
                "public_metrics": {
                    "like_count": 5,
                    "retweet_count": 2,
                    "reply_count": 1,
                },
            }
        ],
        "includes": {
            "users": [{"id": "7", "username": "alice", "name": "Alice"}]
        },
    }
    posts = XApiSource._parse_timeline(payload)
    assert len(posts) == 1
    post = posts[0]
    assert post.author.username == "alice"
    assert post.like_count == 5
    assert post.retweet_count == 2
    assert post.url == "https://x.com/alice/status/42"
