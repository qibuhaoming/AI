import httpx
import pytest

from xdigest.sources.x_api import MissingCredentialsError, XApiError, XApiSource


def test_requires_credentials(monkeypatch):
    monkeypatch.delenv("X_BEARER_TOKEN", raising=False)
    with pytest.raises(MissingCredentialsError):
        XApiSource()


def test_get_raises_xapierror_on_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"title": "Unauthorized"})

    source = XApiSource(token="dummy")
    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        with pytest.raises(XApiError) as excinfo:
            source._get(client, "/users/me")
    assert excinfo.value.status_code == 403
    assert "tier" in str(excinfo.value).lower()


def test_fetch_following_posts_end_to_end_mocked():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/users/me"):
            return httpx.Response(200, json={"data": {"id": "7"}})
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "42",
                        "author_id": "7",
                        "text": "hello",
                        "created_at": "2026-01-01T00:00:00Z",
                        "public_metrics": {
                            "like_count": 3,
                            "retweet_count": 1,
                            "reply_count": 0,
                        },
                    }
                ],
                "includes": {"users": [{"id": "7", "username": "alice", "name": "A"}]},
            },
        )

    source = XApiSource(token="dummy")
    transport = httpx.MockTransport(handler)
    # Patch httpx.Client so the source uses our mock transport.
    real_client = httpx.Client

    def client_factory(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    import xdigest.sources.x_api as mod

    mod.httpx.Client = client_factory
    try:
        posts = source.fetch_following_posts(limit=5)
    finally:
        mod.httpx.Client = real_client

    assert len(posts) == 1
    assert posts[0].author.username == "alice"
    assert posts[0].like_count == 3


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
