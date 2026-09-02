"""FastAPI application exposing the AI text-analysis assistant."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import __version__
from app.analyzer import analyze_text
from xdigest.filtering import InterestProfile, select_interesting
from xdigest.methodology import build_methodology
from xdigest.sources.fixture import FixtureSource

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="AI Text Assistant",
    version=__version__,
    description="A tiny, offline rule-based text-analysis service.",
)


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to analyze")
    keyword_limit: int = Field(5, ge=1, le=20)


class DigestRequest(BaseModel):
    interests: list[str] = Field(default_factory=list)
    min_engagement: int = Field(0, ge=0)
    select_limit: int = Field(20, ge=1, le=100)
    lang: str = Field("auto", pattern="^(auto|en|zh)$")
    url: str | None = Field(
        None, description="Optional X post URL to digest instead of the sample."
    )


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest) -> dict:
    try:
        result = analyze_text(req.text, keyword_limit=req.keyword_limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return result.to_dict()


@app.post("/api/digest")
def digest(req: DigestRequest) -> dict:
    """Run the xdigest pipeline.

    By default this uses the offline sample timeline (no credentials needed). If
    ``url`` is provided, that single public X post is fetched via the public
    syndication endpoint and digested instead.
    """
    if req.url:
        from xdigest.sources.x_syndication import SyndicationError, fetch_post

        try:
            posts = [fetch_post(req.url)]
        except SyndicationError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
    else:
        posts = FixtureSource().fetch_following_posts()
    profile = InterestProfile(
        keywords=req.interests,
        min_engagement=req.min_engagement,
    )
    selected = select_interesting(posts, profile, limit=req.select_limit)
    methodology_md = build_methodology(selected, lang=req.lang)

    return {
        "fetched": len(posts),
        "selected": [
            {
                "id": sp.post.id,
                "author": sp.post.author.handle,
                "name": sp.post.author.name,
                "text": sp.post.text,
                "title": sp.post.title,
                "is_article": sp.post.is_article,
                "engagement": sp.post.engagement,
                "score": round(sp.score, 1),
                "matched_keywords": sp.matched_keywords,
                "url": sp.post.url,
            }
            for sp in selected
        ],
        "methodology_markdown": methodology_md,
    }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/digest")
def digest_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "digest.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
