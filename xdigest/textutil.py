"""Small text helpers for tokenization and theme extraction.

Supports both English (whitespace/latin words) and Chinese (CJK). Chinese is
segmented with ``jieba`` when available, falling back to character bigrams so
the module still works without the dependency.
"""

from __future__ import annotations

import re
from collections import Counter

try:  # Optional dependency; a bigram fallback keeps things working without it.
    import logging

    import jieba

    jieba.setLogLevel(logging.ERROR)

    def _segment_cjk(run: str) -> list[str]:
        return [w for w in jieba.cut(run) if w.strip()]

    HAS_JIEBA = True
except Exception:  # pragma: no cover - exercised only when jieba is absent
    def _segment_cjk(run: str) -> list[str]:
        if len(run) < 2:
            return [run]
        return [run[i : i + 2] for i in range(len(run) - 1)]

    HAS_JIEBA = False


STOP_WORDS = {
    # English
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
    # Chinese
    "的", "了", "和", "是", "我", "你", "他", "她", "它", "我们", "你们",
    "他们", "这", "那", "在", "有", "就", "不", "也", "都", "要", "与", "及",
    "等", "把", "被", "让", "给", "会", "能", "可以", "一个", "一", "很",
    "更", "最", "吗", "呢", "吧", "啊", "什么", "怎么", "为什么", "如何",
    "然后", "而且", "但是", "因为", "所以", "如果", "对", "从", "到", "中",
    "上", "下", "里", "个", "之", "其", "或", "由", "并", "得", "着", "过",
    "已", "还", "再", "又", "为", "以", "使", "这个", "那个", "自己", "没有",
    "而", "则", "且", "非", "只", "才", "去", "来", "说", "做", "用",
}

_LATIN_RE = re.compile(r"[a-zA-Z][a-zA-Z']*")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")


def _is_cjk(token: str) -> bool:
    return bool(token) and "\u4e00" <= token[0] <= "\u9fff"


def tokenize(text: str) -> list[str]:
    """Tokenize mixed English/Chinese text into lowercase tokens."""
    tokens = [m.group(0).lower() for m in _LATIN_RE.finditer(text)]
    for run in _CJK_RE.findall(text):
        tokens.extend(_segment_cjk(run))
    return tokens


def meaningful_tokens(text: str) -> list[str]:
    """Tokens worth counting: drop stop words and too-short latin tokens."""
    out: list[str] = []
    for token in tokenize(text):
        if token in STOP_WORDS:
            continue
        if _is_cjk(token):
            if len(token) >= 2:  # keep 2+ character Chinese words
                out.append(token)
        elif len(token) > 2:
            out.append(token)
    return out


def top_keywords(text: str, limit: int = 8) -> list[tuple[str, int]]:
    counts = Counter(meaningful_tokens(text))
    return counts.most_common(limit)


def cjk_ratio(text: str) -> float:
    """Fraction of non-space characters that are CJK."""
    chars = [c for c in text if not c.isspace()]
    if not chars:
        return 0.0
    cjk = sum(1 for c in chars if "\u4e00" <= c <= "\u9fff")
    return cjk / len(chars)


def detect_lang(text: str, *, threshold: float = 0.2) -> str:
    """Return ``"zh"`` when the text is CJK-heavy, otherwise ``"en"``."""
    return "zh" if cjk_ratio(text) >= threshold else "en"

