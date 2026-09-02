"""Render selected posts into organized Markdown files."""

from __future__ import annotations

import re
from pathlib import Path

from xdigest.filtering import ScoredPost


def _slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "post"


def post_to_markdown(scored: ScoredPost) -> str:
    post = scored.post
    lines: list[str] = []
    heading = post.title or f"Post by {post.author.handle}"
    lines.append(f"# {heading}")
    lines.append("")
    lines.append(f"- **Author:** {post.author.name} ({post.author.handle})")
    lines.append(f"- **Date:** {post.created_at}")
    lines.append(
        "- **Engagement:** "
        f"{post.like_count} likes · {post.retweet_count} retweets · "
        f"{post.reply_count} replies"
    )
    if scored.matched_keywords:
        lines.append(f"- **Matched interests:** {', '.join(scored.matched_keywords)}")
    if post.url:
        lines.append(f"- **Link:** {post.url}")
    lines.append("")
    lines.append("> " + post.text.replace("\n", "\n> "))
    lines.append("")
    return "\n".join(lines)


def write_digest(
    scored_posts: list[ScoredPost],
    out_dir: str | Path,
) -> dict:
    """Write one Markdown file per post plus an ``index.md``.

    Returns a summary dict with the paths written.
    """
    out = Path(out_dir)
    posts_dir = out / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    index_lines = ["# Digest", "", f"{len(scored_posts)} interesting posts.", ""]

    for rank, scored in enumerate(scored_posts, start=1):
        post = scored.post
        filename = f"{rank:02d}-{post.author.username}-{_slugify(post.id)}.md"
        path = posts_dir / filename
        path.write_text(post_to_markdown(scored), encoding="utf-8")
        written.append(path)

        label = post.title or post.text[:70].strip()
        index_lines.append(
            f"{rank}. [{label}](posts/{filename}) — {post.author.handle} "
            f"(score {scored.score:.1f})"
        )

    index_path = out / "index.md"
    index_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    return {
        "index": index_path,
        "posts": written,
        "count": len(written),
    }
