from xdigest.filtering import ScoredPost
from xdigest.methodology import build_methodology
from xdigest.models import Author, Post


def _scored(text, pid, likes=100):
    post = Post(
        id=pid,
        author=Author(username=f"u{pid}", name="U"),
        text=text,
        created_at="2026-01-01T00:00:00Z",
        like_count=likes,
    )
    return ScoredPost(post=post, score=float(likes), relevance=1, matched_keywords=[])


def test_methodology_empty():
    md = build_methodology([])
    assert "No posts" in md


def test_methodology_detects_theme():
    posts = [
        _scored("writing is thinking and writing compounds over time", "1"),
        _scored("a weekly writing habit forces you to think clearly", "2"),
        _scored("focus on one thing and ship it", "3"),
    ]
    md = build_methodology(posts)
    assert "# Methodology" in md
    assert "writing" in md.lower()
    assert "Action plan" in md
    assert "Highlights" in md
