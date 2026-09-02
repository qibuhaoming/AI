"""Orchestrates the end-to-end digest pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from xdigest.filtering import InterestProfile, ScoredPost, select_interesting
from xdigest.markdown import write_digest
from xdigest.methodology import build_methodology
from xdigest.sources.base import PostSource


@dataclass
class PipelineResult:
    fetched: int
    selected: list[ScoredPost]
    index_path: Path
    post_paths: list[Path]
    methodology_path: Path


def run_pipeline(
    source: PostSource,
    profile: InterestProfile,
    out_dir: str | Path,
    *,
    fetch_limit: int = 100,
    select_limit: int = 20,
    lang: str = "auto",
) -> PipelineResult:
    """Fetch → filter → export Markdown → synthesize methodology.

    ``lang`` controls the output language: ``"auto"`` (default), ``"en"`` or
    ``"zh"``.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    posts = source.fetch_following_posts(limit=fetch_limit)
    selected = select_interesting(posts, profile, limit=select_limit)

    digest = write_digest(selected, out, lang=lang)

    methodology_md = build_methodology(selected, lang=lang)
    methodology_path = out / "methodology.md"
    methodology_path.write_text(methodology_md, encoding="utf-8")

    return PipelineResult(
        fetched=len(posts),
        selected=selected,
        index_path=digest["index"],
        post_paths=digest["posts"],
        methodology_path=methodology_path,
    )
