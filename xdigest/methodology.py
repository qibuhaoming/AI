"""Synthesize a methodology from a collection of interesting posts.

The default synthesizer is heuristic and fully offline: it clusters posts by
recurring themes (frequent keywords), then for each theme extracts the
highest-signal posts as evidence and drafts actionable practices.

Output is localized to English or Chinese; ``lang="auto"`` picks the language
from the selected posts. An optional LLM-backed synthesizer can be added behind
an API key; it is off by default so the pipeline stays testable offline.
"""

from __future__ import annotations

from dataclasses import dataclass

from xdigest.filtering import ScoredPost
from xdigest.textutil import detect_lang, meaningful_tokens, top_keywords

_STRINGS = {
    "en": {
        "title": "Methodology derived from your X digest",
        "empty": "_No posts were selected, so no methodology could be derived._",
        "synth": "Synthesized from **{posts} posts** across **{authors} authors**.",
        "themes_h": "## Key themes",
        "theme_item": "- **{kw}** ({n} posts)",
        "no_theme": "- No repeated theme emerged; see the highlights below.",
        "principles_h": "## Principles & evidence",
        "practice": (
            "**Practice:** Adopt the recurring idea around **{kw}**: {who} frames "
            "it well — treat it as a repeatable habit, not a one-off. Schedule it, "
            "measure it, and review it weekly."
        ),
        "action_h": "## Action plan",
        "steps": [
            "Pick the top 2 themes above and turn each into one weekly habit.",
            "Write a short weekly memo on what worked (writing is thinking).",
            "Ship the smallest end-to-end version of a new idea before polishing.",
            "Review your notes' engagement monthly and double down on what compounds.",
        ],
        "highlights_h": "## Highlights",
        "highlight_item": "- {who}: {text} ({eng} engagement)",
    },
    "zh": {
        "title": "根据你的 X 摘要提炼的方法论",
        "empty": "_没有选中任何帖子，无法生成方法论。_",
        "synth": "综合了 **{posts} 条帖子**，来自 **{authors} 位作者**。",
        "themes_h": "## 关键主题",
        "theme_item": "- **{kw}**（{n} 条）",
        "no_theme": "- 没有出现反复的主题；请见下方亮点。",
        "principles_h": "## 原则与依据",
        "practice": (
            "**实践建议：** 把围绕 **{kw}** 的做法固定成习惯：{who} 讲得很好——"
            "排进日程、可度量、每周复盘。"
        ),
        "action_h": "## 行动计划",
        "steps": [
            "从上面选出最重要的 2 个主题，各自变成一个每周习惯。",
            "每周写一篇简短复盘，记录哪些做法有效（写作即思考）。",
            "任何新想法先做最小可用的端到端版本，再打磨。",
            "每月回顾笔记的反馈，加大对能产生复利的内容的投入。",
        ],
        "highlights_h": "## 亮点",
        "highlight_item": "- {who}：{text}（{eng} 互动）",
    },
}


@dataclass
class Theme:
    keyword: str
    posts: list[ScoredPost]

    @property
    def weight(self) -> int:
        return sum(sp.post.engagement for sp in self.posts)


def _build_themes(scored_posts: list[ScoredPost], max_themes: int = 5) -> list[Theme]:
    corpus = " ".join(sp.post.text for sp in scored_posts)
    keywords = [kw for kw, count in top_keywords(corpus, limit=20) if count >= 2]

    themes: list[Theme] = []
    for keyword in keywords:
        members = [
            sp for sp in scored_posts if keyword in meaningful_tokens(sp.post.text)
        ]
        if len(members) < 2:
            continue
        members.sort(key=lambda sp: sp.post.engagement, reverse=True)
        themes.append(Theme(keyword=keyword, posts=members))
        if len(themes) >= max_themes:
            break

    return themes


def _resolve_lang(scored_posts: list[ScoredPost], lang: str) -> str:
    if lang in ("en", "zh"):
        return lang
    corpus = " ".join(sp.post.text for sp in scored_posts)
    return detect_lang(corpus)


def build_methodology(
    scored_posts: list[ScoredPost],
    *,
    lang: str = "auto",
    title: str | None = None,
) -> str:
    """Return a Markdown methodology document, localized to ``lang``."""
    resolved = _resolve_lang(scored_posts, lang)
    s = _STRINGS[resolved]
    doc_title = title or s["title"]

    if not scored_posts:
        return f"# {doc_title}\n\n{s['empty']}\n"

    themes = _build_themes(scored_posts)
    authors = len({sp.post.author.username for sp in scored_posts})

    lines: list[str] = [f"# {doc_title}", ""]
    lines.append(s["synth"].format(posts=len(scored_posts), authors=authors))
    lines.append("")

    lines.append(s["themes_h"])
    lines.append("")
    if themes:
        for theme in themes:
            lines.append(s["theme_item"].format(kw=theme.keyword, n=len(theme.posts)))
    else:
        lines.append(s["no_theme"])
    lines.append("")

    lines.append(s["principles_h"])
    lines.append("")
    for i, theme in enumerate(themes, start=1):
        lines.append(f"### {i}. {theme.keyword}")
        lines.append("")
        for sp in theme.posts[:2]:
            lines.append(f"> {sp.post.text.strip()}")
            lines.append(f"> — {sp.post.author.handle}")
            lines.append("")
        who = theme.posts[0].post.author.handle
        lines.append(s["practice"].format(kw=theme.keyword, who=who))
        lines.append("")

    lines.append(s["action_h"])
    lines.append("")
    for step in s["steps"]:
        lines.append(f"1. {step}")
    lines.append("")

    lines.append(s["highlights_h"])
    lines.append("")
    top_posts = sorted(
        scored_posts, key=lambda sp: sp.post.engagement, reverse=True
    )[:3]
    for sp in top_posts:
        post = sp.post
        lines.append(
            s["highlight_item"].format(
                who=post.author.handle,
                text=post.text.strip()[:120],
                eng=post.engagement,
            )
        )
    lines.append("")

    return "\n".join(lines)
