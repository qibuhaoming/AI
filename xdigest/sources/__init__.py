"""Post sources: where xdigest fetches posts from."""

from xdigest.sources.base import PostSource
from xdigest.sources.fixture import FixtureSource

__all__ = ["PostSource", "FixtureSource"]
