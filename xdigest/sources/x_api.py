"""X (Twitter) API v2 source.

Reads the authenticated user's reverse-chronological home timeline — i.e. posts
from the accounts they follow — using the official X API v2. This is the
ToS-compliant way to access following content; it requires an OAuth 2.0
user-context access token (not raw account credentials).

Required scopes: ``tweet.read``, ``users.read``, ``follows.read``.

The access token is read from the ``X_BEARER_TOKEN`` environment variable by
default, or can be passed explicitly.
"""

from __future__ import annotations

import os

import httpx

from xdigest.models import Author, Post

API_BASE = "https://api.twitter.com/2"


class MissingCredentialsError(RuntimeError):
    """Raised when no X access token is available."""


class XApiError(RuntimeError):
    """Raised when the X API returns an error response."""

    def __init__(self, status_code: int, path: str, body: str) -> None:
        self.status_code = status_code
        self.path = path
        self.body = body
        hint = ""
        if status_code in (401, 403):
            hint = (
                " — this usually means the token is invalid, lacks the required "
                "scopes (tweet.read, users.read, follows.read), is app-only "
                "instead of user-context, or your X API tier does not include "
                "home-timeline reads (Basic tier or higher is required)."
            )
        super().__init__(
            f"X API request to {path} failed with HTTP {status_code}{hint} "
            f"Response: {body[:400]}"
        )


class XApiSource:
    def __init__(
        self,
        token: str | None = None,
        *,
        base_url: str = API_BASE,
        timeout: float = 15.0,
    ) -> None:
        self.token = token or os.environ.get("X_BEARER_TOKEN")
        if not self.token:
            raise MissingCredentialsError(
                "No X access token found. Set the X_BEARER_TOKEN environment "
                "variable to an OAuth 2.0 user-context token with tweet.read, "
                "users.read and follows.read scopes."
            )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def _get(self, client: httpx.Client, path: str, params: dict | None = None) -> dict:
        response = client.get(
            f"{self.base_url}{path}", params=params, headers=self._headers()
        )
        if response.is_error:
            raise XApiError(response.status_code, path, response.text)
        return response.json()

    def fetch_following_posts(self, limit: int = 100) -> list[Post]:
        limit = max(1, min(limit, 100))
        with httpx.Client(timeout=self.timeout) as client:
            me = self._get(client, "/users/me")
            user_id = me["data"]["id"]

            params = {
                "max_results": limit,
                "tweet.fields": "created_at,public_metrics,author_id",
                "expansions": "author_id",
                "user.fields": "name,username",
            }
            payload = self._get(
                client,
                f"/users/{user_id}/timelines/reverse_chronological",
                params=params,
            )

        return self._parse_timeline(payload)

    @staticmethod
    def _parse_timeline(payload: dict) -> list[Post]:
        users = {
            u["id"]: Author(username=u["username"], name=u.get("name", ""))
            for u in payload.get("includes", {}).get("users", [])
        }
        posts: list[Post] = []
        for tweet in payload.get("data", []):
            metrics = tweet.get("public_metrics", {})
            author = users.get(
                tweet.get("author_id"), Author(username="unknown", name="")
            )
            posts.append(
                Post(
                    id=str(tweet["id"]),
                    author=author,
                    text=tweet.get("text", ""),
                    created_at=tweet.get("created_at", ""),
                    url=f"https://x.com/{author.username}/status/{tweet['id']}",
                    like_count=metrics.get("like_count", 0),
                    retweet_count=metrics.get("retweet_count", 0),
                    reply_count=metrics.get("reply_count", 0),
                )
            )
        return posts
