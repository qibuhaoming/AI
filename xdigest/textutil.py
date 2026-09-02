"""Small, dependency-free text helpers for theme extraction."""

from __future__ import annotations

import re
from collections import Counter

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "so", "of", "to",
    "in", "on", "for", "with", "at", "by", "from", "as", "is", "are", "was",
    "were", "be", "been", "being", "it", "this", "that", "these", "those",
    "i", "you", "he", "she", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "our", "their", "its", "do", "does", "did", "have", "has",
    "had", "not", "no", "yes", "can", "will", "would", "should", "could",
    "more", "than", "what", "who", "how", "why", "when", "where", "which",
    "just", "about", "into", "over", "out", "up", "down", "off", "one", "two",
    "there", "here", "now", "some", "any", "all", "each", "most", "much",
    "thing", "things", "get", "got", "make", "made", "makes", "want",
    "really", "even", "also", "like", "know", "many", "every", "own",
}

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z']+")


def tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in _WORD_RE.finditer(text)]


def meaningful_tokens(text: str) -> list[str]:
    return [t for t in tokenize(text) if t not in STOP_WORDS and len(t) > 2]


def top_keywords(text: str, limit: int = 8) -> list[tuple[str, int]]:
    counts = Counter(meaningful_tokens(text))
    return counts.most_common(limit)
