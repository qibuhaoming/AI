"""A fixture-backed source used for offline development, testing, and demos.

It reads posts from a JSON file so the full pipeline can run end-to-end
without X API credentials or network access.
"""

from __future__ import annotations

import json
from pathlib import Path

from xdigest.models import Post

_PKG_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FIXTURE = _PKG_ROOT / "data" / "sample_timeline.json"


class FixtureSource:
    """Load posts from a local JSON fixture."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_FIXTURE

    def fetch_following_posts(self, limit: int = 100) -> list[Post]:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        posts = [Post.from_dict(item) for item in raw]
        return posts[:limit]
