"""Lightweight, dependency-free text analysis.

This module implements a small rule-based "AI" analyzer so the demo runs
completely offline, with no external model or API key required. It supports
both English and Chinese text (Chinese is segmented via ``jieba`` when
available, see :mod:`xdigest.textutil`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from xdigest.textutil import meaningful_tokens, tokenize

POSITIVE_WORDS = {
    # English
    "good", "great", "excellent", "amazing", "awesome", "love", "loved",
    "wonderful", "fantastic", "happy", "nice", "best", "brilliant", "cool",
    "delightful", "perfect", "superb", "enjoy", "enjoyed", "like", "liked",
    # Chinese
    "喜欢", "爱", "棒", "优秀", "完美", "赞", "厉害", "精彩", "出色",
    "满意", "开心", "快乐", "推荐", "高效", "强大", "喜爱", "好评",
}

NEGATIVE_WORDS = {
    # English
    "bad", "terrible", "awful", "horrible", "hate", "hated", "worst",
    "poor", "sad", "angry", "boring", "broken", "buggy", "slow", "ugly",
    "disappointing", "disappointed", "annoying", "useless", "wrong",
    # Chinese
    "糟糕", "讨厌", "失望", "无聊", "崩溃", "错误", "垃圾", "难受",
    "烂", "问题", "差劲", "痛苦", "麻烦", "差评",
}

# Chinese sentence terminators in addition to the latin ones.
_SENTENCE_RE = re.compile(r"[.!?。！？;；]+")


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


def _top_keywords(text: str, limit: int = 5) -> list[str]:
    from collections import Counter

    counts = Counter(meaningful_tokens(text))
    return [word for word, _ in counts.most_common(limit)]


def analyze_text(text: str, keyword_limit: int = 5) -> Analysis:
    """Analyze ``text`` and return an :class:`Analysis`.

    Raises ``ValueError`` when the input contains no analyzable content.
    """
    if text is None or not text.strip():
        raise ValueError("text must not be empty")

    tokens = tokenize(text)
    sentiment, score = _score_sentiment(tokens)
    sentences = [s for s in _SENTENCE_RE.split(text) if s.strip()]
    # Average adult reading speed ~200 words per minute.
    reading_time = round(len(tokens) / 200 * 60) if tokens else 0

    return Analysis(
        text=text,
        word_count=len(tokens),
        char_count=len(text),
        sentence_count=max(len(sentences), 1),
        sentiment=sentiment,
        sentiment_score=score,
        keywords=_top_keywords(text, keyword_limit),
        reading_time_seconds=reading_time,
    )
