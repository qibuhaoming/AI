"""Core data models for xdigest."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Author:
    """The author of a post."""

    username: str
    name: str = ""

    @property
    def handle(self) -> str:
        return f"@{self.username}"


@dataclass
class Post:
    """A single post (tweet or long-form article) fetched from X."""

    id: str
    author: Author
    text: str
    created_at: str  # ISO-8601 timestamp
    url: str = ""
    like_count: int = 0
    retweet_count: int = 0
    reply_count: int = 0
    is_article: bool = False
    title: str | None = None
    tags: list[str] = field(default_factory=list)

    @property
    def engagement(self) -> int:
        """A simple engagement score used for ranking."""
        return self.like_count + 2 * self.retweet_count + self.reply_count

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "author": {"username": self.author.username, "name": self.author.name},
            "text": self.text,
            "created_at": self.created_at,
            "url": self.url,
            "like_count": self.like_count,
            "retweet_count": self.retweet_count,
            "reply_count": self.reply_count,
            "is_article": self.is_article,
            "title": self.title,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Post:
        author_data = data.get("author", {})
        author = Author(
            username=author_data.get("username", "unknown"),
            name=author_data.get("name", ""),
        )
        return cls(
            id=str(data["id"]),
            author=author,
            text=data.get("text", ""),
            created_at=data.get("created_at", ""),
            url=data.get("url", ""),
            like_count=int(data.get("like_count", 0)),
            retweet_count=int(data.get("retweet_count", 0)),
            reply_count=int(data.get("reply_count", 0)),
            is_article=bool(data.get("is_article", False)),
            title=data.get("title"),
            tags=list(data.get("tags", [])),
        )
