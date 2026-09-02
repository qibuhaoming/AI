"""Source interface shared by all post providers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from xdigest.models import Post


@runtime_checkable
class PostSource(Protocol):
    """A source that can return posts from the user's following timeline."""

    def fetch_following_posts(self, limit: int = 100) -> list[Post]:
        """Return up to ``limit`` recent posts from accounts the user follows."""
        ...
