"""Lightweight, dependency-free text analysis.

This module implements a small rule-based "AI" analyzer so the demo runs
completely offline, with no external model or API key required.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

POSITIVE_WORDS = {
    "good", "great", "excellent", "amazing", "awesome", "love", "loved",
    "wonderful", "fantastic", "happy", "nice", "best", "brilliant", "cool",
    "delightful", "perfect", "superb", "enjoy", "enjoyed", "like", "liked",
}

NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "horrible", "hate", "hated", "worst",
    "poor", "sad", "angry", "boring", "broken", "buggy", "slow", "ugly",
    "disappointing", "disappointed", "annoying", "useless", "wrong",
}

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "so", "of", "to",
    "in", "on", "for", "with", "at", "by", "from", "as", "is", "are", "was",
    "were", "be", "been", "being", "it", "this", "that", "these", "those",
    "i", "you", "he", "she", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "our", "their", "its", "do", "does", "did", "have", "has",
    "had", "not", "no", "yes", "can", "will", "would", "should", "could",
}

_WORD_RE = re.compile(r"[a-zA-Z']+")


@dataclass
class Analysis:
    """Result of analyzing a block of text."""

    text: str
    word_count: int
    char_count: int
    sentence_count: int
    sentiment: str
    sentiment_score: int
    keywords: list[str] = field(default_factory=list)
    reading_time_seconds: int = 0

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "word_count": self.word_count,
            "char_count": self.char_count,
            "sentence_count": self.sentence_count,
            "sentiment": self.sentiment,
            "sentiment_score": self.sentiment_score,
            "keywords": self.keywords,
            "reading_time_seconds": self.reading_time_seconds,
        }


def _tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in _WORD_RE.finditer(text)]


def _score_sentiment(tokens: list[str]) -> tuple[str, int]:
    score = 0
    for token in tokens:
        if token in POSITIVE_WORDS:
            score += 1
        elif token in NEGATIVE_WORDS:
            score -= 1
    if score > 0:
        label = "positive"
    elif score < 0:
        label = "negative"
    else:
        label = "neutral"
    return label, score


def _top_keywords(tokens: list[str], limit: int = 5) -> list[str]:
    meaningful = [t for t in tokens if t not in STOP_WORDS and len(t) > 2]
    counts = Counter(meaningful)
    return [word for word, _ in counts.most_common(limit)]


def analyze_text(text: str, keyword_limit: int = 5) -> Analysis:
    """Analyze ``text`` and return an :class:`Analysis`.

    Raises ``ValueError`` when the input contains no analyzable content.
    """
    if text is None or not text.strip():
        raise ValueError("text must not be empty")

    tokens = _tokenize(text)
    sentiment, score = _score_sentiment(tokens)
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    # Average adult reading speed ~200 words per minute.
    reading_time = round(len(tokens) / 200 * 60) if tokens else 0

    return Analysis(
        text=text,
        word_count=len(tokens),
        char_count=len(text),
        sentence_count=max(len(sentences), 1),
        sentiment=sentiment,
        sentiment_score=score,
        keywords=_top_keywords(tokens, keyword_limit),
        reading_time_seconds=reading_time,
    )
