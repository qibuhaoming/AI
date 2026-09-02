"""Synthesize a methodology from a collection of interesting posts.

The default synthesizer is heuristic and fully offline: it clusters posts by
recurring themes (frequent keywords), then for each theme extracts the
highest-signal posts as evidence and drafts actionable practices.

An optional LLM-backed synthesizer can be enabled when an API key and network
egress are available; it is off by default so the pipeline stays testable
offline.
"""

from __future__ import annotations

from dataclasses import dataclass

from xdigest.filtering import ScoredPost
from xdigest.textutil import meaningful_tokens, top_keywords


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
    used_post_ids: set[str] = set()
    for keyword in keywords:
        members = [
            sp for sp in scored_posts if keyword in meaningful_tokens(sp.post.text)
        ]
        if len(members) < 2:
            continue
        members.sort(key=lambda sp: sp.post.engagement, reverse=True)
        themes.append(Theme(keyword=keyword, posts=members))
        used_post_ids.update(sp.post.id for sp in members)
        if len(themes) >= max_themes:
            break

    return themes


def _practice_for(theme: Theme) -> str:
    top = theme.posts[0].post
    return (
        f"Adopt the recurring idea around **{theme.keyword}**: "
        f"{top.author.handle} frames it well — treat it as a repeatable habit, "
        f"not a one-off. Schedule it, measure it, and review it weekly."
    )


def build_methodology(
    scored_posts: list[ScoredPost],
    *,
    title: str = "Methodology derived from your X digest",
) -> str:
    """Return a Markdown methodology document."""
    if not scored_posts:
        return (
            f"# {title}\n\n"
            "_No posts were selected, so no methodology could be derived._\n"
        )

    themes = _build_themes(scored_posts)

    lines: list[str] = [f"# {title}", ""]
    lines.append(
        f"Synthesized from **{len(scored_posts)} posts** across "
        f"**{len({sp.post.author.username for sp in scored_posts})} authors**."
    )
    lines.append("")

    lines.append("## Key themes")
    lines.append("")
    if themes:
        for theme in themes:
            lines.append(f"- **{theme.keyword}** ({len(theme.posts)} posts)")
    else:
        lines.append("- No repeated theme emerged; see the highlights below.")
    lines.append("")

    lines.append("## Principles & evidence")
    lines.append("")
    for i, theme in enumerate(themes, start=1):
        lines.append(f"### {i}. {theme.keyword.title()}")
        lines.append("")
        for sp in theme.posts[:2]:
            post = sp.post
            snippet = post.text.strip()
            lines.append(f"> {snippet}")
            lines.append(f"> — {post.author.handle}")
            lines.append("")
        lines.append(f"**Practice:** {_practice_for(theme)}")
        lines.append("")

    lines.append("## Action plan")
    lines.append("")
    steps = [
        "Pick the top 2 themes above and turn each into one weekly habit.",
        "Write a short weekly memo reflecting on what worked (writing is thinking).",
        "Ship the smallest end-to-end version of any new idea before polishing.",
        "Review engagement of your notes monthly and double down on what compounds.",
    ]
    for step in steps:
        lines.append(f"1. {step}")
    lines.append("")

    lines.append("## Highlights")
    lines.append("")
    top_posts = sorted(
        scored_posts, key=lambda sp: sp.post.engagement, reverse=True
    )[:3]
    for sp in top_posts:
        post = sp.post
        lines.append(
            f"- {post.author.handle}: {post.text.strip()[:120]} "
            f"({post.engagement} engagement)"
        )
    lines.append("")

    return "\n".join(lines)
