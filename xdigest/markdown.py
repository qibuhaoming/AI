"""Render selected posts into organized Markdown files (localized)."""

from __future__ import annotations

import re
from pathlib import Path

from xdigest.filtering import ScoredPost
from xdigest.textutil import detect_lang

_STRINGS = {
    "en": {
        "post_by": "Post by {handle}",
        "author": "Author",
        "date": "Date",
        "engagement": "Engagement",
        "eng_value": "{likes} likes · {rts} retweets · {replies} replies",
        "matched": "Matched interests",
        "link": "Link",
        "digest_h": "# Digest",
        "digest_count": "{n} interesting posts.",
        "score": "score {score:.1f}",
    },
    "zh": {
        "post_by": "{handle} 的帖子",
        "author": "作者",
        "date": "日期",
        "engagement": "互动",
        "eng_value": "{likes} 赞 · {rts} 转发 · {replies} 回复",
        "matched": "命中兴趣",
        "link": "链接",
        "digest_h": "# 摘要",
        "digest_count": "共 {n} 条感兴趣的帖子。",
        "score": "评分 {score:.1f}",
    },
}


def _slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "post"


def post_to_markdown(scored: ScoredPost, lang: str = "en") -> str:
    s = _STRINGS.get(lang, _STRINGS["en"])
    post = scored.post
    lines: list[str] = []
    heading = post.title or s["post_by"].format(handle=post.author.handle)
    lines.append(f"# {heading}")
    lines.append("")
    lines.append(f"- **{s['author']}:** {post.author.name} ({post.author.handle})")
    lines.append(f"- **{s['date']}:** {post.created_at}")
    lines.append(
        f"- **{s['engagement']}:** "
        + s["eng_value"].format(
            likes=post.like_count, rts=post.retweet_count, replies=post.reply_count
        )
    )
    if scored.matched_keywords:
        lines.append(f"- **{s['matched']}:** {', '.join(scored.matched_keywords)}")
    if post.url:
        lines.append(f"- **{s['link']}:** {post.url}")
    lines.append("")
    lines.append("> " + post.text.replace("\n", "\n> "))
    lines.append("")
    return "\n".join(lines)


def _resolve_lang(scored_posts: list[ScoredPost], lang: str) -> str:
    if lang in ("en", "zh"):
        return lang
    corpus = " ".join(sp.post.text for sp in scored_posts)
    return detect_lang(corpus)


def write_digest(
    scored_posts: list[ScoredPost],
    out_dir: str | Path,
    lang: str = "auto",
) -> dict:
    """Write one Markdown file per post plus an ``index.md`` (localized)."""
    resolved = _resolve_lang(scored_posts, lang)
    s = _STRINGS[resolved]

    out = Path(out_dir)
    posts_dir = out / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    index_lines = [s["digest_h"], "", s["digest_count"].format(n=len(scored_posts)), ""]

    for rank, scored in enumerate(scored_posts, start=1):
        post = scored.post
        filename = f"{rank:02d}-{post.author.username}-{_slugify(post.id)}.md"
        path = posts_dir / filename
        path.write_text(post_to_markdown(scored, resolved), encoding="utf-8")
        written.append(path)

        label = post.title or post.text[:70].strip()
        score_txt = s["score"].format(score=scored.score)
        index_lines.append(
            f"{rank}. [{label}](posts/{filename}) — {post.author.handle} ({score_txt})"
        )

    index_path = out / "index.md"
    index_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    return {"index": index_path, "posts": written, "count": len(written)}
