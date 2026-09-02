"""Select the posts a user is likely to find interesting.

A post's interest score combines two signals:

* **Relevance** — how well the post matches the user's declared interests
  (keyword matches in the text).
* **Engagement** — likes, retweets and replies, log-scaled so a few viral
  posts do not completely dominate.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from xdigest.models import Post


@dataclass
class InterestProfile:
    """What the user cares about and their minimum quality bar."""

    keywords: list[str] = field(default_factory=list)
    min_engagement: int = 0
    include_articles_always: bool = True

    def normalized_keywords(self) -> list[str]:
        return [k.strip().lower() for k in self.keywords if k.strip()]


@dataclass
class ScoredPost:
    post: Post
    score: float
    relevance: int
    matched_keywords: list[str]


def _has_cjk(value: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in value)


def _keyword_matches(text: str, keywords: list[str]) -> list[str]:
    lowered = text.lower()
    matched = []
    for keyword in keywords:
        # Chinese has no word boundaries, and phrases are matched as substrings;
        # single latin words use a word-boundary match to avoid false positives.
        if _has_cjk(keyword) or " " in keyword:
            if keyword in lowered:
                matched.append(keyword)
        elif re.search(rf"\b{re.escape(keyword)}\b", lowered):
            matched.append(keyword)
    return matched


def score_post(post: Post, profile: InterestProfile) -> ScoredPost:
    keywords = profile.normalized_keywords()
    matched = _keyword_matches(post.text, keywords)
    relevance = len(matched)

    engagement_score = math.log1p(max(post.engagement, 0))
    # Relevance is weighted heavily; engagement breaks ties and surfaces
    # high-signal posts even when keyword overlap is small.
    score = relevance * 10.0 + engagement_score
    if post.is_article:
        score += 2.0

    return ScoredPost(
        post=post,
        score=score,
        relevance=relevance,
        matched_keywords=matched,
    )


def select_interesting(
    posts: list[Post],
    profile: InterestProfile,
    limit: int = 20,
) -> list[ScoredPost]:
    """Return the most interesting posts, highest score first."""
    scored = [score_post(p, profile) for p in posts]

    keywords = profile.normalized_keywords()
    result = []
    for sp in scored:
        if sp.post.engagement < profile.min_engagement:
            if not (profile.include_articles_always and sp.post.is_article):
                continue
        # When interests are declared, drop posts with zero relevance unless
        # they are articles the user asked to always include.
        if keywords and sp.relevance == 0:
            if not (profile.include_articles_always and sp.post.is_article):
                continue
        result.append(sp)

    result.sort(key=lambda sp: sp.score, reverse=True)
    return result[:limit]
